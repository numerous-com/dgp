"""Build a self-contained optional schema without changing DGP core definitions."""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


def array(items, maximum=32):
    return {"type": "array", "items": items, "minItems": 1, "maxItems": maximum}


def build():
    core = json.loads((ROOT / "schemas/dgp.schema.json").read_text())
    definitions = copy.deepcopy(core["$defs"])
    ident = {"type": "string", "minLength": 1, "maxLength": 200}
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    nullable_number = {"type": ["number", "null"], "minimum": 0}
    nullable_tokens = {"type": ["integer", "null"], "minimum": 0}
    definitions["SharedAssessmentBasis"] = obj({
        "frame_sha256": sha,
        "evidence": {**array(obj({"evidence_id": ident, "sha256": sha}), 128), "minItems": 0},
    })
    definitions["AssessmentBatchRequest"] = obj({
        "dgp": {"const": "0.1"}, "profile": {"const": "assessment-batching@0.1"},
        "batch_id": ident, "frame_id": ident,
        "shared_basis": {"$ref": "#/$defs/SharedAssessmentBasis"},
        "items": array({"$ref": "#/$defs/AssessmentRequest"}),
    })
    binding = {"assessment_id": ident, "frame_id": ident, "decision_id": ident}
    definitions["AssessmentBatchItemResult"] = {
        "oneOf": [
            obj({**binding, "assessment": {"$ref": "#/$defs/Assessment"}}),
            obj({**binding, "error": {"$ref": "#/$defs/Problem"}}),
        ]
    }
    definitions["AssessmentCallUsage"] = obj({
        "call_id": ident, "provider": ident, "model": ident,
        "input_tokens": nullable_tokens, "output_tokens": nullable_tokens,
        "reported_usd": nullable_number, "estimated_usd": nullable_number,
        "estimate_basis": {"type": ["string", "null"], "maxLength": 1000},
    })
    definitions["AssessmentBatchResponse"] = obj({
        "dgp": {"const": "0.1"}, "profile": {"const": "assessment-batching@0.1"},
        "batch_id": ident, "frame_id": ident,
        "items": array({"$ref": "#/$defs/AssessmentBatchItemResult"}),
        "usage": {"type": "array", "items": {"$ref": "#/$defs/AssessmentCallUsage"}, "maxItems": 32},
    })
    operations = ["repo.inventory", "repo.read", "repo.search", "repo.gitstatus",
                  "patch.prepare", "patch.apply", "tests.run"]
    definitions["CodingOperationCatalogue"] = obj({
        "dgp": {"const": "0.1"}, "profile": {"const": "coding-tools@0.1"},
        "coverage": {"const": "partial"}, "catalogue_version": ident,
        "operations": array(obj({
            "canonical_operation_id": {"enum": operations},
            "operation_version": ident, "description": {"type": "string", "minLength": 1, "maxLength": 2000},
            "variables_schema": {"type": "object"},
            "effect": {"$ref": "#/$defs/Effect"},
            "execution": {"enum": ["read", "prepare", "guarded_apply", "sandboxed_test"]},
            "implementation": {"enum": ["not_implemented", "installed_adapter"]},
        }), 7),
    })
    definitions["CodingArtifactBinding"] = obj({
        "repository_id": ident, "base_revision": ident, "artifact_ref": ident,
        "artifact_sha256": sha,
        "preimages": array(obj({"path": ident, "sha256": {"anyOf": [sha, {"type": "null"}]}}), 128),
        "ownership": obj({"agent_id": ident, "worktree_id": ident, "branch_ref": ident}),
    })
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:dgp:jev-harness-profiles:0.1", "$defs": definitions}


if __name__ == "__main__":
    (HERE / "schema.json").write_text(json.dumps(build(), indent=2) + "\n")
