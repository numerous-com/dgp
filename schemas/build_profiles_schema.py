"""Build self-contained, opt-in DGP 0.1 profile schemas without remote refs."""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = json.loads((ROOT / 'dgp.schema.json').read_text())
D = copy.deepcopy(base['$defs'])
S = {'type':'string','minLength':1,'maxLength':2048}
TXT = {'type':'string'}
N = {'type':'integer','minimum':0}
POS = {'type':'integer','minimum':1}
BOOL = {'type':'boolean'}
STAMP = {'type':'string','format':'date-time'}
def ref(n): return {'$ref':'#/$defs/'+n}
def enum(*xs): return {'enum':list(xs)}
def arr(v, unique=False, minimum=0):
    d={'type':'array','items':v,'minItems':minimum}
    if unique:d['uniqueItems']=True
    return d
def obj(p, required=None):
    return {'type':'object','properties':p,'required':list(p) if required is None else required,'additionalProperties':False}
def record(kind,p,required=None):
    p={'dgp':{'const':'0.1'},'record_type':{'const':kind},**p}
    return obj(p, None if required is None else ['dgp','record_type',*required])
D['Interface'] = obj({'interface_id':S,'kind':enum('ui','http_api','mcp','cli','dgp','graphql'),
                      'description':TXT,'descriptor_uri':S,'auth_ref':S})
D['Capability'] = obj({'capability_id':S,'description':TXT,'dgp_support':enum('native','handoff','not_exposed'),
                       'interface_ids':arr(S,True,1),'canonical_operation_id':S},
                       ['capability_id','description','dgp_support','interface_ids'])
D['CapabilityCatalogue'] = record('capability_catalogue',{'catalogue_id':S,'catalogue_version':S,'application_id':S,
    'coverage':enum('partial','complete_declared_scope'),'scope_description':TXT,
    'interfaces':arr(ref('Interface'),minimum=1),'capabilities':arr(ref('Capability'))})
D['EvidenceInclusion'] = obj({'evidence_id':S,'required_for':arr(S,True),'status':enum('included','reference','omitted','redacted','unavailable')})
D['FrameProjection'] = record('frame_projection',{
    'projection_id':S,'view_id':S,'view_version':S,'frame_id':S,'canonical_frame_href':S,
    'surface_id':S,'graph_id':S,'graph_version':S,'policy_ref':S,'created_at':STAMP,'expires_at':STAMP,
    'read_set':arr(ref('ReadVersion'),minimum=1),'purpose':enum('browse','assess'),'decision_scope':arr(S,True),
    'decisions':arr(ref('Decision')),'observations':arr(ref('Evidence')),'evidence_manifest':arr(ref('EvidenceInclusion')),
    'omitted_fields':arr(S,True),'data':{'type':'object'},'required_features':arr(S,True,1)})
D['AssessmentInputManifest'] = obj({'frame_id':S,'decision_id':S,'projection_ids':arr(S,True,1),
    'consumed_evidence_ids':arr(S,True),'omitted_optional_evidence_ids':arr(S,True),
    'contract_complete':{'const':True}})
D['PreparedOperation'] = obj({'operation_id':S,'operation_version':S,'kind':enum('query','assessment','commit'),
    'description':TXT,'variables_schema':{'type':'object'},'result_definition':S,
    'required_features':arr(S,True),'max_retrieval_cost_class':enum('small','bounded_large')})
D['PreparedOperationCatalogue'] = record('prepared_operation_catalogue',{'catalogue_id':S,'catalogue_version':S,
    'application_id':S,'operations':arr(ref('PreparedOperation'),minimum=1)})
D['PreparedOperationRequest'] = record('prepared_operation_request',{'operation_id':S,'operation_version':S,'variables':{'type':'object'}})
D['EvaluationScope'] = obj({'application_id':S,'tenant_id':S,'workspace_id':S})
D['EvaluationPolicy'] = record('evaluation_policy',{'policy_id':S,'policy_version':S,'scope':ref('EvaluationScope'),
    'as_of':STAMP,'limits':obj({'max_running':POS,'max_queued':N,'max_variants_per_submission':POS}),
    'budget':obj({'unit':S,'limit':N,'consumed':N,'reserved':N}),
    'cache_hits_consume_budget':BOOL,'admission_mode':{'const':'all_or_nothing'}})
