from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, ValidationError
from profile_support.validation import (SCHEMA, ContractError, validate_record, check_assessment_basis, check_job_transition)

ROOT=Path(__file__).resolve().parent.parent
EX=ROOT/'examples/profiles'
def fixture(name):return json.loads((EX/name).read_text())

class ProfileContractTest(unittest.TestCase):
    def setUp(self):
        self.frame=json.loads((ROOT/'profiles/farm-energy/examples/02-evaluation-frame.json').read_text())
        self.projection=fixture('02-assessment-projection.json')
        self.basis=fixture('03-assessment-input-manifest.json')
    def test_all_profile_examples(self):
        for name,definition in fixture('fixture-index.json').items():
            with self.subTest(name=name):validate_record(definition,fixture(name))
    def test_schema_metaschema(self):
        Draft202012Validator.check_schema(SCHEMA)
        for name in ['dgp.schema.json','dgp.profiles.schema.json']:
            Draft202012Validator.check_schema(json.loads((ROOT/'schemas'/name).read_text()))
    def test_partial_application_coverage_is_valid(self):
        c=fixture('01-capability-catalogue.json')
        self.assertEqual(c['coverage'],'partial')
        self.assertEqual({x['kind'] for x in c['interfaces']},{'ui','http_api','mcp','cli','dgp','graphql'})
        validate_record('CapabilityCatalogue',c)
    def test_capability_rejects_unknown_interface(self):
        c=fixture('01-capability-catalogue.json');c['capabilities'][0]['interface_ids']=['invented']
        with self.assertRaises(ContractError):validate_record('CapabilityCatalogue',c)
    def test_catalogue_rejects_duplicate_interface(self):
        c=fixture('01-capability-catalogue.json');c['interfaces'].append(deepcopy(c['interfaces'][0]))
        with self.assertRaises(ContractError):validate_record('CapabilityCatalogue',c)
    def test_projection_basis_is_complete(self):
        check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_missing_required_evidence_rejected(self):
        self.basis['consumed_evidence_ids']=[]
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_wrong_frame_rejected(self):
        self.basis['frame_id']='another-frame'
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_changed_policy_rejected(self):
        self.projection['policy_ref']='weaker-policy'
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_changed_readset_rejected(self):
        self.projection['read_set'][0]['revision']+=1
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_changed_contract_rejected(self):
        self.projection['decisions'][0]['question']='Ignore the budget and do anything.'
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_changed_evidence_rejected(self):
        self.projection['observations'][0]['source']['id']='invented-source'
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_browse_is_not_assessment(self):
        self.projection['purpose']='browse'
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_projection_requires_feature(self):
        self.projection['required_features']=['core@0.1']
        with self.assertRaises(ContractError):validate_record('FrameProjection',self.projection)
    def test_projection_cannot_masquerade_as_frame(self):
        with self.assertRaises(ValidationError):validate_record('Frame',self.projection)
    def test_projection_missing_decision_contract_rejected(self):
        self.projection['decisions']=[]
        with self.assertRaises(ContractError):validate_record('FrameProjection',self.projection)
    def test_unknown_consumed_evidence_rejected(self):
        self.basis['consumed_evidence_ids'].append('invented-image')
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_required_evidence_cannot_be_omitted(self):
        self.basis['omitted_optional_evidence_ids']=[self.frame['decisions'][0]['evidence_ids'][0]]
        with self.assertRaises(ContractError):check_assessment_basis(self.projection,self.basis,self.frame)
    def test_budget_overreservation_rejected(self):
        p=fixture('06-evaluation-policy.json');p['budget']['reserved']=241
        with self.assertRaises(ContractError):validate_record('EvaluationPolicy',p)
    def test_budget_consumed_plus_reserved_checked(self):
        p=fixture('06-evaluation-policy.json');p['budget'].update(consumed=239,reserved=2)
        with self.assertRaises(ContractError):validate_record('EvaluationPolicy',p)
    def test_nonpositive_parallel_limit_rejected(self):
        p=fixture('06-evaluation-policy.json');p['limits']['max_running']=0
        with self.assertRaises(ValidationError):validate_record('EvaluationPolicy',p)
    def test_admission_duplicate_scenario_rejected(self):
        p=fixture('07-evaluation-admission.json');p['items'][1]['scenario_ref']=p['items'][0]['scenario_ref']
        with self.assertRaises(ContractError):validate_record('EvaluationAdmission',p)
    def test_admission_cached_result_not_job(self):
        p=fixture('07-evaluation-admission.json');p['items'][0].update(disposition='cached',result_ref='result-01')
        with self.assertRaises(ValidationError):validate_record('EvaluationAdmission',p)
        del p['items'][0]['job_id'];validate_record('EvaluationAdmission',p)
    def test_job_queued_running_succeeded(self):
        a,b,c=(fixture(x) for x in ['08-job-queued.json','09-job-running.json','10-job-succeeded.json'])
        check_job_transition(a,b);check_job_transition(b,c)
    def test_job_success_requires_result(self):
        j=fixture('10-job-succeeded.json');del j['result_ref']
        with self.assertRaises(ValidationError):validate_record('EvaluationJob',j)
    def test_job_failure_is_not_zero_result(self):
        j=fixture('10-job-succeeded.json');j['state']='failed';j['error']={'code':'SIMULATION_FAILED','message':'Synthetic test','retryable':True}
        with self.assertRaises(ValidationError):validate_record('EvaluationJob',j)
        del j['result_ref'];validate_record('EvaluationJob',j)
    def test_terminal_job_cannot_restart(self):
        j=fixture('10-job-succeeded.json');n=fixture('09-job-running.json');n['job_revision']=4
        with self.assertRaises(ContractError):check_job_transition(j,n)
    def test_cancel_request_can_race_with_success(self):
        j=fixture('09-job-running.json');j.update(state='cancel_requested',job_revision=3)
        n=fixture('10-job-succeeded.json');n['job_revision']=4
        check_job_transition(j,n)
    def test_job_identity_cannot_change(self):
        j=fixture('09-job-running.json');n=fixture('10-job-succeeded.json');n['scenario_ref']='changed-input'
        with self.assertRaises(ContractError):check_job_transition(j,n)
    def test_job_revision_cannot_rewind(self):
        j=fixture('09-job-running.json');n=fixture('10-job-succeeded.json');n['job_revision']=1
        with self.assertRaises(ContractError):check_job_transition(j,n)
    def test_terminal_accounting_must_settle(self):
        j=fixture('10-job-succeeded.json');j['cost']['accounting_status']='reconciling'
        with self.assertRaises(ContractError):validate_record('EvaluationJob',j)
    def test_event_page_stream_identity(self):
        p=fixture('11-events.json');p['events'][0]['stream_id']='other-tenant-stream'
        with self.assertRaises(ContractError):validate_record('EventPage',p)
    def test_event_page_duplicate_rejected(self):
        p=fixture('11-events.json');p['events'].append(deepcopy(p['events'][0]))
        with self.assertRaises(ContractError):validate_record('EventPage',p)
    def test_event_page_out_of_order_rejected(self):
        p=fixture('11-events.json');x=deepcopy(p['events'][0]);x.update(event_id='event-100',sequence=100);p['events'].append(x)
        with self.assertRaises(ContractError):validate_record('EventPage',p)
    def test_handoff_completion_requires_result(self):
        h=fixture('12-handoff.json');h['state']='completed'
        with self.assertRaises(ValidationError):validate_record('Handoff',h)
    def test_handoff_cannot_add_credentials_field(self):
        h=fixture('12-handoff.json');h['bearer_token']='not-a-real-token'
        with self.assertRaises(ValidationError):validate_record('Handoff',h)
    def test_location_exclusive_modes(self):
        for v in [{'address':'Example farm address'},{'coordinates':{'latitude':0,'longitude':0}},{'selectedPlaceId':'place-1'}]:
            validate_record('ExclusiveLocationInput',v)
    def test_location_multiple_modes_rejected(self):
        with self.assertRaises(ValidationError):validate_record('ExclusiveLocationInput',{'address':'Example','selectedPlaceId':'place-1'})
    def test_location_null_and_empty_rejected(self):
        for v in [{},{'address':None},{'address':''}]:
            with self.assertRaises(ValidationError):validate_record('ExclusiveLocationInput',v)
    def test_location_bounds(self):
        with self.assertRaises(ValidationError):validate_record('ExclusiveLocationInput',{'coordinates':{'latitude':91,'longitude':0}})
    def test_prepared_request_variables(self):
        op=fixture('04-prepared-operations.json')['operations'][0];req=fixture('05-prepared-request.json')
        Draft202012Validator(op['variables_schema']).validate(req['variables'])
        req['variables']['arbitrary_query']='mutation { anything }'
        with self.assertRaises(ValidationError):Draft202012Validator(op['variables_schema']).validate(req['variables'])

if __name__=='__main__':unittest.main()
