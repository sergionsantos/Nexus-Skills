import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "vtt_to_raw.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import vtt_to_raw  # noqa: E402

VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.480 --> 00:00:02.310 align:start position:0%
hello and welcome<00:00:01.000><c> to the</c><00:00:01.500><c> show</c>

00:00:02.310 --> 00:00:02.320 align:start position:0%
hello and welcome to the show
 

00:00:02.320 --> 00:00:05.000 align:start position:0%
hello and welcome to the show
today we talk &amp; learn

00:00:50.000 --> 00:00:52.000
second block here

00:01:40.000 --> 00:01:42.000
third block
"""


class VttToRaw(unittest.TestCase):
    def test_rolling_cues_deduped_and_tags_stripped(self):
        out = vtt_to_raw.convert(VTT)
        self.assertEqual(out.count("hello and welcome to the show"), 1)
        self.assertIn("today we talk & learn", out)
        self.assertNotIn("<", out)

    def test_headings_every_window(self):
        out = vtt_to_raw.convert(VTT)
        heads = [l for l in out.splitlines() if l.startswith("### [")]
        self.assertEqual(heads, ["### [00:00]", "### [00:50]", "### [01:40]"])

    def test_hour_stamp_and_cli_roundtrip(self):
        vtt = "WEBVTT\n\n01:02:03.000 --> 01:02:05.000\nlate line\n"
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "a.vtt"), os.path.join(d, "a.md")
            with open(src, "w", encoding="utf-8") as f:
                f.write(vtt)
            r = subprocess.run([sys.executable, SCRIPT, "--vtt", src, "--output", dst],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(dst, encoding="utf-8") as f:
                self.assertIn("### [1:02:03]", f.read())


if __name__ == "__main__":
    unittest.main()
