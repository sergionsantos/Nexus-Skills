#!/usr/bin/env python3
"""Tests for verify_quotes.py (snapshot + verbatim/near/missing quote checks)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

from verify_quotes import match_quote, match_quote_detail, normalize  # noqa: E402

SCRIPT = os.path.join(HERE, '..', 'scripts', 'verify_quotes.py')

SOURCE = """The Phase 3 trial enrolled 1,847 patients across 42 sites.
Mortality decreased by 23% (p<0.01) in the treatment group compared with placebo,
while serious adverse events were similar between arms. The authors caution that
follow-up was limited to twelve months and that the population was predominantly
male, which may limit generalisability to other groups."""


class TestMatch(unittest.TestCase):

    def setUp(self):
        self.src = normalize(SOURCE)

    def test_verbatim(self):
        self.assertEqual(match_quote('Mortality decreased by 23% (p<0.01) in the treatment group', self.src)[0], 'verbatim')

    def test_typographic_noise_is_verbatim(self):
        q = 'The authors caution that follow\u2010up was limited to twelve months'
        self.assertEqual(match_quote(q, self.src)[0], 'verbatim')

    def test_elision_is_near(self):
        q = ('The authors caution that follow-up was limited to twelve months ... '
             'which may limit generalisability to other groups')
        self.assertIn(match_quote(q, self.src)[0], ('near', 'verbatim'))

    def test_altered_number_is_missing(self):
        q = 'Mortality decreased by 32% (p<0.01) in the treatment group compared with placebo'
        self.assertEqual(match_quote(q, self.src)[0], 'missing')

    def test_altered_number_at_quote_edge_is_missing(self):
        # Only the first shingle differs, so shingle coverage alone would say 'near'
        q = 'The Phase 3 trial enrolled 1,874 patients across 42 sites and many more words follow here'
        src = normalize('The Phase 3 trial enrolled 1,847 patients across 42 sites and many more words follow here')
        self.assertEqual(match_quote(q.replace('1,874 patients across', '1,847 patients across'), src)[0], 'verbatim')
        self.assertEqual(match_quote('trial enrolled 1,847 patients across 42 sites and many more words follow '
                                     'here 7', src)[0], 'missing')

    def test_paraphrase_is_missing(self):
        q = 'Deaths fell by roughly a quarter for patients receiving the drug versus placebo'
        self.assertEqual(match_quote(q, self.src)[0], 'missing')

    def test_short_quote_whole_words(self):
        self.assertEqual(match_quote('42 sites', self.src)[0], 'verbatim')
        self.assertEqual(match_quote('2 sites', self.src)[0], 'missing')

    def test_empty_quote(self):
        self.assertEqual(match_quote('   ', self.src)[0], 'missing')


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        ev = [
            {'evidence_id': 'e1', 'source_id': 's1', 'evidence_type': 'direct_quote',
             'quote': 'The Phase 3 trial enrolled 1,847 patients across 42 sites.'},
            {'evidence_id': 'e2', 'source_id': 's1', 'evidence_type': 'direct_quote',
             'quote': 'The Phase 3 trial enrolled 2,500 patients across 42 sites.'},
            {'evidence_id': 'e3', 'source_id': 's1', 'evidence_type': 'paraphrase', 'quote': 'about 1.8k people'},
            {'evidence_id': 'e4', 'source_id': 's2', 'evidence_type': 'data_point', 'quote': 'anything'},
        ]
        with open(os.path.join(self.d, 'evidence.jsonl'), 'w', encoding='utf-8') as f:
            for e in ev:
                f.write(json.dumps(e) + '\n')

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def run_vq(self, *args, stdin=None):
        r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding='utf-8', input=stdin)
        return r.returncode, r.stdout

    def test_flow(self):
        rc, out = self.run_vq('snapshot', '--dir', self.d, '--source-id', 's1', '--origin', 'test', stdin=SOURCE)
        self.assertEqual(rc, 0, out)
        rc, out = self.run_vq('verify', '--dir', self.d)
        self.assertEqual(rc, 0, out)
        data = json.loads(out)
        self.assertEqual(data['missing_evidence_ids'], ['e2'])
        self.assertEqual(data['counts'].get('not_checked'), 1)
        self.assertEqual(data['counts'].get('no_snapshot'), 1)
        rc, out = self.run_vq('verify', '--dir', self.d, '--strict')
        self.assertEqual(rc, 1)
        with open(os.path.join(self.d, 'quote_checks.jsonl'), encoding='utf-8') as f:
            rows = {r['evidence_id']: r for r in map(json.loads, f)}
        self.assertEqual(rows['e2'].get('reason'), 'number_not_in_passage')
        self.assertNotIn('reason', rows['e1'])

    def test_rejects_path_traversal_source_id(self):
        rc, _ = self.run_vq('snapshot', '--dir', self.d, '--source-id', '../evil', stdin='x')
        self.assertEqual(rc, 2)

    def test_rejects_empty_snapshot(self):
        rc, _ = self.run_vq('snapshot', '--dir', self.d, '--source-id', 's9', stdin='   ')
        self.assertEqual(rc, 2)


if __name__ == '__main__':
    unittest.main()


class TestFingerprintFallback(unittest.TestCase):
    """OCR/PDF text layers: hyphenation, ligatures and collapsed spaces."""

    SRC = normalize('The investigators reported that the treat-\nment reduced hospitali sations by '
                    'twentythree percent overall, with 123 serious events recorded in the control arm of the main trial.')

    def test_collapsed_spaces_match(self):
        q = 'the treatment reduced hospitalisations by twenty three percent overall'
        self.assertEqual(match_quote(q, self.SRC)[0], 'near')

    def test_number_inside_bigger_number_does_not_match(self):
        # "23 serious events..." is a fingerprint substring of "123 serious events..."
        q = '23 serious events recorded in the control arm of the main trial'
        self.assertEqual(match_quote(q, self.SRC)[0], 'missing')

    def test_short_quotes_do_not_use_fingerprint(self):
        # 6+ words (shingle path) but only 20 alphanumeric chars: below FINGERPRINT_MIN
        src = normalize('thecat saton themat now')
        self.assertEqual(match_quote('the cat sat on the mat now', src)[0], 'missing')


_BODY = ("the regional health authority reported that over the course of the winter season hospital "
         "admissions for respiratory illness among adults aged sixty five and older rose by {n} percent "
         "compared with the same period one year earlier according to figures released by the ministry "
         "on monday morning in the capital city after a lengthy review of all regional data sources")


class TestNearIsNotLoose(unittest.TestCase):
    """'near' tolerates small edits, never a changed number, a flipped
    negation or an elision that changes what the source says."""

    def test_altered_number_fingerprint_path(self):
        # "15" -> "1.5"; 1.5 occurs elsewhere in the source, the fingerprint is identical
        src = normalize('In its annual filing the company said revenue rose 15 billion dollars last year overall. '
                        'The debt ratio stood at 1.5 at year end.')
        q = 'the company said revenue rose 1.5 billion dollars last year overall'
        self.assertEqual(match_quote(q, src)[0], 'missing')

    def test_altered_number_shingle_path(self):
        # 12 -> 15; 15 occurs elsewhere in the source
        src = normalize(_BODY.format(n=12) + '. Separately, staffing levels fell 15 percent.')
        self.assertEqual(match_quote(_BODY.format(n=15), src)[0], 'missing')

    def test_inserted_negation_is_missing(self):
        src = normalize(_BODY.format(n=12))
        q = _BODY.format(n=12).replace('rose by', 'did not rise by')
        self.assertEqual(match_quote(q, src)[0], 'missing')

    def test_dropped_negation_is_missing(self):
        src = normalize(_BODY.format(n=12).replace('rose by', 'did not rise by'))
        q = _BODY.format(n=12).replace('rose by', 'did rise by')
        self.assertEqual(match_quote(q, src)[0], 'missing')

    def test_contraction_equals_not(self):
        src = normalize(_BODY.format(n=12).replace('rose by', 'did not rise by'))
        q = _BODY.format(n=12).replace('rose by', "didn't rise by")
        self.assertEqual(match_quote(q, src)[0], 'near')

    def test_small_edit_without_number_or_negation_change_is_near(self):
        src = normalize(_BODY.format(n=12))
        q = _BODY.format(n=12).replace('lengthy review', 'long review')
        self.assertEqual(match_quote(q, src)[0], 'near')

    def test_elision_dropping_negation_is_missing(self):
        src = normalize('The trial found that the vaccine was not effective against severe disease in older adults.')
        level, _, reason = match_quote_detail('the vaccine was ... effective against severe disease', src)
        self.assertEqual(level, 'missing')
        self.assertIn('negation', reason)

    def test_elision_stitching_sentences_is_missing(self):
        src = normalize('Smoking is associated with many outcomes. Exercise reduces risk. Lung cancer is common.')
        self.assertEqual(match_quote('Smoking ... reduces risk ... lung cancer', src)[0], 'missing')

    def test_elision_across_sentence_marked_in_quote_is_near(self):
        src = normalize('Smoking is associated with many outcomes. Exercise reduces risk. Lung cancer is common.')
        q = 'Smoking is associated with many outcomes. ... Lung cancer is common.'
        self.assertEqual(match_quote(q, src)[0], 'near')

    def test_elision_out_of_order_is_missing(self):
        src = normalize(SOURCE)
        q = ('which may limit generalisability to other groups ... '
             'The authors caution that follow-up was limited to twelve months')
        self.assertEqual(match_quote(q, src)[0], 'missing')

    def test_elision_gap_too_long_is_missing(self):
        filler = ' '.join(f'word{i}' for i in range(120))
        src = normalize(f'The first fragment is here {filler} and the second fragment is there.')
        self.assertEqual(match_quote('The first fragment is here ... the second fragment is there', src)[0], 'missing')
        src_close = normalize('The first fragment is here and then the second fragment is there.')
        self.assertEqual(match_quote('The first fragment is here ... the second fragment is there', src_close)[0], 'near')

    def test_stitched_without_ellipsis_is_missing(self):
        # 20 words from one passage + 20 from a distant one, no "...": global
        # shingle coverage is 30/35 (>= 85%), but no single passage supports it.
        a = ('alpha bravo charlie delta echo foxtrot golf hotel india juliet '
             'kilo lima mike november oscar papa quebec romeo sierra tango')
        b = ('amber basil cedar dahlia ember fennel garnet hazel iris jasper '
             'kelp lotus maple nutmeg olive pepper quartz rowan sage thyme')
        filler = ' '.join(f'word{i}' for i in range(200))
        src = normalize(f'{a} uniform victor. {filler}. {b} umber violet.')
        self.assertEqual(match_quote(f'{a} {b}', src)[0], 'missing')
        self.assertEqual(match_quote(f'{a} uniform victor', src)[0], 'verbatim')

    def test_verbatim_unchanged(self):
        src = normalize(SOURCE)
        self.assertEqual(match_quote_detail('Mortality decreased by 23% (p<0.01)', src), ('verbatim', 1.0, None))
