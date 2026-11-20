#!/usr/bin/env python3
"""Regression tests for the round-4 independent review findings
(.isa/round4-findings.md). Each test names its finding id."""

import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
SCRIPTS = os.path.join(ROOT, 'scripts')
sys.path.insert(0, SCRIPTS)

import claim_ledger as cl  # noqa: E402
import extract_claims as ec  # noqa: E402
from verify_claim_support import compute_support_score, extract_numbers  # noqa: E402
from verify_quotes import match_quote_detail, normalize  # noqa: E402


def gate_hit(claim, report):
    rn = cl.normalise_text(report)
    sents = [(s, cl._shingles(cl.normalise_text(s).split())) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


def mq(quote, source):
    return match_quote_detail(quote, normalize(source))


class TestRefutedText(unittest.TestCase):
    ACME = 'Acme cut 300 jobs at its Ohio plant in 2023 [2].'

    def test_F1_sentence_adverbial_negation_does_not_hide_repeat(self):
        for prefix in ('Not surprisingly, ', 'With no warning, ', 'No doubt ', 'Unsurprisingly, '):
            self.assertIsNotNone(gate_hit(self.ACME, prefix + self.ACME), prefix)

    def test_F1_direct_negation_is_still_the_correction(self):
        # nexus: round 6 design: negate in place, not by prefixing the exact text
        self.assertIsNotNone(gate_hit('Vaccines cause infertility in women [3].',
                                      'No vaccines cause infertility in women [3].'))
        self.assertIsNone(gate_hit('Vaccines cause infertility in women [3].',
                                   'Vaccines do not cause infertility in women [3].'))

    def test_F1_exact_path_reads_negation_per_clause(self):
        # nexus: round 6 design: the exact text counts whatever precedes it
        for prefix in ('Not surprisingly, ', 'With no warning, ', 'There is no evidence that '):
            self.assertIsNotNone(gate_hit(self.ACME, prefix + self.ACME), prefix)

    def test_F9_negated_frame_in_same_clause_is_the_correction(self):
        # nexus: round 6 design (R6-1/R6-2/R6-3): frames around the exact text
        # are not read; the in-place negation is the correction
        claim = 'Vaccines cause autism in children.'
        self.assertIsNotNone(gate_hit(claim, 'There is no evidence that vaccines cause autism in children [4].'))
        self.assertIsNotNone(gate_hit(claim, 'Studies did not find that vaccines cause autism in children [4].'))
        self.assertIsNone(gate_hit(claim, 'Vaccines do not cause autism in children [4].'))

    def test_F2_hedged_repeat_of_refuted_figure_is_caught(self):
        claim = 'In its annual filing Acme Corporation reported that European revenue grew by 12% [3].'
        rep = 'In its annual filing Acme Corporation reported that European revenue grew about 12% [3].'
        self.assertIsNotNone(gate_hit(claim, rep))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(claim, rep.replace('12%', '8%')))

    def test_R1_short_claim_with_reformatted_number_is_caught(self):
        claim = 'The audit tool was tested against 1,500 PyPI packages in 2024 [^1].'
        for new in ('1500', '1.5 thousand'):
            self.assertIsNotNone(gate_hit(claim, claim.replace('1,500', new)), new)
        claim2 = 'European revenue grew 12.0% in 2023 [3].'
        self.assertIsNotNone(gate_hit(claim2, 'European revenue grew 12% in 2023 [3].'))
        self.assertIsNone(gate_hit(claim, claim.replace('1,500', '150')))


