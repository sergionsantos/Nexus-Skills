#!/usr/bin/env python3
"""
Sliding-window transcript dedup v2.

Removes the YouTube auto-transcription artefact where each "logical sentence"
appears 3 times with overlapping sliding windows. Works on lines without
terminal punctuation.

Algorithm:
1. For each line, find the smallest period p where 3 chunks of length p appear
   consecutively with high similarity (>= 80% char match).
2. If found, extract first chunk + everything after position 3*p.
3. Apply global sentence-level dedup (overlap-aware exact match).
4. Apply final cleanup for residual internal repetition.

Usage:
    python3 dedup_transcript_v2.py --raw PATH [--output PATH]
    cat raw.md | python3 dedup_transcript_v2.py --stdin
"""

import argparse
import re
import sys


def detect_sliding_triple(line, min_p=20, max_p=400, threshold=0.80):
    """Find smallest period p such that 3 chunks of length p appear consecutively in line."""
    n = len(line)
    if n < min_p * 3:
        return None
    for p in range(min_p, min(max_p, n // 2) + 1):
        if 3 * p > n + min_p:
            break
        # Compute chunk lengths (last one may be shorter)
        L0 = min(p, n)
        L1 = min(p, max(0, n - p))
        L2 = min(p, max(0, n - 2 * p))
        if L1 < min_p // 2 or L2 < min_p // 2:
            continue
        c0 = line[:L0]
        c1 = line[p:p + L1]
        c2 = line[2 * p:2 * p + L2]
        ref = min(L0, L1, L2)
        match1 = sum(1 for i in range(ref) if c0[i] == c1[i])
        match2 = sum(1 for i in range(ref) if c0[i] == c2[i])
        if match1 >= threshold * ref and match2 >= threshold * ref:
            return p
    return None


def dedupe_line_sliding(line):
    """Detect 3x sliding repetition and extract 1 chunk + remainder."""
    p = detect_sliding_triple(line)
    if not p:
        return line
    # Extract first chunk + everything past the 3rd chunk
    # Cap remainder to avoid runaway if line had MORE than 3 repetitions
    # We detect 3 repetitions minimum; check if there's a 4th
    chunk = line[:p]
    remainder = line[3 * p:].strip()
    # Check if remainder itself is a sliding triple (extending)
    if len(remainder) > p * 2 and detect_sliding_triple(remainder):
        return chunk.strip()
    return chunk.strip() + ((" " + remainder) if remainder else "")


def dedupe_global(sentences):
    """Dedupe adjacent identical sentences; keep sliding-window variants as one."""
    seen_exact = set()
    seen_normalized = set()
    out = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # Normalize: lowercase, collapse whitespace, strip trailing punct
        norm = re.sub(r'\s+', ' ', s.lower()).rstrip('.!?')
        if norm in seen_normalized:
            continue
        seen_normalized.add(norm)
        out.append(s)
    return out


def clean_internal_repetition(s):
    """If a sentence still has X X X internal repetition, try to compress."""
    n = len(s)
    if n < 30:
        return s
    for p in range(20, n // 3 + 5):
        if 3 * p > n + 20:
            break
        chunk = s[:p]
        if not chunk.strip():
            continue
        # Check pure 3x repetition
        repeated = (chunk + " ") * 3
        if repeated[:n] == s[:n] or s.replace("  ", " ").startswith((chunk + " ") * 3):
            return chunk.strip()
        # Check overlapping 3 chunks
        if (s.startswith(chunk) and
            s[p:].startswith(chunk) and
            s[2 * p:].startswith(chunk)):
            return chunk.strip()
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", help="Path to raw transcript file")
    parser.add_argument("--output", help="Path to write cleaned output (default: stdout)")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.raw:
        with open(args.raw) as f:
            text = f.read()
    else:
        print("ERROR: must specify --raw or --stdin", file=sys.stderr)
        sys.exit(1)

    # Skip frontmatter
    frontmatter = ""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            frontmatter = text[:end + 3]
            text = text[end + 3:]

    lines = text.splitlines()

    # Step 1: Per-line sliding-window dedup
    cleaned_lines = []
    for line in lines:
        result = dedupe_line_sliding(line)
        if result.strip():
            cleaned_lines.append(result)

    # Step 2: Global sentence-level dedup
    # Use simple split on double-space or sentence boundary markers
    all_text = "\n".join(cleaned_lines)
    # Split on consecutive whitespace including newlines
    chunks = re.split(r'[\n]+', all_text)
    sentences = []
    for chunk in chunks:
        # Further split on sentence-end punctuation + space
        parts = re.split(r'(?<=[.!?])\s+', chunk.strip())
        for p in parts:
            p = p.strip()
            if p:
                sentences.append(p)

    # Step 3: Global dedup with normalization
    unique = dedupe_global(sentences)

    # Step 4: Final cleanup of residual internal repetition
    final = [clean_internal_repetition(s) for s in unique]
    final = [s for s in final if s.strip()]

    output = "\n".join(final)

    if frontmatter:
        output = frontmatter + "\n" + output

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        reduction = 100 * (1 - len(output) / len(text)) if len(text) else 0
        print(f"Cleaned: {len(text)} -> {len(output)} chars ({reduction:.0f}% reduction)", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
