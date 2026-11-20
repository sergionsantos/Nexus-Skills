#!/usr/bin/env python3
"""Regression tests for the round-8 independent review findings
(.isa/round8-findings.md). Each test names its finding id."""

import os
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import claim_ledger as cl  # noqa: E402
import extract_claims as ec  # noqa: E402
from verify_claim_support import compute_support_score, extract_numbers  # noqa: E402


def gate_hit(claim, report):
    rn = cl.normalise_text(report)
    sents = [(s, cl._shingles(cl.normalise_text(s).split())) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


LONG = 'Acme cut 300 jobs at its Ohio plant in 2021 after the loss of its two largest government contracts.'


class TestFigureFormats(unittest.TestCase):

    def test_R8_C1_language_detection_does_not_split_the_reading(self):
        claim = 'Acme despediu 1.500 trabalhadores na fábrica de Braga durante 2019 após perder contratos.'
        self.assertIsNotNone(gate_hit(claim, claim[:-1] + ', segundo o jornal.'))
        short = 'A Acme despediu 1.500 trabalhadores.'
        self.assertIsNotNone(gate_hit(short, 'O relatório anual foi publicado em março. Não há evidência de que '
                                             'a Acme despediu 1.500 trabalhadores, segundo o sindicato.'))
        en = 'The seal failure rate was 0.005 at Acme plants in Ohio during 2019 across all 12 production lines and shifts.'
        self.assertIsNotNone(gate_hit(en, en[:-1] + ', mostly o-ring seals.'))
        # nexus: the reading no longer depends on the text's language
        self.assertEqual(cl.normalise_text('rate 0.005 for the o-ring'), 'rate 0.005 for the o ring')

    def test_R7_C5_thousands_convention_switch_is_not_a_correction(self):
        claim = 'A Acme despediu 1.500 trabalhadores na fábrica do Porto em 2019.'
        self.assertIsNotNone(gate_hit(claim, 'A Acme despediu 1500 trabalhadores na fábrica do Porto em 2019.'))
        self.assertIsNone(gate_hit(claim, 'A Acme despediu 150 trabalhadores na fábrica do Porto em 2019.'))
        rev = 'A Acme despediu 1500 trabalhadores na fábrica do Porto em 2019.'
        self.assertIsNotNone(gate_hit(rev, 'A Acme despediu 1.500 trabalhadores na fábrica do Porto em 2019.'))
        # nexus: round 9: one token for both spellings, matching both readings
        self.assertEqual(cl.normalise_text('cerca de 12.500 casas'), cl.normalise_text('cerca de 12,500 casas'))
        self.assertEqual(cl._token_keys("12.5'12500"), {'12.5', '12500'})
        self.assertEqual(cl._token_keys('12%'), {'12%'})
        self.assertNotIn('125', cl._token_keys("12.5'12500"))

    def test_R8_C3_dot_thousands_with_decimal_comma(self):
        self.assertEqual(extract_numbers('perdas de 1.500,5 milhões'), {'1500500000'})
        self.assertEqual(extract_numbers('o valor é 1.234,56 euros'), {'1234.56'})
        claim = 'A Acme registou perdas de 1.500,25 euros por trabalhador na fábrica do Porto em 2021.'
        self.assertIsNotNone(gate_hit(claim, claim.replace('1.500,25', '1500,25')))
        st = compute_support_score('A Acme registou perdas de 1.500,5 milhões de euros em 2021 [2].',
                                   ['A Acme registou perdas de 2.700,5 milhões de euros em 2021.'])[0]
        self.assertNotEqual(st, 'supported')


class TestAbbreviations(unittest.TestCase):

    def test_R8_C2_sentence_ending_in_abbreviation_does_not_block_correction(self):
        for prev in ('Acme is headquartered in the U.S.', 'The figures come from Acme Corp.',
                     'Acme sells vitamin D.', 'Acme reported losses since Jan.'):
            rep = prev + ' ' + LONG.replace('Acme cut', 'Acme did not cut')
            # nexus: strict gate — a correction that restates the refuted claim fails
            self.assertIsNotNone(gate_hit(LONG, rep), prev)
        corrected = LONG.replace('300', '30')
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(LONG, 'Payroll fell by 300 in the U.S. ' + corrected))
        self.assertEqual(len(cl.report_sentences('Acme sells vitamin D. Acme grew. O nível do mar. Subiu.')), 4)

    def test_R8_C2_stray_first_word_before_in_place_negation(self):
        rep = 'In a statement Acme said that ' + LONG.replace('Acme cut', 'Acme did not cut')
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(LONG, rep))
        self.assertIsNotNone(gate_hit(LONG, 'In a statement Acme said that ' + LONG))

    def test_R8_C2_claim_last_word_is_not_an_abbreviation(self):
        claim = 'Acme cut 300 jobs in 2021 after the loss of its two largest government contracts in Ohio.'
        rep = 'Payroll fell by 300 in Ohio. ' + claim.replace('300', '30')
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(claim, rep))

    def test_R7_C4_claim_abbreviation_still_joined(self):
        claim = 'Acme Inc. cut 500 jobs at its Ohio plant in March 2019.'
        self.assertIsNotNone(gate_hit(claim, 'Acme Inc. cut 500 jobs at its Ohio plant in early March 2019.'))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(claim, 'Acme Inc. did not cut 500 jobs at its Ohio plant in March 2019.'))

    def test_R8_second_copy_after_stray_first_word(self):
        rep = ('Acme is based in Ohio and Acme did not cut 300 jobs at its Ohio plant in 2021 after the loss '
               'of its two largest government contracts, yet Acme cut 300 jobs at its Ohio plant in 2021 after '
               'the loss of its two largest government contracts.')
        self.assertIsNotNone(gate_hit(LONG, rep))


class TestSections(unittest.TestCase):

    def test_R8_C4_prefix_heading_numbered_like_unnumbered(self):
        t = 'Overall, the evidence suggests demand will keep growing.'
        for sid in ('5_synthesised_findings', '8_conclusionary_remarks', 'synthesis', 'conclusion'):
            self.assertEqual(ec.classify_claim(t, sid), 'synthesis', sid)
        self.assertEqual(ec.classify_claim('Personalised feeds might lift basket size by 35% [3].',
                                           '4_recommendation_algorithms_and_engagement'), 'factual')


class TestDocs(unittest.TestCase):

    def test_R8_docs(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        # nexus: strict gate — negations are not counted
        self.assertNotIn('an odd number of real negations', doc)
        self.assertIn('### Limitations of the lexical filters (layers 1-2)', doc)
        self.assertIn('`1.234,56` = 1234.56', doc)
        self.assertIn('"non" (it)', doc)
        self.assertNotIn('polarity cues for en, pt, es, fr', doc)


if __name__ == '__main__':
    unittest.main()
