"""Selected normative contract checks for DGP optional profiles.

These helpers demonstrate testable invariants. They do not authenticate a caller,
fetch evidence, run a model, or provide a production scheduler.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parent.parent
SCHEMA=json.loads((ROOT/'schemas/dgp.profiles.schema.json').read_text())

class ContractError(ValueError):
    """Semantic contract violation."""

def validate_record(definition: str, value: Any) -> None:
    if definition not in SCHEMA['$defs']:
        raise ContractError(f'Unknown record definition: {definition}')
    schema={'$schema':SCHEMA['$schema'],'$defs':SCHEMA['$defs'],'$ref':'#/$defs/'+definition}
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(value)
    if definition=='CapabilityCatalogue':
        interfaces=[i['interface_id'] for i in value['interfaces']]
        capabilities=[c['capability_id'] for c in value['capabilities']]
        if len(set(interfaces))!=len(interfaces) or len(set(capabilities))!=len(capabilities):
            raise ContractError('Duplicate catalogue identifier')
        for c in value['capabilities']:
            if not set(c['interface_ids'])<=set(interfaces):
                raise ContractError('Capability names an unknown interface')
    elif definition=='EvaluationPolicy':
        b=value['budget']
        if b['consumed']+b['reserved']>b['limit']:
            raise ContractError('Budget ceiling exceeded')
    elif definition=='EvaluationAdmission':
        refs=[x['scenario_ref'] for x in value['items']]
        if len(set(refs))!=len(refs):raise ContractError('Duplicate scenario mapping')
    elif definition=='EvaluationJob':
        if value['state'] in {'succeeded','failed','cancelled'} and value['cost']['accounting_status']!='settled':
            raise ContractError('Terminal evaluation requires settled accounting')
        if value['cost']['accounting_status']=='settled' and value['cost']['reserved_units']!=0:
            raise ContractError('Settled accounting retains a reservation')
    elif definition=='EventPage':
        events=value['events']
        seq=[e['sequence'] for e in events]
        ids=[e['event_id'] for e in events]
        if any(e['stream_id']!=value['stream_id'] for e in events):raise ContractError('Mixed event streams')
        if seq!=sorted(set(seq)) or len(set(ids))!=len(ids):raise ContractError('Unordered/duplicate event page')
    elif definition=='FrameProjection':
        _check_projection_shape(value)

def _check_projection_shape(p: dict[str,Any]) -> None:
    ids=[d['decision_id'] for d in p['decisions']]
    evidence=[o['evidence_id'] for o in p['observations']]
    manifest=[x['evidence_id'] for x in p['evidence_manifest']]
    if len(set(ids))!=len(ids) or len(set(evidence))!=len(evidence) or len(set(manifest))!=len(manifest):
        raise ContractError('Duplicate materialized identifier')
    if p['purpose']=='assess' and set(ids)!=set(p['decision_scope']):
        raise ContractError('Assessment projection lacks complete decision scope')
    for x in p['evidence_manifest']:
        if x['status']=='included' and x['evidence_id'] not in evidence:
            raise ContractError('Included evidence was not materialized')
    if 'frame-projections@0.1' not in p['required_features']:
        raise ContractError('Missing projection feature requirement')

def check_assessment_basis(projection: dict[str,Any], basis: dict[str,Any], canonical: dict[str,Any]) -> None:
    """Check an already-hydrated basis. Consumption remains a client assertion."""
    validate_record('FrameProjection',projection)
    validate_record('AssessmentInputManifest',basis)
    validate_record('Frame',canonical)
    if projection['purpose']!='assess':raise ContractError('Browse view is not assessment-ready')
    for key in ['frame_id','surface_id','graph_id','graph_version','policy_ref','created_at','expires_at','read_set']:
        if projection[key]!=canonical[key]:raise ContractError(f'Projection changed canonical {key}')
    if basis['frame_id']!=canonical['frame_id']:raise ContractError('Mixed frame basis')
    if projection['projection_id'] not in basis['projection_ids']:raise ContractError('Unbound projection')
    decisions={d['decision_id']:d for d in canonical['decisions']}
    observations={o['evidence_id']:o for o in canonical['observations']}
    for d in projection['decisions']:
        if d!=decisions.get(d['decision_id']):raise ContractError('Projected contract was altered')
    for o in projection['observations']:
        if o!=observations.get(o['evidence_id']):raise ContractError('Projected evidence was altered')
    did=basis['decision_id']
    if did not in projection['decision_scope'] or did not in decisions:raise ContractError('Decision outside projection scope')
    decision=decisions[did]
    required={eid for eid in decision['evidence_ids'] if observations[eid]['required']}
    consumed=set(basis['consumed_evidence_ids'])
    omitted=set(basis['omitted_optional_evidence_ids'])
    if not consumed<=set(observations):raise ContractError('Unknown consumed evidence')
    if not required<=consumed:raise ContractError('Required evidence was not consumed')
    if omitted & consumed or omitted & required:raise ContractError('Invalid evidence omission')
    if not omitted<=set(decision['evidence_ids']):raise ContractError('Unknown omitted evidence')

TRANSITIONS={
 'queued':{'running','cancelled','failed'},
 'running':{'succeeded','failed','cancel_requested','reconciling'},
 'cancel_requested':{'cancelled','succeeded','failed','reconciling'},
 'reconciling':{'running','succeeded','failed','cancelled'},
 'succeeded':set(),'failed':set(),'cancelled':set(),
}
def check_job_transition(old: dict[str,Any], new: dict[str,Any]) -> None:
    # Check adjacent persisted snapshots, not arbitrary nonadjacent polling reads.
    validate_record('EvaluationJob',old);validate_record('EvaluationJob',new)
    for k in ['job_id','study_ref','scenario_ref','source_frame_id','admission_receipt_id','canonical_operation_id','accepted_at']:
        if old[k]!=new[k]:raise ContractError(f'Job identity changed: {k}')
    if old['state'] in {'succeeded','failed','cancelled'}:
        raise ContractError('Terminal job is immutable; retries require a new job')
    if new['job_revision']!=old['job_revision']+1:raise ContractError('Nonconsecutive job revision')
    if new['state']!=old['state'] and new['state'] not in TRANSITIONS[old['state']]:
        raise ContractError('Invalid job state transition')
