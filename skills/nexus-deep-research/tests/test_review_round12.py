#!/usr/bin/env python3
"""Regression tests for the round-12 independent review findings
(.isa/round12-findings.md). Each test names its finding id."""

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

    def test_R12_C1_numbered_list_items_are_separate_claims_without_markers(self):
        self.assertEqual(ec.extract_sentences('1. Revenue rose 12% [3].\n2. Costs fell 4% [3].\n3) Margins held at 9% [4].'),
                         ['Revenue rose 12% [3].', 'Costs fell 4% [3].', 'Margins held at 9% [4].'])
        self.assertEqual(ec.extract_sentences('- Revenue rose 12% [3].\n+ Costs fell 4% [3].'),
                         ['Revenue rose 12% [3].', 'Costs fell 4% [3].'])
        # items without a final period are still separate claims
        self.assertEqual(ec.extract_sentences('- Revenue rose 12% in 2023 [3]\n- costs fell 4% in 2023 [3]'),
                         ['Revenue rose 12% in 2023 [3]', 'costs fell 4% in 2023 [3]'])

    def test_R12_C2_label_and_reference_fragments_are_not_claims(self):
        for frag in ('Sources: [1], [2]', 'See also [5].', 'Ibid. [4]', 'See Table 2 below.',
                     'Updated 3 May 2024.', 'Version 2.1 released today.', 'Sources: [1], [2], [4], [5], [6], [7], [8]'):
            self.assertEqual(ec.extract_sentences(frag), [], frag)
        text = 'FActScore breaks text into facts [1].\n\n**Sources:** [1], [2], [4]\n\n---\n\n### Finding 2\n\nGPT-4 scored 58% on it [2].'
        self.assertEqual(ec.extract_sentences(text), ['FActScore breaks text into facts [1].', 'GPT-4 scored 58% on it [2].'])

    def test_R12_C3_F1_short_uncited_figure_sentences_are_claims(self):
        self.assertEqual(ec.extract_sentences('Sales fell 40%. Overhead was 25%. Costs doubled to $4bn. Acme went bankrupt.'),
                         ['Sales fell 40%.', 'Overhead was 25%.', 'Costs doubled to $4bn.'])
        self.assertEqual(ec.extract_sentences('Acme cut 300 jobs.'), ['Acme cut 300 jobs.'])

    def test_R12_C6_F2_only_atx_headings_are_dropped(self):
        self.assertEqual(ec.extract_sentences('#1 cause of death in Portugal is stroke, at 25% of deaths [2].'),
                         ['#1 cause of death in Portugal is stroke, at 25% of deaths [2].'])
        self.assertEqual(ec.extract_sentences('#### Detail\nMemory use rose 25% in the free-threaded build [2].'),
                         ['Memory use rose 25% in the free-threaded build [2].'])

    def test_R12_F5_code_html_blocks_and_comments_end_blocks(self):
        text = ('The Steering Council accepted PEP 703 in 2023 [1].\n```bash\npython3.13t -X gil=0 x.py\n```\n'
                'Early benchmarks showed a 10% slowdown [2].\n<div class="note">\nAcme cut 300 jobs in Ohio [3].\n</div>\n'
                '<!-- Make this actionable and specific -->\nBeta hired 200 engineers in Lisbon [4].')
        self.assertEqual(ec.extract_sentences(text), [
            'The Steering Council accepted PEP 703 in 2023 [1].', 'Early benchmarks showed a 10% slowdown [2].',
            'Acme cut 300 jobs in Ohio [3].', 'Beta hired 200 engineers in Lisbon [4].'])
        self.assertEqual(ec.extract_sentences('> Acme cut 300 jobs in Ohio in 2021 [3].\n> It closed two sites [3].'),
                         ['Acme cut 300 jobs in Ohio in 2021 [3].', 'It closed two sites [3].'])

    def test_R12_F4_template_scaffolding_is_not_claimed(self):
        self.assertTrue(ec.is_non_claim_section('report_metadata'))
        self.assertTrue(ec.is_meta_sentence('Assumption 1: Users run CPython on Linux servers.', 'introduction'))
        self.assertFalse(ec.is_meta_sentence('Assumption 1: 40% of users run CPython 3.13.', 'introduction'))
        self.assertTrue(ec.is_meta_sentence('Confidence Level: High, based on three independent benchmarks.',
                                            'executive_summary'))
        self.assertFalse(ec.is_meta_sentence('Confidence intervals were wide [2].', 'executive_summary'))


class TestGate(unittest.TestCase):

    def test_R12_C4_angle_bracket_prose_is_kept(self):
        self.assertIsNotNone(gate_hit('Acme closed its Ohio plant',
                                      'As the memo put it, <<Acme closed its Ohio plant>> and moved on.'))
        self.assertIsNotNone(gate_hit('O banco fechou a agencia de Braga',
                                      'Segundo a nota, <<O banco fechou a agencia de Braga>> sem aviso.'))
        self.assertIn('higher for group a', cl.normalise_text('scores were <higher for group A than group B> overall'))
        self.assertIsNotNone(gate_hit('a plant was closed in Ohio', 'The memo said <<a plant was closed in Ohio>, sadly.'))

    def test_R12_C5_tags_with_unquoted_equals_and_adjacent_attributes(self):
        claim = 'Revenue grew 12% in 2023'
        for rep in ('Revenue grew <a href=https://x.com/?q=1>12% in 2023</a> overall.',
                    'Revenue grew <a href="x"title="y">12% in 2023</a> overall.',
                    'Revenue grew <a href=/p?a=1&b=2>12% in 2023</a> overall.',
                    'Revenue grew <p data-x=a=b>12% in 2023</p> overall.',
                    'Revenue grew <my-widget kind=x>12% in 2023</my-widget> overall.'):
            self.assertIsNotNone(gate_hit(claim, rep), rep)

    def test_R12_F3_character_references_are_text(self):
        claim = ('Acme cut 1,500 jobs at its Ohio plant in 2021 after the loss of its two largest government '
                 'contracts in the Midwest region.')
        rep = ('Acme cut 1,500&nbsp;jobs at its Ohio&#160;plant in 2021 after the loss of its two largest '
               'government&nbsp;contracts in the Midwest&nbsp;region.')
        self.assertIsNotNone(gate_hit(claim, rep))
        self.assertEqual(cl.normalise_text('&ldquo;Acme&rdquo; &amp; Beta &#8209; 12%'),
                         cl.normalise_text('"Acme" & Beta - 12%'))


class TestDocs(unittest.TestCase):

    def test_R12_docs(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        self.assertIn('Table rows are not claims', doc)
        self.assertIn('a date (with an English or Portuguese month name) or a year', doc)
        self.assertIn('character references', doc)
        self.assertIn('unless an edit next to it', doc)


if __name__ == '__main__':
    unittest.main()
