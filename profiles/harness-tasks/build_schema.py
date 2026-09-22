"""Optional harness task records; copy, never edit, DGP 0.1 core definitions."""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PROFILE = "harness-tasks@0.1"


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


def build():
    definitions = copy.deepcopy(json.loads((ROOT / "schemas/dgp.schema.json").read_text())["$defs"])
    ident = {"type": "string", "minLength": 1, "maxLength": 512}
    revision = {"type": "integer", "minimum": 0}
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    operations = {"enum": ["task.start", "task.steer", "task.stop", "artifact.apply"]}
    binding = {"task_id": ident, "operation": operations,
               "task_revision": revision, "arguments_sha256": sha}
    definitions["TaskFrameExtension"] = obj(binding)
    definitions["TaskReceiptExtension"] = obj({**binding, "admission_status": {
        "enum": ["queued", "requested", "applied", "declined"]}})
    for name, core, extension in (("TaskFrame", "Frame", "TaskFrameExtension"),
                                   ("TaskReceipt", "Receipt", "TaskReceiptExtension")):
        extra = {"properties": {"extensions": {
            "type": "object", "properties": {PROFILE: {"$ref": "#/$defs/" + extension}},
            "required": [PROFILE]}}, "required": ["extensions"]}
        if name == "TaskFrame":
            extra["properties"]["required_features"] = {"contains": {"const": PROFILE}}
        definitions[name] = {"allOf": [{"$ref": "#/$defs/" + core}, extra]}
    common = {"dgp": {"const": "0.1"}, "profile": {"const": PROFILE}}
    definitions["TaskSnapshot"] = obj({
        **common, "host_id": ident, "task_id": ident, "stream_id": ident, "revision": revision,
        "status": {"enum": ["queued", "running", "completed", "failed", "cancelled", "interrupted"]},
        "request_sha256": sha, "result": {"type": ["object", "null"]},
        "extensions": {"type": "object"},
    }, [*common, "host_id", "task_id", "revision", "status", "request_sha256", "result"])
    definitions["TaskEvent"] = obj({
        "sequence": {"type": "integer", "minimum": 1}, "kind": ident,
        "data": {"type": "object"},
    })
    definitions["TaskWatchPage"] = obj({
        **common, "host_id": ident, "task_id": ident, "stream_id": ident,
        "events": {"type": "array", "items": {"$ref": "#/$defs/TaskEvent"}, "maxItems": 256},
        "next_cursor": {"type": ["string", "null"], "maxLength": 4096},
        "has_more": {"type": "boolean"}, "gap": {"type": "boolean"},
        "rebootstrap_required": {"type": "boolean"},
    }, [*common, "host_id", "task_id", "stream_id", "events", "next_cursor", "has_more", "gap"])
    definitions["TaskArtifact"] = obj({
        "task_id": ident, "artifact_ref": ident, "artifact_sha256": sha,
        "repository_id": ident, "base_revision": ident,
        "preimages": {"type": "array", "minItems": 1, "maxItems": 128,
                      "items": obj({"path": ident, "sha256": {"anyOf": [sha, {"type": "null"}]}})},
    })
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:dgp:harness-tasks:0.1", "$defs": definitions}


if __name__ == "__main__":
    (HERE / "schema.json").write_text(json.dumps(build(), indent=2) + "\n")
