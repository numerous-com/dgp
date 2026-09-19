"""Regenerate the bundled, self-contained DGP 0.1 JSON Schema."""
import json
from pathlib import Path

S = {"type": "string", "minLength": 1, "maxLength": 512}
TXT = {"type": "string"}
NUM = {"type": "number", "minimum": 0, "maximum": 1}

def ref(name): return {"$ref": f"#/$defs/{name}"}
def arr(item): return {"type": "array", "items": item}
def obj(props, required=None):
    props = dict(props)
    props["extensions"] = {"type": "object"}
    return {"type": "object", "properties": props,
            "required": list(required if required is not None else (k for k in props if k != "extensions")),
            "additionalProperties": False}

def enum(*xs): return {"enum": list(xs)}
def msg(props, required=None):
    p = {"dgp": {"const": "0.1"}, **props}
    return obj(p, ["dgp"] + required if required is not None else None)

D = {}
D['ReadVersion'] = obj({'resource_id': S, 'revision': {'type':'integer','minimum':0}})
D['Source'] = obj({'kind': enum('application','user','model'), 'id': S, 'model': TXT,
                   'based_on_frame': S}, ['kind','id'])
D['Blob'] = obj({'href': S, 'sha256': {'type':'string','pattern':'^[a-f0-9]{64}$'},
                 'byte_length': {'type':'integer','minimum':1}})
D['Evidence'] = obj({'evidence_id':S,'kind':enum('text','json','image','audio','video','document','timeseries'),
                    'mime_type':S,'required':{'type':'boolean'}, 'trust':enum('observed','untrusted','derived'),
                    'source':ref('Source'), 'content':{}, 'blob':ref('Blob'), 'derived_from':arr(S)},
                    ['evidence_id','kind','mime_type','required','trust','source'])
D['Evidence']['oneOf'] = [{'required':['content'],'not':{'required':['blob']}},
                          {'required':['blob'],'not':{'required':['content']}}]
D['Evidence']['allOf'] = [
 {'if':{'properties':{'kind':{'const':'text'}}},'then':{'required':['content'],'properties':{'content':{'type':'string'}}}},
 {'if':{'properties':{'kind':{'enum':['image','audio','video','document']}}},'then':{'required':['blob']}}
]
D['Effect'] = obj({'world_mutation':enum('none','internal','external'),
                  'recovery':enum('not_applicable','exact','compensatable','irreversible','unknown'),
                  'data_egress':enum('none','approved_provider','external'),
                  'speculation':enum('evaluation_only','sandbox_only','forbidden'),
                  'required_actor':enum('any_authorized','human'), 'simulation':{'type':'boolean'}})
D['Option'] = obj({'id':S,'label':TXT,'meaning':TXT,'input_schema':{'type':'object'},'effect':ref('Effect')})
D['Fulfillment'] = obj({'service_id':S,'purpose':TXT,'output_field':S})
D['Decision'] = obj({'decision_id':S,'node_id':S,'kind':enum('choice','score','probability','input'),
                    'question':TXT,'evidence_ids':arr(S), 'dispatch':enum('automatic','on_request'),
                    'options':arr(ref('Option')), 'levels':{'type':'array','items':TXT,'minItems':2},
                    'input_schema':{'type':'object'}, 'effect':ref('Effect'), 'fulfillment':ref('Fulfillment'),
                    'execution': obj({'conflict_keys':arr(S),'depends_on':arr(S),'exclusive_group':S},['conflict_keys','depends_on'])},
                    ['decision_id','node_id','kind','question','evidence_ids','dispatch','execution'])
D['Decision']['allOf'] = [
 {'if':{'properties':{'kind':{'const':'choice'}}},'then':{'required':['options'],'properties':{'options':{'minItems':1}}}},
 {'if':{'properties':{'kind':{'const':'input'}}},'then':{'required':['input_schema','effect']}},
 {'if':{'properties':{'kind':{'const':'score'}}},'then':{'required':['levels']}}
]
D['Preview'] = obj({'graph_id':S,'graph_version':S,'horizon':{'type':['integer','null'],'minimum':0},
                    'completeness':enum('complete_template','partial'), 'nodes':arr(S),'edges':arr(ref('Edge')),
                    'omitted_reason':TXT},['graph_id','graph_version','horizon','completeness','nodes','edges'])
D['Disclosure'] = obj({'requested':enum('next','horizon','full'),'provided':enum('next','horizon','full'),
                       'preview':ref('Preview')}, ['requested','provided'])