class TestNumbers(unittest.TestCase):

    def test_F3_range_shares_its_kind(self):
        q = ['Analysts expect margins of 10% to 12% in 2025.']
        for c in ('Analysts expect margins of 10-12% in 2025 [1].',
                  'Analysts expect margins of between 10 and 12% in 2025 [1].',
                  'Analysts expect margins of 10 to 12 percent in 2025 [1].'):
            self.assertEqual(compute_support_score(c, q)[0], 'supported', c)
        self.assertEqual(extract_numbers('between 10 and 12%'), {'10%', '12%'})

    def test_F4_F5_portuguese_scale(self):
        self.assertEqual(extract_numbers('2.000 milhões'), extract_numbers('2 mil milhões'))
        self.assertEqual(extract_numbers('2 mil milhões'), {'2000000000'})
        self.assertEqual(extract_numbers('1,5 mil milhões'), {'1500000000'})
        self.assertEqual(extract_numbers('1,5 milhões'), {'1500000'})
        self.assertEqual(extract_numbers('1.500 mil'), {'1500000'})
        st = compute_support_score('O investimento foi de 2 milhões de euros em 2023 [1].',
                                   ['O investimento foi de 2.000 milhões de euros em 2023.'])[0]
        self.assertNotEqual(st, 'supported')

    def test_F8_times_a_day_is_frequency(self):
        self.assertEqual(extract_numbers('3 times a day'), {'3'})
        self.assertEqual(extract_numbers('3 times higher'), {'3x'})
        st = compute_support_score('Patients in the trial took the drug 3 times a day for 12 weeks [1].',
                                   ['Patients in the trial took 3 doses of the drug a day for 12 weeks.'])[0]
        self.assertEqual(st, 'supported')


class TestQuotes(unittest.TestCase):

    def test_F6_decimal_figure_ends_a_sentence(self):
        src = 'Revenue reached $4.5bn. Losses at the retail unit doubled after the company closed 40 stores.'
        self.assertEqual(mq('Revenue ... doubled after the company closed 40 stores', src)[0], 'missing')
        src2 = 'Inflation was 2.5%. Wages at the retail unit doubled after the company closed 40 stores.'
        self.assertEqual(mq('Inflation ... doubled after the company closed 40 stores', src2)[0], 'missing')

    def test_F6_dotted_abbreviation_still_not_a_break(self):
        src = 'Sales in the U.S. market doubled after the company closed 40 stores in the region.'
        self.assertNotEqual(mq('Sales ... doubled after the company closed 40 stores in the region', src)[0],
                            'missing')

    def test_F7_cjk_exception_compound_is_not_negation(self):
        self.assertEqual(mq('中国经济增长', '近年来中国经济增长的速度非常快。')[0], 'verbatim')
        self.assertEqual(mq('会增加心血管风险', '研究发现，这种药物不会增加心血管风险。')[0], 'missing')


class TestExtract(unittest.TestCase):

    def test_F10_numbered_headings(self):
        self.assertTrue(ec.is_non_claim_section('7_references'))
        self.assertTrue(ec.is_non_claim_section('8_bibliography'))
        self.assertFalse(ec.is_non_claim_section('2_findings'))
        self.assertTrue(ec.is_meta_sentence('This report covers robots in Europe.', '1_introduction'))
        self.assertEqual(ec.classify_claim('Firms should adopt robots.', '9_recommendations'), 'recommendation')
        ids = [sid for sid, _ in ec.parse_sections('# R\n\n## 7. References\n\n[1] A. https://x.org\n')]
        self.assertTrue(any(ec.is_non_claim_section(s) for s in ids), ids)


class TestHelpAndDocs(unittest.TestCase):

    def test_M2_strict_help_matches_layer4_handoff(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'verify_claim_support.py'), 'verify', '--help'],
                           capture_output=True, text=True)
        out = ' '.join(r.stdout.split())
        self.assertNotIn('supported or contested', out)
        self.assertIn('layer 4 has not finished', out)

    def test_M1_methodology_evidence_example_has_provenance(self):
        with open(os.path.join(ROOT, 'reference', 'methodology.md'), encoding='utf-8') as f:
            doc = f.read()
        line = next(ln for ln in doc.splitlines() if 'evidence_store.py add' in ln)
        for field in ('retrieval_id', 'capture_tool', 'verbatim'):
            self.assertIn(field, line)

    def test_M4_methodology_follows_retrieval_rules(self):
        with open(os.path.join(ROOT, 'reference', 'methodology.md'), encoding='utf-8') as f:
            doc = f.read()
        self.assertNotIn('Use WebFetch for deep dives', doc)
        self.assertNotIn('continue remaining parallel searches in background', doc)


if __name__ == '__main__':
    unittest.main()
