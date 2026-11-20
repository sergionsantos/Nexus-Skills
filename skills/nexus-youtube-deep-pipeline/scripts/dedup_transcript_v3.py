#!/usr/bin/env python3
"""
Sliding-window transcript dedup v3.

Removes the YouTube auto-transcription artefact where each "logical sentence"
appears 3 times with overlapping sliding windows. Works on lines without
terminal punctuation by detecting longest matching 3-consecutive identical chunks.

Algorithm:
1. For each line, find longest chunks (length 12-80) that appear 3 times
   consecutively with EXACT match.
2. Remove 2nd and 3rd copies (keep first).
3. After 3-dedup, repeat for 2-consecutive identical chunks (in case any remain).
4. Apply global sentence-level dedup to remove residual exact duplicates.

Usage:
    python3 dedup_transcript_v3.py --raw PATH [--output PATH]
    cat raw.md | python3 dedup_transcript_v3.py --stdin
"""

import argparse
import re
import sys


def find_repeated_chunks(line, min_L=12, max_L=80, min_count=3):
    """Find all positions where min_count consecutive identical chunks of length L appear."""
    n = len(line)
    chunks = []
    for L in range(max_L, min_L - 1, -1):
        i = 0
        while i <= n - min_count * L:
            identical = True
            for j in range(1, min_count):
                if line[i:i+L] != line[i + j*L:i + (j+1)*L]:
                    identical = False
                    break
            if identical:
                chunks.append((i, L, min_count))
                i += min_count * L
            else:
                i += 1
    chunks.sort()
    return chunks


def find_repeated_pair(line, min_L=12, max_L=200):
    """Find positions where 2 consecutive identical chunks appear."""
    n = len(line)
    chunks = []
    for L in range(max_L, min_L - 1, -1):
        i = 0
        while i <= n - 2 * L:
            if line[i:i+L] == line[i+L:i+2*L]:
                chunks.append((i, L))
                i += 2 * L
            else:
                i += 1
    chunks.sort()
    return chunks


def dedupe_line(line, min_count=3):
    """Iteratively remove min_count+ consecutive identical chunks."""
    # Phase 1: remove 3+ consecutive identical chunks (greedy, longest first)
    for _ in range(50):
        chunks = find_repeated_chunks(line, min_count=min_count)
        if not chunks:
            break
        new = ""
        prev_end = 0
        for start, L, _ in chunks:
            new += line[prev_end:start + L]
            prev_end = start + min_count * L
        new += line[prev_end:]
        if new == line:
            break
        line = new
    # Phase 2: remove 2 consecutive identical chunks (after 3-dedup may leave pairs)
    for _ in range(50):
        chunks = find_repeated_pair(line)
        if not chunks:
            break
        new = ""
        prev_end = 0
        for start, L in chunks:
            new += line[prev_end:start + L]
            prev_end = start + 2 * L
        new += line[prev_end:]
        if new == line:
            break
        line = new
    return line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", help="Path to raw transcript file")
    parser.add_argument("--output", help="Path to write cleaned output (default: stdout)")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.raw:
        with open(args.raw, encoding="utf-8") as f:
            text = f.read()
    else:
        print("ERROR: must specify --raw or --stdin", file=sys.stderr)
        sys.exit(1)

    frontmatter = ""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            frontmatter = text[:end + 3]
            text = text[end + 3:]

    lines = text.splitlines()

    # Per-line dedup
    cleaned = []
    for line in lines:
        result = dedupe_line(line)
        if result.strip():
            cleaned.append(result)

    output = "\n".join(cleaned)

    if frontmatter:
        output = frontmatter + "\n" + output

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        if len(text):
            reduction = 100 * (1 - len(output) / len(text))
            print(f"Cleaned: {len(text)} -> {len(output)} chars ({reduction:.0f}% reduction)", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
