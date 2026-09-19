"""Protocol objects shared by the demo, test fixtures, and schema generation."""
from __future__ import annotations
import copy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1"

class Problem(Exception):
    def __init__(self, code: str, detail: str, status: int = 400):
        super().__init__(detail)
        self.code, self.detail, self.status = code, detail, status

    def as_dict(self) -> dict[str, Any]:
        return {"type": f"urn:dgp:problem:{self.code.lower().replace('_', '-')}",
                "title": self.code, "status": self.status, "detail": self.detail,
                "code": self.code, "dgp": VERSION}

def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def stable(value: Any) -> str:
    # Local fingerprint encoding only; NOT an interoperable JSON canonicalization claim.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def digest(value: Any) -> str:
    return hashlib.sha256(stable(value).encode()).hexdigest()

def clone(value: Any) -> Any:
    return copy.deepcopy(value)

def validate_input_schema(schema: dict[str, Any]) -> None:
    """Only server-authored schemas are accepted; never fetch remote schema references."""
    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("$ref", "$dynamicRef"):
                    raise Problem("SCHEMA_UNSUPPORTED", "Input schemas in this demo must be self-contained.", 422)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(schema)
    Draft202012Validator.check_schema(schema)

def validate_payload(schema: dict[str, Any], value: Any) -> None:
    validate_input_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise Problem("INVALID_INPUT", errors[0].message, 422)

def empty_input() -> dict[str, Any]:
    return {"type": "object", "properties": {}, "additionalProperties": False}

def text_input(name: str, maximum: int = 4000) -> dict[str, Any]:
    return {"type": "object", "properties": {name: {"type": "string", "minLength": 1, "maxLength": maximum}},
            "required": [name], "additionalProperties": False}

def effect(*, mutation: str = "internal", recovery: str = "unknown", human: bool = False) -> dict[str, Any]:
    return {"world_mutation": mutation, "recovery": recovery, "data_egress": "none",
            "speculation": "forbidden", "required_actor": "human" if human else "any_authorized",
            "simulation": True}

def option(oid: str, label: str, meaning: str, *, human: bool = False) -> dict[str, Any]:
    return {"id": oid, "label": label, "meaning": meaning, "input_schema": empty_input(),
            "effect": effect(mutation="external" if human else "internal",
                             recovery="irreversible" if human else "unknown", human=human)}

def validate_result(decision: dict[str, Any], result: dict[str, Any]) -> None:
    """Additional semantic validation beyond the structural JSON Schema."""
    if result.get("status") == "abstain":
        return
    if result.get("status") != "answered":
        raise Problem("INVALID_ANSWER", "Expected answered or abstain.", 422)
    answer = result.get("answer")
    if not isinstance(answer, dict):
        raise Problem("INVALID_ANSWER", "Answer must be an object.", 422)
    kind = decision["kind"]
    if kind == "choice":
        if set(answer) != {"choice", "input"}:
            raise Problem("INVALID_ANSWER", "Choice answers require only choice and input.", 422)
        chosen = next((o for o in decision["options"] if o["id"] == answer.get("choice")), None)
        if not chosen:
            raise Problem("INVALID_CHOICE", "Selected option was not offered in this frame.", 422)
        validate_payload(chosen["input_schema"], answer["input"])
    elif kind == "input":
        if set(answer) != {"value"}:
            raise Problem("INVALID_ANSWER", "Input answers require only value.", 422)
        validate_payload(decision["input_schema"], answer["value"])
    elif kind == "probability":
        p = answer.get("probability")
        if set(answer) != {"probability"} or type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
            raise Problem("INVALID_ANSWER", "Probability must be finite and between zero and one.", 422)
    elif kind == "score":
        p = answer.get("score")
        if set(answer) != {"score"} or type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= len(decision["levels"]) - 1:
            raise Problem("INVALID_ANSWER", "Score must be within the zero-based rubric range.", 422)
    else:
        raise Problem("UNSUPPORTED_KIND", kind, 422)
    u = result.get("uncertainty", {})
    distribution = u.get("distribution")
    if distribution is not None:
        expected = ({o["id"] for o in decision["options"]} if kind == "choice"
                    else {str(i) for i in range(len(decision.get("levels", [])))})
        if kind not in ("choice", "score") or set(distribution) != expected:
            raise Problem("INVALID_DISTRIBUTION", "Distribution keys must exactly match this decision's options or levels.", 422)
        values = list(distribution.values())
        if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values) or abs(sum(values) - 1) > 1e-6:
            raise Problem("INVALID_DISTRIBUTION", "Probabilities must be finite, in [0,1], and sum to one.", 422)
