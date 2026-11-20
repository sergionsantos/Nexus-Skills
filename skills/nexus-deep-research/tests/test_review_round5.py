#!/usr/bin/env python3
"""Regression tests for the round-5 independent review findings
(.isa/round5-findings.md). Each test names its finding id."""

import os
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

    def test_R5_1_negation_of_another_verb_does_not_hide_repeat(self):
        claim = 'Acme cut 300 jobs in 2021.'
        for prefix in ('Nobody disputes that ', 'No analyst was surprised when ', 'Never before had ',
                       'No one seriously doubts that '):
            self.assertIsNotNone(gate_hit(claim, prefix + claim[0].lower() + claim[1:]), prefix)

    def test_R5_1_portuguese_contraction_no_is_not_negation(self):
        claim = 'O desemprego subiu para 12% em 2023.'
        self.assertIsNotNone(gate_hit(claim, 'No ano passado o desemprego subiu para 12% em 2023.'))
        # nexus: strict gate — negations are not read at all: the gate is exact
        # text or shingle overlap >= 0.8, nothing else. A word inserted into a
        # 7-word claim leaves 3/5 shingles (< 0.8): documented short-claim limit
        self.assertIsNotNone(gate_hit(claim, 'Não é verdade que o desemprego subiu para 12% em 2023.'))
        self.assertIsNone(gate_hit(claim, 'O desemprego não subiu para 12% em 2023.'))
        self.assertIsNone(gate_hit(claim, 'O desemprego desceu para 7% em 2023.'))

    def test_R5_1_verbatim_path_reads_negation_of_another_verb(self):
        # nexus: round 6 design: the exact text counts whatever precedes it
        claim = 'Acme cut 300 jobs in 2021.'
        self.assertIsNotNone(gate_hit(claim, 'Nobody disputes that Acme cut 300 jobs in 2021.'))
        self.assertIsNotNone(gate_hit(claim, 'There is no evidence that Acme cut 300 jobs in 2021.'))

    def test_R5_1_near_path_reads_negation_of_another_verb(self):
        claim = 'Acme cut 300 jobs at its Ohio plant in 2021.'
        self.assertIsNotNone(gate_hit(claim, 'Nobody disputes that Acme cut 300 jobs at its Ohio plant '
                                             'in early 2021.'))
        # nexus: round 6 design: a frame around the claim is not read
        self.assertIsNotNone(gate_hit(claim, 'There is no evidence that Acme cut 300 jobs at its Ohio plant '
                                             'in early 2021.'))
        self.assertIsNone(gate_hit(claim, 'Acme did not cut 300 jobs at its Ohio plant in early 2021.'))

    def test_R5_1_correction_frames_still_correct(self):
        # nexus: round 6 design: frames around the exact text fail; in place passes
        claim = 'Vaccines cause autism in children.'
        for rep in ('There is no evidence that vaccines cause autism in children [4].',
                    'Studies did not find that vaccines cause autism in children [4].',
                    'It is not true that vaccines cause autism in children [4].',
                    'No vaccines cause autism in children [4].'):
            self.assertIsNotNone(gate_hit(claim, rep), rep)
        self.assertIsNone(gate_hit(claim, 'Vaccines do not cause autism in children [4].'))
        self.assertIsNotNone(gate_hit('As vacinas causam autismo em crianças.',
                                      'Não há evidência de que as vacinas causam autismo em crianças.'))
        self.assertIsNone(gate_hit('As vacinas causam autismo em crianças.',
                                   'As vacinas não causam autismo em crianças.'))

    def test_R5_4_spaced_range_refuted_claim_is_caught(self):
        claim = 'Administrative overhead at the agency was 10 – 12% of the total budget in 2022 [2].'
        rep = 'Administrative overhead at the agency was about 10 – 12% of the total budget in 2022 [2].'
        self.assertIsNotNone(gate_hit(claim, rep))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(claim, 'Administrative overhead at the agency was not 10 – 12% '
                                          'of the total budget in 2022 [2].'))

    def test_R5_4_dash_after_year_keeps_refuted_claim_caught(self):
        self.assertIsNotNone(gate_hit('In 2023, 12% of firms closed.', 'In 2023 – 12% of firms closed.'))


