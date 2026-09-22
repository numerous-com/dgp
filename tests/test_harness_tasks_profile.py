"""Offline contracts, not evidence of a running harness task service."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import ValidationError

from profile_support.harness_tasks import (
    PROFILE, check_task_artifact, check_task_commit, check_task_frame,
    check_task_receipt, check_task_watch, validate_record,
)
from profile_support.jev_harness import ProfileError

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'profiles/harness-tasks/examples' / (name + '.json')).read_text())


class TaskProfileTests(unittest.TestCase):
    def setUp(self):
        self.frame = read('01-frame')
        self.assessment = read('02-assessment')
        self.commit = read('03-commit')
        self.receipt = read('04-receipt')
        self.page = read('06-watch')

    def test_examples_and_core_records_validate(self):
        check_task_frame(self.frame, read('08-arguments'))
        check_task_commit(self.frame, self.assessment, self.commit)
        check_task_receipt(self.frame, self.assessment, self.receipt)
        validate_record('TaskSnapshot', read('05-snapshot'))
        check_task_artifact(read('07-artifact'))
        self.watch(self.page)
        for definition, record in [('Frame', self.frame), ('AssessmentRequest', self.assessment),
                                   ('CommitRequest', self.commit), ('Receipt', self.receipt)]:
            validate_record(definition, record)

    def test_core_definitions_unchanged_and_generated_schema_reproducible(self):
        schema = json.loads((ROOT / 'profiles/harness-tasks/schema.json').read_text())
        core = json.loads((ROOT / 'schemas/dgp.schema.json').read_text())
        for name, definition in core['$defs'].items():
            self.assertEqual(schema['$defs'][name], definition)
        spec = importlib.util.spec_from_file_location('task_builder', ROOT / 'profiles/harness-tasks/build_schema.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.build(), schema)

    def test_arguments_are_bound_before_commit(self):
        arguments = read('08-arguments')
        arguments['request']['enrich'] = 1
        with self.assertRaisesRegex(ProfileError, 'task_arguments_changed'):
            check_task_frame(self.frame, arguments)
        self.assessment['result']['answer']['input'] = {'command': 'unoffered'}
        with self.assertRaisesRegex(ProfileError, 'must_be_prepared'):
            check_task_commit(self.frame, self.assessment, self.commit)

    def test_speculative_and_mismatched_commits_rejected(self):
        self.assessment['mode'] = 'speculative'
        with self.assertRaisesRegex(ProfileError, 'speculative_task_commit'):
            check_task_commit(self.frame, self.assessment, self.commit)
        self.assessment['mode'] = 'live'
        self.commit['assessment_id'] = 'different'
        with self.assertRaisesRegex(ProfileError, 'binding_mismatch'):
            check_task_commit(self.frame, self.assessment, self.commit)

    def test_task_operations_and_extensions_are_negotiated(self):
        self.frame['extensions'][PROFILE]['operation'] = 'shell.exec'
        with self.assertRaises(ValidationError):
            validate_record('TaskFrame', self.frame)
        self.frame = read('01-frame')
        self.frame['required_features'].remove(PROFILE)
        with self.assertRaises(ValidationError):
            validate_record('TaskFrame', self.frame)

    def test_admission_is_not_application_or_task_completion(self):
        self.receipt['extensions'][PROFILE]['admission_status'] = 'applied'
        with self.assertRaisesRegex(ProfileError, 'not_application'):
            check_task_receipt(self.frame, self.assessment, self.receipt)
        self.receipt['extensions'][PROFILE]['admission_status'] = 'completed'
        with self.assertRaises(ValidationError):
            validate_record('TaskReceipt', self.receipt)

    def test_receipt_cannot_change_task_or_artifact_arguments(self):
        for field, value in [('task_id', 'another'), ('arguments_sha256', '0' * 64)]:
            receipt = copy.deepcopy(self.receipt)
            receipt['extensions'][PROFILE][field] = value
            with self.assertRaisesRegex(ProfileError, 'binding_mismatch'):
                check_task_receipt(self.frame, self.assessment, receipt)

    def watch(self, page, **kwargs):
        return check_task_watch(page, host_id='host-demo', task_id='task-demo-1', stream_id='stream-demo-1', **kwargs)

    def test_watch_is_scoped_contiguous_and_not_a_hidden_gap(self):
        for field in ('host_id', 'task_id', 'stream_id'):
            page = copy.deepcopy(self.page)
            page[field] = 'different'
            with self.assertRaisesRegex(ProfileError, 'scope_mismatch'):
                self.watch(page)
        for sequence in (0, 2):
            page = copy.deepcopy(self.page)
            page['events'][0]['sequence'] = sequence
            with self.assertRaises((ProfileError, ValidationError)):
                self.watch(page)
        self.page['events'].append(copy.deepcopy(self.page['events'][0]))
        with self.assertRaisesRegex(ProfileError, 'gap_or_duplicate'):
            self.watch(self.page)

    def test_gap_requires_explicit_rebootstrap_and_no_fake_continuation(self):
        self.page.update(gap=True, events=[], next_cursor=None, has_more=False, rebootstrap_required=True)
        self.watch(self.page)
        self.page.pop('rebootstrap_required')
        with self.assertRaisesRegex(ProfileError, 'invalid_task_gap'):
            self.watch(self.page)

    def test_artifact_requires_exact_hash_and_relative_unique_preimages(self):
        artifact = read('07-artifact')
        artifact['artifact_sha256'] = 'latest'
        with self.assertRaises(ValidationError):
            check_task_artifact(artifact)
        for path in ('../outside.py', '/root/private', 'a/../b', 'a\\b'):
            artifact = read('07-artifact')
            artifact['preimages'][0]['path'] = path
            with self.assertRaisesRegex(ProfileError, 'invalid_artifact_path'):
                check_task_artifact(artifact)
        artifact = read('07-artifact')
        artifact['preimages'].append(copy.deepcopy(artifact['preimages'][0]))
        with self.assertRaisesRegex(ProfileError, 'duplicate_artifact_path'):
            check_task_artifact(artifact)
