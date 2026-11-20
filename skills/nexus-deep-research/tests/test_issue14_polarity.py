#!/usr/bin/env python3
"""Regression tests for upstream issue #14 and the multilingual/polarity layer.

Issue #14: verify_claim_support.compute_support_score() labelled evidence that
negates a claim as 'supported' (1.0 EN / 0.6 ZH), and unrelated or empty
non-Latin evidence as 'supported' (0.6) because absent dimensions defaulted to
a perfect match.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from verify_claim_support import compute_support_score  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'verify_claim_support.py')


class TestIssue14Reproducer(unittest.TestCase):
    """The exact cases from the issue reproducer."""

    def test_en_positive_control(self):
        status, score, _ = compute_support_score('The museum is open on Mondays.', ['The museum is open on Mondays.'])
        self.assertEqual(status, 'supported')
        self.assertGreaterEqual(score, 0.9)

    def test_en_negated_evidence(self):
        status, _, notes = compute_support_score('The museum is open on Mondays.', ['The museum is not open on Mondays.'])
        self.assertEqual(status, 'contradicted', notes)

    def test_en_negated_claim(self):
        status, _, _ = compute_support_score('The museum is not open on Mondays.', ['The museum is open on Mondays.'])
        self.assertEqual(status, 'contradicted')

    def test_zh_positive_control(self):
        status, _, _ = compute_support_score('示例馆周一开放。', ['示例馆周一开放。'])
        self.assertEqual(status, 'supported')

    def test_zh_negated_evidence(self):
        status, _, _ = compute_support_score('示例馆周一开放。', ['示例馆周一不开放。'])
        self.assertEqual(status, 'contradicted')

    def test_zh_unrelated_evidence(self):
        status, score, _ = compute_support_score('示例馆周一开放。', ['今天下雨。'])
        self.assertNotEqual(status, 'supported')
        self.assertLess(score, 0.35)

    def test_zh_empty_quote(self):
        status, score, _ = compute_support_score('示例馆周一开放。', [''])
        self.assertEqual(status, 'unsupported')
        self.assertEqual(score, 0.0)

    def test_no_evidence(self):
        status, _, _ = compute_support_score('The museum is open on Mondays.', [])
        self.assertEqual(status, 'unsupported')


class TestOtherLanguages(unittest.TestCase):
    """nexus additions on top of the FFV47 lexicon (en/pt/zh)."""

    def test_portuguese(self):
        status, _, _ = compute_support_score('O museu abre às segundas-feiras.', ['O museu não abre às segundas-feiras.'])
        self.assertEqual(status, 'contradicted')

    def test_german(self):
        status, _, _ = compute_support_score('Das Museum öffnet montags.', ['Das Museum öffnet montags nicht.'])
        self.assertEqual(status, 'contradicted')

    def test_japanese(self):
        status, _, _ = compute_support_score('博物館は月曜日に開館する。', ['博物館は月曜日に開館しない。'])
        self.assertEqual(status, 'contradicted')

    def test_neither_nor(self):
        status, _, _ = compute_support_score('The drug is safe and effective.', ['The drug is neither safe nor effective.'])
        self.assertEqual(status, 'contradicted')

    def test_contraction(self):
        status, _, _ = compute_support_score('The museum is open on Mondays.', ["The museum isn't open on Mondays."])
        self.assertEqual(status, 'contradicted')

    def test_not_only_is_affirmative(self):
        status, _, _ = compute_support_score('The drug is safe and effective.',
                                             ['The drug is not only safe but also effective.'])
        self.assertEqual(status, 'supported')


class TestNoFreeDimensions(unittest.TestCase):
    """Absent dimensions must not inflate the score."""

    def test_unrelated_english_without_numbers(self):
        status, score, _ = compute_support_score('Remote work improves developer satisfaction.',
                                                 ['Bananas are a good source of potassium.'])
        self.assertEqual(status, 'needs_review')
        self.assertLess(score, 0.2)

    def test_matching_numbers_without_topic_is_not_support(self):
        status, _, _ = compute_support_score('Revenue grew 12% in 2024.',
                                             ['The bridge is 12% longer since 2024.'])
        self.assertNotEqual(status, 'supported')


class TestNumericConflict(unittest.TestCase):

    def test_different_number_same_topic(self):
        status, _, notes = compute_support_score('Global smartphone shipments fell 12% last quarter.',
                                                 ['Global smartphone shipments fell 3% last quarter.'])
        self.assertEqual(status, 'needs_review')
        self.assertIn('numeric conflict', notes)

    def test_thousands_separator_equivalence(self):
        status, _, _ = compute_support_score('The trial enrolled 1,847 patients across sites.',
                                             ['Across sites the trial enrolled 1847 patients.'])
        self.assertEqual(status, 'supported')

    def test_one_agreeing_quote_wins_but_flags_conflict(self):
        status, _, notes = compute_support_score(
            'The museum is open on Mondays.',
            ['The museum is open on Mondays.', 'The museum is not open on Mondays.'],
        )
        self.assertEqual(status, 'supported')
        self.assertIn('conflict', notes)


class TestStrictCLI(unittest.TestCase):
    """--strict must fail on contradicted factual claims (not only unsupported)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        with open(os.path.join(self.tmp, 'evidence.jsonl'), 'w', encoding='utf-8') as f:
            f.write(json.dumps({'evidence_id': 'e1', 'source_id': 's1',
                                'quote': 'The museum is not open on Mondays.'}) + '\n')
        with open(os.path.join(self.tmp, 'claims.jsonl'), 'w', encoding='utf-8') as f:
            f.write(json.dumps({'claim_id': 'c1', 'section_id': 'finding_1',
                                'text': 'The museum is open on Mondays.', 'claim_type': 'factual',
                                'cited_source_ids': ['s1'], 'evidence_ids': ['e1'],
                                'support_status': 'unverified'}) + '\n')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_strict_fails_on_contradicted(self):
        r = subprocess.run([sys.executable, SCRIPT, 'verify', '--dir', self.tmp, '--strict'],
                           capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out['factual_contradicted'], 1)

    def test_report_never_claims_adequate_support(self):
        subprocess.run([sys.executable, SCRIPT, 'verify', '--dir', self.tmp], capture_output=True, text=True, encoding='utf-8')
        r = subprocess.run([sys.executable, SCRIPT, 'report', '--dir', self.tmp], capture_output=True, text=True, encoding='utf-8')
        self.assertNotIn('adequate support', r.stdout)
        self.assertIn('[contradicted]', r.stdout)


if __name__ == '__main__':
    unittest.main()
