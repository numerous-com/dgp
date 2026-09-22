"""Selected task-profile contract checks, not a task server or authorization layer."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from profile_support.jev_harness import ProfileError, fingerprint

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "harness-tasks@0.1"


def validate_record(definition, value):
    json.dumps(value, allow_nan=False)
    schema = json.loads((ROOT / "profiles/harness-tasks/schema.json").read_text())
    Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + definition},
                        format_checker=FormatChecker()).validate(value)


def check_task_frame(frame, arguments):
    validate_record("TaskFrame", frame)
    binding = frame["extensions"][PROFILE]
    if binding["arguments_sha256"] != fingerprint(arguments):
        raise ProfileError("task_arguments_changed")
    if len(frame["decisions"]) != 1:
        raise ProfileError("one_task_decision_required")
    decision = frame["decisions"][0]
    if (decision["kind"] != "choice" or decision["node_id"] != binding["operation"]
            or len(decision["options"]) != 2
            or {option["id"] for option in decision["options"]} != {"execute", "stop"}):
        raise ProfileError("invalid_task_options")
    observed = {row["evidence_id"]: row for row in frame["observations"]}
    if (not decision["evidence_ids"] or any(key not in observed for key in decision["evidence_ids"])
            or not any(observed[key]["required"] for key in decision["evidence_ids"])):
        raise ProfileError("task_basis_missing")
    for option in decision["options"]:
        schema = option["input_schema"]
        if schema != {"type": "object", "additionalProperties": False}:
            raise ProfileError("task_arguments_must_be_prepared")
        if option["effect"]["simulation"] is not False:
            raise ProfileError("task_effect_must_not_claim_simulation")
    return binding


def check_task_commit(frame, assessment, commit):
    """Record consistency only. Freshness, identity and replay require durable host guards."""
    validate_record("TaskFrame", frame)
    validate_record("AssessmentRequest", assessment)
    validate_record("CommitRequest", commit)
    decision = frame["decisions"][0]
    if assessment["mode"] != "live":
        raise ProfileError("speculative_task_commit_forbidden")
    if (assessment["frame_id"] != frame["frame_id"]
            or assessment["decision_id"] != decision["decision_id"]
            or any(commit[key] != assessment[key] for key in
                   ("frame_id", "decision_id", "assessment_id"))):
        raise ProfileError("task_commit_binding_mismatch")
    result = assessment["result"]
    answer = result.get("answer", {})
    if (result["status"] != "answered" or set(answer) != {"choice", "input"}
            or answer["choice"] not in {"execute", "stop"} or answer["input"] != {}):
        raise ProfileError("task_arguments_must_be_prepared")


def check_task_receipt(frame, assessment, receipt):
    validate_record("TaskReceipt", receipt)
    if any(receipt[key] != assessment[key] for key in
           ("frame_id", "decision_id", "assessment_id")):
        raise ProfileError("task_receipt_binding_mismatch")
    binding = frame["extensions"][PROFILE]
    value = receipt["extensions"][PROFILE]
    if any(value[key] != binding[key] for key in ("task_id", "operation", "arguments_sha256")):
        raise ProfileError("task_receipt_binding_mismatch")
    if value["task_revision"] < binding["task_revision"]:
        raise ProfileError("task_revision_regressed")
    if binding["operation"] != "artifact.apply" and value["admission_status"] == "applied":
        raise ProfileError("admission_is_not_application")


def check_task_watch(page, *, host_id, task_id, stream_id, after=0):
    validate_record("TaskWatchPage", page)
    if any(page[key] != expected for key, expected in
           (("host_id", host_id), ("task_id", task_id), ("stream_id", stream_id))):
        raise ProfileError("task_cursor_scope_mismatch")
    if type(after) is not int or after < 0:
        raise ProfileError("invalid_task_cursor")
    if page["gap"]:
        if (page["events"] or page["next_cursor"] is not None or page["has_more"]
                or page.get("rebootstrap_required") is not True):
            raise ProfileError("invalid_task_gap")
        return
    if page.get("rebootstrap_required") is True:
        raise ProfileError("invalid_task_gap")
    expected = list(range(after + 1, after + 1 + len(page["events"])))
    if [row["sequence"] for row in page["events"]] != expected:
        raise ProfileError("task_event_gap_or_duplicate")
    if page["has_more"] and (not page["events"] or page["next_cursor"] is None):
        raise ProfileError("task_watch_cannot_advance")


def check_task_artifact(artifact):
    validate_record("TaskArtifact", artifact)
    paths = [row["path"] for row in artifact["preimages"]]
    if len(paths) != len(set(paths)):
        raise ProfileError("duplicate_artifact_path")
    if any(path.startswith(("/", "\\")) or "\\" in path
           or any(part in {"", ".", ".."} for part in path.split("/")) for path in paths):
        raise ProfileError("invalid_artifact_path")
