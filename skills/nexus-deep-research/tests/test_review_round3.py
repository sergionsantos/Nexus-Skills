#!/usr/bin/env python3
"""Regression tests for the round-3 independent review findings
(.isa/round3-findings.md). Each test names its finding id."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
SCRIPTS = os.path.join(ROOT, 'scripts')
sys.path.insert(0, SCRIPTS)

import claim_ledger as cl  # noqa: E402
from extract_claims import classify_claim  # noqa: E402
from verify_claim_support import compute_support_score, extract_numbers  # noqa: E402
from verify_coverage import is_extract_tool  # noqa: E402
from verify_quotes import match_quote_detail, normalize  # noqa: E402


def run(script, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                          capture_output=True, text=True)


def write_jsonl(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')


def mq(quote, source):
    return match_quote_detail(quote, normalize(source))


def gate_hit(claim, report):
    rn = cl.normalise_text(report)
    sents = [(s, cl._shingles(cl.normalise_text(s).split())) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


# ---------------------------------------------------------------------------
# verify_quotes
# ---------------------------------------------------------------------------

class TestQuotes(unittest.TestCase):

    def test_R3_01_cjk_quote_cannot_drop_adjacent_negation_or_numeral(self):
        for quote, src in [
            ('会增加心血管风险', '研究发现，这种药物不会增加心血管风险。'),
            ('副作用は報告され', '臨床試験では重い副作用は報告されなかった。'),
            ('五十万人', '该国共有一百五十万人感染。'),
        ]:
            self.assertEqual(mq(quote, src)[0], 'missing', quote)

    def test_R3_01_cjk_mid_run_substring_still_verbatim(self):
        self.assertEqual(mq('增加心血管风险', '研究发现，这种药物会增加心血管风险。')[0], 'verbatim')
        self.assertEqual(mq('五十万人', '该国共有五十万人感染。')[0], 'verbatim')

    def test_R3_08_elision_cannot_cross_sentence_ending_in_symbol(self):
        r = mq('Smoking raised the cancer risk ... reduces cancer risk in adults',
               'Smoking raised the cancer risk by 20%. Regular exercise reduces cancer risk in adults.')
        self.assertEqual(r[0], 'missing', r)
        r = mq('Smoking raised the cancer risk ... reduces cancer risk in adults',
               'Smoking raised the cancer risk (in 2019). Regular exercise reduces cancer risk in adults.')
        self.assertEqual(r[0], 'missing', r)

    def test_R3_09_ambiguous_abbreviation_does_not_hide_sentence_end(self):
        r = mq('Patients reported nausea ... reduces mortality in adults',
               'Patients reported nausea, headaches, etc. The placebo group showed that exercise '
               'reduces mortality in adults.')
        self.assertEqual(r[0], 'missing', r)

    def test_R3_09_title_abbreviation_still_not_a_break(self):
        r = mq('The trial led by ... found lower mortality in adults',
               'The trial led by Dr. Smith found lower mortality in adults.')
        self.assertEqual(r[0], 'near', r)

    def test_R3_12_antonym_edit_is_not_near(self):
        src = ('In the randomised trial of 4,200 adults followed for five years across eleven hospitals '
               'in three countries, the researchers reported that the daily dose of the compound '
               'increased the rate of serious cardiac events compared with placebo, and the independent '
               'safety board recommended that enrolment continue under closer monitoring of every '
               'participant in the treatment arm.')
        r = mq(src.replace('increased', 'decreased'), src)
        self.assertEqual(r[0], 'missing', r)
        self.assertEqual(r[2], 'antonym_mismatch')
        # a harmless one-word edit is still near
        self.assertEqual(mq(src.replace('closer', 'careful'), src)[0], 'near')


# ---------------------------------------------------------------------------
# claim_ledger refuted-text gate
# ---------------------------------------------------------------------------

CLAIM_B = ('Acme Corporation reported that its cloud revenue grew by 1,500 percent between the '
           'first and fourth quarters of fiscal 2023 after the merger with Beta Systems.')


class TestRefutedText(unittest.TestCase):

    def test_R3_02_reformatted_refuted_figure_still_caught(self):
        for old, new in [('1,500 percent', '1500 percent'), ('1,500 percent', '1.5 thousand percent'),
                         ('1,500 percent', '1,500%')]:
            self.assertIsNotNone(gate_hit(CLAIM_B, 'Intro. ' + CLAIM_B.replace(old, new) + ' Outro.'), new)
        claim = CLAIM_B.replace('1,500 percent', '12.0%')
        self.assertIsNotNone(gate_hit(claim, 'Intro. ' + CLAIM_B.replace('1,500 percent', '12%') + ' Outro.'))

    def test_R3_02_corrected_figure_is_not_refuted_text(self):
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(CLAIM_B, 'Intro. ' + CLAIM_B.replace('1,500', '150') + ' Outro.'))

    def test_R3_03_unrelated_negation_elsewhere_does_not_hide_refuted_text(self):
        claim = ('The regional health agency confirmed that the vaccine does not cause infertility '
                 'in women of childbearing age after the large national cohort study.')
        report = ('Background text. The regional health agency has confirmed that the vaccine does not '
                  'cause infertility in women of childbearing age after the large national cohort '
                  'study; no recall followed. More text.')
        self.assertIsNotNone(gate_hit(claim, report))

    def test_R3_03_negation_before_the_first_claim_word_is_the_correction(self):
        # nexus: round 6 design (R6-1/R6-3): a negation PREFIXED to the exact
        # refuted text no longer counts as a correction; negate in place.
        claim = ('Vaccines cause infertility in women of childbearing age according to the large '
                 'national cohort study of the regional health agency.')
        report = ('No vaccines cause infertility in women of childbearing age according to the large '
                  'national cohort study of the regional health agency.')
        self.assertIsNotNone(gate_hit(claim, report))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(claim, report.replace('No vaccines cause', 'Vaccines do not cause')))

    def test_R3_03_negated_rewrite_is_still_the_correction(self):
        claim = ('The regional health agency confirmed that the vaccine causes infertility '
                 'in women of childbearing age after the large national cohort study.')
        report = ('The regional health agency has confirmed that the vaccine never causes infertility '
                  'in women of childbearing age after the large national cohort study.')
        self.assertIsNone(gate_hit(claim, report))


# ---------------------------------------------------------------------------
# verify_claim_support numbers
# ---------------------------------------------------------------------------

class TestNumbers(unittest.TestCase):

    def test_R3_04_decimal_comma_and_dot_thousands(self):
        self.assertEqual(extract_numbers('subiu para 4,5% em março'), extract_numbers('rose to 4.5%'))
        self.assertEqual(extract_numbers('1.500.000 pessoas'), extract_numbers('1,500,000 people'))
        self.assertEqual(extract_numbers('1,5 milhões'), extract_numbers('1.5 million'))
        status, _, notes = compute_support_score(
            'A inflação em Portugal subiu para 4,5% em março de 2024.',
            ['A inflação em Portugal subiu para 3,2% em março de 2024.'])
        self.assertEqual(status, 'needs_review', notes)

    def test_R3_05_kind_is_part_of_the_value(self):
        status, _, notes = compute_support_score(
            "Acme's cloud revenue grew 3x in fiscal 2023.", ["Acme's cloud revenue grew 3% in fiscal 2023."])
        self.assertEqual(status, 'needs_review', notes)
        self.assertEqual(extract_numbers('5 percent'), extract_numbers('5%'))
        self.assertEqual(extract_numbers('3 times'), extract_numbers('3x'))
        self.assertNotEqual(extract_numbers('3x'), extract_numbers('3'))

    def test_R3_06_figures_from_two_quotes_each_with_another_number(self):
        claim = ('Acme Corporation revenue rose 10% in 2023 while Acme Corporation operating margin '
                 'reached 12% in 2023.')
        quotes = ['Acme Corporation revenue rose 10% in 2023 to $5 billion, while operating margin improved.',
                  'Acme Corporation operating margin reached 12% in 2023, up from 9% while revenue rose.']
        status, _, notes = compute_support_score(claim, quotes)
        self.assertEqual(status, 'supported', notes)

    def test_R3_06_every_quote_disagreeing_is_still_flagged(self):
        claim = 'Revenue rose from 10% to 12% at Acme Corp in 2023.'
        quotes = ['Revenue rose from 10% to 15% at Acme Corp in 2023.',
                  'Revenue rose from 9% to 12% at Acme Corp in 2023.']
        self.assertEqual(compute_support_score(claim, quotes)[0], 'needs_review')

    def test_R3_07_percentage_not_backed_by_a_count(self):
        claim = 'Acme Corporation revenue rose 12% to $4 billion in 2023.'
        quotes = ['Acme Corporation revenue rose to $4 billion in 2023.',
                  'Acme Corporation revenue in 2023 came from 12 regional offices.']
        status, _, notes = compute_support_score(claim, quotes)
        self.assertEqual(status, 'needs_review', notes)


# ---------------------------------------------------------------------------
# verify_claim_support --strict and layer 4
# ---------------------------------------------------------------------------

class TestStrictLayer4(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.d, 'evidence.jsonl'), [
            {'evidence_id': 'e1', 'source_id': 's1',
             'quote': 'Acme cut 12 jobs across 300 plants in Ohio.'}])
        write_jsonl(os.path.join(self.d, 'claims.jsonl'), [
            {'claim_id': 'a' * 16, 'section_id': 'f1', 'claim_type': 'factual',
             'text': 'Acme cut 300 jobs across 12 plants in Ohio.',
             'evidence_ids': ['e1'], 'cited_source_ids': [], 'support_status': 'unverified'}])

    def tearDown(self):
        shutil.rmtree(self.d)

    def vote(self, vid, verdict):
        args = ['vote', '--dir', self.d, '--claim-id', 'a' * 16, '--verifier-id', vid, '--verdict', verdict]
        if verdict == 'refuted':
            args += ['--failure-patterns', 'number-error']
        r = run('claim_ledger.py', *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def strict(self, *extra):
        return run('verify_claim_support.py', 'verify', '--dir', self.d, '--strict', *extra)

    def test_E2_refuted_flag_is_handed_to_the_ledger_gate(self):
        self.vote('v1', 'refuted')
        self.vote('v2', 'refuted')
        r = self.strict()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_E2_unverified_after_full_verification_is_handed_to_the_ledger_gate(self):
        for v in ('v1', 'v2', 'v3'):
            self.vote(v, 'unverifiable')
        self.assertEqual(self.strict().returncode, 0)

    def test_E2_unfinished_verification_still_fails(self):
        self.assertEqual(self.strict().returncode, 1)
        self.vote('v1', 'unverifiable')
        self.assertEqual(self.strict().returncode, 1)

    def test_R3_10_thresholds_are_validated(self):
        self.vote('v1', 'refuted')
        r = self.strict('--support-threshold', '0')
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('thresholds must be >= 1', r.stdout + r.stderr)


# ---------------------------------------------------------------------------
# extract_claims
# ---------------------------------------------------------------------------

class TestExtract(unittest.TestCase):

    def test_E1_hedging_words_do_not_hide_cited_figures(self):
        for text in ['The 2021 trial suggests a 40% mortality reduction in adults [3].',
                     'Analysts might have overstated the 12% growth [4].',
                     'Early benchmarks suggest a 25% slowdown on ARM servers [2].']:
            self.assertEqual(classify_claim(text, 'finding_1'), 'factual', text)
        self.assertEqual(classify_claim('Regulators considered the drug unsafe in 2019 [2].', 'finding_1'),
                         'factual')
        self.assertEqual(classify_claim('Buyers should wait for the second generation.', 'recommendations'),
                         'recommendation')
        self.assertEqual(classify_claim('Consider a pilot before a full migration.', 'recommendations'),
                         'recommendation')
        self.assertEqual(classify_claim('Overall, the evidence suggests the market is consolidating.',
                                        'synthesis'), 'synthesis')
        self.assertEqual(classify_claim('Prices might eventually fall once supply recovers.', 'finding_1'),
                         'speculation')

    def setUp(self):
        self.d = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.d, 'sources.jsonl'),
                    [{'source_id': f's{i}', 'url': f'https://e.com/{i}', 'title': f'T{i}'} for i in (1, 2, 3)])

    def tearDown(self):
        shutil.rmtree(self.d)

    def extract(self, report):
        path = os.path.join(self.d, 'report.md')
        with open(path, 'w') as f:
            f.write(report)
        r = run('extract_claims.py', 'extract', '--dir', self.d, '--report', path)
        self.assertEqual(r.returncode, 0, r.stderr)
        claims = [json.loads(line) for line in open(os.path.join(self.d, 'claims.jsonl'))]
        return json.loads(r.stdout), {c['text'].split()[0]: c for c in claims}

    def test_R3_11_ranges_semicolons_and_footnotes_link(self):
        out, claims = self.extract(
            '# R\n\n## Finding 1: X\n\nRangeclaim revenue rose 10% in the first half [2-3].\n'
            'Semicolonclaim revenue rose 10% in the first half [1; 3].\n'
            'Footnoteclaim revenue rose 10% in the first half [^2].\n'
            'Unlinkedclaim revenue rose 10% in the first half [7].\n')
        self.assertEqual(claims['Rangeclaim']['cited_source_ids'], ['s2', 's3'])
        self.assertEqual(claims['Semicolonclaim']['cited_source_ids'], ['s1', 's3'])
        self.assertEqual(claims['Footnoteclaim']['cited_source_ids'], ['s2'])
        self.assertEqual(out['unlinked_citation_numbers'], [7])

    def test_E3_reference_and_meta_prose_is_not_extracted(self):
        _, claims = self.extract(
            '# R\n\n## Introduction\n\nThisscope review covers the status of the market as seen by buyers.\n'
            'Citedintro revenue in the sector rose 10% last year [1].\n\n'
            '## Finding 1: X\n\nUncitedfinding revenue in the sector rose sharply last year overall.\n\n'
            '## Limitations\n\nFewvendors published comparable figures for this review period.\n\n'
            '## Bibliography\n\nBibentry Smith, J. (2023). A long title of a paper. Journal [1].\n\n'
            '## Methodology Appendix\n\nMethodsentence searches ran on three engines over two days.\n')
        self.assertNotIn('Thisscope', claims)
        self.assertNotIn('Fewvendors', claims)
        self.assertNotIn('Bibentry', claims)
        self.assertNotIn('Methodsentence', claims)
        self.assertIn('Citedintro', claims)
        self.assertEqual(claims['Uncitedfinding']['claim_type'], 'factual')


# ---------------------------------------------------------------------------
# verify_coverage / source_evaluator
# ---------------------------------------------------------------------------

class TestMisc(unittest.TestCase):

    def test_R3_13_browser_input_actions_and_glued_names(self):
        for tool in ('browser_type_text', 'browser_fill_text', 'browser_set_content', 'browser_press_key'):
            self.assertFalse(is_extract_tool(tool), tool)
        for tool in ('BrowserGetPageContent', 'browser_get_text', 'WebExtract', 'BrowserSnapshot'):
            self.assertTrue(is_extract_tool(tool), tool)
        self.assertFalse(is_extract_tool('WebFetch'))
        self.assertFalse(is_extract_tool('BrowserTakeScreenshot'))

    def test_E4_source_evaluator_has_a_cli(self):
        r = run('source_evaluator.py', '--help')
        self.assertEqual(r.returncode, 0)
        self.assertIn('usage', r.stdout.lower())
        self.assertNotIn('Quantum', r.stdout)
        r = run('source_evaluator.py', 'evaluate', '--url', 'https://www.nature.com/articles/x',
                '--title', 'A study', '--date', '2025-01-01')
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertIn('overall_score', out)
        self.assertIn('recommendation', out)


if __name__ == '__main__':
    unittest.main()
