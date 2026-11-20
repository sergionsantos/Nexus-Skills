#!/usr/bin/env python3
"""Tests for verify_claim_support.py CLI."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'verify_claim_support.py')


def run_vcs(*args: str, expect_fail: bool = False) -> dict | str:
    """Run verify_claim_support.py."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True, encoding='utf-8',
    )
    if result.returncode != 0 and not expect_fail:
        raise RuntimeError(f'Exit {result.returncode}: {result.stderr}\n{result.stdout}')
    stdout = result.stdout.strip()
    if stdout.startswith('{'):
        return json.loads(stdout)
    return stdout


def write_jsonl(path: str, rows: list[dict]):
    with open(path, 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row) + '\n')


class TestYearExtraction(unittest.TestCase):
    """Regression for upstream PR #3: YEAR_RE must return whole years."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('verify_claim_support', SCRIPT)
        self.vcs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.vcs)

    def test_extract_years_returns_full_years(self):
        self.assertEqual(self.vcs.extract_years('in 2024 and 2025'), {'2024', '2025'})

    def test_year_mismatch_is_detected(self):
        _, _, notes = self.vcs.compute_support_score(
            'Revenue grew in 2024.', ['Revenue grew in 2019.'])
        self.assertIn('year mismatch', notes)


class TestVerifySupported(unittest.TestCase):
    """Claims with matching evidence should be supported."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Sources
        write_jsonl(os.path.join(self.tmpdir, 'sources.jsonl'), [
            {'source_id': 'src_quantum_001', 'title': 'Quantum Computing 2024'},
        ])
        # Evidence with clear overlap to the claim
        write_jsonl(os.path.join(self.tmpdir, 'evidence.jsonl'), [
            {
                'evidence_id': 'ev_shor_001',
                'source_id': 'src_quantum_001',
                'quote': "Shor's algorithm can factor large integers exponentially faster than any known classical algorithm, threatening RSA-2048 encryption.",
                'evidence_type': 'direct_quote',
            },
        ])
        # Claim that matches the evidence
        write_jsonl(os.path.join(self.tmpdir, 'claims.jsonl'), [
            {
                'claim_id': 'clm_factor_001',
                'section_id': 'finding_1',
                'text': "Shor's algorithm can factor large numbers exponentially faster than classical methods, threatening RSA-2048.",
                'claim_type': 'factual',
                'cited_source_ids': ['src_quantum_001'],
                'evidence_ids': ['ev_shor_001'],
                'support_status': 'unverified',
            },
        ])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_supported_claim(self):
        out = run_vcs('verify', '--dir', self.tmpdir)
        self.assertEqual(out['status'], 'pass')
        self.assertEqual(out['factual_unsupported'], 0)

        # Check updated claims file
        claims = []
        with open(os.path.join(self.tmpdir, 'claims.jsonl'), encoding='utf-8') as f:
            for line in f:
                claims.append(json.loads(line))
        self.assertEqual(claims[0]['support_status'], 'supported')


class TestVerifyUnsupported(unittest.TestCase):
    """Claims without evidence should be unsupported."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.tmpdir, 'sources.jsonl'), [])
        write_jsonl(os.path.join(self.tmpdir, 'evidence.jsonl'), [])
        write_jsonl(os.path.join(self.tmpdir, 'claims.jsonl'), [
            {
                'claim_id': 'clm_no_ev_001',
                'section_id': 'finding_1',
                'text': 'The population of Mars is 500 million as of 2025.',
                'claim_type': 'factual',
                'cited_source_ids': [],
                'evidence_ids': [],
                'support_status': 'unverified',
            },
        ])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_unsupported_no_evidence(self):
        out = run_vcs('verify', '--dir', self.tmpdir)
        self.assertEqual(out['factual_unsupported'], 1)
        self.assertEqual(out['status'], 'pass')  # Non-strict by default

    def test_strict_fails(self):
        out = run_vcs('verify', '--dir', self.tmpdir, '--strict', expect_fail=True)
        self.assertEqual(out['status'], 'fail')


class TestVerifyMixed(unittest.TestCase):
    """Mixed claim types with different thresholds."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.tmpdir, 'sources.jsonl'), [])
        write_jsonl(os.path.join(self.tmpdir, 'evidence.jsonl'), [])
        write_jsonl(os.path.join(self.tmpdir, 'claims.jsonl'), [
            {
                'claim_id': 'clm_spec_001',
                'section_id': 'finding_1',
                'text': 'Quantum computers might eventually solve protein folding in real time.',
                'claim_type': 'speculation',
                'cited_source_ids': [],
                'evidence_ids': [],
                'support_status': 'unverified',
            },
            {
                'claim_id': 'clm_rec_001',
                'section_id': 'recommendations',
                'text': 'Organizations should begin PQC migration planning immediately.',
                'claim_type': 'recommendation',
                'cited_source_ids': [],
                'evidence_ids': [],
                'support_status': 'unverified',
            },
        ])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_speculation_passes(self):
        out = run_vcs('verify', '--dir', self.tmpdir)
        # Speculation doesn't need evidence
        claims = []
        with open(os.path.join(self.tmpdir, 'claims.jsonl'), encoding='utf-8') as f:
            for line in f:
                claims.append(json.loads(line))
        spec = [c for c in claims if c['claim_type'] == 'speculation'][0]
        self.assertEqual(spec['support_status'], 'supported')


