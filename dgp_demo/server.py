"""Loopback-only demo HTTP server. Use a hardened app server/auth layer for deployment."""
from __future__ import annotations
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import secrets
import urllib.parse
from .contracts import ROOT, Problem, VERSION
from .engine import Engine, GRAPH, SERVICES

MAX_BODY=512*1024

def strict_json(raw: bytes) -> dict:
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise ValueError('Duplicate JSON key')
            d[k]=v
        return d
    data=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))
    if not isinstance(data,dict): raise ValueError('Expected a JSON object')
    return data

def handler_class(engine: Engine, tokens: dict[str,tuple[str,str]]):
    class Handler(BaseHTTPRequestHandler):
        server_version='ThreadDesk/0.1'
        def log_message(self,fmt,*args): pass  # Do not leak tokens or untrusted messages to logs.

        def _send(self,status: int,data,ctype='application/json'):
            raw=json.dumps(data,ensure_ascii=False,allow_nan=False).encode() if ctype in ('application/json','application/problem+json') else data
            self.send_response(status)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers(); self.wfile.write(raw)

        def _boundary(self):
            host=self.headers.get('Host','')
            expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            if host not in expected: raise Problem('UNTRUSTED_HOST','Unexpected Host header.',403)
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://{x}' for x in expected}:
                raise Problem('UNTRUSTED_ORIGIN','Cross-origin access is not enabled.',403)

        def _actor(self):
            supplied=self.headers.get('Authorization','')
            if not supplied.startswith('Bearer '): raise Problem('UNAUTHENTICATED','Bearer token required.',401)
            candidate=supplied[7:]
            for token,principal in tokens.items():
                if hmac.compare_digest(candidate,token): return principal
            raise Problem('UNAUTHENTICATED','Invalid bearer token.',401)

        def _dispatch(self,method):
            self._boundary()
            parts=urllib.parse.urlsplit(self.path)
            path=parts.path
            if method=='GET' and path in ('/','/app.js','/style.css'):
                name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path]
                ctype={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[path]
                return self._send(200,(ROOT/'web'/name).read_bytes(),ctype)
            if method=='GET' and path=='/.well-known/dgp': return self._send(200,engine.manifest())
            actor,role=self._actor()
            if method=='GET':
                if path=='/dgp/surfaces': return self._send(200,engine.surfaces())
                if path=='/dgp/services': return self._send(200,{'dgp':VERSION,'services':SERVICES})
                if path=='/dgp/graphs': return self._send(200,{'dgp':VERSION,'graphs':[{'graph_id':'thread-recovery','href':'/dgp/graphs/thread-recovery'}]})
                if path=='/dgp/graphs/thread-recovery': return self._send(200,GRAPH)
                if path=='/dgp/bulletin': return self._send(200,engine.bulletin())
                if path=='/dgp/schema': return self._send(200,json.loads((ROOT/'schemas/dgp.schema.json').read_text()))
                seg=path.strip('/').split('/')
                if len(seg)==4 and seg[:2]==['dgp','surfaces'] and seg[-1]=='frame':
                    q=urllib.parse.parse_qs(parts.query)
                    try: horizon=int(q.get('horizon',['2'])[0])
                    except ValueError: raise Problem('INVALID_HORIZON','horizon must be an integer.',422)
                    return self._send(200,engine.frame(urllib.parse.unquote(seg[2]),q.get('disclosure',['next'])[0],horizon))
                if len(seg)==3 and seg[0]=='dgp' and seg[1] in ('frames','assessments','receipts'):
                    return self._send(200,engine.record(seg[1],urllib.parse.unquote(seg[2])))
                if len(seg)==4 and seg[:2]==['dgp','blobs']:
                    mime,data=engine.blob(seg[2],seg[3]); return self._send(200,data,mime)
            elif method=='POST':
                if self.headers.get('Transfer-Encoding'): raise Problem('INVALID_TRANSFER','Chunked request bodies are not supported.',400)
                if self.headers.get_content_type()!='application/json': raise Problem('UNSUPPORTED_MEDIA_TYPE','Use application/json.',415)
                try: size=int(self.headers.get('Content-Length','0'))
                except ValueError: raise Problem('INVALID_LENGTH','Invalid Content-Length.',400)
                if not 0<size<=MAX_BODY: raise Problem('PAYLOAD_TOO_LARGE','Body must be 1..524288 bytes.',413)
                try: data=strict_json(self.rfile.read(size))
                except (ValueError,UnicodeDecodeError): raise Problem('INVALID_JSON','Malformed JSON, duplicate key, or non-finite number.',400)
                if path=='/dgp/assessments': return self._send(200,engine.assess(data,actor))
                if path=='/dgp/commits': return self._send(200,engine.commit(data,actor,role,self.headers.get('Idempotency-Key','')))
            raise Problem('NOT_FOUND','Unknown route.',404)

        def _handle(self,method):
            try: self._dispatch(method)
            except Problem as e: self._send(e.status,e.as_dict(),'application/problem+json')
            except (BrokenPipeError,ConnectionResetError): pass
            except Exception:
                self._send(500,Problem('INTERNAL_ERROR','Unexpected demo server error.',500).as_dict(),'application/problem+json')
        def do_GET(self): self._handle('GET')
        def do_POST(self): self._handle('POST')
    return Handler

def make_server(engine: Engine, tokens: dict[str,tuple[str,str]], port: int=8765):
    return ThreadingHTTPServer(('127.0.0.1',port),handler_class(engine,tokens))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--db',default='threaddesk.sqlite3')
    a=p.parse_args()
    agent=os.getenv('DGP_AGENT_TOKEN') or secrets.token_urlsafe(32)
    human=os.getenv('DGP_HUMAN_TOKEN') or secrets.token_urlsafe(32)
    if agent==human: p.error('Agent and human tokens must differ.')
    e=Engine(a.db)
    s=make_server(e,{agent:('agent-local','agent'),human:('human-local','human')},a.port)
    print(f'ThreadDesk demo: http://127.0.0.1:{s.server_port}',flush=True)
    print(f'Agent token: {agent}\nHuman token (paste in UI): {human}',flush=True)
    print('Local simulation only. No real CI/Git/mail operations. Ctrl-C to stop.',flush=True)
    try: s.serve_forever()
    except KeyboardInterrupt: pass
    finally: s.server_close();e.close()

if __name__=='__main__': main()
