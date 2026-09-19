"""Jev-first DGP client. `mock` is explicit; live providers are never auto-enabled."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import threading
import urllib.parse
import uuid
from .contracts import Problem, VERSION, now, validate_result
from .providers import JsonHTTP, JevResolver, MockResolver, MockAssistant, OpenAIAssistant

class Client:
    def __init__(self, base: str, token: str, http: JsonHTTP | None = None):
        self.base=base.rstrip('/')
        p=urllib.parse.urlsplit(self.base)
        if p.scheme!='https' and not (p.scheme=='http' and p.hostname in ('127.0.0.1','localhost','::1')):
            raise Problem('UNSAFE_TRANSPORT','Only HTTPS or HTTP loopback is allowed.')
        if p.username or p.password or p.query or p.fragment:
            raise Problem('UNSAFE_TRANSPORT','Base URL must not contain userinfo, query, or fragment.')
        self.origin=(p.scheme,p.hostname,p.port)
        self.token=token
        self.http=http or JsonHTTP()

    def call(self, path: str, data: dict | None = None, key: str | None = None) -> dict:
        url=urllib.parse.urljoin(self.base+'/',path)
        p=urllib.parse.urlsplit(url)
        if (p.scheme,p.hostname,p.port)!=self.origin:
            raise Problem('UNTRUSTED_LINK','DGP links must remain on the configured origin.')
        return self.http.request(url,token=self.token,data=data,headers={'Idempotency-Key':key} if key else None)

class Runner:
    def __init__(self, client: Client, resolver, assistant, *, trace: str | None = None,
                 max_service_calls: int = 2, speculative: bool = False):
        self.client,self.resolver,self.assistant=client,resolver,assistant
        self.trace=Path(trace) if trace else None
        self.lock=threading.Lock()
        self.max_service_calls=max_service_calls
        self.service_calls=0
        self.speculative=speculative

    def record(self, item: dict) -> None:
        item={'at':now(),**item}
        line=json.dumps(item,ensure_ascii=False)
        with self.lock:
            if self.trace:
                with self.trace.open('a',encoding='utf-8') as f: f.write(line+'\n')
            print(line,flush=True)

    def step(self, sid: str) -> bool:
        frame=self.client.call(f'/dgp/surfaces/{urllib.parse.quote(sid,safe="")}/frame')
        supported={'core@0.1','graph-preview@0.1','speculative-assessment@0.1','service-input@0.1','image-evidence@0.1','judgment-rubrics@0.1'}
        unknown=set(frame.get('required_features',[]))-supported
        if unknown:
            raise Problem('CAPABILITY_REQUIRED','Unsupported frame features: '+', '.join(sorted(unknown)),406)
        decision=next((d for d in frame['decisions'] if d['dispatch']=='automatic'),None)
        if decision is None:
            self.record({'surface':sid,'event':'quiescent'}); return False
        if decision['kind']=='input':
            if self.speculative:
                self.record({'surface':sid,'event':'stopped','reason':'Speculative demo mode only assesses choices; it does not purchase generation.'}); return False
            if 'fulfillment' not in decision:
                self.record({'surface':sid,'event':'input_required'}); return False
            with self.lock:
                if self.service_calls>=self.max_service_calls:
                    raise Problem('CLIENT_BUDGET_EXHAUSTED','Local service-call limit reached.',409)
                self.service_calls+=1
            # A fulfillment node follows an explicit Jev-selected service request.
            text,resolver=self.assistant.fulfill(frame,decision)
            result={'status':'answered','answer':{'value':{decision['fulfillment']['output_field']:text}}}
        else:
            result,resolver=self.resolver.resolve(frame,decision)
        validate_result(decision,result)
        assessment={'dgp':VERSION,'assessment_id':'a-'+uuid.uuid4().hex,'frame_id':frame['frame_id'],
                    'decision_id':decision['decision_id'],'mode':'speculative' if self.speculative else 'live',
                    'resolver':resolver,'result':result}
        self.client.call('/dgp/assessments',assessment)
        self.record({'surface':sid,'event':'assessed','assessment':assessment})
        if self.speculative or result['status']=='abstain': return False
        # Human-only options are a stop, even when model confidence is high.
        answer=result['answer']
        chosen=next((o for o in decision.get('options',[]) if o['id']==answer.get('choice')),None)
        if chosen and chosen['effect']['required_actor']=='human':
            self.record({'surface':sid,'event':'human_review_required','frame_id':frame['frame_id'],'assessment_id':assessment['assessment_id']})
            return False
        commit={'dgp':VERSION,'frame_id':frame['frame_id'],'decision_id':decision['decision_id'],
                'assessment_id':assessment['assessment_id']}
        key='k-'+uuid.uuid4().hex
        # Persist intent before network I/O. After an uncertain response, reuse this key and exact body.
        self.record({'surface':sid,'event':'commit_intent','idempotency_key':key,'request':commit})
        receipt=self.client.call('/dgp/commits',commit,key)
        self.record({'surface':sid,'event':'committed','receipt':receipt})
        return True

    def run_surface(self, sid: str, steps: int) -> None:
        for _ in range(steps):
            try:
                if not self.step(sid): return
            except Problem as e:
                self.record({'surface':sid,'event':'stopped','problem':e.as_dict()}); return
        self.record({'surface':sid,'event':'step_budget_reached'})

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',default='http://127.0.0.1:8765')
    p.add_argument('--token',default=os.getenv('DGP_AGENT_TOKEN',''))
    p.add_argument('--resolver',choices=['mock','jev'],default='mock')
    p.add_argument('--assistant',choices=['mock','openai'],default='mock')
    p.add_argument('--surface',action='append')
    p.add_argument('--steps',type=int,default=6)
    p.add_argument('--parallel',type=int,default=1)
    p.add_argument('--max-service-calls',type=int,default=3)
    p.add_argument('--trace',default='agent-trace.jsonl')
    p.add_argument('--speculative',action='store_true')
    args=p.parse_args()
    if not args.token: p.error('Set DGP_AGENT_TOKEN or --token to the server agent token.')
    if args.steps<1 or not 1<=args.parallel<=8 or args.max_service_calls<0:
        p.error('steps must be positive, parallel 1..8, and max-service-calls nonnegative.')
    try:
        client=Client(args.base,args.token)
        manifest=client.call('/.well-known/dgp')
        if manifest.get('dgp')!='0.1': raise Problem('VERSION_UNSUPPORTED','This client supports DGP 0.1 only.')
        resolver=JevResolver() if args.resolver=='jev' else MockResolver()
        assistant=OpenAIAssistant() if args.assistant=='openai' else MockAssistant()
        runner=Runner(client,resolver,assistant,trace=args.trace,max_service_calls=args.max_service_calls,speculative=args.speculative)
        surfaces=list(dict.fromkeys(args.surface or [s['surface_id'] for s in client.call(manifest['links']['surfaces'])['surfaces']]))
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            list(pool.map(lambda sid:runner.run_surface(sid,args.steps),surfaces))
    except Problem as e:
        p.exit(1,json.dumps(e.as_dict())+'\n')

if __name__=='__main__': main()
