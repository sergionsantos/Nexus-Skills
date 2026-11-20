#!/usr/bin/env python3
"""Regression tests for the round-16 independent re-review findings
(.isa/round16-findings.md)."""

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
sys.path.insert(0, HERE)

import verify_claim_support as vcs  # noqa: E402
import verify_quotes as vq  # noqa: E402
from test_review_round15 import BIB_OK  # noqa: E402


def status(claim, *quotes):
    return vcs.compute_support_score(claim, list(quotes))[0]


class TestDirection(unittest.TestCase):

    def test_F16_C1_D2_direction_vocabulary(self):
        cases = [
            ('Sales were up 12% in 2023 [1].', 'Sales were down 12% in 2023.'),
            ('As vendas registaram uma subida de 12% em 2023 [1].', 'As vendas registaram uma queda de 12% em 2023.'),
            ('O desemprego registou um aumento de 12% em 2023 [1].', 'O desemprego registou uma descida de 12% em 2023.'),
            ('As vendas tinham aumentado 12% em 2023 [1].', 'As vendas tinham diminuído 12% em 2023.'),
            ('Os preços baixaram 12% em 2023 [1].', 'Os preços subiram 12% em 2023.'),
        ]
        for claim, quote in cases:
            self.assertNotEqual(status(claim, quote), 'supported', claim)
        # controls: "up to" is not a direction; same direction agrees
        self.assertNotEqual(status(
            'In Q3 2023, Vaillant reported heat pump revenue of €5 bn, down 8% from a year earlier [13].',
            'In Q3 2023, Vaillant reported heat pump revenue of €5 bn, up 8% from a year earlier.'), 'supported')
        self.assertEqual(status('Subsidies cover up to 70% of costs in 2024 [1].',
                                'Subsidies cover up to 70% of costs in 2024.'), 'supported')
        self.assertNotEqual(status('Subsidies cover up to 70% of installation costs in 2024 [1].',
                                   'Subsidies cover 70% of installation costs in 2024 as prices went down.'),
                            'contradicted')
        self.assertEqual(status('Sales were up 12% in 2023 [1].', 'Sales were up 12% in 2023.'), 'supported')

    def test_F16_C2_D1_other_direction_in_another_clause(self):
        self.assertNotEqual(status('Sales rose 12% in 2023 [1].', 'Sales fell 12% in 2023, while costs rose.'),
                            'supported')
        self.assertNotEqual(status('Heat pump orders fell 30% in 2023 [1].',
                                   'Heat pump orders rose 30% in 2023, while gas boiler orders fell 40%.'),
                            'supported')
        self.assertNotEqual(status('As encomendas caíram 30% em 2023 [1].',
                                   'As encomendas subiram 30% em 2023, enquanto as de caldeiras caíram 40%.'),
                            'supported')
        # control: the matching clause agrees, the other clause has the other direction
        self.assertEqual(status('Sales rose 12% in 2023 [1].', 'Sales rose 12% in 2023, while costs fell.'),
                         'supported')

    def test_F16_C3_D3_spelled_quarters(self):
        self.assertNotEqual(status('Sales rose 12% in the third quarter of 2023 [1].',
                                   'Sales rose 12% in the first quarter of 2023.'), 'supported')
        self.assertNotEqual(status('Sales rose 12% in the first half of 2023 [1].',
                                   'Sales rose 12% in the second half of 2023.'), 'supported')
        self.assertNotEqual(status('As vendas subiram 12% no terceiro trimestre de 2023 [1].',
                                   'As vendas subiram 12% no primeiro trimestre de 2023.'), 'supported')
        self.assertEqual(status('Sales rose 12% in the third quarter of 2023 [1].',
                                'Sales rose 12% in Q3 2023.'), 'supported')


class TestOther(unittest.TestCase):

    def test_F16_C4_no_in_text_citations(self):
        import pathlib
        text = ('# R\n\n## Executive Summary\n\n' + ('Word ' * 220) + '\n\n## Introduction\n\nIntro.\n\n'
                '## Main Analysis\n\nSales rose 21% in 2023.\n\n## Synthesis\n\nS.\n\n## Limitations\n\nL.\n\n'
                '## Recommendations\n\nR.\n\n## Bibliography\n\n' + BIB_OK + '\n\n## Methodology Appendix\n\nM.\n')
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d, 'r.md')
            p.write_text(text, encoding='utf-8')
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'validate_report.py'), '--report', str(p)],
                               capture_output=True, text=True, timeout=60)
        self.assertNotEqual(r.returncode, 0, r.stdout[-500:])
        self.assertIn('No citations', r.stdout)

    def test_F16_C5_minus_sign(self):
        src = vq.normalize('Output changed by -5% in 2020 and by −3% in 2021.')
        self.assertEqual(vq.match_quote_detail('5% in 2020', src)[0], 'missing')
        self.assertEqual(vq.match_quote_detail('3% in 2021', src)[0], 'missing')
        self.assertEqual(vq.match_quote_detail('-5% in 2020', src)[0], 'verbatim')

    def test_F16_D4_wrong_field_types(self):
        with tempfile.TemporaryDirectory() as d:
            run = lambda *a: subprocess.run([sys.executable, *a], capture_output=True, text=True, timeout=60)  # noqa: E731
            run(os.path.join(SCRIPTS, 'citation_manager.py'), 'init-run', '--dir', d, '--query', 'q')
            for script, payload in (('evidence_store.py', {'source_id': 5, 'quote': 7}),
                                    ('evidence_store.py', {'source_id': 'src_1', 'quote': 'q', 'locator': 5}),
                                    ('citation_manager.py', {'raw_url': 123, 'title': 't'}),
                                    ('citation_manager.py', {'raw_url': 'https://a.org', 'title': 5})):
                cmd = 'add' if script == 'evidence_store.py' else 'register-source'
                r = run(os.path.join(SCRIPTS, script), cmd, '--dir', d, '--json', json.dumps(payload))
                self.assertNotIn('Traceback', r.stderr, (script, payload, r.stderr[-300:]))

    def test_F16_D5_docstring(self):
        self.assertNotIn('antonyms alone do not count', vcs.negation_mismatch.__doc__)


if __name__ == '__main__':
    unittest.main()
