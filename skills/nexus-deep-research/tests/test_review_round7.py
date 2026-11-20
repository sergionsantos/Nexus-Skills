#!/usr/bin/env python3
"""Regression tests for the round-7 independent review findings
(.isa/round7-findings.md). Each test names its finding id."""

import os
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import claim_ledger as cl  # noqa: E402
import extract_claims as ec  # noqa: E402


def gate_hit(claim, report):
    rn = cl.normalise_text(report)
    sents = [(s, cl._shingles(cl.normalise_text(s).split())) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


ACME = 'Acme cut 500 jobs at its Ohio plant in 2019.'


class TestGate(unittest.TestCase):

    def test_R7_C1_second_affirmed_copy_in_a_negated_sentence(self):
        rep = ('Acme did not cut 500 jobs at its Ohio plant in 2019, the union claimed, but payroll '
               'records show the company cut 500 jobs at its Ohio plant in 2019.')
        self.assertIsNotNone(gate_hit(ACME, rep))
        # control: one copy negated in place is the correction
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(ACME, 'Acme did not cut 500 jobs at its Ohio plant in 2019, '
                                         'the union said.'))

    def test_R7_C4_abbreviation_does_not_split_a_near_duplicate(self):
        claim = 'Acme Inc. cut 500 jobs at its Ohio plant in March 2019.'
        self.assertIsNotNone(gate_hit(claim, 'Acme Inc. cut 500 jobs at its Ohio plant in early March 2019.'))
        self.assertIsNotNone(gate_hit('The U.S. economy grew 4% in the third quarter of 2023 after strong consumer spending.',
                                      'The U.S. economy grew roughly 4% in the third quarter of 2023 after strong consumer spending.'))
        # nexus: round 8 (R8-C2): sentences are not merged; the join is tried
        # only for an abbreviation the claim itself contains
        self.assertEqual(cl.report_sentences('Acme Inc. cut jobs. Then it grew.'),
                         ['Acme Inc.', 'cut jobs.', 'Then it grew.'])

    def test_R7_C5_portuguese_dot_thousands_restated(self):
        claim = 'A Acme despediu 1.500 trabalhadores na fábrica do Porto em 2019.'
        self.assertIsNotNone(gate_hit(claim, 'A Acme despediu 1500 trabalhadores na fábrica do Porto em 2019.'))
        self.assertIsNone(gate_hit(claim, 'A Acme despediu 150 trabalhadores na fábrica do Porto em 2019.'))
        # nexus: round 9: "1.500" and "1500" share a reading
        self.assertIn('1500', cl._token_keys(cl.normalise_text('1.500')))

    def test_R7_DBLNEG2_even_negations_keep_the_claim(self):
        long = 'Acme cut 300 jobs at its Ohio plant in 2021 after losing two government contracts.'
        self.assertIsNotNone(gate_hit(long, long.replace('Acme cut', 'Acme did not not cut')))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(long, long.replace('Acme cut', 'Acme did not cut')))
        neg = long.replace('Acme cut', 'Acme did not cut')
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(neg, long))


class TestSections(unittest.TestCase):

    def test_R7_C6_numbered_conclusion_heading_like_unnumbered(self):
        t = 'Overall, the evidence suggests demand will keep growing.'
        self.assertEqual(ec.classify_claim(t, '8_conclusion_and_outlook'), 'synthesis')
        self.assertEqual(ec.classify_claim(t, 'conclusion'), 'synthesis')
        self.assertEqual(ec.classify_claim(t, '6_synthesis_of_evidence'), 'synthesis')
        # R6-4 still holds
        self.assertEqual(ec.classify_claim('Personalised feeds might lift basket size by 35% [3].',
                                           '4_recommendation_algorithms_and_engagement'), 'factual')


class TestDocs(unittest.TestCase):

    def test_R7_C2_C3_limitations_documented(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        # nexus: strict gate — R7-C2/C3 are gone with the in-place reading
        self.assertNotIn('any part of the claim', doc)
        self.assertIn('Não é verdade que X', doc)


if __name__ == '__main__':
    unittest.main()
