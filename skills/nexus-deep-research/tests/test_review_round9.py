#!/usr/bin/env python3
"""Regression tests for the round-9 independent review findings
(.isa/round9-findings.md). Each test names its finding id."""

import os
import sys
import time
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import claim_ledger as cl  # noqa: E402


def gate_hit(claim, report):
    rn = cl.normalise_text(report)
    sents = [(s, cl._shingles(cl.normalise_text(s).split())) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


LONG = 'Acme cut 300 jobs at its Ohio plant in 2021 after the loss of its two largest government contracts.'


class TestRound9(unittest.TestCase):

    def test_R9_C1_negation_of_a_separate_clause_is_not_in_place(self):
        claim = 'The company cut 500 jobs at its Lisbon plant in March 2020.'
        rep = 'Acme, which had promised it would not, cut 500 jobs at its Lisbon plant in March 2020.'
        self.assertIsNotNone(gate_hit(claim, rep))

    def test_R9_C2_one_figure_switched_convention(self):
        claim = 'A Acme despediu 1500 trabalhadores em Braga e 12.500 no Porto em 2019.'
        rep = 'A Acme despediu 1.500 trabalhadores em Braga e 12500 no Porto em 2019.'
        self.assertIsNotNone(gate_hit(claim, rep))

    def test_R9_EN12500_comma_group_switched_to_dot(self):
        claim = 'Acme cut 12,500 jobs at its Ohio plants in 2021 after losing two government contracts.'
        self.assertIsNotNone(gate_hit(claim, claim.replace('12,500', '12.500')))
        self.assertIsNone(gate_hit(claim, claim.replace('12,500', '1,250')))

    def test_R9_CORR25_plain_figure_correction_by_1000_passes(self):
        claim = 'The Ohio plant emitted 2500 tonnes of sulphur dioxide in 2021 according to the regional agency.'
        self.assertIsNone(gate_hit(claim, claim.replace('2500', '2.5')))
        self.assertIsNone(gate_hit(claim, claim.replace('2500', '250')))

    def test_R9_C3_claim_with_two_abbreviations(self):
        claim = 'In 2021 the Ohio plant of Acme Inc. in the U.S. cut 300 jobs after losing two contracts.'
        self.assertIsNotNone(gate_hit(claim, claim.replace('cut 300', 'cut about 300')))
        # nexus: strict gate — a correction that restates the claim fails
        self.assertIsNotNone(gate_hit(claim, claim.replace('cut 300', 'did not cut 300')))
        self.assertIsNone(gate_hit(claim, 'Acme kept its Ohio staff in 2021.'))

    def test_R10_strict_exact_text_of_a_short_claim(self):
        # nexus: strict gate — a 2-word refuted claim inside a longer sentence
        # has no 3-word shingle; the exact-text check catches it
        self.assertIsNotNone(gate_hit('Acme collapsed.', 'In 2020 Acme collapsed overnight.'))
        self.assertIsNone(gate_hit('Acme collapsed.', 'In 2020 Acme recovered.'))

    def test_R10_strict_frames_and_negations_fail(self):
        # nexus: strict gate — nothing is interpreted
        claim = 'Vaccines cause infertility in women of childbearing age according to the cohort study.'
        for rep in ('It is not true that ' + claim[0].lower() + claim[1:],
                    'There is no evidence that ' + claim[0].lower() + claim[1:],
                    claim[:-1] + ', but the study was retracted.',
                    claim.replace('Vaccines cause', 'Vaccines do not cause')):
            self.assertIsNotNone(gate_hit(claim, rep), rep)
        self.assertIsNotNone(gate_hit('As vendas cresceram 12% em 2023 segundo o relatório anual da empresa.',
                                      'Não é verdade que as vendas cresceram 12% em 2023 segundo o relatório '
                                      'anual da empresa.'))
        self.assertIsNone(gate_hit('As vendas cresceram 12% em 2023 segundo o relatório anual da empresa.',
                                   'As vendas cresceram 3% em 2023.'))

    def test_R9_C4_long_sentence_is_bounded(self):
        # nexus: one long list-like sentence with many "the" (review9 perf.py)
        claim = 'the company cut 500 jobs at the Lisbon plant in March 2020 after the merger with the rival'
        filler = '; '.join(f'the unit {i} of the group kept the staff at the site {i}' for i in range(500))
        rep = filler + '; the company axed 500 jobs at the Lisbon plant in March 2020 after the merger with the rival.'
        t = time.time()
        self.assertIsNotNone(gate_hit(claim, rep))
        self.assertLess(time.time() - t, 2)


if __name__ == '__main__':
    unittest.main()
