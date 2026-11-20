#!/usr/bin/env python3
"""Regression tests for the round-2 independent review findings
(.isa/round2-findings.md). Each test names its finding id."""

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
import registry_check as rc  # noqa: E402
from verify_claim_support import compute_support_score  # noqa: E402
from verify_coverage import is_extract_tool  # noqa: E402
from verify_quotes import match_quote_detail, normalize  # noqa: E402


def run(script, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                          capture_output=True, text=True)


def write_jsonl(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')


# ---------------------------------------------------------------------------
# verify_claim_support
# ---------------------------------------------------------------------------

class TestNumericClaims(unittest.TestCase):

    def test_C1_changed_or_swapped_number_is_not_supported(self):
        cases = [
            ('Revenue rose from 10% to 12% at Acme Corp in 2023.',
             'Revenue rose from 10% to 15% at Acme Corp in 2023.'),
            ('Acme cut 300 jobs across 12 plants in Ohio.',
             'Acme cut 12 jobs across 300 plants in Ohio.'),
            ('The vaccine was 95% effective in 40000 trial participants.',
             'The vaccine was 52% effective in 40000 trial participants.'),
        ]
        for claim, quote in cases:
            status, _, notes = compute_support_score(claim, [quote])
            self.assertEqual(status, 'needs_review', (claim, notes))

    def test_C1_quote_sharing_one_number_is_a_surfaced_conflict(self):
        claim = 'Revenue rose from 10% to 12% at Acme Corp in 2023.'
        quotes = ['Revenue rose from 10% to 15% at Acme Corp in 2023.',
                  'Revenue at Acme Corp rose to 12% in 2023, from 10% a year earlier.']
        status, _, notes = compute_support_score(claim, quotes)
        self.assertEqual(status, 'supported', notes)
        self.assertIn('1 other quote(s) conflict', notes)

    def test_C1_all_numbers_matching_is_supported(self):
        status, _, _ = compute_support_score(
            'Acme cut 300 jobs across 12 plants in Ohio.',
            ['Acme cut 300 jobs across 12 plants in Ohio, the company said.'])
        self.assertEqual(status, 'supported')

    def test_C7_equivalent_number_forms_match(self):
        cases = [
            ('The new chip is 3x faster than its predecessor, Intel said.',
             'The new chip is 3 times faster than its predecessor, Intel said.'),
            ('Tesla raised $4 billion in new funding from investors.',
             'Tesla raised $4bn in new funding from investors.'),
            ('Unemployment fell to 4.0% in the United States.',
             'Unemployment fell to 4% in the United States.'),
            ('The fund manages 1.5 million accounts for Vanguard clients.',
             'The fund manages 1,500,000 accounts for Vanguard clients.'),
            ('Unemployment fell to 4 percent in the United States.',
             'Unemployment fell to 4% in the United States.'),
        ]
        for claim, quote in cases:
            status, _, notes = compute_support_score(claim, [quote])
            self.assertEqual(status, 'supported', (claim, notes))

    def test_C7_identifier_digits_are_not_figures(self):
        status, _, notes = compute_support_score(
            'COVID-19 vaccines reduce hospitalization among older adults.',
            ['SARS-CoV-2 vaccines reduce hospitalization among older adults.'])
        self.assertNotIn('number', notes)
        self.assertNotEqual(status, 'needs_review', notes)

    def test_C7_identifier_mismatch_still_counts_lexically(self):
        # GPT-4 vs GPT-5: the identifier is a token, so it lowers overlap
        s4, score4, _ = compute_support_score('GPT-4 scored highest on the bar exam.',
                                              ['GPT-4 scored highest on the bar exam.'])
        s5, score5, _ = compute_support_score('GPT-4 scored highest on the bar exam.',
                                              ['GPT-5 scored highest on the bar exam.'])
        self.assertEqual(s4, 'supported')
        self.assertLess(score5, score4)

    def test_D3_citation_markers_are_not_claim_numbers(self):
        for claim in ('Revenue grew strongly at Acme Corp last year [3].',
                      'Revenue grew strongly at Acme Corp last year [1][2].',
                      'Revenue grew strongly at Acme Corp last year [1, 4].',
                      'Revenue grew strongly at Acme Corp last year.[^7]'):
            status, _, notes = compute_support_score(
                claim, ['Revenue grew strongly at Acme Corp last year, filings show.'])
            self.assertEqual(status, 'supported', (claim, notes))

    def test_D3_number_in_lower_scoring_agreeing_quote_counts(self):
        claim = ('PEP 703 proposes a build configuration that lets CPython run Python code '
                 'without the global interpreter lock.')
        quotes = ['This proposal adds a build configuration that lets CPython run Python code '
                  'without the global interpreter lock.',
                  'PEP 703 makes the global interpreter lock optional in CPython builds.']
        status, _, notes = compute_support_score(claim, quotes)
        self.assertEqual(status, 'supported', notes)

    def test_D3_number_absent_from_all_evidence_still_needs_review(self):
        claim = ('PEP 703 proposes a build configuration that lets CPython run Python code '
                 'without the global interpreter lock.')
        quotes = ['This proposal adds a build configuration that lets CPython run Python code '
                  'without the global interpreter lock.']
        self.assertEqual(compute_support_score(claim, quotes)[0], 'needs_review')


class TestLayer1HonoursVerifierVotes(unittest.TestCase):
    """D4: a layer-1 flag that layer-4 verifiers resolved does not keep --strict red."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.d, 'evidence.jsonl'), [
            {'evidence_id': 'e1', 'source_id': 's1',
             'quote': 'The drug did not reduce mortality in the trial population.'},
            {'evidence_id': 'e2', 'source_id': 's1',
             'quote': 'The plant produced electricity for the regional grid.'},
        ])
        write_jsonl(os.path.join(self.d, 'claims.jsonl'), [
            {'claim_id': 'c' * 16, 'section_id': 'f1', 'claim_type': 'factual',
             'text': 'The drug reduced mortality in the trial population.',
             'evidence_ids': ['e1'], 'cited_source_ids': [], 'support_status': 'unverified'},
            {'claim_id': 'd' * 16, 'section_id': 'f1', 'claim_type': 'factual',
             'text': 'The plant produced 40 MW of electricity for the regional grid.',
             'evidence_ids': ['e2'], 'cited_source_ids': [], 'support_status': 'unverified'},
        ])

    def tearDown(self):
        shutil.rmtree(self.d)

    def vote(self, cid, vid, verdict):
        args = ['vote', '--dir', self.d, '--claim-id', cid, '--verifier-id', vid, '--verdict', verdict]
        if verdict == 'refuted':
            args += ['--failure-patterns', 'number-error']
        r = run('claim_ledger.py', *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unresolved_flags_fail_strict(self):
        r = run('verify_claim_support.py', 'verify', '--dir', self.d, '--strict')
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_resolved_flags_pass_strict(self):
        for cid in ('c' * 16, 'd' * 16):
            self.vote(cid, 'v1', 'supported')
            self.vote(cid, 'v2', 'supported')
        r = run('verify_claim_support.py', 'verify', '--dir', self.d, '--strict')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out['resolved_by_verifiers'], 2)
        # the deterministic statuses stay visible in claims.jsonl
        claims = [json.loads(line) for line in open(os.path.join(self.d, 'claims.jsonl'))]
        self.assertEqual({c['support_status'] for c in claims}, {'contradicted', 'needs_review'})

    def test_refuted_flag_is_handed_to_the_ledger_gate(self):
        # round 3 (E-2): once layer 4 has decided a flagged claim, --strict
        # no longer blocks on it; claim_ledger gate enforces the removal
        self.vote('d' * 16, 'v1', 'refuted')
        self.vote('d' * 16, 'v2', 'refuted')
        self.vote('c' * 16, 'v1', 'supported')
        self.vote('c' * 16, 'v2', 'supported')
        r = run('verify_claim_support.py', 'verify', '--dir', self.d, '--strict')
        self.assertEqual(r.returncode, 0, r.stdout)


# ---------------------------------------------------------------------------
# claim_ledger
# ---------------------------------------------------------------------------

def gate_hit(claim, report):
    rn = cl.normalise_text(report)
    sents = [(s, cl._shingles(cl.normalise_text(s).split())) for s in cl.report_sentences(report)]
    return cl.refuted_in_report(claim, rn, sents)


class TestLedger(unittest.TestCase):

    def test_D5_contradicted_without_votes_is_unverified(self):
        r = cl.resolve_claim([], 'contradicted', dict(cl.DEFAULTS))
        self.assertEqual(r['final_status'], 'unverified')

    def test_C4_parenthetical_claim_is_not_a_citation(self):
        hit = gate_hit('Acme Holdings went bankrupt in 2019',
                       'The firm later restructured its debt (Acme Holdings went bankrupt in 2019).')
        self.assertIsNotNone(hit)

    def test_C4_real_author_year_citations_still_stripped(self):
        for cite in ('(Smith, 2020)', '(Smith et al., 2020)', '(Smith & Jones 2019; Lee 2020)',
                     '(World Health Organization, 2021)', '(van der Berg et al. 2018a)'):
            self.assertEqual(cl.normalise_text(f'Sales grew {cite}.'), 'sales grew', cite)

    def test_C5_corrected_rewrites_are_not_refuted_text(self):
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(
            'The company increased its annual sales in Europe by 20 percent in 2023',
            'The company increased its annual sales in Europe by 20 percent in 2022.'))
        # nexus: strict gate — a correction that restates the refuted claim fails
        self.assertIsNotNone(gate_hit(
            'The regulator approved the merger between the two largest airlines in the country last year',
            'The regulator never approved the merger between the two largest airlines in the country last year.'))

    def test_C5_near_duplicate_with_same_numbers_still_caught(self):
        self.assertIsNotNone(gate_hit(
            'The company increased its annual sales in Europe by 20 percent in 2023',
            'As noted, the company increased its annual sales in Europe by 20 percent in 2023, analysts said.'))


class TestTableAppendix(unittest.TestCase):
    """D6: pasting `table` as the appendix must not trip the refuted-text gate."""

    def test_table_appendix_passes_gate(self):
        d = tempfile.mkdtemp()
        try:
            write_jsonl(os.path.join(d, 'claims.jsonl'), [
                {'claim_id': 'a' * 16, 'section_id': 'f1', 'claim_type': 'factual',
                 'text': 'The free-threaded build became the default build in Python 3.13.',
                 'support_status': 'supported'},
                {'claim_id': 'b' * 16, 'section_id': 'f1', 'claim_type': 'factual',
                 'text': 'The steering council accepted the proposal.',
                 'support_status': 'supported'},
            ])
            for vid in ('v1', 'v2'):
                run('claim_ledger.py', 'vote', '--dir', d, '--claim-id', 'a' * 16, '--verifier-id', vid,
                    '--verdict', 'refuted', '--failure-patterns', 'stale')
                run('claim_ledger.py', 'vote', '--dir', d, '--claim-id', 'b' * 16, '--verifier-id', vid,
                    '--verdict', 'supported')
            table = run('claim_ledger.py', 'table', '--dir', d).stdout
            self.assertIn('a' * 16, table)
            self.assertNotIn('default build', table)
            report = os.path.join(d, 'report.md')
            with open(report, 'w') as f:
                f.write('# R\n\nThe steering council accepted the proposal.\n\n## Claim ledger\n\n' + table)
            r = run('claim_ledger.py', 'gate', '--dir', d, '--report', report)
            self.assertEqual(r.returncode, 0, r.stdout)
        finally:
            shutil.rmtree(d)


# ---------------------------------------------------------------------------
# verify_quotes
# ---------------------------------------------------------------------------

LONG = ('In the first quarter revenue grew 5 percent to a record high while operating costs rose 12 percent '
        'as the company expanded its logistics network across the northern region and hired many additional '
        'warehouse staff to meet seasonal demand from retail partners nationwide while management kept '
        'guidance unchanged for the remainder of the fiscal year citing stable input prices and a strong '
        'order book that analysts at several brokerages described as the healthiest in more than a decade '
        'of public reporting by the group and its predecessor companies according to filings reviewed by '
        'the newspaper and interviews with three former executives who asked not to be named because the '
        'discussions were private and the board had yet to approve the final plan for the coming season')


class TestQuotes(unittest.TestCase):

    def test_C2_number_swapped_for_one_elsewhere_in_passage(self):
        q = LONG.replace('costs rose 12 percent', 'costs rose 5 percent')
        self.assertEqual(match_quote_detail(q, normalize(LONG))[0], 'missing')

    def test_C3_negation_moved_between_clauses(self):
        src = normalize(LONG.replace('revenue grew', 'revenue did not grow'))
        q = LONG.replace('analysts at several brokerages described',
                         'analysts at several brokerages did not describe')
        self.assertEqual(match_quote_detail(q, src)[0], 'missing')

    def test_near_still_tolerates_small_non_numeric_edit(self):
        q = LONG.replace('many additional warehouse', 'many extra warehouse')
        self.assertEqual(match_quote_detail(q, normalize(LONG))[0], 'near')

    def test_C8_elision_over_abbreviation(self):
        src = normalize('The lead author, Dr. Smith of Harvard, said the results were robust across all cohorts.')
        q = 'The lead author ... said the results were robust across all cohorts.'
        self.assertEqual(match_quote_detail(q, src)[0], 'near')

    def test_C8_real_sentence_break_still_rejected(self):
        src = normalize('Smoking is harmful. Exercise reduces the risk of heart disease in adults.')
        q = 'Smoking ... reduces the risk of heart disease in adults.'
        self.assertEqual(match_quote_detail(q, src)[2], 'elision_crosses_sentence')

    def test_C9_cjk_substring(self):
        src = normalize('研究表明该药物没有降低死亡率。')
        self.assertEqual(match_quote_detail('该药物没有降低死亡率', src)[0], 'verbatim')
        src2 = normalize('研究表明该药物降低死亡率。')
        self.assertEqual(match_quote_detail('该药物降低死亡率', src2)[0], 'verbatim')
        self.assertEqual(match_quote_detail('该药物没有降低死亡率', src2)[0], 'missing')
        # Latin word boundaries still apply
        self.assertEqual(match_quote_detail('rain', normalize('The training data')), ('missing', 0.0, 'segment_not_found'))


# ---------------------------------------------------------------------------
# verify_coverage / registry_check / extract_claims / md_to_html / citation_manager
# ---------------------------------------------------------------------------

class TestMisc(unittest.TestCase):

    def test_C6_browser_actions_are_not_raw_text(self):
        for tool in ('browser_screenshot', 'browser_click', 'browser_vision', 'browser_type',
                     'mcp__browser_navigate', 'mcp__playwright__browser_take_screenshot'):
            self.assertFalse(is_extract_tool(tool), tool)
        for tool in ('browser', 'browser_snapshot', 'BrowserSnapshot', 'mcp__playwright__browser_snapshot',
                     'browser_get_text'):
            self.assertTrue(is_extract_tool(tool), tool)

    def test_C10_doi_bot_wall_is_unknown_not_absent(self):
        class F(rc.Fetcher):
            def __init__(self, code):
                super().__init__(pause=0)
                self.code = code

            def get(self, url, accept='application/json'):
                return (self.code, '') if 'doi.org' in url and 'crossref' not in url else (404, '')
        for code in (401, 403):
            self.assertIsNone(rc.lookup_doi('10.5281/zenodo.1', F(code))['found'], code)

    def test_C11_invented_subtitle_is_not_full_match(self):
        sim = rc.title_similarity('Attention is all you need: fabricated subtitle about cats',
                                  'Attention is all you need')
        self.assertLess(sim, 0.85)
        self.assertEqual(rc.title_similarity('Attention is all you need',
                                             'Attention is all you need: a subtitle'), 1.0)

    def test_C11_crossref_subtitle_is_part_of_registry_title(self):
        class F(rc.Fetcher):
            def get(self, url, accept='application/json'):
                if 'api.crossref.org' in url:
                    return 200, json.dumps({'message': {'title': ['Deep learning for retinopathy'],
                                                        'subtitle': ['a validation study'],
                                                        'issued': {'date-parts': [[2016]]}}})
                return 503, ''
        meta = rc.lookup_doi('10.1/x', F(pause=0))
        self.assertEqual(rc.title_similarity('Deep learning for retinopathy: a validation study',
                                             meta['title']), 1.0)

    def test_D11_extract_links_citations_and_matches_schema(self):
        d = tempfile.mkdtemp()
        try:
            write_jsonl(os.path.join(d, 'sources.jsonl'), [
                {'source_id': '1' * 16}, {'source_id': '1' * 16}, {'source_id': '2' * 16}])
            report = os.path.join(d, 'report.md')
            with open(report, 'w') as f:
                f.write('# Report\n\n## Findings\n\nThe model improved accuracy on the benchmark [2]. '
                        'Another study found a smaller effect in older adults [1, 2].\n')
            r = run('extract_claims.py', 'extract', '--dir', d, '--report', report)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            rows = [json.loads(line) for line in open(os.path.join(d, 'claims.jsonl'))]
            with open(os.path.join(ROOT, 'schemas', 'claim.schema.json')) as f:
                allowed = set(json.load(f)['properties'])
            for row in rows:
                self.assertLessEqual(set(row), allowed, row)
            linked = {row['text'].split()[0]: row['cited_source_ids'] for row in rows}
            self.assertEqual(linked['The'], ['2' * 16])
            self.assertEqual(linked['Another'], ['1' * 16, '2' * 16])
            nums = json.loads(run('citation_manager.py', 'assign-display-numbers', '--dir', d).stdout)
            self.assertEqual(nums, {'1' * 16: 1, '2' * 16: 2})
        finally:
            shutil.rmtree(d)

    def test_D12_md_to_html_help(self):
        r = run('md_to_html.py', '--help')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('usage', r.stdout.lower())


if __name__ == '__main__':
    unittest.main()
