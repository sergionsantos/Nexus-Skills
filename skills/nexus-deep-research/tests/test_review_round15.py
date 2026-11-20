#!/usr/bin/env python3
"""Regression tests for the round-15 (final) independent review findings
(.isa/round15-findings.md)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
SCRIPTS = os.path.join(ROOT, 'scripts')
sys.path.insert(0, SCRIPTS)

import claim_ledger as cl  # noqa: E402
import extract_claims as ec  # noqa: E402
import verify_claim_support as vcs  # noqa: E402
import verify_quotes as vq  # noqa: E402
from validate_report import ReportValidator  # noqa: E402


def status(claim, *quotes):
    return vcs.compute_support_score(claim, list(quotes))[0]


class TestLayer1(unittest.TestCase):

    def test_F15_C1_antonym_flip_without_negation(self):
        self.assertNotEqual(status('Sales rose 12% in 2023 [1].', 'Sales fell 12% in 2023.'), 'supported')
        self.assertNotEqual(status("Acme's revenue grew 12% in 2023.", "Acme's revenue declined 12% in 2023."),
                            'supported')
        self.assertNotEqual(status('O desemprego aumentou para 12% em 2023.', 'O desemprego diminuiu para 12% em 2023.'),
                            'supported')
        # controls
        self.assertEqual(status('Sales rose 12% in 2023 [1].', 'Sales rose 12% in 2023.'), 'supported')
        self.assertNotEqual(status('Sales did not fall in 2023.', 'Sales rose in 2023.'), 'contradicted')

    def test_F15_C4_D5_entity_substitution(self):
        self.assertNotEqual(status("Germany's GDP grew 2% in 2023 [1].", "France's GDP grew 2% in 2023."), 'supported')
        self.assertNotEqual(status('Sales at Siemens rose 21% in 2023 [1].', 'Sales at Bosch rose 21% in 2023.'),
                            'supported')
        self.assertNotEqual(status('As vendas na Áustria subiram 21% em 2023 [1].',
                                   'As vendas na Alemanha subiram 21% em 2023.'), 'supported')
        # controls: same entity, extra entity in the quote, sentence-initial common word
        self.assertEqual(status("Germany's GDP grew 2% in 2023 [1].", "Germany's GDP grew 2% in 2023."), 'supported')
        self.assertEqual(status('Sales in Germany rose 21% in 2023 [1].',
                                'According to Eurostat, sales in Germany rose 21% in 2023.'), 'supported')

    def test_F15_C5_currency_scale_period(self):
        self.assertNotEqual(status('Revenue reached $5 bn in 2023 [1].', 'Revenue reached $5 mn in 2023.'), 'supported')
        self.assertNotEqual(status('Revenue reached $5 billion in 2023 [1].', 'Revenue reached €5 billion in 2023.'),
                            'supported')
        self.assertNotEqual(status('Sales rose 12% in Q3 2023 [1].', 'Sales rose 12% in Q1 2023.'), 'supported')
        self.assertNotEqual(status('Sales rose 12% in March 2023 [1].', 'Sales rose 12% in June 2023.'), 'supported')
        self.assertEqual(vcs.extract_numbers('$5 bn'), vcs.extract_numbers('$5 billion'))
        # controls
        self.assertEqual(status('Revenue reached $5 bn in 2023 [1].', 'Revenue reached $5 billion in 2023.'),
                         'supported')
        self.assertEqual(status('Sales rose 12% in Q3 2023 [1].', 'Sales rose 12% in Q3 2023.'), 'supported')


class TestQuotes(unittest.TestCase):

    def test_F15_C3_quote_edge_inside_a_number(self):
        src = vq.normalize('only 2.5% of patients relapsed within a year. The company hired 12,000 people in 2023. '
                           'Revenue was $4.5bn.')
        for q in ('5% of patients relapsed within a year.', 'The company hired 12', 'Revenue was $4'):
            self.assertEqual(vq.match_quote_detail(q, src)[0], 'missing', q)
        self.assertEqual(vq.match_quote_detail('2.5% of patients relapsed within a year.', src)[0], 'verbatim')
        self.assertEqual(vq.match_quote_detail('The company hired 12,000 people', src)[0], 'verbatim')


class TestGate(unittest.TestCase):

    def gate_hit(self, claim, report):
        norm = cl.normalise_text(report)
        sents = [(s, set()) for s in cl.report_sentences(report)]
        return cl.refuted_in_report(claim, norm, sents)

    def test_F15_C6_escaped_percent_and_spaced_scale(self):
        self.assertIsNotNone(self.gate_hit('Sales rose 12% in 2023 at Acme.', 'Sales rose 12\\% in 2023 at Acme [1].'))
        self.assertIsNotNone(self.gate_hit('Revenue reached $5 billion in 2023.', 'Revenue reached $5 bn in 2023 [1].'))

    def test_F15_D1_did_not_plus_base_verb(self):
        # nexus: strict gate
        self.assertIsNotNone(self.gate_hit(
            'Germany banned new gas boilers in all buildings from January 2024 [1].',
            'Germany did not ban new gas boilers in all buildings from January 2024 [1].'))
        self.assertIsNotNone(self.gate_hit(
            'Heat pump prices in Germany fell 12% in 2023 for 1,500 households [1].',
            'Heat pump prices in Germany did not fall 12% in 2023 for 1,500 households [1].'))
        # control: a rewritten correction passes
        self.assertIsNone(self.gate_hit(
            'Germany banned new gas boilers in all buildings from January 2024 [1].',
            'The 2024 rules require 65% renewable heat in new installations [1].'))


BIB_OK = '\n'.join(f'[{i}] Org {i} (2023). "Title {i}". Site. https://example.org/{i}' for i in range(1, 13))


def validate(body, bib=BIB_OK):
    text = ('# R\n\n## Executive Summary\n\n' + ('Word ' * 220) + '[1].\n\n## Introduction\n\nIntro [2].\n\n'
            '## Main Analysis\n\n' + body + '\n\n## Synthesis\n\nS [3].\n\n## Limitations\n\nL.\n\n'
            '## Recommendations\n\nR.\n\n## Bibliography\n\n' + bib + '\n\n## Methodology Appendix\n\nM.\n')
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(text)
    try:
        v = ReportValidator(__import__('pathlib').Path(f.name))
        with open(os.devnull, 'w', encoding='utf-8') as dn:
            old = sys.stdout
            sys.stdout = dn
            try:
                ok = v.validate()
            finally:
                sys.stdout = old
        return ok, v.errors
    finally:
        os.unlink(f.name)


class TestValidateReport(unittest.TestCase):

    def test_F15_D2_grouped_citations_checked(self):
        for marker in ('[1, 13]', '[1; 13]', '[12-13]', '[^13]'):
            ok, errors = validate(f'Sales rose 21% in 2023 {marker}. Others [4][5][6][7][8][9][10][11][12].')
            self.assertFalse(ok, marker)
            self.assertTrue(any('13' in e for e in errors), (marker, errors))
        ok, errors = validate('Sales rose 21% in 2023 [1, 12]. Others [4][5][6][7][8][9][10][11].')
        self.assertTrue(ok, errors)

    def test_F15_D3_template_and_ellipsis_bibliography_entries(self):
        tmpl = ('[13] Author Name or Organization ([YEAR]). "Full Title of Article or Paper". '
                'Publication Name or Website. https://full-url.com (Retrieved: [CURRENT_DATE])')
        for entry in (tmpl, '[13] ...', '[13] tbd'):
            ok, errors = validate('Sales rose 21% in 2023 [13]. Others [4][5][6][7][8][9][10][11][12].',
                                  BIB_OK + '\n' + entry)
            self.assertFalse(ok, (entry, errors))


class TestTyping(unittest.TestCase):

    def test_F15_D4_uncited_figure_with_hedge_is_factual(self):
        self.assertEqual(ec.classify_claim('Heat pump sales in Spain fell 30% in 2023, and prices there might follow.',
                                           'finding_1'), 'factual')
        self.assertEqual(ec.classify_claim('Heat pump sales in Spain fell 30% in 2023, so Madrid should act.',
                                           'finding_1'), 'factual')
        # controls
        self.assertEqual(ec.classify_claim('Madrid should act quickly.', 'finding_1'), 'recommendation')
        self.assertEqual(ec.classify_claim('Cut tariffs by 30% by 2030; ministries should act.', 'recommendations'),
                         'recommendation')


class TestDocs(unittest.TestCase):

    def read(self, name):
        with open(os.path.join(ROOT, 'reference', name), encoding='utf-8') as f:
            return f.read()

    def test_F15_D7_quality_gates_matches_validate_report(self):
        doc = self.read('quality-gates.md')
        self.assertNotIn('200-400 words)', doc.split('validate_report')[1][:2000] if 'validate_report' in doc else doc)
        self.assertNotIn('500-10000', doc)
        self.assertIn('Content truncation', doc)

    def test_F15_D8_html_generation_paths(self):
        doc = self.read('html-generation.md')
        self.assertNotIn('~/.claude/skills/deep-research', doc)
        self.assertNotIn('outputs two parts', doc)


class TestCrashes(unittest.TestCase):

    def run_script(self, *args):
        return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding='utf-8', timeout=60)

    def test_F15_crash_bad_url_and_non_object_json(self):
        with tempfile.TemporaryDirectory() as d:
            self.run_script(os.path.join(SCRIPTS, 'citation_manager.py'), 'init-run', '--dir', d, '--query', 'q')
            r = self.run_script(os.path.join(SCRIPTS, 'citation_manager.py'), 'register-source', '--dir', d,
                                '--json', json.dumps({'raw_url': 'http://[::1/a', 'title': 't'}))
            self.assertNotIn('Traceback', r.stderr)
            self.assertNotEqual(r.returncode, 0)
            r = self.run_script(os.path.join(SCRIPTS, 'evidence_store.py'), 'add', '--dir', d, '--json', '[1,2]')
            self.assertNotIn('Traceback', r.stderr)
            self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
