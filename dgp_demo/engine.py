"""Durable local app + DGP boundary. No real Git/CI/mail operations are executed."""
from __future__ import annotations
import base64
import binascii
import hashlib
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator
from jsonschema import Draft202012Validator, FormatChecker
from .contracts import (ROOT, VERSION, Problem, clone, digest, effect, now, option,
                        stable, text_input, validate_result)

FEATURES = ['core@0.1','graph-preview@0.1','speculative-assessment@0.1',
            'service-input@0.1','image-evidence@0.1']
SCHEMA = json.loads((ROOT / 'schemas/dgp.schema.json').read_text())

def check(name: str, data: Any) -> None:
    schema = {'$schema':SCHEMA['$schema'],'$defs':SCHEMA['$defs'],'$ref':f'#/$defs/{name}'}
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
    if errors:
        raise Problem('INVALID_MESSAGE', f'{name}: {errors[0].message}', 422)
    for feature in data.get('required_features', []):
        if feature not in FEATURES:
            raise Problem('CAPABILITY_REQUIRED', f'Unsupported required feature: {feature}', 406)

GRAPH = {
 'dgp': VERSION, 'graph_id':'thread-recovery', 'graph_version':'1',
 'completeness':'complete_template',
 'semantics':'Descriptive template, not an executable guard language. Current frames are authoritative. Repeated visits create new decision instances.',
 'nodes':[
  {'id':'recovery','kind':'choice','summary':'Choose a bounded next recovery action.'},
  {'id':'analysis_result','kind':'input','summary':'Supply derived diagnostic text.'},
  {'id':'update','kind':'choice','summary':'Choose whether to draft an update or finish.'},
  {'id':'draft_result','kind':'input','summary':'Supply draft text.'},
  {'id':'review','kind':'choice','summary':'Publish, discard, or hold the draft.'},
  {'id':'done','kind':'terminal','summary':'No autonomous work remains.'},
  {'id':'note','kind':'input','summary':'Optional free-text note; available in every state.'},
  {'id':'attach_image','kind':'input','summary':'Optional image evidence; available in every state.'}],
 'edges':[
  {'from':'recovery','to':'update','on':'retry','guard_summary':'Demo fixture succeeds on its single retry; real test outcomes would add branches.'},
  {'from':'recovery','to':'analysis_result','on':'request_reasoning'},
  {'from':'analysis_result','to':'recovery','on':'submit'},
  {'from':'recovery','to':'done','on':'investigate'},
  {'from':'recovery','to':'done','on':'pause'},
  {'from':'update','to':'draft_result','on':'draft_update'},
  {'from':'update','to':'done','on':'finish'},
  {'from':'draft_result','to':'review','on':'submit'},
  {'from':'review','to':'done','on':'publish','guard_summary':'Authenticated human only; appends to a LOCAL simulated bulletin.'},
  {'from':'review','to':'done','on':'discard'},
  {'from':'review','to':'done','on':'hold'}]}

SERVICES = [
 {'service_id':'llm.reason','operation':'reason','input_modalities':['text','json'],
  'output_kind':'text','max_output_chars':4000,'side_effects':'provider_cost_and_data_egress',
  'purpose':'Provide a brief diagnostic assessment with uncertainties, not hidden chain-of-thought or commands.'},
 {'service_id':'llm.generate_text','operation':'generate_text','input_modalities':['text','json'],
  'output_kind':'text','max_output_chars':2000,'side_effects':'provider_cost_and_data_egress',
  'purpose':'Write a factual status-update draft. Never publish it.'}]