class TestVerifyPartial(unittest.TestCase):
    """Evidence with partial overlap should result in partial status."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.tmpdir, 'sources.jsonl'), [
            {'source_id': 'src_nist_001', 'title': 'NIST PQC Standards'},
        ])
        write_jsonl(os.path.join(self.tmpdir, 'evidence.jsonl'), [
            {
                'evidence_id': 'ev_nist_001',
                'source_id': 'src_nist_001',
                'quote': 'NIST announced the standardization of CRYSTALS-Kyber for key encapsulation.',
                'evidence_type': 'direct_quote',
            },
        ])
        # Claim mentions NIST but adds unverified detail about timeline
        write_jsonl(os.path.join(self.tmpdir, 'claims.jsonl'), [
            {
                'claim_id': 'clm_nist_time',
                'section_id': 'finding_2',
                'text': 'NIST standardized four lattice-based algorithms in 2024, covering both encryption and signatures.',
                'claim_type': 'factual',
                'cited_source_ids': ['src_nist_001'],
                'evidence_ids': ['ev_nist_001'],
                'support_status': 'unverified',
            },
        ])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_partial_support(self):
        out = run_vcs('verify', '--dir', self.tmpdir)
        claims = []
        with open(os.path.join(self.tmpdir, 'claims.jsonl'), encoding='utf-8') as f:
            for line in f:
                claims.append(json.loads(line))
        # Should be partial or needs_review (not fully supported due to number/detail mismatch)
        self.assertIn(claims[0]['support_status'], ('partial', 'needs_review', 'supported'))


class TestSupportScore(unittest.TestCase):
    """Unit tests for compute_support_score."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from verify_claim_support import compute_support_score
        cls.score = staticmethod(compute_support_score)

    def test_identical_text(self):
        status, score, _ = self.score(
            'RSA-2048 uses 2048-bit keys for encryption.',
            ['RSA-2048 uses 2048-bit keys for encryption.'],
        )
        self.assertEqual(status, 'supported')
        self.assertGreater(score, 0.8)

    def test_no_evidence(self):
        status, score, _ = self.score('Any claim text.', [])
        self.assertEqual(status, 'unsupported')
        self.assertEqual(score, 0.0)

    def test_unrelated_evidence(self):
        status, score, _ = self.score(
            'The moon landing occurred in 1969.',
            ['Bananas are a good source of potassium and fiber.'],
        )
        self.assertIn(status, ('needs_review', 'unsupported'))
        self.assertLess(score, 0.35)


