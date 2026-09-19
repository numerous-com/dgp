"""Selected optional-profile invariants, not registration or execution services."""

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


class ProfileError(ValueError):
    pass


def fingerprint(value):
    """Example publisher-local encoding; not a cross-language canonicalization claim."""
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def validate_record(definition, value):
    json.dumps(value, allow_nan=False)
    schema = json.loads((ROOT / "profiles/jev-harness/schema.json").read_text())
    Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + definition},
                        format_checker=FormatChecker()).validate(value)


def check_batch_envelope(request, frame):
    """Envelope/basis only: answer/ownership errors belong to per-item core processing."""
    validate_record("AssessmentBatchRequest", request)
    validate_record("Frame", frame)
    if request["frame_id"] != frame["frame_id"]:
        raise ProfileError("mixed_frame")
    basis = request["shared_basis"]
    if basis["frame_sha256"] != fingerprint(frame):
        raise ProfileError("changed_frame")
    offered = {d["decision_id"]: d for d in frame["decisions"]}
    observations = {e["evidence_id"]: e for e in frame["observations"]}
    if len(offered) != len(frame["decisions"]) or len(observations) != len(frame["observations"]):
        raise ProfileError("duplicate_frame_identifier")
    evidence = {e["evidence_id"]: e["sha256"] for e in basis["evidence"]}
    if len(evidence) != len(basis["evidence"]):
        raise ProfileError("duplicate_evidence")
    if any(key not in observations or sha != fingerprint(observations[key])
           for key, sha in evidence.items()):
        raise ProfileError("changed_evidence")
    ids, decisions = set(), set()
    for item in request["items"]:
        if item["assessment_id"] in ids or item["decision_id"] in decisions:
            raise ProfileError("duplicate_item")
        ids.add(item["assessment_id"])
        decisions.add(item["decision_id"])
        if item["frame_id"] != frame["frame_id"] or item["decision_id"] not in offered:
            raise ProfileError("decision_not_offered")
        decision = offered[item["decision_id"]]
        for key in decision["evidence_ids"]:
            if key not in observations:
                raise ProfileError("frame_missing_evidence")
            if observations[key]["required"] and key not in evidence:
                raise ProfileError("required_evidence_missing")


def check_batch_response(request, response):
    validate_record("AssessmentBatchRequest", request)
    validate_record("AssessmentBatchResponse", response)
    if any(request[k] != response[k] for k in ("batch_id", "frame_id")):
        raise ProfileError("response_binding")
    if len(response["items"]) != len(request["items"]):
        raise ProfileError("response_item_count")
    for sent, got in zip(request["items"], response["items"], strict=True):
        if any(sent[k] != got[k] for k in ("assessment_id", "frame_id", "decision_id")):
            raise ProfileError("response_item_binding")
        if "assessment" in got:
            recorded = got["assessment"]
            if not set(sent) <= set(recorded) or fingerprint({k: recorded[k] for k in sent}) != fingerprint(sent):
                raise ProfileError("recorded_assessment_changed")
    calls = response["usage"]
    if len({c["call_id"] for c in calls}) != len(calls):
        raise ProfileError("duplicate_usage")
    for call in calls:
        if call["estimated_usd"] is not None and not call["estimate_basis"]:
            raise ProfileError("missing_estimate_basis")


def check_coding_catalogue(catalogue):
    validate_record("CodingOperationCatalogue", catalogue)
    seen = set()
    for operation in catalogue["operations"]:
        name, effect = operation["canonical_operation_id"], operation["effect"]
        if name in seen:
            raise ProfileError("duplicate_operation")
        seen.add(name)
        expected = "read" if name.startswith("repo.") else {
            "patch.prepare": "prepare", "patch.apply": "guarded_apply", "tests.run": "sandboxed_test"
        }[name]
        if operation["execution"] != expected:
            raise ProfileError("operation_execution_mismatch")
        if expected == "read" and effect["world_mutation"] != "none":
            raise ProfileError("read_mutation")
        if expected != "read" and effect["world_mutation"] == "none":
            raise ProfileError("effectful_operation_labeled_pure")
        if name in ("patch.apply", "tests.run") and effect["speculation"] != "forbidden":
            raise ProfileError("unguarded_speculation")
        Draft202012Validator.check_schema(operation["variables_schema"])


def check_artifact(binding):
    validate_record("CodingArtifactBinding", binding)
    paths = [item["path"] for item in binding["preimages"]]
    if len(set(paths)) != len(paths):
        raise ProfileError("duplicate_preimage")
    for path in paths:
        if path.startswith("/") or "\\" in path or ":" in path or "\x00" in path or any(p in ("", ".", "..") for p in path.split("/")):
            raise ProfileError("invalid_relative_path")
    # Deliberately no filesystem access: symlink/root authorization is executor work.