class TestNumbers(unittest.TestCase):

    def test_R5_4_year_does_not_take_a_kind(self):
        self.assertEqual(extract_numbers('In 2023 – 12% of firms closed'), {'2023', '12%'})
        self.assertEqual(extract_numbers('300 jobs and 12%'), {'300', '12%'})
        self.assertEqual(extract_numbers('In 2023 and 12% of firms'), {'2023', '12%'})
        self.assertEqual(extract_numbers('between 10 and 12%'), {'10%', '12%'})
        self.assertEqual(extract_numbers('cut 40 and 12% of staff respectively'), {'40%', '12%'})
        self.assertEqual(extract_numbers('10 – 12%'), {'10%', '12%'})

    def test_R5_5_times_is_multiplier_unless_frequency(self):
        self.assertEqual(extract_numbers("3 times a typical rival's revenue"), {'3x'})
        self.assertEqual(extract_numbers('3 times a day'), {'3'})
        self.assertEqual(extract_numbers('2 times per week'), {'2'})
        st = compute_support_score('Acme revenue is 3x that of a typical rival [1].',
                                   ["Acme revenue is 3 times a typical rival's revenue."])[0]
        self.assertEqual(st, 'supported')

    def test_R5_6_portuguese_decimal_comma(self):
        self.assertEqual(extract_numbers('1,250 milhões'), {'1250000'})
        self.assertEqual(extract_numbers('1,500 mil'), {'1500'})
        self.assertEqual(extract_numbers('1,5 mil milhões'), {'1500000000'})
        self.assertEqual(extract_numbers('2.000 milhões'), {'2000000000'})
        self.assertEqual(extract_numbers('1,500 million'), {'1500000000'})
        st = compute_support_score('O investimento foi de 1,5 mil milhões de euros em 2023 [1].',
                                   ['O investimento foi de 1,500 milhões de euros em 2023.'])[0]
        self.assertNotEqual(st, 'supported')


class TestQuotes(unittest.TestCase):

    def test_R5_2_exception_straddling_quote_edge_does_not_hide_negation(self):
        for quote, src in [
            ('来过北京', '报告指出，该总统从未来过北京，也没有会见当地官员。'),
            ('常见', '这种副作用并非常见。'),
            ('来得及完成测试', '工程师们未来得及完成测试。'),
        ]:
            self.assertEqual(mq(quote, src)[0], 'missing', quote)

    def test_R5_2_exception_wholly_outside_is_still_masked(self):
        self.assertEqual(mq('中国经济增长', '近年来中国经济增长的速度非常快。')[0], 'verbatim')


class TestExtract(unittest.TestCase):

    def test_R5_8_section_kinds_match_by_prefix(self):
        self.assertEqual(ec.classify_claim('Regulators should raise the cap to 15% by 2027 [3].',
                                           '9_recommendations_for_policyma'), 'recommendation')
        self.assertEqual(ec.classify_claim('Taken together, the evidence is mixed.',
                                           '6_synthesis_and_discussion'), 'synthesis')


class TestDocs(unittest.TestCase):

    def test_E_BIB_bibliography_heading_documented(self):
        with open(os.path.join(ROOT, 'SKILL.md'), encoding='utf-8') as f:
            self.assertIn('exactly `## Bibliography`', f.read())

    def test_R5_3_R5_7_limitations_documented(self):
        # nexus: round 6 replaced the R5-3/R5-7 limitations by the plain rule
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        self.assertIn('There is no evidence that X', doc)
        # nexus: strict gate — frames and corrections are not interpreted
        self.assertIn('Negations, frames and corrections are **not** interpreted', doc)


if __name__ == '__main__':
    unittest.main()