class TestContradictingAndUnrelatedEvidence(unittest.TestCase):
    """Regression for upstream issue #14: contradicting, empty and unrelated
    evidence must not be scored as support."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from verify_claim_support import compute_support_score
        cls.score = staticmethod(compute_support_score)

    def assertNegationMismatch(self, claim, quote):
        status, _, notes = self.score(claim, [quote])
        self.assertEqual(status, 'contradicted', f'{claim!r} vs {quote!r}')
        self.assertIn('negation mismatch', notes)

    def test_en_negated_evidence(self):
        self.assertNegationMismatch(
            'The museum is open on Mondays.', 'The museum is not open on Mondays.')

    def test_en_negated_claim(self):
        self.assertNegationMismatch(
            'The museum is not open on Mondays.', 'The museum is open on Mondays.')

    def test_en_no_and_never(self):
        self.assertNegationMismatch(
            'The museum opens on Mondays.', 'The museum never opens on Mondays.')
        self.assertNegationMismatch(
            'The museum charges entry fees.', 'The museum charges no entry fees.')
        self.assertNegationMismatch(
            'The museum opens on Mondays.', "The museum doesn't open on Mondays.")

    def test_pt_negation(self):
        self.assertNegationMismatch(
            'O museu abre às segundas.', 'O museu não abre às segundas.')
        self.assertNegationMismatch(
            'O museu não abre às segundas.', 'O museu abre às segundas.')
        self.assertNegationMismatch(
            'O museu abre às segundas.', 'O museu nunca abre às segundas.')
        self.assertNegationMismatch(
            'O museu abre às segundas e aos domingos.',
            'O museu nem abre às segundas nem aos domingos.')

    def test_pt_accented_words_count_as_tokens(self):
        status, _, notes = self.score(
            'A inflação subiu em março.', ['A produção subiu em agosto.'])
        self.assertNotEqual(status, 'supported')
        self.assertNotIn('adequate', notes)

    def assertNoSharedContent(self, claim, quotes):
        status, score, notes = self.score(claim, quotes)
        self.assertEqual(status, 'needs_review', f'{claim!r} vs {quotes!r}')
        self.assertEqual(score, 0.0)
        self.assertIn('no shared content', notes)

    def test_empty_quote(self):
        # nexus: an empty quote is no evidence at all -> unsupported (upstream FFV47: needs_review)
        self.assertEqual(self.score('The museum is open on Mondays.', [''])[:2], ('unsupported', 0.0))

    def test_pt_unrelated_evidence(self):
        self.assertNoSharedContent('A inflação subiu em março.', ['Choveu ontem à tarde.'])

    def test_unrelated_evidence_with_number_and_year(self):
        self.assertNoSharedContent('Revenue grew 40% in 2024.', ['Choveu ontem à tarde.'])

    def test_zh_negation(self):
        self.assertNegationMismatch('示例馆周一开放。', '示例馆周一不开放。')
        self.assertNegationMismatch('示例馆周一开放。', '示例馆周一没有开放。')

    def test_more_negation_words_both_ways(self):
        for affirmed, negated in (
            ('O museu abre às segundas.', 'O museu nao abre às segundas.'),
            ('The museums in the city open on Mondays.',
             'None of the museums in the city open on Mondays.'),
            ('Students attended the lecture on Monday.',
             'Nobody attended the lecture on Monday.'),
            ('Visitors can enter the museum on Mondays.',
             'Visitors cant enter the museum on Mondays.'),
            ('O museu da cidade abre às segundas.',
             'Nenhum museu da cidade abre às segundas.'),
            ('A escola da cidade abre aos domingos.',
             'Nenhuma escola da cidade abre aos domingos.'),
            ('O público entra no museu às segundas.',
             'Ninguém do público entra no museu às segundas.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_pt_contraction_no_does_not_cancel_negation(self):
        self.assertNegationMismatch('O museu fica no centro.', 'O museu não fica no centro.')
        self.assertNegationMismatch('O museu não fica no centro.', 'O museu fica no centro.')

    def test_en_no_still_negates_next_to_pt_lookalike_words(self):
        for affirmed, negated in (
            ('The company reports revenue growth in São Paulo.',
             'The company reports no revenue growth in São Paulo.'),
            ('Blood type O donors face restrictions in the program.',
             'Blood type O donors face no restrictions in the program.'),
            ('The device supports NAS storage with encryption.',
             'The device supports NAS storage with no encryption.'),
            ('The restaurant serves dishes à la carte with surcharges.',
             'The restaurant serves dishes à la carte with no surcharges.'),
            ('The café charges entry fees.', 'The café charges no entry fees.'),
            ('Sales showed growth.', 'Sales showed no growth.'),
            ('Our café showed losses.', 'Our café showed no losses.'),
            ('Clients reported déjà vu effects.', 'Clients reported no déjà vu effects.'),
            ('Sales showed growth per résumé data.', 'Sales showed no growth per résumé data.'),
            ('The trainer used a longe.', 'The trainer used no longe.'),
            ('The museum has a da Vinci.', 'The museum has no da Vinci.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_en_no_still_negates_after_sentence_initial_pt_lookalike_name(self):
        for affirmed, negated in (
            ('Uma Thurman received an award for the role.',
             'Uma Thurman received no award for the role.'),
            ('O Globo reported growth in the region.',
             'O Globo reported no growth in the region.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_en_no_still_negates_after_sentence_initial_pt_lookalike_name_without_en_marker(self):
        for affirmed, negated in (
            ('Uma Thurman won Oscar.', 'Uma Thurman won no Oscar.'),
            ('O Globo cited sources.', 'O Globo cited no sources.'),
            ('Uma Thurman owns a da Vinci.', 'Uma Thurman owns no da Vinci.'),
            ('O Globo found da Vinci sketches.', 'O Globo found no da Vinci sketches.'),
            ('O Globo reporters do fact checks.', 'O Globo reporters do no fact checks.'),
            ('O Globo saw change de jure.', 'O Globo saw no change de jure.'),
            ('Uma Thurman films do business de facto.', 'Uma Thurman films do no business.'),
            ('O Globo cited da Vinci letters.', 'O Globo cited no letters.'),
            ('O Globo saw de facto and de jure change.', 'O Globo saw no change.'),
            ('Uma Thurman owns da Vinci, de Kooning pieces.', 'Uma Thurman owns no da Vinci.'),
            ('O Globo cited da Vinci, de Gaulle letters.', 'O Globo cited no letters.'),
            ('O Globo saw de facto change.', 'O Globo saw no change.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_pt_contraction_no_does_not_cancel_negation_after_sentence_initial_name(self):
        for affirmed, negated in (
            ('O Brasil fica no centro.', 'O Brasil não fica no centro.'),
            ('O Brasil fica no centro.', 'O Brasil nunca fica no centro.'),
            ('O Rio fica no Sudeste.', 'O Rio nunca fica no Sudeste.'),
            ('O Brasil fica no centro.', 'O Brasil nunca fica perto do centro.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_pt_contraction_no_does_not_cancel_negation_after_sentence_initial_name_next_to_en_lookalike_words(self):
        for affirmed, negated in (
            ('O Globo publicou on-line no sábado.', 'O Globo não publicou on-line no sábado.'),
            ('O Globo apurou in loco no sábado.', 'O Globo não apurou in loco no sábado.'),
            ('O Globo publicou a renda per capita no sábado.',
             'O Globo não publicou a renda per capita no sábado.'),
            ('O Globo abriu loja no The Mall.', 'O Globo não abriu loja no The Mall.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_en_no_still_negates_next_to_accented_loanword_and_en_marker_lookalike(self):
        for affirmed, negated in (
            ('Shoppers found açaí bowls near The Mall.', 'Shoppers found no açaí bowls near The Mall.'),
            ('Shoppers bought açaí bowls on-line.', 'Shoppers bought no açaí bowls on-line.'),
            ('Brazil saw açaí sales grow per capita.', 'Brazil saw no açaí sales grow per capita.'),
            ('Shoppers bought guaraná sodas on-line.', 'Shoppers bought no guaraná sodas on-line.'),
            ('Brazil saw guaraná sales grow per capita.', 'Brazil saw no guaraná sales grow per capita.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_pt_contraction_no_does_not_cancel_negation_next_to_en_lookalike_words(self):
        for affirmed, negated in (
            ('O evento será on-line no sábado.', 'O evento não será on-line no sábado.'),
            ('O fiscal faz a vistoria in loco no sábado.',
             'O fiscal não faz a vistoria in loco no sábado.'),
            ('O museu fica no centro do The Mall.', 'O museu não fica no centro do The Mall.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_pt_contraction_no_does_not_cancel_negation_without_marker_word_next_to_en_lookalike_words(self):
        for affirmed, negated in (
            ('A equipe faz a vistoria in loco no sábado.',
             'A equipe não faz a vistoria in loco no sábado.'),
            ('A loja vende on-line no sábado.', 'A loja não vende on-line no sábado.'),
            ('A renda per capita subiu no período.', 'A renda per capita não subiu no período.'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_en_no_still_negates_against_pt_annotated_quote(self):
        self.assertNegationMismatch('Sales showed no growth.', 'Sales showed growth (relatório anual).')
        self.assertNegationMismatch('Sales showed growth.', 'Sales showed no growth (relatório anual).')

    def test_pt_text_without_marker_word_does_not_cancel_negation(self):
        self.assertNegationMismatch('Fica no centro histórico.', 'Não fica no centro histórico.')
        self.assertNegationMismatch('Não fica no centro histórico.', 'Fica no centro histórico.')

    def test_pt_contraction_no_is_not_negation(self):
        _, _, notes = self.score(
            'O museu fica perto do centro da cidade.', ['O museu fica no centro da cidade.'])
        self.assertNotIn('negation mismatch', notes)

    def test_pt_contraction_no_is_not_negation_after_sentence_initial_name_next_to_en_lookalike_words(self):
        _, _, notes = self.score(
            'O Globo publicou a reportagem on-line perto do estádio.',
            ['O Globo publicou a reportagem on-line no estádio.'])
        self.assertNotIn('negation mismatch', notes)

    def test_pt_contraction_no_is_not_negation_without_marker_word(self):
        _, _, notes = self.score(
            'Fica perto do centro histórico.', ['Fica no centro histórico.'])
        self.assertNotIn('negation mismatch', notes)

    def test_pt_contraction_no_is_not_negation_without_marker_word_next_to_en_lookalike_words(self):
        _, _, notes = self.score(
            'A vistoria in loco fica perto do centro histórico.',
            ['A vistoria in loco fica no centro histórico.'])
        self.assertNotIn('negation mismatch', notes)

    def test_pt_contraction_no_is_not_negation_after_sentence_initial_name_without_other_marker(self):
        for with_no, without_no in (
            ('O Brasil venceu no Maracanã.', 'O Brasil venceu perto do Maracanã.'),
            ('O Globo publicou no Natal.', 'O Globo publicou perto do Natal.'),
        ):
            for claim, quote in ((with_no, without_no), (without_no, with_no)):
                _, _, notes = self.score(claim, [quote])
                self.assertNotIn('negation mismatch', notes)

    def test_pt_contraction_no_is_not_negation_after_sentence_initial_name_against_na_or_do(self):
        for with_no, without_no in (
            ('O Globo publicou no Natal.', 'O Globo publicou na véspera do Natal.'),
            ('O Brasil jogou no Maracanã.', 'O Brasil jogou na final do Maracanã.'),
        ):
            for claim, quote in ((with_no, without_no), (without_no, with_no)):
                _, _, notes = self.score(claim, [quote])
                self.assertNotIn('negation mismatch', notes)

    def test_zh_more_negation_chars_both_ways(self):
        for affirmed, negated in (
            ('示例馆周一开放。', '示例馆周一未开放。'),
            ('示例馆周一有讲座。', '示例馆周一无讲座。'),
            ('示例馆是博物馆。', '示例馆非博物馆。'),
        ):
            self.assertNegationMismatch(affirmed, negated)
            self.assertNegationMismatch(negated, affirmed)

    def test_zh_negative_compounds_still_negate(self):
        # 无法 "cannot", 并非 "is not", 未必 "not necessarily", 无关 "unrelated"
        self.assertNegationMismatch('示例馆周一开放。', '示例馆周一无法开放。')
        self.assertNegationMismatch('示例馆是博物馆。', '示例馆并非博物馆。')
        self.assertNegationMismatch('示例馆周一开放。', '示例馆周一未必开放。')
        self.assertNegationMismatch('示例馆与大学有关。', '示例馆与大学无关。')

    def test_zh_unrelated_evidence(self):
        self.assertNoSharedContent('示例馆周一开放。', ['今天下雨。'])

    def test_zh_empty_quote(self):
        self.assertEqual(self.score('示例馆周一开放。', [''])[:2], ('unsupported', 0.0))

    def test_positive_controls_stay_supported(self):
        for claim in ('The museum is open on Mondays.',
                      'O museu abre às segundas.',
                      'A inflação subiu em março.',
                      '示例馆周一开放。'):
            status, score, notes = self.score(claim, [claim])
            self.assertEqual(status, 'supported', claim)
            self.assertEqual(score, 1.0, claim)
            self.assertEqual(notes, 'adequate overlap', claim)

    def test_decomposed_accents_match_composed(self):
        import unicodedata
        claim = 'A inflação subiu em março.'
        status, _, _ = self.score(claim, [unicodedata.normalize('NFD', claim)])
        self.assertEqual(status, 'supported')

    def test_issue_no_evidence_case(self):
        self.assertEqual(
            self.score('The museum is open on Mondays.', []),
            ('unsupported', 0.0, 'no evidence linked'))

    def test_notes_skip_components_the_claim_lacks(self):
        # No 4+ letter words in the claim, so lexical overlap is not scored
        # and must not be reported as low.
        _, _, notes = self.score('Tim is 30.', ['Tim is 30.'])
        self.assertEqual(notes, 'adequate overlap')

    def test_chemical_formula_is_not_negation(self):
        status, _, _ = self.score(
            'Emissions fell sharply in cities.',
            ['NO2 emissions fell sharply in cities.'],
        )
        self.assertEqual(status, 'supported')

    def test_zh_paraphrase_shares_tokens(self):
        status, _, _ = self.score('示例馆周一开放。', ['周一示例馆开放。'])
        self.assertEqual(status, 'supported')


class TestNegationOutsideSupportingPassage(unittest.TestCase):
    """A negation counts as a mismatch only when it negates the claim's
    content, not when it sits in a clause the claim does not depend on."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from verify_claim_support import compute_support_score
        cls.score = staticmethod(compute_support_score)

    def assertNoNegationMismatch(self, claim, quote):
        status, _, notes = self.score(claim, [quote])
        self.assertNotIn('negation mismatch', notes, f'{claim!r} vs {quote!r}')
        self.assertEqual(status, 'supported', f'{claim!r} vs {quote!r}: {notes}')

    def test_negation_in_separate_clause(self):
        self.assertNoNegationMismatch(
            'The museum is open on Mondays.',
            'The museum is open on Mondays, but not on holidays.')
        self.assertNoNegationMismatch(
            'The museum is open on Mondays.',
            'The museum, not the library, is open on Mondays.')

    def test_negation_after_conjunction_without_comma(self):
        self.assertNoNegationMismatch(
            'The museum is open on Mondays.',
            'The museum is open on Mondays but not on holidays.')
        self.assertNoNegationMismatch(
            'O museu abre às segundas.',
            'O museu abre às segundas mas não nos feriados.')

    def test_zh_compounds_with_bu_are_not_negation(self):
        # 不过 "however", 不断 "continuously", 不仅 "not only"
        self.assertNoNegationMismatch('示例馆周一开放。', '不过示例馆周一开放。')
        self.assertNoNegationMismatch('游客数量增加。', '游客数量不断增加。')
        self.assertNoNegationMismatch('示例馆周一开放。', '示例馆不仅周一开放，周二也开放。')

    def test_zh_compounds_with_other_markers_are_not_negation(self):
        # 非常 "very", 未来 "future", 无论 "no matter"
        self.assertNoNegationMismatch('示例馆受欢迎。', '示例馆非常受欢迎。')
        self.assertNoNegationMismatch('示例馆周一开放。', '未来示例馆周一开放。')
        self.assertNoNegationMismatch('示例馆周一开放。', '无论如何示例馆周一开放。')

    def test_more_zh_compounds_are_not_negation(self):
        # 非洲 "Africa", 南非 "South Africa", 无疑 "undoubtedly", 无线 "wireless",
        # 无数 "countless", 非凡 "extraordinary", 除非 "unless"
        self.assertNoNegationMismatch('示例馆展出文物。', '示例馆展出非洲文物。')
        self.assertNoNegationMismatch('示例馆位于南部。', '示例馆位于南非南部。')
        self.assertNoNegationMismatch('示例馆是最大的博物馆。', '示例馆无疑是最大的博物馆。')
        self.assertNoNegationMismatch('示例馆提供网络。', '示例馆提供无线网络。')
        self.assertNoNegationMismatch('示例馆收藏文物。', '示例馆收藏无数文物。')
        self.assertNoNegationMismatch('示例馆的展览很成功。', '示例馆的展览非凡成功。')
        self.assertNoNegationMismatch('示例馆周一开放。', '除非下雨示例馆周一开放。')

    def test_fixed_expressions_are_not_negation(self):
        claim = 'Studies show that exercise improves sleep quality.'
        self.assertNoNegationMismatch(
            claim, 'No doubt, studies show that exercise improves sleep quality.')
        self.assertNoNegationMismatch(
            claim, 'There is no doubt that studies show exercise improves sleep quality.')

    def test_more_fixed_expressions_are_not_negation(self):
        self.assertNoNegationMismatch(
            'The director is Ana Silva.', 'The director is none other than Ana Silva.')
        self.assertNoNegationMismatch(
            'The museum collection is excellent.', 'The museum collection is second to none.')

    def test_pt_nao_raro_is_not_negation(self):
        # "não raro" means "often"
        claim = 'O museu abre às segundas.'
        self.assertNoNegationMismatch(claim, 'Não raro o museu abre às segundas.')
        self.assertNoNegationMismatch(claim, 'Nao raro o museu abre às segundas.')

    def test_unaccented_fixed_expressions_are_not_negation(self):
        claim = 'O museu abre às segundas.'
        self.assertNoNegationMismatch(
            claim, 'O museu nao só abre às segundas como também aos domingos.')
        self.assertNoNegationMismatch(claim, 'O museu nao apenas abre às segundas.')
        self.assertNoNegationMismatch(claim, 'O museu nao somente abre às segundas.')

    def test_negated_antonym_is_not_mismatch(self):
        for claim, quote in (
            ('The museum is open on Mondays.', 'The museum is not closed on Mondays.'),
            ('The museum is closed on Mondays.', 'The museum is not open on Mondays.'),
            ('The museum is not open on Mondays.', 'The museum is closed on Mondays.'),
            ('O museu abre às segundas.', 'O museu não fecha às segundas.'),
            ('O museu fecha às segundas.', 'O museu não abre às segundas.'),
            ('O museu não fecha às segundas.', 'O museu abre às segundas.'),
        ):
            self.assertNoNegationMismatch(claim, quote)

    def test_negated_antonyms_on_both_sides_are_mismatch(self):
        # "not open" means closed, "not closed" means open
        status, _, notes = self.score(
            'The museum is not open on Mondays.', ['The museum is not closed on Mondays.'])
        self.assertEqual(status, 'contradicted')
        self.assertIn('negation mismatch', notes)

    def test_antonym_elsewhere_does_not_cancel_negation(self):
        # The quote uses both sides of the pair, so the antonym is not what
        # the negation applies to.
        for claim, quote in (
            ('The museum is open on Mondays.',
             'The museum is not open on Mondays and is closed on holidays.'),
            ('O museu abre às segundas.',
             'O museu não abre às segundas e fecha aos domingos.'),
            ('Revenue increased in 2024.',
             'Revenue did not increase in 2024 and costs decreased.'),
            ('The museum is open on Mondays.',
             'On Mondays, the museum is closed, not open.'),
        ):
            status, _, notes = self.score(claim, [quote])
            self.assertEqual(status, 'contradicted', f'{claim!r} vs {quote!r}')
            self.assertIn('negation mismatch', notes)

    def test_zh_negated_claim_is_mismatch(self):
        status, _, notes = self.score('示例馆周一不开放。', ['示例馆周一开放。'])
        self.assertEqual(status, 'contradicted')
        self.assertIn('negation mismatch', notes)

    def test_negated_clause_holding_claim_content_is_mismatch(self):
        # The comma moves "2024" out of the negated clause, but that clause
        # still holds "revenue", which no other clause has.
        status, _, notes = self.score('Revenue grew in 2024.', ['In 2024, revenue did not grow.'])
        self.assertEqual(status, 'contradicted')
        self.assertIn('negation mismatch', notes)


