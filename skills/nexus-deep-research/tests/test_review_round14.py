#!/usr/bin/env python3
"""Regression tests for the round-14 independent review findings
(.isa/round14-findings.md)."""

import os
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import extract_claims as ec  # noqa: E402


class TestRound14(unittest.TestCase):

    def test_R14_C1_accented_summary_heading(self):
        for sec in ('sumário_executivo', 'sumário', '1_sumário_executivo', 'resumo_executivo', 'executive_summary'):
            self.assertTrue(ec.is_meta_sentence('Nível de confiança: Médio, com base em 3 estudos independentes.', sec), sec)
        self.assertFalse(ec.is_meta_sentence('Nível de confiança: Médio, com base em 3 estudos independentes.', 'finding_1'))

    def test_R14_C2_year_or_quarter_label_with_cited_figure(self):
        self.assertEqual(ec.extract_sentences('- 2022: 12% [3]\n- 2023: 19% [4]\n- Q3 2024: 21% [4]'),
                         ['2022: 12% [3]', '2023: 19% [4]', 'Q3 2024: 21% [4]'])
        self.assertEqual(ec.extract_sentences('- 2023 [4]\n- Table 3 [4]'), [])

    def test_R14_C3_numbered_continuation_inside_a_list_item(self):
        text = '- Acme reported revenue of $4.2bn for fiscal\n  2023. Margins were stable at 12% in the period [1].'
        self.assertEqual(ec.extract_sentences(text),
                         ['Acme reported revenue of $4.2bn for fiscal\n2023.', 'Margins were stable at 12% in the period [1].'])
        text = '1. Acme reported revenue of $4.2bn for fiscal\n2023. Margins were stable [1].\n2. Costs fell 4% in 2023 [3].'
        self.assertEqual(ec.extract_sentences(text), ['Acme reported revenue of $4.2bn for fiscal\n2023.',
                                                      'Margins were stable [1].', 'Costs fell 4% in 2023 [3].'])

    def test_R14_F1_docs_preamble(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        self.assertIn('Text above the first `##` heading', doc)


if __name__ == '__main__':
    unittest.main()
