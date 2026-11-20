#!/usr/bin/env python3
"""Regression tests for the round-10 independent review findings
(.isa/round10-findings.md). Each test names its finding id."""

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
    sents = [(s, None) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


LONG = 'Acme cut 300 jobs at its Ohio plant in 2021 after the merger with Beta.'


class TestRound10(unittest.TestCase):

    def test_R10_A1_bare_claim_figure_given_a_kind_by_the_report_context(self):
        # nexus: "25 and 30%" reads 25 as a percent range end in the report only
        self.assertIsNotNone(gate_hit('Average class size fell to 25.',
                                      'Average class size fell to 25 and 30% of schools closed.'))
        self.assertIsNotNone(gate_hit('O desemprego desceu para 6.',
                                      'O desemprego desceu para 6 e 20% dos jovens encontraram emprego.'))
        # a kind in the claim must still be stated with that kind
        self.assertIsNone(gate_hit('Average class size fell by 25%.', 'Average class size fell by 25 pupils.'))

    def test_R10_A2_claim_spanning_several_report_sentences(self):
        claim = 'O desemprego em Portugal subiu para 12% em 2023. É o valor mais alto registado desde 2010 [1].'
        self.assertIsNotNone(gate_hit(claim, claim.replace('2010', '2012')))
        claim = ('Acme cut 300 jobs at its Ohio plant in 2021. 12% of its remaining staff then left the '
                 'company within a year [1].')
        self.assertIsNotNone(gate_hit(claim, claim.replace('12%', '15%')))
        claim = ('Acme cut 300 jobs at its Ohio plant in 2021 after losing two contracts [1]\n'
                 'Beta Corp hired 200 engineers in Lisbon during the same year [2]')
        rep = ('- Acme cut 300 jobs at its Ohio plant in 2021 after losing two contracts [1]\n'
               '- Beta Corp hired 250 engineers in Lisbon during the same year [2]')
        self.assertIsNotNone(gate_hit(claim, rep))
        # control: unrelated neighbouring sentences do not add up to the claim
        self.assertIsNone(gate_hit(claim, 'Acme reported results in 2021. Beta Corp opened an office in Lisbon.'))

    def test_R10_A3_abbreviation_with_citation_marker_in_the_claim(self):
        claim = 'Acme Inc.[3] cut 300 jobs at its Ohio plant in 2021 after the merger with Beta.'
        self.assertIsNotNone(gate_hit(claim, claim.replace('cut 300', 'cut about 300')))
        self.assertIsNone(gate_hit(claim, 'Acme Inc.[3] kept its Ohio staff in 2021.'))

    def test_R10_A4_less_than_sign_in_prose_is_not_an_html_tag(self):
        claim = 'Response rates stayed <half of the target in 2021.'
        self.assertIsNotNone(gate_hit(claim, claim + ' Later, growth was >10%.'))
        self.assertEqual(cl.normalise_text('Acme <b>cut</b> 300<sup>3</sup> jobs<br/>'), 'acme cut 300 jobs')

    def test_R10_B1_many_refuted_claims_on_a_long_report(self):
        report = ' '.join(f'Unit {i} of the group kept {i} staff at site {i} in 2021 after the review.'
                          for i in range(1500))
        sents = [(s, None) for s in cl.report_sentences(report)]
        rn = cl.normalise_text(report)
        t = time.time()
        for k in range(20):
            self.assertIsNone(cl.refuted_in_report(f'Acme cut {k} jobs at its Ohio plant in March 2020 after '
                                                   f'the merger with the rival.', rn, sents))
        self.assertLess(time.time() - t, 6)


class TestDocs(unittest.TestCase):

    def test_R10_F1_F2_docs(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        self.assertIn('space-grouped thousands', doc)
        block = doc.split('## Layer 6')[1].split('```bash')[1].split('```')[0]
        self.assertTrue(block.strip().splitlines()[0].startswith(
            'python scripts/extract_claims.py extract --dir [run] --report [run]/report.md'))


if __name__ == '__main__':
    unittest.main()
