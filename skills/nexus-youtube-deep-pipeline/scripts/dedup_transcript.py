#!/usr/bin/env python3
"""
Sliding-window transcript dedup.

Removes the YouTube auto-transcription artefact where each line has 3 overlapping
copies of the same content with variable stride. Implements the 4-step algorithm
described in references/transcript-triplication-dedup.md.

Usage:
    python3 dedup_transcript.py --raw PATH [--output PATH]
    cat raw.md | python3 dedup_transcript.py --stdin
"""

import argparse
import re
import sys


def tokenize(line):
    """Tokenize a line into atomic sentence-like units ending in .!? or [tag]."""
    tokens = []
    i = 0
    n = len(line)
    while i < n:
        while i < n and line[i] == ' ':
            i += 1
        if i >= n:
            break
        if line[i] == '[':
            j = line.find(']', i)
            if j != -1:
                tokens.append(line[i:j+1])
                i = j + 1
                continue
        j = i
        while j < n and line[j] not in '.!?[':
            j += 1
        if j < n and line[j] in '.!?':
            tokens.append(line[i:j+1])
            i = j + 1
        else:
            rest = line[i:].strip()
            if rest:
                tokens.append(rest)
            i = n
    return tokens


def dedup_line(line):
    """Remove consecutive identical tokens within a single line."""
    toks = tokenize(line)
    if not toks:
        return ""
    out = []
    i = 0
    n = len(toks)
    while i < n:
        if i + 2 < n and toks[i] == toks[i+1] == toks[i+2]:
            out.append(toks[i])
            i += 3
        elif i + 1 < n and toks[i] == toks[i+1]:
            out.append(toks[i])
            i += 2
        else:
            out.append(toks[i])
            i += 1
    return " ".join(out)


def clean_internal_repetition(s):
    """If a sentence still has X X X internal repetition, extract one copy."""
    n = len(s)
    if n < 30:
        return s
    for p in range(1, n // 3 + 1):
        chunk = s[:p]
        if s == (chunk * 3)[:n]:
            return chunk.strip()
        if s.startswith(chunk) and s[p:].startswith(chunk) and s[2*p:].startswith(chunk):
            return chunk.strip()
    return s


def main():
    parser = argparse.ArgumentParser(description="Dedupe YouTube transcript sliding-window artefact")
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

    # Skip frontmatter (between --- markers at top of file)
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            frontmatter = text[:end + 3]
            text = text[end + 3:]
        else:
            frontmatter = ""
    else:
        frontmatter = ""

    # Step 1+2: per-line tokenize and dedupe
    lines = text.splitlines()
    per_line = []
    all_sents = []
    for line in lines:
        cleaned = dedup_line(line)
        if cleaned.strip():
            per_line.append(cleaned)
            for sent in tokenize(line):
                if sent.strip():
                    all_sents.append(sent.strip())

    # Step 3: global dedup
    seen = set()
    unique_sents = []
    for s in all_sents:
        if s not in seen:
            seen.add(s)
            unique_sents.append(s)

    # Step 4: cleanup residual internal repetition
    final_sents = [clean_internal_repetition(s) for s in unique_sents]
    final_sents = [s for s in final_sents if s.strip()]

    output = "\n".join(final_sents)

    if frontmatter:
        output = frontmatter + "\n" + output

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Cleaned: {len(text)} -> {len(output)} chars ({100*len(output)//len(text)}%)", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