D['Frame'] = msg({'frame_id':S,'surface_id':S,'graph_id':S,'graph_version':S,'policy_ref':S,
                  'created_at':{'type':'string','format':'date-time'},'expires_at':{'type':'string','format':'date-time'},
                  'read_set':{'type':'array','items':ref('ReadVersion'),'minItems':1},
                  'observations':arr(ref('Evidence')),'decisions':arr(ref('Decision')),
                  'disclosure':ref('Disclosure'), 'service_calls_remaining':{'type':'integer','minimum':0},
                  'required_features':arr(S)})
D['Resolver'] = obj({'kind':enum('decision_model','llm','human','rule'),'provider':TXT,'model':TXT},['kind'])
D['Uncertainty'] = obj({'distribution':{'type':'object','additionalProperties':NUM},
                        'provider_confidence':NUM,'semantics':TXT,
                        'selection_propensity':NUM,'calibration_ref':S},['semantics'])
D['Answer'] = {'oneOf':[
 obj({'choice':S,'input':{'type':'object'}}), obj({'value':{}}),
 obj({'probability':NUM}), obj({'score':{'type':'number'}})
]}
D['Result'] = obj({'status':enum('answered','abstain'),'answer':ref('Answer'),'reason':TXT,
                   'uncertainty':ref('Uncertainty')},['status'])
D['Result']['allOf'] = [
 {'if':{'properties':{'status':{'const':'answered'}}},'then':{'required':['answer']}},
 {'if':{'properties':{'status':{'const':'abstain'}}},'then':{'not':{'required':['answer']}}}
]
D['Assumption'] = obj({'description':TXT,'expected_decision_id':S,'expected_choice':S},['description'])
D['AssessmentRequest'] = msg({'assessment_id':S,'frame_id':S,'decision_id':S,'mode':enum('live','speculative'),
                              'resolver':ref('Resolver'),'result':ref('Result'),'assumptions':arr(ref('Assumption')),
                              'required_features':arr(S)},
                              ['assessment_id','frame_id','decision_id','mode','resolver','result'])
D['Assessment'] = msg({'assessment_id':S,'frame_id':S,'decision_id':S,'mode':enum('live','speculative'),
                       'resolver':ref('Resolver'),'result':ref('Result'),'assumptions':arr(ref('Assumption')),
                       'required_features':arr(S),'recorded_at':TXT,'submitted_by':S,
                       'claim_provenance':{'const':'client_asserted'}},
                       ['assessment_id','frame_id','decision_id','mode','resolver','result','recorded_at','submitted_by','claim_provenance'])
D['CommitRequest'] = msg({'frame_id':S,'decision_id':S,'assessment_id':S,'required_features':arr(S)},
                         ['frame_id','decision_id','assessment_id'])
D['Receipt'] = msg({'receipt_id':S,'frame_id':S,'decision_id':S,'assessment_id':S,'submitted_by':S,
                    'status':enum('succeeded'),'committed_at':TXT,'state_revision':{'type':'integer','minimum':0},
                    'effect':ref('Effect'),'outcome':TXT,'next_frame_href':S})
D['Node'] = obj({'id':S,'kind':enum('choice','input','terminal'),'summary':TXT})
D['Edge'] = obj({'from':S,'to':S,'on':S,'guard_summary':TXT},['from','to','on'])
D['Graph'] = msg({'graph_id':S,'graph_version':S,'completeness':enum('complete_template','partial'),
                  'nodes':arr(ref('Node')),'edges':arr(ref('Edge')),'semantics':TXT})
D['Service'] = obj({'service_id':S,'operation':enum('reason','generate_text'),
                    'input_modalities':arr(S),'output_kind':{'const':'text'},
                    'max_output_chars':{'type':'integer','minimum':1},
                    'side_effects':{'const':'provider_cost_and_data_egress'},'purpose':TXT})
D['Manifest'] = msg({'name':TXT,'status':{'const':'experimental'},'features':arr(S),
                     'evidence_modalities':arr(S),'decision_kinds':arr(S),'input_schema_dialect':S,
                     'links':obj({'surfaces':S,'graphs':S,'assessments':S,'commits':S,'services':S}),
                     'auth':TXT,'idempotency_retention':TXT})
D['Problem'] = msg({'type':S,'title':TXT,'status':{'type':'integer'},'detail':TXT,'code':S})
root = {'$schema':'https://json-schema.org/draft/2020-12/schema',
        '$id':'urn:dgp:0.1:schema', 'title':'Decision Graph Protocol 0.1 (experimental)', '$defs':D}
Path(__file__).with_name('dgp.schema.json').write_text(json.dumps(root,indent=2)+'\n')
