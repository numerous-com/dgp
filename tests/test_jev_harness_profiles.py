"""Offline checks for selected contracts; no server, provider or executor launched."""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import ValidationError

from profile_support.jev_harness import (
    ProfileError,
    check_artifact,
    check_batch_envelope,
    check_batch_response,
    check_coding_catalogue,
    fingerprint,
    validate_record,
)

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text())


class HarnessProfileTests(unittest.TestCase):
    def setUp(self):
        self.frame = read("examples/02-frame-next.json")
        self.request = read("profiles/jev-harness/examples/01-batch-request.json")
        self.response = read("profiles/jev-harness/examples/02-batch-partial-response.json")
        self.catalogue = read("profiles/jev-harness/examples/03-coding-catalogue.json")
        self.artifact = read("profiles/jev-harness/examples/04-patch-artifact-binding.json")

    def bind(self):
        self.request["shared_basis"] = {
            "frame_sha256": fingerprint(self.frame),
            "evidence": [{"evidence_id": e["evidence_id"], "sha256": fingerprint(e)}
                         for e in self.frame["observations"]],
        }

    def test_examples_validate_with_partial_item_error(self):
        check_batch_envelope(self.request, self.frame)
        check_batch_response(self.request, self.response)
        check_coding_catalogue(self.catalogue)
        check_artifact(self.artifact)
        self.assertIn("assessment", self.response["items"][0])
        self.assertIn("error", self.response["items"][1])
        self.assertEqual(self.response["usage"], [])

    def test_template_node_is_not_an_offered_decision(self):
        self.request["items"][1]["decision_id"] = self.frame["frame_id"] + ":future-review"
        with self.assertRaisesRegex(ProfileError, "decision_not_offered"):
            check_batch_envelope(self.request, self.frame)

    def test_duplicate_assessment_and_decision_ids_rejected(self):
        for field in ("assessment_id", "decision_id"):
            request = copy.deepcopy(self.request)
            request["items"][1][field] = request["items"][0][field]
            with self.assertRaisesRegex(ProfileError, "duplicate_item"):
                check_batch_envelope(request, self.frame)

    def test_changed_frame_and_required_evidence_rejected(self):
        self.frame["observations"][0]["content"]["retries"] = 999
        with self.assertRaisesRegex(ProfileError, "changed_frame"):
            check_batch_envelope(self.request, self.frame)
        self.bind()
        self.request["shared_basis"]["evidence"].pop()
        with self.assertRaisesRegex(ProfileError, "required_evidence_missing"):
            check_batch_envelope(self.request, self.frame)

    def test_changed_evidence_hash_and_mixed_frame_rejected(self):
        self.request["shared_basis"]["evidence"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ProfileError, "changed_evidence"):
            check_batch_envelope(self.request, self.frame)
        self.bind()
        self.request["items"][1]["frame_id"] = "another-frame"
        with self.assertRaisesRegex(ProfileError, "decision_not_offered"):
            check_batch_envelope(self.request, self.frame)

    def test_zero_required_evidence_is_valid(self):
        self.frame["observations"] = []
        for decision in self.frame["decisions"]:
            decision["evidence_ids"] = []
        self.bind()
        check_batch_envelope(self.request, self.frame)

    def test_speculative_mode_preserved_never_promoted_by_response(self):
        self.request["items"][0]["mode"] = "speculative"
        check_batch_envelope(self.request, self.frame)
        with self.assertRaisesRegex(ProfileError, "recorded_assessment_changed"):
            check_batch_response(self.request, self.response)

    def test_response_requires_all_item_bindings_in_order(self):
        response = copy.deepcopy(self.response)
        response["items"].reverse()
        with self.assertRaisesRegex(ProfileError, "response_item_binding"):
            check_batch_response(self.request, response)
        response = copy.deepcopy(self.response)
        response["items"].pop()
        with self.assertRaisesRegex(ProfileError, "response_item_count"):
            check_batch_response(self.request, response)
        del self.response["items"][1]["decision_id"]
        with self.assertRaises(ValidationError):
            check_batch_response(self.request, self.response)

    def test_recorded_input_does_not_equate_boolean_and_integer(self):
        self.request["items"][0]["result"]["answer"]["input"] = {"flag": True}
        self.response["items"][0]["assessment"]["result"]["answer"]["input"] = {"flag": 1}
        with self.assertRaisesRegex(ProfileError, "recorded_assessment_changed"):
            check_batch_response(self.request, self.response)

    def test_usage_once_unknown_preserved_estimate_requires_basis(self):
        usage = {"call_id": "example-call", "provider": "fixture", "model": "no-model-called",
                 "input_tokens": None, "output_tokens": None,
                 "reported_usd": None, "estimated_usd": None, "estimate_basis": None}
        self.response["usage"] = [usage]
        check_batch_response(self.request, self.response)
        self.response["usage"].append(copy.deepcopy(usage))
        with self.assertRaisesRegex(ProfileError, "duplicate_usage"):
            check_batch_response(self.request, self.response)
        self.response["usage"] = [{**usage, "estimated_usd": 0.1}]
        with self.assertRaisesRegex(ProfileError, "missing_estimate_basis"):
            check_batch_response(self.request, self.response)

    def test_no_nonfinite_cost(self):
        self.response["usage"] = [{"call_id": "x", "provider": "fixture", "model": "fixture",
            "input_tokens": None, "output_tokens": None, "reported_usd": float("nan"),
            "estimated_usd": None, "estimate_basis": None}]
        with self.assertRaises(ValueError):
            check_batch_response(self.request, self.response)

    def test_tests_and_apply_cannot_claim_read_only_or_speculative(self):
        for name in ("patch.apply", "tests.run"):
            catalogue = copy.deepcopy(self.catalogue)
            op = next(o for o in catalogue["operations"] if o["canonical_operation_id"] == name)
            op["effect"]["world_mutation"] = "none"
            with self.assertRaisesRegex(ProfileError, "labeled_pure"):
                check_coding_catalogue(catalogue)
            op["effect"]["world_mutation"] = "internal"
            op["effect"]["speculation"] = "evaluation_only"
            with self.assertRaisesRegex(ProfileError, "unguarded_speculation"):
                check_coding_catalogue(catalogue)

    def test_catalogue_is_fixed_operation_allowlist(self):
        self.catalogue["operations"][0]["canonical_operation_id"] = "shell.arbitrary"
        with self.assertRaises(ValidationError):
            check_coding_catalogue(self.catalogue)

    def test_patch_paths_require_unique_portable_relative_preimages(self):
        for path in ("../secret", "/etc/passwd", "C:secret", "C:/secret", "a\\b", "a\x00b"):
            artifact = copy.deepcopy(self.artifact)
            artifact["preimages"][0]["path"] = path
            with self.assertRaisesRegex(ProfileError, "invalid_relative_path"):
                check_artifact(artifact)
        self.artifact["preimages"].append(copy.deepcopy(self.artifact["preimages"][0]))
        with self.assertRaisesRegex(ProfileError, "duplicate_preimage"):
            check_artifact(self.artifact)

    def test_core_definitions_unchanged_in_extension(self):
        core = read("schemas/dgp.schema.json")["$defs"]
        extended = read("profiles/jev-harness/schema.json")["$defs"]
        self.assertEqual({k: extended[k] for k in core}, core)
        validate_record("Frame", self.frame)


if __name__ == "__main__":
    unittest.main()
