#!/usr/bin/env python3
"""Tests for claim_ledger.py (votes, resolution, early exit, independence, gate)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

from claim_ledger import (DEFAULTS, build_ledger, normalise_text, registrable_domain,  # noqa: E402
                          resolve_claim, shingle_overlap, source_family, votes_still_needed)

SCRIPT = os.path.join(HERE, '..', 'scripts', 'claim_ledger.py')


def V(*verdicts):
    return [{'verdict': v, 'verifier_id': f'v{i}'} for i, v in enumerate(verdicts)]


class TestResolve(unittest.TestCase):
    cfg = dict(DEFAULTS)

    def st(self, votes, det=None):
        return resolve_claim(votes, det, self.cfg)['final_status']

    def test_no_votes_is_unverified(self):
        self.assertEqual(self.st([]), 'unverified')

    def test_unverifiable_is_not_refuted(self):
        self.assertEqual(self.st(V('unverifiable', 'unverifiable', 'unverifiable')), 'unverified')

    def test_two_supports(self):
        self.assertEqual(self.st(V('supported', 'supported')), 'supported')

    def test_two_refutes(self):
        self.assertEqual(self.st(V('refuted', 'refuted', 'supported')), 'refuted')

    def test_single_refute_does_not_kill(self):
        r = resolve_claim(V('supported', 'refuted', 'supported'), None, self.cfg)
        self.assertEqual(r['final_status'], 'supported')
        self.assertEqual(r['dissent'], 1)

    def test_both_thresholds_contested(self):
        cfg = dict(self.cfg, max_verifiers=5)
        self.assertEqual(resolve_claim(V('supported', 'supported', 'refuted', 'refuted'), None, cfg)['final_status'],
                         'contested')

    def test_deterministic_contradiction_blocks_support(self):
        self.assertEqual(self.st(V('supported', 'supported'), det='contradicted'), 'contested')
        # round 2 (D5): undecided votes on a contradicted claim leave it unverified
        self.assertEqual(self.st([], det='contradicted'), 'unverified')


class TestEarlyExit(unittest.TestCase):

    def test_default_flow(self):
        cfg = dict(DEFAULTS)  # 2/2/3
        self.assertEqual(votes_still_needed([], cfg), 2)
        self.assertEqual(votes_still_needed(V('supported'), cfg), 1)
        self.assertEqual(votes_still_needed(V('supported', 'supported'), cfg), 0)
        self.assertEqual(votes_still_needed(V('refuted', 'refuted'), cfg), 0)
        self.assertEqual(votes_still_needed(V('supported', 'refuted'), cfg), 1)
        self.assertEqual(votes_still_needed(V('supported', 'refuted', 'unverifiable'), cfg), 0)

    def test_undecidable_stops(self):
        cfg = dict(DEFAULTS)
        self.assertEqual(votes_still_needed(V('unverifiable', 'unverifiable'), cfg), 0)

    def test_olympiad_asymmetric(self):
        cfg = {'support_threshold': 4, 'refute_threshold': 2, 'max_verifiers': 5}
        self.assertEqual(votes_still_needed(V('supported', 'supported', 'supported'), cfg), 1)
        self.assertEqual(votes_still_needed(V('supported', 'supported', 'supported', 'supported'), cfg), 0)
        self.assertEqual(votes_still_needed(V('refuted', 'refuted'), cfg), 0)


class TestFamilies(unittest.TestCase):

    def test_registrable_domain(self):
        self.assertEqual(registrable_domain('www.bbc.co.uk'), 'bbc.co.uk')
        self.assertEqual(registrable_domain('news.example.com'), 'example.com')
        self.assertEqual(registrable_domain('dre.gov.pt'), 'dre.gov.pt')
        self.assertEqual(registrable_domain('portal.dre.gov.pt'), 'dre.gov.pt')

    def test_same_site_is_one_family(self):
        a = source_family({'canonical_locator': 'https://docs.example.com/a'})
        b = source_family({'canonical_locator': 'https://blog.example.com/b'})
        self.assertEqual(a, b)

    def test_explicit_family_wins(self):
        self.assertEqual(source_family({'canonical_locator': 'https://x.com', 'source_family': 'Reuters'}), 'reuters')

    def test_arxiv_versions_and_datacite_doi_are_one_family(self):
        locs = ['arxiv:2305.14251v1', 'arxiv:2305.14251v2', 'doi:10.48550/arxiv.2305.14251',
                'doi:10.48550/arXiv.2305.14251', 'ARXIV:2305.14251', 'arxiv:2305.14251']
        fams = {source_family({'canonical_locator': loc}) for loc in locs}
        self.assertEqual(fams, {'arxiv:2305.14251'})

    def test_arxiv_and_doi_urls_without_canonical_locator(self):
        a = source_family({'raw_url': 'https://arxiv.org/abs/2305.14251v3'})
        b = source_family({'raw_url': 'https://doi.org/10.48550/arXiv.2305.14251'})
        c = source_family({'raw_url': 'https://arxiv.org/pdf/2305.14251v1.pdf'})
        self.assertEqual({a, b, c}, {'arxiv:2305.14251'})
        # Two different arXiv papers stay two families (not collapsed to arxiv.org).
        self.assertNotEqual(source_family({'raw_url': 'https://arxiv.org/abs/2401.00001'}), a)

    def test_old_style_arxiv_version_stripped(self):
        self.assertEqual(source_family({'canonical_locator': 'arxiv:hep-th/9901001v2'}), 'arxiv:hep-th/9901001')
        self.assertEqual(source_family({'canonical_locator': 'arXiv:HEP-TH/9901001'}), 'arxiv:hep-th/9901001')

    def test_other_dois_untouched(self):
        self.assertEqual(source_family({'canonical_locator': 'doi:10.1038/NATURE12373'}), 'doi:10.1038/nature12373')
        self.assertNotEqual(source_family({'canonical_locator': 'doi:10.1038/x1'}),
                            source_family({'canonical_locator': 'doi:10.1038/x2'}))

    def test_explicit_family_arxiv_normalised(self):
        self.assertEqual(source_family({'canonical_locator': 'https://x.com', 'source_family': 'arXiv:2305.14251v2'}),
                         'arxiv:2305.14251')

    def test_build_ledger_counts_one_family_for_paper_versions(self):
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, 'claims.jsonl'), 'w') as f:
                f.write(json.dumps({'claim_id': 'a' * 16, 'text': 'X.', 'claim_type': 'factual',
                                    'cited_source_ids': ['s1', 's2', 's3']}) + '\n')
            with open(os.path.join(d, 'sources.jsonl'), 'w') as f:
                for sid, loc in (('s1', 'arxiv:2305.14251v1'), ('s2', 'arxiv:2305.14251v2'),
                                 ('s3', 'doi:10.48550/arxiv.2305.14251')):
                    f.write(json.dumps({'source_id': sid, 'canonical_locator': loc}) + '\n')
            rows = build_ledger(d, dict(DEFAULTS), ['factual'])
            self.assertEqual(rows[0]['source_families'], ['arxiv:2305.14251'])
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestReportNormalisation(unittest.TestCase):

    def test_norm_strips_formatting_and_citations(self):
        a = normalise_text('**Revenue** grew 50% in 2023 according to the _filing_ [1, 2].')
        b = normalise_text('Revenue grew 50 % in 2023 according to the filing.')
        self.assertEqual(a, b)

    def test_norm_variants(self):
        base = normalise_text('The council accepted PEP 703 and it became the default build.')
        for v in ('The council accepted PEP 703 and it became the **default build** [1].',
                  'The council accepted PEP 703 and it became the default build [1][2].',
                  'The council accepted PEP 703 and it became the default build [^3].',
                  'The council accepted PEP 703 and it became the default build (Smith et al., 2020).',
                  'The council accepted PEP 703 and it became the default build (Smith, 2020; Lee 2021b).',
                  'The   council\naccepted `PEP 703` and it became the *default* build.',
                  'THE COUNCIL ACCEPTED PEP 703 AND IT BECAME THE DEFAULT BUILD.',
                  'The council accepted [PEP 703](https://peps.python.org/pep-0703/) and it became the default build.',
                  'The council accepted PEP 703 and it became the default build<sup>1</sup>.',
                  'The council accepted PEP 703 and it became the default build [1](#ref-1).',
                  'The council accepted PEP\u00a0703 and it became the default build\u00b9.'):
            self.assertEqual(normalise_text(v), base, v)

    def test_norm_quotes_and_dashes(self):
        self.assertEqual(normalise_text('It\u2019s a \u201cfree\u2013threaded\u201d build'),
                         normalise_text("It's a \"free-threaded\" build"))

    def test_norm_keeps_numbers_distinct(self):
        self.assertNotEqual(normalise_text('grew 50% in 2023'), normalise_text('grew 30% in 2023'))
        self.assertNotEqual(normalise_text('cost 1.5 million'), normalise_text('cost 15 million'))

    def test_shingle_overlap(self):
        claim = 'The Steering Council accepted PEP 703 and the free-threaded build became the default build.'
        self.assertEqual(shingle_overlap(claim, claim), 1.0)
        near = 'The Steering Council accepted PEP 703 and the free-threaded build then became the default build.'
        self.assertGreaterEqual(shingle_overlap(claim, near), 0.8)
        other = 'FActScore computes the percentage of atomic facts supported by a knowledge source.'
        self.assertLess(shingle_overlap(claim, other), 0.2)


REFUTED = 'The Steering Council accepted PEP 703 and the free-threaded build became the default build [1].'


class TestGateRefutedVariants(unittest.TestCase):
    """A refuted claim must not slip through the gate via cosmetic edits."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        claims = [
            {'claim_id': 'r' * 16, 'section_id': 'finding_1', 'text': REFUTED, 'claim_type': 'factual',
             'cited_source_ids': ['s1'], 'support_status': 'supported'},
        ]
        with open(os.path.join(self.d, 'claims.jsonl'), 'w') as f:
            for c in claims:
                f.write(json.dumps(c) + '\n')
        with open(os.path.join(self.d, 'sources.jsonl'), 'w') as f:
            f.write(json.dumps({'source_id': 's1', 'canonical_locator': 'https://peps.python.org/x'}) + '\n')
        for v in ('v1', 'v2'):
            subprocess.run([sys.executable, SCRIPT, 'vote', '--dir', self.d, '--claim-id', 'r' * 16,
                            '--verifier-id', v, '--verdict', 'refuted', '--failure-patterns', 'stale'],
                           capture_output=True, text=True, check=True)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def gate(self, report_body):
        path = os.path.join(self.d, 'report.md')
        with open(path, 'w') as f:
            f.write('# Report\n\n## Finding 1\n\nPEP 703 proposes removing the GIL [2]. ' + report_body + '\n')
        r = subprocess.run([sys.executable, SCRIPT, 'gate', '--dir', self.d, '--report', path,
                            '--max-unverified-rate', '1'], capture_output=True, text=True)
        return r.returncode, r.stdout

    def assert_blocked(self, body):
        rc, out = self.gate(body)
        self.assertEqual(rc, 1, f'{body!r} passed the gate:\n{out}')
        self.assertIn('r' * 16, out)

    def test_verbatim_blocked(self):
        self.assert_blocked(REFUTED)

    def test_bold_blocked(self):
        self.assert_blocked('The Steering Council accepted PEP 703 and the free-threaded build became the '
                            '**default build** [1].')

    def test_italic_and_code_blocked(self):
        self.assert_blocked('The Steering Council accepted `PEP 703` and the *free-threaded* build became the '
                            '_default build_ [1].')

    def test_citation_changed_blocked(self):
        self.assert_blocked('The Steering Council accepted PEP 703 and the free-threaded build became the '
                            'default build [1, 2].')

    def test_citation_removed_blocked(self):
        self.assert_blocked('The Steering Council accepted PEP 703 and the free-threaded build became the '
                            'default build.')

    def test_whitespace_and_case_blocked(self):
        self.assert_blocked('The Steering  Council accepted PEP 703\nand the free\u2013threaded build became the '
                            'Default Build [^1].')

    def test_near_duplicate_blocked(self):
        rc, out = self.gate('The Steering Council accepted PEP 703 and the free-threaded build then became the '
                            'default build [1].')
        self.assertEqual(rc, 1, out)
        self.assertIn('overlap', out)

    def test_rewritten_claim_passes(self):
        rc, out = self.gate('The Steering Council accepted PEP 703 as an experimental, opt-in build; it is not '
                            'the default [1].')
        self.assertEqual(rc, 0, out)

    def test_removed_claim_passes(self):
        rc, out = self.gate('')
        self.assertEqual(rc, 0, out)


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        claims = [
            {'claim_id': 'a' * 16, 'section_id': 'finding_1', 'text': 'Alpha claim text.', 'claim_type': 'factual',
             'cited_source_ids': ['s1', 's2'], 'support_status': 'supported'},
            {'claim_id': 'b' * 16, 'section_id': 'finding_2', 'text': 'Beta claim text.', 'claim_type': 'factual',
             'cited_source_ids': ['s1'], 'support_status': 'supported'},
            {'claim_id': 'c' * 16, 'section_id': 'recommendations', 'text': 'Do X.', 'claim_type': 'recommendation',
             'cited_source_ids': [], 'support_status': 'unsupported'},
        ]
        with open(os.path.join(self.d, 'claims.jsonl'), 'w') as f:
            for c in claims:
                f.write(json.dumps(c) + '\n')
        with open(os.path.join(self.d, 'sources.jsonl'), 'w') as f:
            f.write(json.dumps({'source_id': 's1', 'canonical_locator': 'https://www.nature.com/x'}) + '\n')
            f.write(json.dumps({'source_id': 's2', 'canonical_locator': 'https://www.reuters.com/y'}) + '\n')

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def run_cl(self, *args):
        r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
        return r.returncode, r.stdout

    def vote(self, cid, vid, verdict, patterns=None):
        args = ['vote', '--dir', self.d, '--claim-id', cid, '--verifier-id', vid, '--verdict', verdict]
        if patterns:
            args += ['--failure-patterns', patterns]
        return self.run_cl(*args)

    def test_refute_requires_pattern(self):
        rc, out = self.vote('a' * 16, 'v1', 'refuted')
        self.assertEqual(rc, 2, out)

    def test_unknown_pattern_rejected(self):
        rc, _ = self.vote('a' * 16, 'v1', 'refuted', 'made-up')
        self.assertEqual(rc, 2)

    def test_one_vote_per_verifier(self):
        self.assertEqual(self.vote('a' * 16, 'v1', 'supported')[0], 0)
        self.assertEqual(self.vote('a' * 16, 'v1', 'supported')[0], 2)

    def test_unknown_claim_rejected(self):
        self.assertEqual(self.vote('f' * 16, 'v1', 'supported')[0], 2)

    def test_pending_only_factual(self):
        rc, out = self.run_cl('pending', '--dir', self.d)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data['pending'], 2)
        self.assertTrue(all(c['launch_verifiers'] == 2 for c in data['claims']))

    def test_gate_flow(self):
        for v in ('v1', 'v2'):
            self.vote('a' * 16, v, 'supported')
        self.vote('b' * 16, 'v1', 'refuted', 'number-error')
        self.vote('b' * 16, 'v2', 'refuted', 'stale,number-error')
        report_path = os.path.join(self.d, 'report.md')
        with open(report_path, 'w') as f:
            f.write('Alpha claim text. Beta claim text.')
        rc, out = self.run_cl('gate', '--dir', self.d, '--report', report_path)
        self.assertEqual(rc, 1, out)
        self.assertIn('refuted claim still present', out)
        with open(report_path, 'w') as f:
            f.write('Alpha claim text.')
        rc, out = self.run_cl('gate', '--dir', self.d, '--report', report_path)
        self.assertEqual(rc, 0, out)

    def test_gate_independence(self):
        self.vote('a' * 16, 'v1', 'supported')
        self.vote('a' * 16, 'v2', 'supported')
        self.vote('b' * 16, 'v1', 'supported')
        self.vote('b' * 16, 'v2', 'supported')
        rc, out = self.run_cl('gate', '--dir', self.d)
        self.assertEqual(rc, 0, out)
        self.assertIn('bbbbbbbbbbbbbbbb: supported by 1 source family', out)
        rc, out = self.run_cl('gate', '--dir', self.d, '--strict-independence')
        self.assertEqual(rc, 1)

    def test_gate_unacknowledged_unverified(self):
        report_path = os.path.join(self.d, 'report.md')
        with open(report_path, 'w') as f:
            f.write('Alpha claim text. Beta claim text.')
        rc, out = self.run_cl('gate', '--dir', self.d, '--report', report_path, '--max-unverified-rate', '1')
        self.assertEqual(rc, 1)
        self.assertIn('not listed in the report claim ledger', out)

    def test_correction_only_with_refuted(self):
        args = ['vote', '--dir', self.d, '--claim-id', 'a' * 16, '--verifier-id', 'v1',
                '--verdict', 'supported', '--correction', 'X']
        self.assertEqual(self.run_cl(*args)[0], 2)

    def test_corrections_surface_in_ledger(self):
        for v in ('v1', 'v2'):
            rc, _ = self.run_cl('vote', '--dir', self.d, '--claim-id', 'b' * 16, '--verifier-id', v,
                                '--verdict', 'refuted', '--failure-patterns', 'number-error',
                                '--correction', 'Beta was 3%, not 12%.')
            self.assertEqual(rc, 0)
        self.run_cl('resolve', '--dir', self.d)
        with open(os.path.join(self.d, 'claim_ledger.jsonl')) as f:
            rows = {r['claim_id']: r for r in map(json.loads, f)}
        self.assertEqual(rows['b' * 16]['final_status'], 'refuted')
        self.assertEqual(rows['b' * 16]['corrections'], ['Beta was 3%, not 12%.'] * 2)
        rc, out = self.run_cl('table', '--dir', self.d)
        self.assertIn('2 correction(s) proposed', out)

    def test_table(self):
        rc, out = self.run_cl('table', '--dir', self.d)
        self.assertEqual(rc, 0)
        self.assertIn('| Claim | Section | Status |', out)
        self.assertIn('**unverified**', out)


if __name__ == '__main__':
    unittest.main()
