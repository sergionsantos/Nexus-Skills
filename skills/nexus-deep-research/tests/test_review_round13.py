#!/usr/bin/env python3
"""Regression tests for the round-13 independent review findings
(.isa/round13-findings.md). C* = code review, E* = docs/e2e review."""

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
    sents = [(s, None) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


class TestExtraction(unittest.TestCase):

    def test_R13_C1_numbered_continuation_line_is_not_a_list_item(self):
        text = 'Acme reported revenue of $4.2bn for fiscal\n2023. Margins were stable at 12% in the period [1].'
        self.assertEqual(ec.extract_sentences(text),
                         ['Acme reported revenue of $4.2bn for fiscal\n2023.', 'Margins were stable at 12% in the period [1].'])
        # a list still starts after a blank line, with "1." inside a paragraph, and continues with 2.
        self.assertEqual(ec.extract_sentences('Results:\n1. Revenue rose 12% [3].\n2. Costs fell 4% [3].'),
                         ['Revenue rose 12% [3].', 'Costs fell 4% [3].'])
        self.assertEqual(ec.extract_sentences('\n3. Revenue rose 12% [3].\n4. Costs fell 4% [3].'),
                         ['Revenue rose 12% [3].', 'Costs fell 4% [3].'])

    def test_R13_C2_inline_comment_does_not_split_a_sentence(self):
        self.assertEqual(ec.extract_sentences('Revenue grew <!-- check Q4 --> 12% in 2023 [1].'),
                         ['Revenue grew 12% in 2023 [1].'])
        self.assertEqual(ec.extract_sentences('Acme cut 300 jobs in Ohio [3].\n<!-- reviewer note -->\nBeta hired 200 staff [4].'),
                         ['Acme cut 300 jobs in Ohio [3].', 'Beta hired 200 staff [4].'])
        # a comment on its own line ends the paragraph, even without a final period
        self.assertEqual(ec.extract_sentences('Acme cut 300 jobs in Ohio [3]\n<!-- reviewer note -->\nbeta hired 200 staff [4]'),
                         ['Acme cut 300 jobs in Ohio [3]', 'beta hired 200 staff [4]'])

    def test_R13_C3_one_word_label_with_cited_figure_is_a_claim(self):
        self.assertEqual(ec.extract_sentences('- Slowdown: 8% [2]\n- Memory: +15% [3]\n- Sources: [1], [2]'),
                         ['Slowdown: 8% [2]', 'Memory: +15% [3]'])

    def test_R13_C4_E1_month_words_must_be_whole_months(self):
        for s in ('Prices fell in 3 markets.', 'Costs doubled in 3 decades.', 'Sales declined 12%.',
                  'Costs decreased 8%.', 'Abriram 12 novas fábricas.', 'Exports declined 7% [2].'):
            self.assertEqual(ec.extract_sentences(s), [s], s)
        for s in ('Updated 3 May 2024.', 'Published on 12 March.', 'Revisto a 3 de março.', 'Due by Sept. 4.'):
            self.assertEqual(ec.extract_sentences(s), [], s)

    def test_R13_E2_year_shaped_percent_is_a_figure(self):
        self.assertEqual(ec.extract_sentences('Revenue grew 2023%.'), ['Revenue grew 2023%.'])
        self.assertEqual(ec.extract_sentences('It changed in 2023.'), [])

    def test_R13_C5_fences_inside_lists_and_blockquotes_are_not_text(self):
        text = ('1. Install the build first:\n\n    ```bash\n    uv python install 3.13t\n    PYTHON_GIL=0 python3.13t bench.py --runs 12\n    ```\n\n'
                '> ```\n> rows = 400 per batch, limit 12\n> ```\n> The batch size was 400 rows in 2024 [2].')
        self.assertEqual(ec.extract_sentences(text), ['The batch size was 400 rows in 2024 [2].'])

    def test_R13_E3_confidence_label_only_in_summary_and_pt(self):
        self.assertTrue(ec.is_meta_sentence('Confidence Level: High, based on three benchmarks.', 'executive_summary'))
        self.assertTrue(ec.is_meta_sentence('Nível de confiança: Médio, com base em três estudos.', 'resumo_executivo'))
        self.assertFalse(ec.is_meta_sentence('Confidence: 95% of users rated the build stable.', 'finding_1'))


class TestGate(unittest.TestCase):

    def test_R13_C6_less_than_a_is_prose(self):
        claim = '<a quarter of SMEs used cloud AI tools in 2023 [2].'
        self.assertIsNotNone(gate_hit(claim, '<a quarter of SMEs used cloud AI tools in 2023 vs >60% of large firms.'))
        self.assertIn('a year in most cases', cl.normalise_text('Recovery took <a year in most cases and >3 years in severe ones.'))
        self.assertEqual(cl.normalise_text('<td nowrap>12%</td> <details open>x</details>'), '12% x')

    def test_R13_C7_tag_before_greater_than_text_is_stripped(self):
        self.assertIsNotNone(gate_hit('Acme cut >300 jobs at its Ohio plant in 2021.',
                                      'Acme cut <strong>>300</strong> jobs at its Ohio plant in 2021.'))

    def test_R13_C8_html_comments_are_not_report_text(self):
        self.assertIsNotNone(gate_hit('Acme cut 300 jobs at its Ohio plant in 2021.',
                                      'Acme cut 300 jobs <!-- x --> at its Ohio plant in 2021.'))
        self.assertIsNotNone(gate_hit('O banco fechou 12 agencias em Braga em 2023.',
                                      'O banco fechou 12 agencias <!-- confirmar --> em Braga em 2023.'))


class TestDocs(unittest.TestCase):

    def test_R13_docs(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        self.assertIn('inside list items and blockquotes', doc)
        self.assertIn('4-digit number from 1900 to 2099', doc)
        self.assertIn('Nível de confiança', doc)
        self.assertIn('HTML comments', doc.split('Final statuses')[1])


if __name__ == '__main__':
    unittest.main()
