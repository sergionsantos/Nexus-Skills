#!/usr/bin/env python3
"""Regression tests for the round-11 independent review findings
(.isa/round11-findings.md). Each test names its finding id."""

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

    def test_R11_F1_sentence_after_subheading_or_table_is_extracted(self):
        text = ('### Proposal\n\nPEP 703 proposes a build that is 30% faster on four cores [1][2].\n\n'
                '| a | b |\n|---|---|\n| 1 | 2 |\n\nThe table shows that 12% of packages failed the suite [3].')
        sents = ec.extract_sentences(text)
        self.assertIn('PEP 703 proposes a build that is 30% faster on four cores [1][2].', sents)
        self.assertIn('The table shows that 12% of packages failed the suite [3].', sents)
        # no blank line between heading/table and text
        sents = ec.extract_sentences('### Proposal\nPEP 703 proposes a build that is 30% faster [1].')
        self.assertEqual(sents, ['PEP 703 proposes a build that is 30% faster [1].'])
        self.assertFalse(any(s.startswith(('#', '|')) for s in ec.extract_sentences(text)))

    def test_R11_F2_short_cited_sentence_is_extracted(self):
        self.assertIn('Memory use rose 9% [2].', ec.extract_sentences('Memory use rose 9% [2]. Costs fell.'))
        self.assertIn('Memory use rose sharply [2].', ec.extract_sentences('Memory use rose sharply [2]. Costs fell.'))
        self.assertIn('Costs fell 9% overall.', ec.extract_sentences('Costs fell 9% overall. Costs fell [3].'))
        self.assertEqual(ec.extract_sentences('See table 4. Costs fell.'), [])
        self.assertNotIn('Costs fell.', ec.extract_sentences('Memory use rose 9% [2]. Costs fell.'))


class TestGate(unittest.TestCase):

    def test_R11_F3_any_well_formed_inline_tag_is_markup(self):
        claim = ('Acme cut 1,500 jobs at its Ohio plant in 2021 after the loss of its two largest '
                 'government contracts in the Midwest region [3].')
        rep = ('Acme cut 1,500 jobs at its <samp>Ohio</samp> plant in <time datetime="2021">2021</time> after the '
               'loss of its <nobr>two</nobr> largest <var>government</var> contracts in the Midwest region [3].')
        self.assertIsNotNone(gate_hit(claim, rep))
        self.assertEqual(cl.normalise_text('a <font color="red">b</font> <data value=3>c</data> d'), 'a b c d')
        # prose comparisons are not tags (R10-A4)
        self.assertEqual(cl.normalise_text('stayed <half of the target in 2021. Later >10%.'),
                         'stayed half of the target in 2021 later 10%')


class TestDocs(unittest.TestCase):

    def test_R11_docs(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        with open(os.path.join(ROOT, 'SKILL.md'), encoding='utf-8') as f:
            skill = f.read()
        self.assertIn('up to about 16 words', doc)                     # C1
        self.assertIn('window of consecutive report sentences', skill)  # C2
        self.assertNotIn('shingle overlap in a sentence', skill)
        self.assertIn('up to 8', doc)
        self.assertIn('neighbouring sentences', doc)                    # D1
        self.assertIn('30 characters', doc)                             # F2
        self.assertIn('research_report_', doc)                          # F4
        self.assertIn('in the same section keeps its claim id', doc)    # F5
        self.assertNotIn('or if a report sentence shares', open(os.path.join(ROOT, 'scripts', 'claim_ledger.py'),
                                                                 encoding='utf-8').read())


if __name__ == '__main__':
    unittest.main()
