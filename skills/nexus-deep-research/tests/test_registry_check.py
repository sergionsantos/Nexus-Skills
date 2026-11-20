#!/usr/bin/env python3
"""Offline tests for registry_check.py (fake fetcher with registry-shaped payloads)."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from unittest import mock

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

import registry_check as rc  # noqa: E402

WAKEFIELD_CSL = {
    'title': 'RETRACTED: Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive developmental disorder in children',
    'issued': {'date-parts': [[1998, 2]]},
    'updated-by': [
        {'type': 'correction', 'source': 'retraction-watch'},
        {'type': 'retraction', 'source': 'retraction-watch'},
    ],
}
DEEP_LEARNING_CSL = {'title': 'Deep learning', 'issued': {'date-parts': [[2015, 5, 27]]}}
CONCERN_CSL = {'title': 'A study of things', 'issued': {'date-parts': [[2020]]},
               'updated-by': [{'type': 'expression_of_concern'}]}

ARXIV_OK = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2305.14251v2</id><published>2023-05-23T17:06:00Z</published>
<title>FActScore: Fine-grained Atomic Evaluation of Factual
  Precision in Long Form Text Generation</title><summary>We introduce...</summary></entry></feed>"""
ARXIV_EMPTY = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>"""
PUBMED_RETRACTED = {'result': {'9500320': {'title': 'Ileal-lymphoid-nodular hyperplasia...', 'pubdate': '1998 Feb 28',
                                           'pubtype': ['Journal Article', 'Retracted Publication']}}}
PUBMED_MISSING = {'result': {'1': {'error': 'cannot get document summary'}}}


class FakeFetcher(rc.Fetcher):
    def __init__(self, routes):
        super().__init__(pause=0)
        self.routes = routes
        self.calls = []

    def get(self, url, accept='application/json'):
        self.calls.append(url)
        for key, resp in self.routes.items():
            if key in url:
                status, body = resp
                return status, body if isinstance(body, str) else json.dumps(body)
        return 404, ''


class TestParse(unittest.TestCase):

    def test_forms(self):
        self.assertEqual(rc.parse_identifier('doi:10.1038/nature14539'), ('doi', '10.1038/nature14539'))
        self.assertEqual(rc.parse_identifier('https://doi.org/10.1038/nature14539'), ('doi', '10.1038/nature14539'))
        self.assertEqual(rc.parse_identifier('https://arxiv.org/abs/2305.14251v2'), ('arxiv', '2305.14251v2'))
        self.assertEqual(rc.parse_identifier('https://arxiv.org/pdf/2305.14251.pdf'), ('arxiv', '2305.14251'))
        self.assertEqual(rc.parse_identifier('https://pubmed.ncbi.nlm.nih.gov/9500320/'), ('pmid', '9500320'))
        self.assertIsNone(rc.parse_identifier('https://example.com/blog/10.5-reasons'))


class TestLookups(unittest.TestCase):

    def test_retracted_doi(self):
        f = FakeFetcher({'doi.org/10.1016': (200, WAKEFIELD_CSL)})
        r = rc.check_locator('doi:10.1016/S0140-6736(97)11096-0', 'Ileal-lymphoid-nodular hyperplasia', 1998, f)
        self.assertEqual(r['status'], 'retracted')

    def test_verified_doi(self):
        f = FakeFetcher({'doi.org/10.1038': (200, DEEP_LEARNING_CSL)})
        r = rc.check_locator('doi:10.1038/nature14539', 'Deep Learning', '2015', f)
        self.assertEqual(r['status'], 'verified')

    def test_wrong_title_for_real_doi(self):
        f = FakeFetcher({'doi.org/10.1038': (200, DEEP_LEARNING_CSL)})
        r = rc.check_locator('doi:10.1038/nature14539', 'Quantum supremacy using a programmable processor', 2019, f)
        self.assertEqual(r['status'], 'metadata_mismatch')

    def test_wrong_title_same_year(self):
        # Year agrees, so only the title check can catch this (guards the title threshold)
        f = FakeFetcher({'doi.org/10.1038': (200, DEEP_LEARNING_CSL)})
        r = rc.check_locator('doi:10.1038/nature14539', 'Human-level control through deep reinforcement learning', 2015, f)
        self.assertEqual(r['status'], 'metadata_mismatch')
        self.assertIn('different title', r['detail'])

    def test_year_tolerance_one(self):
        f = FakeFetcher({'doi.org/10.1038': (200, DEEP_LEARNING_CSL)})
        self.assertEqual(rc.check_locator('doi:10.1038/nature14539', 'Deep learning', 2016, f)['status'], 'verified')
        self.assertEqual(rc.check_locator('doi:10.1038/nature14539', 'Deep learning', 2019, f)['status'],
                         'metadata_mismatch')

    def test_fabricated_doi(self):
        f = FakeFetcher({})
        self.assertEqual(rc.check_locator('doi:10.9999/fake.123', 'X', 2020, f)['status'], 'not_found')

    def test_network_error_is_not_a_pass(self):
        f = FakeFetcher({'doi.org/': (0, 'timeout'), 'api.crossref.org': (429, '')})
        r = rc.check_locator('doi:10.1038/nature14539', 'Deep learning', 2015, f)
        self.assertEqual(r['status'], 'error')

    def test_transient_doi_org_failure_plus_crossref_404_is_unknown(self):
        """A DataCite DOI (Zenodo) is absent from Crossref; if doi.org could not be
        reached, a Crossref 404 is not evidence of fabrication."""
        for status in (0, 408, 429, 500, 503):
            f = FakeFetcher({'doi.org/': (status, 'timed out' if status == 0 else ''),
                             'api.crossref.org': (404, '')})
            r = rc.check_locator('doi:10.5281/zenodo.1234567', 'Some dataset', 2020, f)
            self.assertEqual(r['status'], 'error', status)
            self.assertNotIn(r['status'], rc.FAILING)

    def test_transient_crossref_failure_is_unknown(self):
        f = FakeFetcher({'doi.org/': (403, ''), 'api.crossref.org': (502, '')})
        self.assertEqual(rc.check_locator('doi:10.1/x', 'X', 2020, f)['status'], 'error')

    def test_doi_org_resolves_without_metadata_is_not_fabricated(self):
        # doi.org redirected to an HTML landing page (no CSL JSON): the DOI exists.
        f = FakeFetcher({'doi.org/': (200, '<html>landing page</html>'), 'api.crossref.org': (404, '')})
        self.assertEqual(rc.check_locator('doi:10.5281/zenodo.1', 'X', 2020, f)['status'], 'error')

    def test_authoritative_404_without_transient_error_is_not_found(self):
        f = FakeFetcher({'doi.org/': (404, ''), 'api.crossref.org': (503, '')})
        self.assertEqual(rc.check_locator('doi:10.9999/fake.1', 'X', 2020, f)['status'], 'not_found')
        f = FakeFetcher({'doi.org/': (400, ''), 'api.crossref.org': (404, '')})
        self.assertEqual(rc.check_locator('doi:10.9999/fake.1', 'X', 2020, f)['status'], 'not_found')

    def test_crossref_fallback(self):
        f = FakeFetcher({'doi.org/': (503, ''), 'api.crossref.org': (200, {'message': {**DEEP_LEARNING_CSL, 'title': ['Deep learning']}})})
        r = rc.check_locator('doi:10.1038/nature14539', 'Deep learning', 2015, f)
        self.assertEqual(r['status'], 'verified')
        self.assertEqual(r['registry'], 'crossref')

    def test_concern(self):
        f = FakeFetcher({'doi.org/': (200, CONCERN_CSL)})
        self.assertEqual(rc.check_locator('doi:10.1/x', 'A study of things', 2020, f)['status'], 'concern')

    def test_arxiv(self):
        f = FakeFetcher({'arxiv.org/api': (200, ARXIV_OK)})
        r = rc.check_locator('arxiv:2305.14251', 'FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation', 2023, f)
        self.assertEqual(r['status'], 'verified')
        f = FakeFetcher({'arxiv.org/api': (200, ARXIV_EMPTY)})
        self.assertEqual(rc.check_locator('arxiv:2399.99999', 'X', 2023, f)['status'], 'not_found')

    def test_pubmed(self):
        f = FakeFetcher({'esummary': (200, PUBMED_RETRACTED)})
        self.assertEqual(rc.check_locator('pmid:9500320', None, None, f)['status'], 'retracted')
        f = FakeFetcher({'esummary': (200, PUBMED_MISSING)})
        self.assertEqual(rc.check_locator('pmid:1', None, None, f)['status'], 'not_found')

    def test_plain_url_skipped_without_network(self):
        f = FakeFetcher({})
        self.assertEqual(rc.check_locator('https://www.reuters.com/x', 'T', None, f)['status'], 'skipped')
        self.assertEqual(f.calls, [])


LONG_TITLE = 'Deep learning for automated detection of diabetic retinopathy in fundus photographs'


class TestTitleMatch(unittest.TestCase):

    def meta(self, title):
        return {'found': True, 'title': title, 'year': 2016, 'flags': set(), 'source': 'doi.org'}

    def test_short_prefix_is_not_a_match(self):
        for claimed in ('De', 'Deep', 'Deep learning'):
            self.assertLess(rc.title_similarity(claimed, LONG_TITLE), 0.6, claimed)
            self.assertEqual(rc.assess('doi', '10.1/x', self.meta(LONG_TITLE), claimed, 2016)['status'],
                             'metadata_mismatch', claimed)

    def test_prefix_not_ending_at_separator_uses_normal_similarity(self):
        self.assertLess(rc.title_similarity('Deep learning for automated', LONG_TITLE), 1.0)
        self.assertLess(rc.title_similarity('Deep learning for', 'Deep learning for robots: a survey'), 1.0)

    def test_subtitle_omitted(self):
        for registry in ('Deep learning for retinopathy: a validation study',
                         'Deep learning for retinopathy - a validation study',
                         'Deep learning for retinopathy \u2014 a validation study',
                         'Does deep learning help? A validation study',
                         'Deep learning for retinopathy. A validation study'):
            claimed = registry.split(':')[0].split(' - ')[0].split(' \u2014 ')[0].split('?')[0].split('. ')[0]
            self.assertEqual(rc.title_similarity(claimed, registry), 1.0, registry)
            # registry record lacking the subtitle the citation carries: partial
            # (round 2: an added subtitle may be invented)
            self.assertEqual(rc.title_similarity(registry, claimed), rc.SUBTITLE_ADDED_SCORE, registry)

    def test_two_word_prefix_before_separator_is_not_enough(self):
        self.assertLess(rc.title_similarity('Deep learning', 'Deep learning: a very long subtitle here'), 1.0)


class TestCheckCommand(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        rows = [
            {'source_id': 'a', 'canonical_locator': 'doi:10.1038/nature14539', 'title': 'Deep learning', 'year': '2015'},
            {'source_id': 'b', 'canonical_locator': 'doi:10.1016/S0140-6736(97)11096-0', 'title': 'Ileal', 'year': '1998'},
            {'source_id': 'c', 'canonical_locator': 'https://example.com/page', 'title': 'Page'},
        ]
        with open(os.path.join(self.d, 'sources.jsonl'), 'w', encoding='utf-8') as fh:
            for r in rows:
                fh.write(json.dumps(r) + '\n')
        self.f = FakeFetcher({'doi.org/10.1038': (200, DEEP_LEARNING_CSL), 'doi.org/10.1016': (200, WAKEFIELD_CSL)})

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_strict_fails_on_retracted(self):
        with mock.patch('sys.stdout', new=StringIO()) as out:
            code = rc.main(['check', '--dir', self.d, '--strict'], fetcher=self.f)
        self.assertEqual(code, 1)
        data = json.loads(out.getvalue())
        self.assertEqual(data['counts'], {'verified': 1, 'retracted': 1, 'skipped': 1})
        self.assertTrue(os.path.exists(os.path.join(self.d, 'registry_checks.jsonl')))

    def test_strict_does_not_fail_on_unknown(self):
        """doi.org unreachable + Crossref 404 must not be counted as fabricated by --strict."""
        with open(os.path.join(self.d, 'sources.jsonl'), 'w', encoding='utf-8') as fh:
            fh.write(json.dumps({'source_id': 'z', 'canonical_locator': 'doi:10.5281/zenodo.1234567',
                                 'title': 'Some dataset', 'year': '2020'}) + '\n')
        f = FakeFetcher({'doi.org/': (0, 'timed out'), 'api.crossref.org': (404, '')})
        with mock.patch('sys.stdout', new=StringIO()) as out:
            code = rc.main(['check', '--dir', self.d, '--strict'], fetcher=f)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())['counts'], {'error': 1})

    def test_non_strict_passes(self):
        with mock.patch('sys.stdout', new=StringIO()):
            self.assertEqual(rc.main(['check', '--dir', self.d], fetcher=self.f), 0)


if __name__ == '__main__':
    unittest.main()