D['AdmissionItem'] = obj({'scenario_ref':S,'disposition':enum('job','cached'),'job_id':S,'result_ref':S},['scenario_ref','disposition'])
D['AdmissionItem']['allOf']=[
    {'if':{'properties':{'disposition':{'const':'job'}}},'then':{'required':['job_id'],'not':{'required':['result_ref']}}},
    {'if':{'properties':{'disposition':{'const':'cached'}}},'then':{'required':['result_ref'],'not':{'required':['job_id']}}}]
D['EvaluationAdmission'] = obj({'batch_id':S,'policy_ref':S,'canonical_operation_id':S,
    'admission_mode':{'const':'all_or_nothing'},'items':arr(ref('AdmissionItem'),minimum=1)})
D['JobCost'] = obj({'unit':S,'reserved_units':N,'consumed_units':N,'accounting_status':enum('reserved','settled','reconciling')})
D['JobError'] = obj({'code':S,'message':TXT,'retryable':BOOL})
D['EvaluationJob'] = record('evaluation_job',{'job_id':S,'job_revision':POS,'study_ref':S,'scenario_ref':S,
    'source_frame_id':S,'admission_receipt_id':S,'canonical_operation_id':S,
    'state':enum('queued','running','cancel_requested','reconciling','succeeded','failed','cancelled'),
    'accepted_at':STAMP,'updated_at':STAMP,'cost':ref('JobCost'),'result_ref':S,'error':ref('JobError'),'retry_of':S},
    ['job_id','job_revision','study_ref','scenario_ref','source_frame_id','admission_receipt_id','canonical_operation_id',
     'state','accepted_at','updated_at','cost'])
D['EvaluationJob']['allOf']=[
    {'if':{'properties':{'state':{'const':'succeeded'}}},'then':{'required':['result_ref'],'not':{'required':['error']}}},
    {'if':{'properties':{'state':{'const':'failed'}}},'then':{'required':['error'],'not':{'required':['result_ref']}}},
    {'if':{'properties':{'state':{'enum':['queued','running','cancel_requested','reconciling','cancelled']}}},
     'then':{'not':{'anyOf':[{'required':['result_ref']},{'required':['error']}]}}}]
D['Event'] = obj({'event_id':S,'stream_id':S,'sequence':POS,'occurred_at':STAMP,
    'kind':enum('frame_available','job_updated','budget_updated'),'resource_ref':S,'resource_revision':POS,
    'correlation_id':S},['event_id','stream_id','sequence','occurred_at','kind','resource_ref','resource_revision'])
D['EventPage'] = record('event_page',{'stream_id':S,'events':arr(ref('Event')),'next_cursor':S,'has_more':BOOL,
    'snapshot_ref':S,'snapshot_watermark':N},['stream_id','events','next_cursor','has_more'])
D['Handoff'] = record('handoff',{'handoff_id':S,'handoff_revision':POS,'application_id':S,'origin_frame_id':S,
    'origin_decision_id':S,'capability_id':S,'canonical_operation_id':S,'target_interface_id':S,
    'scope_ref':S,'arguments':{'type':'object'},'expected_result_schema':{'type':'object'},'correlation_id':S,
    'expires_at':STAMP,'effect':enum('read','write'),'state':enum('offered','completed','expired','cancelled'),'result_ref':S},
    ['handoff_id','handoff_revision','application_id','origin_frame_id','origin_decision_id','capability_id',
     'canonical_operation_id','target_interface_id','scope_ref','arguments','expected_result_schema','correlation_id',
     'expires_at','effect','state'])
D['Handoff']['allOf']=[{'if':{'properties':{'state':{'const':'completed'}}},'then':{'required':['result_ref']}}]
D['CoordinatesInput'] = obj({'latitude':{'type':'number','minimum':-90,'maximum':90},
                            'longitude':{'type':'number','minimum':-180,'maximum':180}})
D['ExclusiveLocationInput'] = obj({'address':{'type':'string','minLength':1},'coordinates':ref('CoordinatesInput'),'selectedPlaceId':S},[])
D['ExclusiveLocationInput']['oneOf']=[{'required':[k]} for k in ['address','coordinates','selectedPlaceId']]
root={'$schema':base['$schema'],'$id':'urn:dgp:0.1:profiles:schema','title':'DGP 0.1 optional profile definitions','$defs':D}
(ROOT/'dgp.profiles.schema.json').write_text(json.dumps(root,indent=2)+'\n')
print('Profile definitions:',len(D)-len(base['$defs']))
