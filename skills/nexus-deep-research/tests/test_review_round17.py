#!/usr/bin/env python3
"""Regression tests for the round-17 re-review findings (.isa/round17-findings.md)."""

import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

import verify_claim_support as vcs  # noqa: E402
import verify_quotes as vq  # noqa: E402


def status(claim, *quotes):
    return vcs.compute_support_score(claim, list(quotes))[0]


class TestRound17(unittest.TestCase):

    def test_F17_1_direction_noun_does_not_cancel_the_verb(self):
        cases = [
            ('Wage growth fell to 2% in 2023 [1].', 'Wage growth rose to 2% in 2023.'),
            ('Wage growth increased to 2% in 2023 [1].', 'Wage growth decreased to 2% in 2023.'),
            ('O crescimento do PIB caiu para 2% em 2023 [1].', 'O crescimento do PIB subiu para 2% em 2023.'),
            ('O aumento dos preços caiu para 2% em 2023 [1].', 'O aumento dos preços subiu para 2% em 2023.'),
            ('Sales fell 12% in 2023 despite growth in exports [1].',
             'Sales rose 12% in 2023 despite growth in exports.'),
            ('The company set up 12 plants as sales fell 5% in 2023 [1].',
             'The company set up 12 plants as sales rose 5% in 2023.'),
        ]
        for claim, quote in cases:
            self.assertNotEqual(status(claim, quote), 'supported', claim)
        # R16 noun cases still caught; agreeing noun + verb still supported
        self.assertNotEqual(status('As vendas registaram uma subida de 12% em 2023 [1].',
                                   'As vendas registaram uma queda de 12% em 2023.'), 'supported')
        self.assertEqual(status('Wage growth fell to 2% in 2023 [1].', 'Wage growth fell to 2% in 2023.'),
                         'supported')

    def test_F18_1_negated_direction_noun_kept(self):
        for claim, quote in (
            ('Sales rose 5% in 2023 [1].', 'There was no growth in 2023: sales fell 5%.'),
            ('Sales rose 5% in 2023 [1].', 'Sales were not up in 2023; they fell 5%.'),
            ('As vendas aumentaram 5% em 2023 [1].', 'As vendas não registaram crescimento e caíram 5% em 2023.'),
            ('As vendas subiram 5% em 2023 [1].', 'Não houve crescimento em 2023: as vendas caíram 5%.'),
        ):
            self.assertNotEqual(status(claim, quote), 'supported', (claim, quote))

    def test_F17_2_hyphenated_quarters(self):
        self.assertNotEqual(status('Siemens reported third-quarter revenue of 5 billion in 2023 [1].',
                                   'Siemens reported first-quarter revenue of 5 billion in 2023.'), 'supported')
        self.assertNotEqual(status('Sales rose 12% in the second-half of 2023 [1].',
                                   'Sales rose 12% in the first-half of 2023.'), 'supported')

    def test_F17_3_minus_dropped_mid_quote(self):
        src = vq.normalize('Real wages in the euro area changed by -5% in 2023 compared with the previous year.')
        q = 'Real wages in the euro area changed by 5% in 2023 compared with the previous year'
        self.assertEqual(vq.match_quote_detail(q, src)[0], 'missing')
        ok = vq.normalize('The COVID-19 rules changed by 5% in 2023 compared with the previous year.')
        self.assertEqual(vq.match_quote_detail('The COVID-19 rules changed by 5% in 2023', ok)[0], 'verbatim')


if __name__ == '__main__':
    unittest.main()