class Engine:
    def __init__(self, path: str = ':memory:', *, frame_ttl: int = 900):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.frame_ttl = frame_ttl
        self.db.executescript('''
          PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value INTEGER NOT NULL);
          INSERT OR IGNORE INTO meta VALUES('policy_revision',1);
          CREATE TABLE IF NOT EXISTS frames(id TEXT PRIMARY KEY, surface TEXT NOT NULL, body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY, actor TEXT NOT NULL, fingerprint TEXT NOT NULL, body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY, body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS requests(actor TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL, receipt_id TEXT NOT NULL, PRIMARY KEY(actor,key));
          CREATE TABLE IF NOT EXISTS blobs(id TEXT NOT NULL, surface TEXT NOT NULL, mime TEXT NOT NULL, data BLOB NOT NULL, PRIMARY KEY(id,surface));
          CREATE TABLE IF NOT EXISTS bulletin(id TEXT PRIMARY KEY, surface TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')
        with self.tx():
            for sid, title, log in [
                ('thread-42','Transient CI failure','Connection timed out before any test assertions ran. Database health was temporarily unavailable.'),
                ('thread-73','Ambiguous integration failure','Runner terminated. Last log line: loading configuration. No reliable error classification is available.')]:
                state = {'title':title,'status':'blocked','log':log,'retries':0,
                         'reason_count':0,'draft_count':0,'notes':[],'analysis':[],
                         'draft':None,'images':[],'service_calls':0}
                self.db.execute('INSERT OR IGNORE INTO entities VALUES(?,1,?)',(sid,stable(state)))

    def close(self) -> None:
        with self.lock: self.db.close()

    @contextmanager
    def tx(self) -> Iterator[None]:
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise

    def _entity(self, sid: str) -> tuple[int, dict[str, Any]]:
        row = self.db.execute('SELECT * FROM entities WHERE id=?',(sid,)).fetchone()
        if not row: raise Problem('NOT_FOUND','Unknown surface.',404)
        return row['revision'], json.loads(row['body'])

    def _policy_revision(self) -> int:
        return self.db.execute("SELECT value FROM meta WHERE key='policy_revision'").fetchone()[0]

    def manifest(self) -> dict[str, Any]:
        return {'dgp':VERSION,'name':'ThreadDesk','status':'experimental','features':FEATURES,
                'evidence_modalities':['text','json','image'], 'decision_kinds':['choice','input'],
                'input_schema_dialect':'https://json-schema.org/draft/2020-12/schema',
                'links':{'surfaces':'/dgp/surfaces','graphs':'/dgp/graphs',
                         'assessments':'/dgp/assessments','commits':'/dgp/commits','services':'/dgp/services'},
                'auth':'Bearer tokens, single local tenant. Principal comes from the server token map, never the request body.',
                'idempotency_retention':'For the lifetime of this demo database; deleting it loses deduplication history.'}

    def surfaces(self) -> dict[str, Any]:
        with self.lock:
            rows = self.db.execute('SELECT * FROM entities ORDER BY id').fetchall()
            return {'dgp':VERSION,'surfaces':[{'surface_id':r['id'], 'title':json.loads(r['body'])['title'],
                'state':json.loads(r['body'])['status'],'frame_href':f"/dgp/surfaces/{r['id']}/frame"} for r in rows]}

    def _decision(self, node: str, fid: str, sid: str, evidence: list[str], kind: str,
                  question: str, *, dispatch: str = 'automatic') -> dict[str, Any]:
        return {'decision_id':f'{fid}:{node}','node_id':node,'kind':kind,'question':question,
                'evidence_ids':evidence,'dispatch':dispatch,
                'execution':{'conflict_keys':[f'thread:{sid}'],'depends_on':[]}}

    def _decisions(self, fid: str, sid: str, state: dict[str, Any], evidence: list[str]) -> list[dict[str, Any]]:
        ds = []
        status = state['status']
        if status == 'blocked':
            d = self._decision('recovery',fid,sid,evidence,'choice','Which immediate recovery route fits the reported failure?')
            d['options'] = []
            if state['retries'] < 1:
                d['options'].append(option('retry','Retry tests','A transient failure prevented the tests from running. Retry once.'))
            d['options'].append(option('investigate','Investigate','A persistent or unresolved issue needs engineering investigation. Stop autonomous recovery.'))
            if state['reason_count'] < 1 and state['service_calls'] < 3:
                d['options'].append(option('request_reasoning','Request reasoning','The evidence is too ambiguous. Obtain one brief LLM analysis before judging again.'))
            d['options'].append(option('pause','Pause','Do not act further; leave this thread for a human.'))
            ds.append(d)
        elif status == 'needs_analysis':
            d = self._decision('analysis_result',fid,sid,evidence,'input','Provide a brief diagnostic analysis and its uncertainties.')
            d.update(input_schema=text_input('analysis'),effect=effect(),
                     fulfillment={'service_id':'llm.reason','purpose':SERVICES[0]['purpose'],'output_field':'analysis'})
            ds.append(d)
        elif status == 'ready':
            d = self._decision('update',fid,sid,evidence,'choice','Should this completed recovery receive a status-update draft?')
            d['options'] = [option('finish','Finish without update','No status draft is needed.')]
            if state['draft_count'] < 1 and state['service_calls'] < 3:
                d['options'].insert(0,option('draft_update','Draft an update','Prepare a short factual update for human review.'))
            ds.append(d)
        elif status == 'needs_draft':
            d = self._decision('draft_result',fid,sid,evidence,'input','Write a short factual status update. Do not claim unsimulated work happened.')
            d.update(input_schema=text_input('text',2000),effect=effect(),
                     fulfillment={'service_id':'llm.generate_text','purpose':SERVICES[1]['purpose'],'output_field':'text'})
            ds.append(d)
        elif status == 'review':
            d = self._decision('review',fid,sid,evidence,'choice','Is this draft suitable for publication to the local demo bulletin?')
            d['options'] = [option('publish','Publish (human only)','The draft is accurate and ready. An authenticated human must authorize publication.',human=True),
                            option('discard','Discard','The draft is incorrect or unnecessary.'),
                            option('hold','Hold for later','Keep the draft without publishing.')]
            ds.append(d)
        note = self._decision('note',fid,sid,evidence,'input','Add a free-text note to this thread.',dispatch='on_request')
        note.update(input_schema=text_input('text'),effect=effect())
        ds.append(note)
        image = self._decision('attach_image',fid,sid,evidence,'input','Attach PNG, JPEG or WebP evidence. It will be required evidence in subsequent frames.',dispatch='on_request')
        image.update(input_schema={'type':'object','properties':{
            'mime_type':{'enum':['image/png','image/jpeg','image/webp']},
            'data_base64':{'type':'string','minLength':1,'maxLength':350000}},
            'required':['mime_type','data_base64'],'additionalProperties':False},effect=effect())
        ds.append(image)
        return ds

    def frame(self, sid: str, disclosure: str = 'next', horizon: int = 2) -> dict[str, Any]:
        if disclosure not in ('next','horizon','full'):
            raise Problem('INVALID_DISCLOSURE','Use next, horizon, or full.',422)
        if not 0 <= horizon <= 20:
            raise Problem('INVALID_HORIZON','Horizon must be between 0 and 20.',422)
        with self.tx():
            rev,state = self._entity(sid)
            fid = 'f-' + uuid.uuid4().hex
            p = self._policy_revision()
            ts = datetime.now(timezone.utc)
            def ev(eid: str, kind: str, content: Any, trust: str = 'observed', source: dict | None = None) -> dict:
                return {'evidence_id':eid,'kind':kind,'mime_type':'text/plain' if kind == 'text' else 'application/json',
                        'required':True,'trust':trust,'source':source or {'kind':'application','id':'threaddesk'},'content':content}
            obs = [ev('state','json',{k:state[k] for k in ['title','status','retries','reason_count','draft_count','service_calls']}),
                   ev('failure-log','text',state['log'],'untrusted')]
            for i,n in enumerate(state['notes']): obs.append(ev(f'note-{i}','text',n['text'],'untrusted',{'kind':'user','id':n['actor']}))
            for i,a in enumerate(state['analysis']):
                item = ev(f'analysis-{i}','text',a['text'],'derived',{'kind':'model','id':a['actor'],'model':a['model'],'based_on_frame':a['frame_id']})
                item['derived_from'] = ['failure-log']; obs.append(item)
            if state['draft'] is not None: obs.append(ev('draft','text',state['draft'],'derived'))
            for i,im in enumerate(state['images']):
                obs.append({'evidence_id':f'image-{i}','kind':'image','mime_type':im['mime_type'],
                  'required':True,'trust':'untrusted','source':{'kind':'user','id':im['actor']},
                  'blob':{'href':f"/dgp/blobs/{sid}/{im['sha256']}",'sha256':im['sha256'],'byte_length':im['byte_length']}})
            ds = self._decisions(fid,sid,state,[e['evidence_id'] for e in obs])
            disc = {'requested':disclosure,'provided':disclosure}
            if disclosure != 'next':
                roots = {d['node_id'] for d in ds}
                included = set(roots)
                for _ in range(horizon if disclosure == 'horizon' else len(GRAPH['nodes'])):
                    included |= {e['to'] for e in GRAPH['edges'] if e['from'] in included}
                if disclosure == 'full': included = {n['id'] for n in GRAPH['nodes']}
                edges = [e for e in GRAPH['edges'] if e['from'] in included and e['to'] in included]
                disc['preview'] = {'graph_id':GRAPH['graph_id'],'graph_version':'1',
                  'horizon':horizon if disclosure == 'horizon' else None,
                  'completeness':'complete_template' if disclosure == 'full' else 'partial',
                  'nodes':sorted(included),'edges':clone(edges)}
            frame = {'dgp':VERSION,'frame_id':fid,'surface_id':sid,'graph_id':GRAPH['graph_id'],'graph_version':'1',
              'policy_ref':f'thread-policy@{p}','created_at':ts.isoformat().replace('+00:00','Z'),
              'expires_at':(ts + timedelta(seconds=self.frame_ttl)).isoformat().replace('+00:00','Z'),
              'read_set':[{'resource_id':f'thread:{sid}','revision':rev},{'resource_id':'policy:thread-policy','revision':p}],
              'observations':obs,'decisions':ds,'disclosure':disc,'service_calls_remaining':max(0,3-state['service_calls']),
              'required_features':['core@0.1'] + (['image-evidence@0.1'] if state['images'] else [])}
            check('Frame',frame)
            self.db.execute('INSERT INTO frames VALUES(?,?,?)',(fid,sid,stable(frame)))
            return frame

    def _record(self, table: str, rid: str) -> dict[str, Any]:
        # table is an internal constant, never a user-supplied SQL identifier.
        row = self.db.execute(f'SELECT body FROM {table} WHERE id=?',(rid,)).fetchone()
        if not row: raise Problem('NOT_FOUND',f'Unknown {table} record.',404)
        return json.loads(row[0])

    def record(self, table: str, rid: str) -> dict[str, Any]:
        if table not in ('frames','assessments','receipts'): raise ValueError('Invalid record table')
        with self.lock: return self._record(table,rid)

    def _find_decision(self, frame: dict, did: str) -> dict:
        d = next((x for x in frame['decisions'] if x['decision_id'] == did),None)
        if not d: raise Problem('DECISION_NOT_OFFERED','Decision is not present in the referenced frame.',422)
        return d

    def assess(self, data: dict, actor: str) -> dict:
        check('AssessmentRequest',data)
        fp = digest(data)
        with self.tx():
            row = self.db.execute('SELECT * FROM assessments WHERE id=?',(data['assessment_id'],)).fetchone()
            if row:
                if row['actor'] != actor or row['fingerprint'] != fp:
                    raise Problem('ASSESSMENT_ID_REUSED','Assessment ID already has different content or owner.',409)
                return json.loads(row['body'])
            frame = self._record('frames',data['frame_id'])
            d = self._find_decision(frame,data['decision_id'])
            validate_result(d,data['result'])
            a = {**clone(data),'recorded_at':now(),'submitted_by':actor,'claim_provenance':'client_asserted'}
            check('Assessment',a)
            self.db.execute('INSERT INTO assessments VALUES(?,?,?,?)',(a['assessment_id'],actor,fp,stable(a)))
            return a

    def commit(self, data: dict, actor: str, role: str, key: str) -> dict:
        check('CommitRequest',data)
        if not isinstance(key,str) or not 1 <= len(key) <= 200:
            raise Problem('IDEMPOTENCY_KEY_REQUIRED','Supply a nonempty Idempotency-Key of at most 200 characters.',400)
        fp = digest(data)
        with self.tx():
            # Deduplicate BEFORE stale-state/expiry checks: a successful replay returns its original receipt.
            old = self.db.execute('SELECT * FROM requests WHERE actor=? AND key=?',(actor,key)).fetchone()
            if old:
                if old['fingerprint'] != fp: raise Problem('IDEMPOTENCY_KEY_REUSED','Same key, different commit payload.',409)
                return self._record('receipts',old['receipt_id'])
            f = self._record('frames',data['frame_id'])
            a = self._record('assessments',data['assessment_id'])
            if a['submitted_by'] != actor: raise Problem('FORBIDDEN','Cannot commit another principal\'s assessment.',403)
            if a['frame_id'] != data['frame_id'] or a['decision_id'] != data['decision_id']:
                raise Problem('ASSESSMENT_MISMATCH','Assessment and commit do not refer to the same frame and decision.',422)
            if a['mode'] != 'live': raise Problem('SPECULATIVE_ONLY','Speculative assessments cannot be committed.',409)
            if a['result']['status'] != 'answered': raise Problem('ABSTAINED','An abstention does not authorize a transition.',409)
            if datetime.now(timezone.utc) >= datetime.fromisoformat(f['expires_at'].replace('Z','+00:00')):
                raise Problem('FRAME_EXPIRED','Read a fresh frame and assess it again.',409)
            rev,state = self._entity(f['surface_id'])
            versions = {x['resource_id']:x['revision'] for x in f['read_set']}
            if versions.get(f"thread:{f['surface_id']}") != rev or versions.get('policy:thread-policy') != self._policy_revision():
                raise Problem('STALE_FRAME','State or policy changed; reassess a fresh frame.',409)
            d = self._find_decision(f,data['decision_id'])
            # Recompute the authoritative enabled nodes/options, not just the client or historical graph.
            current = self._decisions(f['frame_id'],f['surface_id'],state,d['evidence_ids'])
            live = next((x for x in current if x['decision_id'] == d['decision_id']),None)
            if live is None: raise Problem('DECISION_NOT_AVAILABLE','Decision no longer available.',409)
            validate_result(live,a['result'])
            answer = a['result']['answer']
            selected = next((o for o in live.get('options',[]) if o['id'] == answer.get('choice')),None)
            e = selected['effect'] if selected else live.get('effect',effect(mutation='none',recovery='not_applicable'))
            if e['required_actor'] == 'human' and role != 'human':
                raise Problem('HUMAN_APPROVAL_REQUIRED','A human must review the draft and submit their own assessment and commit.',403)
            outcome = self._apply(f,live,answer,state,actor,a)
            next_rev = rev+1
            self.db.execute('UPDATE entities SET revision=?,body=? WHERE id=?',(next_rev,stable(state),f['surface_id']))
            r = {'dgp':VERSION,'receipt_id':'r-'+uuid.uuid4().hex,'frame_id':f['frame_id'],
                 'decision_id':d['decision_id'],'assessment_id':a['assessment_id'],'submitted_by':actor,
                 'status':'succeeded','committed_at':now(),'state_revision':next_rev,'effect':e,'outcome':outcome,
                 'next_frame_href':f"/dgp/surfaces/{f['surface_id']}/frame"}
            check('Receipt',r)
            self.db.execute('INSERT INTO receipts VALUES(?,?)',(r['receipt_id'],stable(r)))
            self.db.execute('INSERT INTO requests VALUES(?,?,?,?)',(actor,key,fp,r['receipt_id']))
            return r

    def _apply(self, f: dict, d: dict, answer: dict, s: dict, actor: str, a: dict) -> str:
        node, choice = d['node_id'], answer.get('choice')
        if node == 'recovery':
            if choice == 'retry':
                s['retries'] += 1; s['status']='ready'
                return 'Simulated one CI retry; fixture result is success. No tests were actually run.'
            if choice == 'request_reasoning':
                if s['service_calls'] >= 3: raise Problem('BUDGET_EXHAUSTED','Service request budget exhausted.',409)
                s['reason_count'] += 1; s['service_calls'] += 1; s['status']='needs_analysis'
                return 'Reasoning requested. This transition did not call an external provider.'
            s['status']='investigating' if choice == 'investigate' else 'paused'
            return 'Thread left for human investigation.' if choice == 'investigate' else 'Thread paused.'
        if node == 'analysis_result':
            s['analysis'].append({'text':answer['value']['analysis'],'frame_id':f['frame_id'],
                                 'actor':actor,'model':a['resolver'].get('model','unspecified')})
            s['status']='blocked'; return 'Stored derived analysis; recovery must be assessed again.'
        if node == 'update':
            if choice == 'draft_update':
                if s['service_calls'] >= 3: raise Problem('BUDGET_EXHAUSTED','Service request budget exhausted.',409)
                s['draft_count'] += 1; s['service_calls'] += 1; s['status']='needs_draft'
                return 'Draft requested. No text generated or published by this transition.'
            s['status']='done'; return 'Recovery finished without an update.'
        if node == 'draft_result':
            s['draft']=answer['value']['text']; s['status']='review'
            return 'Stored draft text for a new review decision.'
        if node == 'review':
            if choice == 'publish':
                self.db.execute('INSERT INTO bulletin VALUES(?,?,?,?)',('p-'+uuid.uuid4().hex,f['surface_id'],s['draft'],now()))
                s['status']='published'; return 'Published to LOCAL demo bulletin only. No external message was sent.'
            if choice == 'discard': s['draft']=None
            s['status']='done' if choice == 'discard' else 'held'
            return 'Draft discarded.' if choice == 'discard' else 'Draft held without publication.'
        if node == 'note':
            s['notes'].append({'text':answer['value']['text'],'actor':actor}); return 'Free-text note stored.'
        if node == 'attach_image':
            v=answer['value']; mime=v['mime_type']
            try: raw=base64.b64decode(v['data_base64'],validate=True)
            except (ValueError,binascii.Error): raise Problem('INVALID_IMAGE','Invalid base64.',422)
            if not 0 < len(raw) <= 256*1024: raise Problem('INVALID_IMAGE','Image limit is 256 KiB.',422)
            signatures={'image/png':raw.startswith(b'\x89PNG\r\n\x1a\n'),
                        'image/jpeg':raw.startswith(b'\xff\xd8\xff'),
                        'image/webp':raw.startswith(b'RIFF') and raw[8:12]==b'WEBP'}
            if not signatures.get(mime): raise Problem('INVALID_IMAGE','MIME type and file signature disagree.',422)
            sha=hashlib.sha256(raw).hexdigest()
            self.db.execute('INSERT OR IGNORE INTO blobs VALUES(?,?,?,?)',(sha,f['surface_id'],mime,raw))
            s['images'].append({'sha256':sha,'mime_type':mime,'byte_length':len(raw),'actor':actor})
            return 'Stored image evidence. A text-only resolver must not silently omit it.'
        raise Problem('UNSUPPORTED_TRANSITION',node,422)

    def blob(self, sid: str, sha: str) -> tuple[str,bytes]:
        with self.lock:
            row=self.db.execute('SELECT mime,data FROM blobs WHERE id=? AND surface=?',(sha,sid)).fetchone()
            if not row: raise Problem('NOT_FOUND','Unknown blob.',404)
            return row['mime'],row['data']

    def bulletin(self) -> dict:
        with self.lock:
            return {'dgp':VERSION,'entries':[dict(x) for x in self.db.execute('SELECT * FROM bulletin ORDER BY created_at')]}
