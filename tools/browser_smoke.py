"""Offline browser DOM smoke test; no browser network access is used."""
import sys,contextlib,io,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dgp_demo.engine import Engine,GRAPH,SERVICES
from dgp_demo.contracts import Problem
from dgp_demo.providers import MockResolver,MockAssistant
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit,parse_qs
root=Path(__file__).resolve().parents[1];e=Engine();checks=[]

def dispatch(path,options):
 try:
  principal={'Bearer qa-agent':('agent-local','agent'),'Bearer qa-human':('human-local','human')}.get(options.get('headers',{}).get('Authorization'))
  if not principal: raise Problem('UNAUTHENTICATED','Bearer token required.',401)
  actor,role=principal;parts=urlsplit(path);p=parts.path;data=json.loads(options['body']) if options.get('body') else None
  if p=='/dgp/surfaces':result=e.surfaces()
  elif p=='/dgp/bulletin':result=e.bulletin()
  elif p=='/dgp/graphs/thread-recovery':result=GRAPH
  elif p.startswith('/dgp/surfaces/'):
   q=parse_qs(parts.query);result=e.frame(p.split('/')[3],q.get('disclosure',['next'])[0],int(q.get('horizon',['2'])[0]))
  elif p=='/dgp/assessments':result=e.assess(data,actor)
  elif p=='/dgp/commits':result=e.commit(data,actor,role,options['headers'].get('Idempotency-Key',''))
  else:raise Problem('NOT_FOUND',p,404)
  return {'ok':True,'status':200,'body':result}
 except Problem as p:return {'ok':False,'status':p.status,'body':p.as_dict()}

def advance(sid):
 import uuid
 for i in range(6):
  f=e.frame(sid);d=next((d for d in f['decisions'] if d['dispatch']=='automatic'),None)
  if d is None:return
  if d['kind']=='input':
   txt,prov=MockAssistant().fulfill(f,d);r={'status':'answered','answer':{'value':{d['fulfillment']['output_field']:txt}}}
  else:r,prov=MockResolver().resolve(f,d)
  a={'dgp':'0.1','assessment_id':'qa-'+uuid.uuid4().hex,'frame_id':f['frame_id'],'decision_id':d['decision_id'],
     'mode':'live','resolver':prov,'result':r}
  e.assess(a,'agent-local')
  if r['answer'].get('choice')=='publish':return
  e.commit({'dgp':'0.1','assessment_id':a['assessment_id'],'frame_id':f['frame_id'],'decision_id':d['decision_id']},'agent-local','agent',str(uuid.uuid4()))

try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
  page.expose_function('fixtureHttp',dispatch)
  page.set_content((root/'web/index.html').read_text().replace('<link rel="stylesheet" href="/style.css">','').replace('<script src="/app.js" defer></script>',''))
  page.add_style_tag(path=str(root/'web/style.css'))
  page.add_script_tag(content="""window.fetch=async(path,options={})=>{const r=await window.fixtureHttp(path,options);return {ok:r.ok,status:r.status,json:async()=>r.body};};if(!crypto.randomUUID){crypto.randomUUID=()=>String(Date.now())+'-'+Math.random().toString(36).slice(2);}""")
  page.add_script_tag(path=str(root/'web/app.js'))
  page.locator('#token').fill('qa-human');page.get_by_role('button',name='Connect / refresh').click()
  page.wait_for_selector('.card');assert page.locator('.card').count()==2
  checks.append('Offline DOM renderer displays both authorized fixture surfaces.')
  advance('thread-42');advance('thread-73')
  page.get_by_role('button',name='Connect / refresh').click();page.get_by_role('button',name='Publish (human only)').wait_for()
  assert e.bulletin()['entries']==[];checks.append('Publication control is rendered for the review frame; no publication occurred automatically.')
  page.screenshot(path=str(root/'docs/UI_PREVIEW.png'),full_page=True)
  page.on('dialog',lambda d:d.accept());page.get_by_role('button',name='Publish (human only)').click()
  page.wait_for_function("document.querySelectorAll('#bulletin .bullet').length === 1")
  checks.append('UI assessment/commit payloads successfully publish one LOCAL fixture entry through the engine.')
  first=page.locator('.card').first;first.locator('textarea').first.fill('<script>window.evil=true</script> Unicode æøå')
  first.get_by_role('button',name='Submit text').first.click()
  page.wait_for_function("document.querySelector('#threads').textContent.includes('Unicode æøå')")
  assert page.evaluate('window.evil') is None;checks.append('Free-text Unicode round-trip; script-like text is not executed.')
  page.locator('#disclosure').select_option('full');page.wait_for_function("document.querySelector('#threads').textContent.includes('complete_template')")
  checks.append('Full disclosure is rendered in the raw frame inspector.')
  page.set_viewport_size({'width':390,'height':844})
  w=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
  if w['scroll']>w['width']+2:raise RuntimeError('Mobile overflow: '+str(w))
  checks.append('390-pixel viewport has no horizontal overflow.')
  assert not errors,errors;checks.append('No JavaScript errors in the exercised offline flows.')
  browser.close()
finally:e.close()
(root/'docs/BROWSER_CHECK.txt').write_text('Mode: offline browser renderer with in-memory DGP responses. Browser loopback navigation was blocked by environment policy; real HTTP flows were separately tested with the Python client.\n\n'+'\n'.join('PASS: '+x for x in checks)+'\n')
print('\n'.join(checks))
