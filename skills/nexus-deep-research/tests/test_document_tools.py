#!/usr/bin/env python3
"""Smoke tests for the scripts adopted from necopinus/hermes-skill-deep-research:
extract_office_text.py (docx/pptx -> heading-safe markdown) and verify_pdf_text.py."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(__file__)
EXTRACT = os.path.join(HERE, '..', 'scripts', 'extract_office_text.py')
VERIFY_PDF = os.path.join(HERE, '..', 'scripts', 'verify_pdf_text.py')

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'


def make_docx(path, paragraphs):
    body = ''.join(f'<w:p><w:r><w:t>{p}</w:t></w:r></w:p>' for p in paragraphs)
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('word/document.xml', f'<w:document {W}><w:body>{body}</w:body></w:document>')


def make_pptx(path, slides, notes=None):
    notes = notes or {}
    with zipfile.ZipFile(path, 'w') as z:
        for n, text in enumerate(slides, 1):
            z.writestr(f'ppt/slides/slide{n}.xml', f'<p:sld {A}><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:sld>')
            if n in notes:
                z.writestr(f'ppt/slides/_rels/slide{n}.xml.rels',
                           f'<Relationships><Relationship Target="../notesSlides/notesSlide{n}.xml"/></Relationships>')
                z.writestr(f'ppt/notesSlides/notesSlide{n}.xml',
                           f'<p:notes {A}><a:p><a:r><a:t>{notes[n]}</a:t></a:r></a:p></p:notes>')


def make_pdf(path, text):
    """Minimal single-page PDF with one Helvetica text line (valid xref)."""
    stream = f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'.encode('latin-1')
    objs = [b'<< /Type /Catalog /Pages 2 0 R >>',
            b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R '
            b'/Resources << /Font << /F1 5 0 R >> >> >>',
            b'<< /Length %d >>\nstream\n' % len(stream) + stream + b'\nendstream',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    out, offsets = bytearray(b'%PDF-1.4\n'), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b'%d 0 obj\n' % i + body + b'\nendobj\n'
    xref = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objs) + 1)
    out += b''.join(b'%010d 00000 n \n' % o for o in offsets)
    out += b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objs) + 1, xref)
    with open(path, 'wb') as f:
        f.write(bytes(out))


class TestExtractOffice(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def run_extract(self, *srcs):
        out = os.path.join(self.d, 'out')
        r = subprocess.run([sys.executable, EXTRACT, *srcs, '--out', out], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 0, r.stderr)
        return out

    def test_docx_text_and_heading_safety(self):
        src = os.path.join(self.d, 'Report Q3.docx')
        make_docx(src, ['Revenue grew 12% in 2024.', '# not a heading', '--', 'Ação e informação.'])
        with open(os.path.join(self.run_extract(src), 'Report_Q3.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertIn('Revenue grew 12% in 2024.', md)
        self.assertIn('\\# not a heading', md)   # escaped, cannot become a heading
        self.assertIn('\\--', md)                # short rule escaped, cannot be a setext underline
        self.assertIn('Ação e informação.', md)  # UTF-8 preserved

    def test_pptx_slides_and_notes(self):
        src = os.path.join(self.d, 'deck.pptx')
        make_pptx(src, ['Agenda', 'Results'], notes={2: 'Mention the 1,847 patients.'})
        with open(os.path.join(self.run_extract(src), 'deck.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertIn('## Slide 1', md)
        self.assertIn('## Slide 2', md)
        self.assertIn('### Speaker notes', md)
        self.assertIn('Mention the 1,847 patients.', md)
        self.assertEqual(md.count('### Speaker notes'), 1)

    def write_docx_xml(self, name, body):
        src = os.path.join(self.d, name)
        with zipfile.ZipFile(src, 'w') as z:
            z.writestr('word/document.xml', f'<w:document {W}><w:body>{body}</w:body></w:document>')
        return src

    def test_docx_multi_run_paragraph_is_clean_text(self):
        # nexus: <w:tab/> matched the old r'<w:t[^>]*>' run pattern and leaked raw XML
        body = ('<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="720"/></w:tabs></w:pPr>'
                '<w:r><w:t>Total</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>42 units</w:t></w:r></w:p>'
                '<w:p><w:r><w:t>Rev</w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>enue</w:t></w:r>'
                '<w:r><w:t xml:space="preserve"> grew &amp; held</w:t></w:r></w:p>'
                '<w:p><w:r><w:t>Line one</w:t><w:br/><w:t>Line two</w:t></w:r></w:p>'
                '<w:p><w:r><w:t>Intro</w:t><w:br/><w:t># fake heading</w:t></w:r></w:p>'
                '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cell</w:t></w:r><w:r><w:t>Text</w:t></w:r></w:p>'
                '</w:tc></w:tr></w:tbl>'
                '<w:p><w:r><w:t>Outer</w:t><w:pict><w:txbxContent><w:p><w:r><w:t>Boxed</w:t></w:r></w:p>'
                '</w:txbxContent></w:pict></w:r></w:p>')
        src = self.write_docx_xml('runs.docx', body)
        with open(os.path.join(self.run_extract(src), 'runs.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertNotIn('<w:', md)
        self.assertNotIn('</w:', md)
        self.assertIn('Total 42 units', md)        # w:tab -> space; tab-stop defs ignored
        self.assertIn('Revenue grew & held', md)  # runs concatenated, entities decoded
        self.assertIn('Line one\nLine two', md)    # w:br -> newline
        self.assertIn('Intro\n\\# fake heading', md)  # a w:br line cannot become a heading
        self.assertIn('CellText', md)              # table paragraphs extracted
        self.assertEqual(md.count('Boxed'), 1)     # text-box paragraph emitted once, on its own
        self.assertNotIn('OuterBoxed', md)

    def test_docx_reproducer_namespace_prefix_only(self):
        # Reproducer r05 used a non-standard namespace URI bound to the w: prefix
        src = os.path.join(self.d, 'a.docx')
        with zipfile.ZipFile(src, 'w') as z:
            z.writestr('word/document.xml',
                       '<?xml version="1.0"?><w:document xmlns:w="x"><w:body>'
                       '<w:p><w:r><w:t>Total</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>42 units</w:t></w:r></w:p>'
                       '</w:body></w:document>')
        with open(os.path.join(self.run_extract(src), 'a.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertEqual(md.splitlines()[-1], 'Total 42 units')

    def test_pptx_images_skip_missing_and_external_media(self):
        src = os.path.join(self.d, 'pics.pptx')
        with zipfile.ZipFile(src, 'w') as z:
            z.writestr('ppt/slides/slide1.xml', f'<p:sld {A}><a:p><a:r><a:t>Hello</a:t></a:r></a:p></p:sld>')
            z.writestr('ppt/slides/_rels/slide1.xml.rels',
                       '<Relationships>'
                       '<Relationship Id="rId1" Target="../media/present.png"/>'
                       '<Relationship Id="rId2" Target="../media/gone.png"/>'
                       '<Relationship Id="rId3" Target="https://cdn.example.com/media/logo.png" '
                       'TargetMode="External"/></Relationships>')
            z.writestr('ppt/media/present.png', b'PNGDATA')
            # same basename as the external link: must not be misattributed to the slide
            z.writestr('ppt/media/logo.png', b'LOCALLOGO')
        out = os.path.join(self.d, 'out')
        r = subprocess.run([sys.executable, EXTRACT, src, '--out', out, '--images'],
                           capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('gone.png', r.stderr)
        self.assertIn('logo.png', r.stderr)
        with open(os.path.join(out, 'images', 'pics', 'slide_001_present.png'), 'rb') as f:
            self.assertEqual(f.read(), b'PNGDATA')
        self.assertFalse(os.path.exists(os.path.join(out, 'images', 'pics', 'slide_001_gone.png')))
        self.assertFalse(os.path.exists(os.path.join(out, 'images', 'pics', 'slide_001_logo.png')))
        with open(os.path.join(out, 'images', 'MANIFEST.md'), encoding='utf-8') as f:
            manifest = f.read()
        self.assertIn('slide_001_present.png', manifest)
        self.assertNotIn('slide_001_gone.png', manifest)


class TestFusedWordHeuristic(unittest.TestCase):
    """Unit tests for verify_pdf_text's fused-word detector (no pdftotext needed)."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
        import verify_pdf_text
        cls.vpt = verify_pdf_text

    @unittest.skipUnless(os.path.exists('/usr/share/dict/words'), 'no system word list')
    def test_common_english_compounds_not_flagged(self):
        # nexus: reproducer r05 (c) — every one of these was reported as fused
        text = ('The newspaper reported that everybody in the courthouse saw firsthand how groundwater '
                'contamination spread; from this standpoint the storyboard was clear.')
        self.assertEqual(self.vpt.check_run_together(text), [])

    @unittest.skipUnless(os.path.exists('/usr/share/dict/words'), 'no system word list')
    def test_inflected_compounds_not_flagged(self):
        self.assertEqual(self.vpt.check_run_together('newspapers storyboards standpoints courthouses'), [])
        # web2 lists 'understate'/'overstate' but not their -s forms, which split
        # into common words ('under'+'states'); the plural must still count as a word
        self.assertEqual(self.vpt.check_run_together('it understates and overstates'), [])

    @unittest.skipUnless(os.path.exists('/usr/share/dict/words'), 'no system word list')
    def test_only_plural_inflections_are_stripped(self):
        # 'mostlike'/'allwork' are web2 words; stripping -ly/-ing would hide these fusions
        flagged = self.vpt.check_run_together('it is mostlikely that allworking stops')
        self.assertIn('mostlikely', flagged)
        self.assertIn('allworking', flagged)

    def test_without_word_list_halves_stay_four_chars(self):
        # fallback keeps the original precision-first rule
        self.assertFalse(self.vpt.looks_fused('thereport', dictionary=frozenset()))
        self.assertTrue(self.vpt.looks_fused('thereport', dictionary=frozenset({'report'})))

    def test_dictionary_membership_is_the_gate(self):
        self.assertTrue(self.vpt.looks_fused('newspaper', dictionary=frozenset()))
        self.assertFalse(self.vpt.looks_fused('newspaper', dictionary=frozenset({'newspaper'})))
        self.assertFalse(self.vpt.looks_fused('newspapers', dictionary=frozenset({'newspaper'})))

    @unittest.skipUnless(any(os.path.exists(p) for p in ('/usr/share/dict/words', '/usr/share/dict/american-english')),
                         'needs a system word list (/usr/share/dict)')
    def test_real_run_together_text_still_flagged(self):
        flagged = self.vpt.check_run_together('The reportshows growth and the researchshows more; '
                                              'see thereport for details.')
        for token in ('reportshows', 'researchshows', 'thereport'):
            self.assertIn(token, flagged)

    def test_hard_ceiling_still_flags_long_fusions(self):
        fused = 'thetrialenrolledmanypatientsacrossseveralsites'
        self.assertIn(fused, self.vpt.check_run_together(f'Intro {fused} outro'))

    @unittest.skipUnless(os.path.exists('/usr/share/dict/words'), 'no system word list')
    def test_hard_ceiling_dictionary_words_vs_fused_phrases(self):
        # a >20-char single dictionary word is legitimate ...
        self.assertEqual(self.vpt.check_run_together('see anthropomorphologically here'), [])
        # ... but a multi-word phrase with its spaces lost is an artifact (web2a lists
        # 'activated sludge process' as a phrase; it must not whitelist the fusion)
        self.assertIn('activatedsludgeprocess',
                      self.vpt.check_run_together('see activatedsludgeprocess here'))


@unittest.skipUnless(shutil.which('pdftotext'), 'pdftotext not installed')
class TestVerifyPdfText(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def check(self, text, *flags):
        path = os.path.join(self.d, 'r.pdf')
        make_pdf(path, text)
        return subprocess.run([sys.executable, VERIFY_PDF, '--pdf', path, *flags], capture_output=True, text=True, encoding='utf-8')

    def test_clean_text_passes(self):
        r = self.check('The trial enrolled many patients across several sites and reported the main outcome '
                       'with a clear method that other teams can repeat in the same way.')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_run_together_words_fail(self):
        fused = 'Thetrialenrolledmanypatientsacrossseveralsitesandreportedthemainoutcome'
        r = self.check(' '.join([fused] * 6), '--strict')
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_missing_file_is_error(self):
        r = subprocess.run([sys.executable, VERIFY_PDF, '--pdf', os.path.join(self.d, 'nope.pdf')],
                           capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
