#!/usr/bin/env python3
"""Rows written by the real scripts must validate against schemas/*.json.

The schemas use additionalProperties:false, so any field a script adds without a
matching schema property is a contract break. Uses jsonschema when importable;
otherwise falls back to a minimal required/additionalProperties key check.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')
SCHEMAS = os.path.join(ROOT, 'schemas')
sys.path.insert(0, SCRIPTS)

from retrieval_health import CATEGORIES  # noqa: E402

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only without jsonschema
    jsonschema = None


def load_schema(name):
    with open(os.path.join(SCHEMAS, name), encoding='utf-8') as f:
        return json.load(f)


def _minimal_errors(schema, row):
    errors = [f'missing required {k}' for k in schema.get('required', []) if k not in row]
    if schema.get('additionalProperties') is False:
        allowed = set(schema.get('properties', {}))
        errors += [f'unexpected {k}' for k in row if k not in allowed]
    return errors


def schema_errors(name, row):
    schema = load_schema(name)
    if jsonschema is None:
        return _minimal_errors(schema, row)
    validator = jsonschema.Draft202012Validator(schema)
    return [f'{"/".join(map(str, e.absolute_path))}: {e.message}' for e in validator.iter_errors(row)]


def run(script, *args):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f'{script} {args} failed: {r.stderr}')
    return r.stdout


def read_jsonl(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


class TestScriptRowsConformToSchemas(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name

    def assertConforms(self, schema_name, row):
        self.assertEqual(schema_errors(schema_name, row), [], f'{schema_name} rejects {row}')

    def test_run_manifest_from_init_run(self):
        run('citation_manager.py', 'init-run', '--out-dir', self.dir, '--query', 'Q?', '--mode', 'deep')
        with open(os.path.join(self.dir, 'run_manifest.json'), encoding='utf-8') as f:
            self.assertConforms('run_manifest.schema.json', json.load(f))

    def test_run_manifest_with_recorded_preflight_and_stop(self):
        run('citation_manager.py', 'init-run', '--out-dir', self.dir, '--query', 'Q?')
        with open(os.path.join(self.dir, 'run_manifest.json'), encoding='utf-8') as f:
            manifest = json.load(f)
        # retrieval_health reads `preflight.get('reason') or ...`: an ok preflight has no reason
        manifest['search_preflight'] = {'status': 'ok', 'reason': None, 'selected_tool': 'search'}
        manifest['retrieval_stop'] = {'reason': 'budget-exhausted', 'at': '2026-01-01T00:00:00Z',
                                      'round': 2, 'unresolved_high_priority_facet_ids': ['f1'],
                                      'remaining_gaps': ['no RCT found'], 'basis': 'two rounds spent'}
        self.assertConforms('run_manifest.schema.json', manifest)

    def test_evidence_rows_from_evidence_store(self):
        src = 'c' * 16
        run('evidence_store.py', 'add', '--dir', self.dir,
            '--json', json.dumps({'source_id': src, 'quote': 'Revenue grew 12% in 2023.'}))
        run('evidence_store.py', 'add', '--dir', self.dir, '--json', json.dumps({
            'source_id': src, 'quote': 'Margins fell.', 'locator': 'p. 4',
            'evidence_type': 'data_point', 'retrieval_query': 'margins 2023',
            'retrieval_id': 'r1', 'capture_tool': 'curl', 'verbatim': True}))
        rows = read_jsonl(os.path.join(self.dir, 'evidence.jsonl'))
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertConforms('evidence.schema.json', row)

    def test_claim_rows_from_extract_claims_and_verify_claim_support(self):
        src = 'c' * 16
        out = run('evidence_store.py', 'add', '--dir', self.dir,
                  '--json', json.dumps({'source_id': src, 'quote': 'Revenue grew 12% in 2023.'}))
        eid = json.loads(out)['evidence_id']
        run('extract_claims.py', 'add', '--dir', self.dir, '--json', json.dumps({
            'section_id': 'findings', 'text': 'Revenue grew 12% in 2023.', 'claim_type': 'factual',
            'evidence_ids': [eid], 'cited_source_ids': [src]}))
        run('extract_claims.py', 'add', '--dir', self.dir, '--json', json.dumps({
            'section_id': 'findings', 'text': 'Costs will fall.', 'claim_type': 'speculation'}))
        claims_path = os.path.join(self.dir, 'claims.jsonl')
        for row in read_jsonl(claims_path):
            self.assertConforms('claim.schema.json', row)
        run('verify_claim_support.py', 'verify', '--dir', self.dir)
        rows = read_jsonl(claims_path)
        self.assertTrue(any('_support_score' in r and '_support_notes' in r for r in rows))
        for row in rows:
            self.assertConforms('claim.schema.json', row)


class TestFailureFieldsConsumedByRetrievalHealth(unittest.TestCase):
    """retrieval_health.py / verify_coverage.py read error_category and provider_failures
    from queries.jsonl and retrievals.jsonl rows, so the schemas must accept them."""

    RETRIEVAL = {'retrieval_id': 'r1', 'query_id': 'q1', 'tool': 'curl', 'url': 'https://x.org/a',
                 'document_key': 'x.org/a', 'status': 'failed', 'content_scope': 'none',
                 'error': 'HTTP 403'}
    QUERY = {'query_id': 'q1', 'round': 1, 'facet_ids': ['f1'], 'gap': 'g', 'family': 'literal',
             'query': 'x', 'provider': 'brave', 'expected_evidence': 'e', 'result_source_ids': [],
             'new_relevant_source_ids': [], 'coverage_changed': False, 'notes': '',
             'status': 'failed', 'error': 'quota'}

    def test_retrieval_error_category_every_known_category_and_null(self):
        for cat in list(CATEGORIES) + [None]:
            row = dict(self.RETRIEVAL, error_category=cat)
            self.assertEqual(schema_errors('retrieval.schema.json', row), [], cat)

    def test_query_error_category_and_provider_failures(self):
        row = dict(self.QUERY, error_category='billing_quota',
                   provider_failures=[{'provider': 'brave', 'category': 'auth'},
                                      {'provider': 'exa', 'category': None, 'reason': 'HTTP 429'}])
        self.assertEqual(schema_errors('query.schema.json', row), [])
        self.assertEqual(schema_errors('query.schema.json', dict(self.QUERY, error_category=None,
                                                                 provider_failures=[])), [])

    @unittest.skipIf(jsonschema is None, 'type checks need jsonschema')
    def test_failure_fields_are_typed(self):
        self.assertTrue(schema_errors('retrieval.schema.json', dict(self.RETRIEVAL, error_category='nope')))
        self.assertTrue(schema_errors('query.schema.json', dict(self.QUERY, error_category=7)))
        self.assertTrue(schema_errors('query.schema.json', dict(self.QUERY, provider_failures='brave')))
        self.assertTrue(schema_errors('query.schema.json',
                                      dict(self.QUERY, provider_failures=[{'category': 'auth'}])))

    def test_schema_categories_match_retrieval_health(self):
        for name in ('retrieval.schema.json', 'query.schema.json'):
            enum = load_schema(name)['$defs']['error_category']['enum']
            self.assertEqual([c for c in enum if c is not None], list(CATEGORIES), name)
            self.assertIn(None, enum, name)

    @unittest.skipIf(jsonschema is None, 'type checks need jsonschema')
    def test_claim_support_fields_are_typed(self):
        claim = {'claim_id': 'a' * 16, 'section_id': 's', 'text': 't', 'claim_type': 'factual',
                 'support_status': 'supported'}
        self.assertEqual(schema_errors('claim.schema.json',
                                       dict(claim, _support_score=0.5, _support_notes='ok')), [])
        self.assertTrue(schema_errors('claim.schema.json', dict(claim, _support_score='high')))
        self.assertTrue(schema_errors('claim.schema.json', dict(claim, _support_score=1.5)))
        self.assertTrue(schema_errors('claim.schema.json', dict(claim, _support_notes=3)))


if __name__ == '__main__':
    unittest.main()