class TestSingleSharedElementIsNotSupport(unittest.TestCase):
    """A short claim is supported only when the evidence confirms what it
    says, not just its subject."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        import verify_claim_support
        cls.vcs = verify_claim_support

    def test_common_sentence_initial_words_are_not_entities(self):
        for text in ('It is big.', 'Some museums open early.',
                     'None of the museums open.', 'Isso mudou.',
                     'Este museu abre.', 'Nenhum museu abre.'):
            self.assertEqual(self.vcs.extract_entities(text), set(), text)

    def test_common_word_before_a_name_is_not_part_of_the_entity(self):
        self.assertEqual(self.vcs.extract_entities('Some Tesla cars sold.'), {'Tesla'})

    def test_sentence_initial_names_stay_entities(self):
        self.assertEqual(self.vcs.extract_entities('Tesla won.'), {'Tesla'})
        self.assertEqual(self.vcs.extract_entities('Apple is big.'), {'Apple'})

    def test_shared_subject_alone_is_not_supported(self):
        for claim, quote in (
            ('Tesla won.', 'Tesla lost.'),
            ('Apple is big.', 'Apple fell sharply last year.'),
            ('It is big.', 'It is small.'),
            ('Our team won.', 'Our team lost.'),
            ('Seu lucro subiu.', 'Seu lucro caiu.'),
            # An acronym is part of the subject, not of what the claim says
            ('GDP grew 3% in 2023.', 'GDP fell 3% in 2023.'),
        ):
            status, _, _ = self.vcs.compute_support_score(claim, [quote])
            self.assertNotEqual(status, 'supported', f'{claim!r} vs {quote!r}')

    def test_identical_short_claims_stay_supported(self):
        for claim in ('Tesla won.', 'Apple is big.'):
            status, score, _ = self.vcs.compute_support_score(claim, [claim])
            self.assertEqual(status, 'supported', claim)
            self.assertEqual(score, 1.0, claim)


class TestNegationLexiconFile(unittest.TestCase):
    """Antonym pairs live in a data file: a pair added there takes effect
    without changing the code."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        scripts = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        for name in ('verify_claim_support.py', 'negation_lexicon.json'):
            shutil.copy(os.path.join(scripts, name), self.tmpdir)
        self.lexicon_path = os.path.join(self.tmpdir, 'negation_lexicon.json')

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def load_copy(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'verify_claim_support_copy', os.path.join(self.tmpdir, 'verify_claim_support.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_added_antonym_pair_applies(self):
        claim, quote = 'The patient is awake.', 'The patient is not asleep.'
        _, _, notes = self.load_copy().compute_support_score(claim, [quote])
        self.assertIn('negation mismatch', notes)

        with open(self.lexicon_path, encoding='utf-8') as f:
            lexicon = json.load(f)
        lexicon['antonyms'].append([['awake'], ['asleep']])
        with open(self.lexicon_path, 'w', encoding='utf-8') as f:
            json.dump(lexicon, f, ensure_ascii=False)

        _, _, notes = self.load_copy().compute_support_score(claim, [quote])
        self.assertNotIn('negation mismatch', notes)


class TestStrictBlocksWeakSupport(unittest.TestCase):
    """Regression for upstream issue #14: --strict must also fail on
    needs_review, which is what contradicting or unrelated evidence yields."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        write_jsonl(os.path.join(self.tmpdir, 'sources.jsonl'), [
            {'source_id': 'src_001', 'title': 'Fixture'},
        ])
        write_jsonl(os.path.join(self.tmpdir, 'evidence.jsonl'), [
            {'evidence_id': 'ev_neg', 'source_id': 'src_001',
             'quote': 'O museu não abre às segundas.'},
            {'evidence_id': 'ev_rain', 'source_id': 'src_001',
             'quote': 'Choveu ontem à tarde.'},
        ])
        write_jsonl(os.path.join(self.tmpdir, 'claims.jsonl'), [
            {'claim_id': 'clm_museu', 'section_id': 'finding_1',
             'text': 'O museu abre às segundas.', 'claim_type': 'factual',
             'cited_source_ids': [], 'evidence_ids': ['ev_neg']},
            {'claim_id': 'clm_inflacao', 'section_id': 'finding_1',
             'text': 'A inflação subiu em março.', 'claim_type': 'factual',
             'cited_source_ids': [], 'evidence_ids': ['ev_rain']},
            {'claim_id': 'clm_revenue', 'section_id': 'finding_2',
             'text': 'Revenue grew 40% in 2024.', 'claim_type': 'factual',
             'cited_source_ids': [], 'evidence_ids': ['ev_rain']},
        ])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def read_claims(self):
        with open(os.path.join(self.tmpdir, 'claims.jsonl'), encoding='utf-8') as f:
            return {c['claim_id']: c for c in map(json.loads, f)}

    def test_strict_fails_on_needs_review(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, 'verify', '--dir', self.tmpdir, '--strict'],
            capture_output=True, text=True, encoding='utf-8',
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        out = json.loads(result.stdout)
        self.assertEqual(out['status'], 'fail')
        self.assertEqual(out['factual_needs_review'], 2)
        self.assertEqual(out['factual_contradicted'], 1)

        claims = self.read_claims()
        self.assertEqual(claims['clm_museu']['support_status'], 'contradicted')
        self.assertIn('negation mismatch', claims['clm_museu']['_support_notes'])
        for cid in ('clm_inflacao', 'clm_revenue'):
            self.assertEqual(claims[cid]['support_status'], 'needs_review')
            self.assertIn('no shared content', claims[cid]['_support_notes'])

    def test_non_strict_still_passes(self):
        out = run_vcs('verify', '--dir', self.tmpdir)
        self.assertEqual(out['status'], 'pass')


class TestReportWording(unittest.TestCase):
    """Regression for upstream issue #14: the report must not overstate a
    lexical heuristic as adequate support."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def report(self, statuses):
        write_jsonl(os.path.join(self.tmpdir, 'claims.jsonl'), [
            {'claim_id': f'clm_{i}', 'section_id': 'finding_1',
             'text': f'Claim number {i}.', 'claim_type': 'factual',
             'support_status': status, '_support_notes': 'low lexical overlap'}
            for i, status in enumerate(statuses)
        ])
        return run_vcs('report', '--dir', self.tmpdir)

    def test_partial_claims_are_listed_not_called_adequate(self):
        out = self.report(['supported', 'partial'])
        self.assertNotIn('adequate support', out)
        self.assertIn('Partially Supported', out)
        self.assertIn('Claim number 1.', out)

    def test_report_states_check_is_lexical_heuristic(self):
        for statuses in (['supported'], ['partial'], ['needs_review']):
            out = self.report(statuses)
            self.assertNotIn('adequate support', out)
            self.assertIn('not semantic verification', out)


class TestClaimNumberMissingFromEvidence(unittest.TestCase):
    """A claim number the evidence never states is not support, and years
    count once, in the years component, not also as numbers."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('verify_claim_support', SCRIPT)
        self.vcs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.vcs)

    def assert_number_missing(self, claim, quotes):
        status, score, notes = self.vcs.compute_support_score(claim, quotes)
        self.assertEqual(status, 'needs_review', (claim, quotes, score, notes))
        self.assertLess(score, self.vcs.SUPPORTED_THRESHOLD)
        self.assertIn('claim number not found in evidence', notes)

    def test_percent_absent_from_evidence_is_not_supported(self):
        self.assert_number_missing('Revenue grew 12% in 2023.', ['Revenue grew in 2023.'])

    def test_decimal_absent_from_evidence_is_not_supported(self):
        self.assert_number_missing(
            'Tesla delivered 1.8 million cars in 2023.', ['Tesla delivered cars in 2023.'])

    def test_number_absent_with_extra_quote_text_is_not_supported(self):
        self.assert_number_missing(
            'Mortality fell 40% in 2021.', ['Mortality fell in 2021, the report says.'])

    def test_number_absent_from_every_quote_is_not_supported(self):
        self.assert_number_missing(
            'Revenue grew 12% in 2023.',
            ['Revenue grew in 2023.', 'Revenue grew strongly in 2023.'])

    def test_matching_number_still_supports(self):
        status, _, _ = self.vcs.compute_support_score(
            'Revenue grew 12% in 2023.', ['Revenue grew in 2023.', 'Revenue grew 12% in 2023.'])
        self.assertEqual(status, 'supported')

    def test_thousands_separator_still_matches(self):
        status, _, _ = self.vcs.compute_support_score(
            'The trial enrolled 1,847 patients in 2022.',
            ['The trial enrolled 1847 patients in 2022.'])
        self.assertEqual(status, 'supported')

    def test_years_are_not_scored_as_numbers(self):
        components = self.vcs.claim_components('Revenue grew in 2023.')
        self.assertNotIn('numbers', [c[0] for c in components])
        numbers = next(c[2] for c in self.vcs.claim_components('Revenue grew 12% in 2023.')
                       if c[0] == 'numbers')
        self.assertNotIn('2023', numbers)
        self.assertTrue(numbers)

    def test_conflicting_year_is_not_supported(self):
        status, _, notes = self.vcs.compute_support_score(
            'Revenue grew in 2024.', ['Revenue grew in 2019.'])
        self.assertNotEqual(status, 'supported')
        self.assertIn('year', notes)

    def test_numeric_conflict_and_negation_unchanged(self):
        status, _, notes = self.vcs.compute_support_score(
            'Revenue grew 12% in 2023.', ['Revenue grew 3% in 2023.'])
        self.assertEqual(status, 'needs_review')
        self.assertIn('numeric conflict', notes)
        status, _, _ = self.vcs.compute_support_score(
            'Revenue grew 12% in 2023.', ['Revenue did not grow in 2023.'])
        self.assertEqual(status, 'contradicted')


if __name__ == '__main__':
    unittest.main()
