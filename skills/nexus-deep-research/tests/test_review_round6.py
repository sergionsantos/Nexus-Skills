#!/usr/bin/env python3
"""Regression tests for the round-6 independent review findings
(.isa/round6-findings.md). Round 6 changes the refuted-text design: the gate
no longer reads negation frames around the exact refuted text; only a figure
change or an in-place negation is a rewrite. Each test names its finding id."""

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


LONG = 'Acme cut 300 jobs at its Ohio plant in 2021 after the loss of its two largest government contracts [3].'


class TestRefutedTextDesign(unittest.TestCase):

    def test_R6_3_negation_of_an_earlier_predicate_does_not_hide_repeat(self):
        claim = 'Vaccines cause autism in children.'
        for rep in ('A study that received no industry support found that vaccines cause autism in children.',
                    'A trial with no missing data showed that vaccines cause autism in children.'):
            self.assertIsNotNone(gate_hit(claim, rep), rep)

    def test_R6_F3_rhetorical_negative_questions_repeat(self):
        claim = 'Vaccines cause autism in children.'
        for rep in ("Isn't it true that vaccines cause autism in children?",
                    'Is it not the case that vaccines cause autism in children?'):
            self.assertIsNotNone(gate_hit(claim, rep), rep)

    def test_R6_1_R6_2_frames_are_a_documented_rule_not_a_guess(self):
        # nexus: every frame fails the same way (no closed word list to miss)
        claim = 'MMR vaccination causes autism in children.'
        for rep in ('There is no evidence to suggest that MMR vaccination causes autism in children.',
                    'There is no evidence that the MMR vaccination causes autism in children.',
                    'No study has found that MMR vaccination causes autism in children.'):
            self.assertIsNotNone(gate_hit(claim, rep), rep)
        msg = gate_hit(claim, 'No study has found that MMR vaccination causes autism in children.')
        self.assertIn('even negated', msg)

    def test_R6_F1_negated_aside_inside_the_claim_does_not_hide_it(self):
        for aside in (', not in 2019,', ' (not its smaller ones)'):
            rep = LONG.replace(' in 2021', ' in 2021' + aside) if 'not in' in aside else \
                LONG.replace('contracts', 'contracts' + aside)
            self.assertIsNotNone(gate_hit(LONG, rep), aside)

    def test_R6_F2_portuguese_no_contraction_in_the_near_path(self):
        claim = ('O desemprego no Porto subiu para 12% em 2023 segundo os dados trimestrais '
                 'do instituto nacional de estatística [2].')
        for rep in (claim.replace('no Porto', 'na cidade do Porto'),
                    claim.replace('O desemprego', 'O desemprego no setor privado')):
            self.assertIsNotNone(gate_hit(claim, rep), rep)

    def test_R6_in_place_negation_is_the_correction(self):
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(LONG, LONG.replace('Acme cut', 'Acme did not cut')))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(LONG, LONG.replace('Acme cut', 'Acme never cut')))
        neg = LONG.replace('Acme cut', 'Acme did not cut')
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(neg, LONG))              # refuted negative claim, "not" removed
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(LONG, LONG.replace('300', '30')))  # figure corrected

    def test_R6_in_place_check_requires_only_negation_words(self):
        # nexus: strict gate — the in-place negation reading was removed
        self.assertFalse(hasattr(cl, '_negated_in_place'))
        self.assertIsNotNone(gate_hit(LONG, LONG.replace('Acme cut', 'Acme did not cut').replace('300', '30')))


class TestSections(unittest.TestCase):

    def test_R6_4_descriptive_heading_is_not_recommendations(self):
        t = "TikTok's recommendation algorithm drives 90% of watch time on the platform [2]."
        self.assertEqual(ec.classify_claim(t, '4_recommendation_algorithms_and_engagement'), 'factual')
        t2 = 'Personalised product feeds might lift basket size by 35% [3].'
        self.assertEqual(ec.classify_claim(t2, '4_recommendation_algorithms_and_engagement'), 'factual')
        self.assertEqual(ec.classify_claim('Regulators should raise the cap to 15% by 2027 [3].',
                                           '9_recommendations_for_policyma'), 'recommendation')
        self.assertEqual(ec.classify_claim('Regulators should raise the cap to 15% by 2027 [3].',
                                           'recommendation'), 'recommendation')


class TestNumbers(unittest.TestCase):

    def test_R6_5_times_per_any_unit_is_a_count(self):
        for text, want in (('100 times per second', {'100'}), ('4 times per shift', {'4'}),
                           ('2 times per cycle', {'2'}), ('3 times each session', {'3'}),
                           ('5 times a second', {'5'}), ("3 times a typical rival's revenue", {'3x'}),
                           ('3 times an average household', {'3x'})):
            self.assertEqual(extract_numbers(text), want, text)
        st = compute_support_score('The accelerometer samples motion 100 times per second [3].',
                                   ['The device accelerometer samples motion at 100 readings per second.'])[0]
        self.assertEqual(st, 'supported')


class TestDocs(unittest.TestCase):

    def test_R6_docs_state_the_correction_rule(self):
        with open(os.path.join(ROOT, 'reference', 'adversarial-verification.md'), encoding='utf-8') as f:
            doc = f.read()
        # nexus: strict gate — no in-place negation rule any more
        self.assertIn('rewrite **without restating it**', doc)
        self.assertNotIn('negate it in place', doc)
        self.assertNotIn('correction frame', doc)


if __name__ == '__main__':
    unittest.main()
