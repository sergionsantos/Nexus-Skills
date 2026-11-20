#!/usr/bin/env python3
"""
Convert a yt-dlp .vtt subtitle file into the raw transcript format this skill
expects: UTF-8 text with `### [mm:ss]` headings every ~45 s (h:mm:ss from one
hour on), each followed by one paragraph of transcript text.

Rolling auto-captions repeat the previous cue's last line as the first line of
the next cue; consecutive identical lines are dropped here. The sliding-window
overlap that remains is handled by dedup_transcript_v3.py (Step 2).

Usage:
    python3 vtt_to_raw.py --vtt IN.en.vtt --output RAW.md [--window 45]
"""

import argparse
import html
import re
import sys

TIME = re.compile(
    r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,]\d{3}\s*-->\s*(?:\d+:)?\d{1,2}:\d{2}[.,]\d{3}")
TAG = re.compile(r"<[^>]*>")


def _stamp(sec):
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def parse_cues(text):
    """Yield (start_seconds, [clean text lines]) for each cue."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines):
        m = TIME.match(lines[i])
        if not m:
            i += 1
            continue
        start = int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        i += 1
        body = []
        while i < len(lines) and lines[i].strip():
            clean = html.unescape(TAG.sub("", lines[i])).strip()
            clean = re.sub(r"\s+", " ", clean)
            if clean:
                body.append(clean)
            i += 1
        yield start, body


def convert(text, window=45):
    sections = []  # (start, [lines])
    prev = None
    for start, body in parse_cues(text):
        for line in body:
            if line == prev:
                continue
            prev = line
            if not sections or start - sections[-1][0] >= window:
                sections.append((start, []))
            sections[-1][1].append(line)
    out = []
    for start, body in sections:
        out.append(f"### [{_stamp(start)}]\n\n{' '.join(body)}\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="yt-dlp .vtt -> raw transcript with ### [mm:ss] headings")
    ap.add_argument("--vtt", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--window", type=int, default=45, help="seconds per heading (default 45)")
    a = ap.parse_args()
    with open(a.vtt, encoding="utf-8") as f:
        raw = convert(f.read(), a.window)
    if not raw.strip():
        print("ERROR: no cues found in VTT", file=sys.stderr)
        return 1
    with open(a.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(raw)
    print(f"wrote {a.output} ({len(raw)} chars)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
