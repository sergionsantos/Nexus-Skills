#!/usr/bin/env python3
"""
Mechanical fact-check of a deep knowledge document against its cleaned transcript.

Every quoted passage and every number in the draft is looked up in the
transcript. Nothing is sampled and nothing is guessed: what the transcript
does not contain is reported, with its line in the draft.

Usage:
    python3 fact_check.py --draft DRAFT --cleaned-transcript TRANSCRIPT [--report REPORT.json]

Exit code: 0 = every quote and number found; 1 = something is missing or
unmatched (listed on stdout); 2 = bad input.

What it checks
  Quotes   Text inside "..." / “...” / «...» of >= 4 words. `exact` = verbatim
           substring (case, punctuation and accents ignored); `near` = >= 80% of
           its 4-word runs occur in the transcript (ASR drift, a dropped word);
           `missing` = anything less. Fragments split by "..." / "…" are checked
           independently. [bracketed insertions] inside a quote are ignored.
  Numbers  Every figure of 2+ digits, or with %, $, a decimal or a k/M/B suffix,
           compared by VALUE: 250k = 250,000 = "250 thousand" = "250 mil"; 1M =
           "1 million" = "1 milhão" = "a million"; 93% = "93 percent"; "nine"
           matches 9. PT decimals (5,5) and thousands (250.000) are normalised.

Known ceilings (deliberate)
  * Proper names, tool names and commands are NOT checked. An ASR error such as
    "Churnney" is copied faithfully and still passes: read the transcript's own
    warning about auto-captions.
  * A quote that is real but attributed to the wrong speaker passes.
  * Numbers are matched anywhere in the transcript, not in the right context.
  * A translated quote (draft in PT, transcript in EN) reports `missing` by design.
"""

import argparse
import json
import re
import sys
import unicodedata

QUOTE_RES = (
    re.compile(r'"([^"\n]+)"'),
    re.compile(r'“([^”\n]+)”'),
    re.compile(r'«([^»\n]+)»'),
)
MIN_QUOTE_WORDS = 4
NEAR_THRESHOLD = 0.8
GRAM = 4

# Sections whose numbers are structure (timestamps, extraction notes), not claims.
SKIP_SECTIONS = ("metadados internos", "estrutura por cap", "conceitos-âncora", "conceitos-ancora")

_TS_PREFIX = re.compile(r'^\s*\[\d+:\d{2}(?::\d{2})?\]\s*', re.M)
_TS_INLINE = re.compile(r'\[?\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[–-]\s*\d{1,2}:\d{2}(?::\d{2})?)?\]?')
_NUM = re.compile(
    r'(?<![\w/.])(\$?)(\d+(?:[.,]\d+)*)\s?'
    r'(%|percent\b|[kKmMbB]\b|million\b|billion\b|thousand\b|mil\b|milh(?:ão|ões|ao|oes)\b)?')
_MULT = {"k": 1e3, "thousand": 1e3, "mil": 1e3, "m": 1e6, "million": 1e6, "milhão": 1e6,
         "milhões": 1e6, "milhao": 1e6, "milhoes": 1e6, "b": 1e9, "billion": 1e9}

_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * (i + 2) for i, w in enumerate(
    "twenty thirty forty fifty sixty seventy eighty ninety".split())}
_BIG = {"hundred": 1e2, "thousand": 1e3, "million": 1e6, "billion": 1e9}


def norm(text):
    """Lowercase, drop accents, apostrophes and punctuation, collapse spaces."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[’'`]", "", text)
    text = re.sub(r"[^\w\s]|_", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_frontmatter(lines):
    """Drop a leading YAML block; returns (body_lines, first_body_line_no)."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:], i + 2
    return lines, 1


def _grams(words):
    n = min(GRAM, len(words))
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]


def check_fragment(fragment, transcript_norm):
    """'exact' | 'near' | 'missing' for one quote fragment."""
    frag = norm(fragment)
    words = frag.split()
    if len(words) < 3:
        return "exact" if frag and frag in transcript_norm else "missing"
    if frag in transcript_norm:
        return "exact"
    grams = _grams(words)
    hit = sum(g in transcript_norm for g in grams)
    return "near" if hit / len(grams) >= NEAR_THRESHOLD else "missing"


def extract_quotes(line):
    """Quoted spans of the line worth checking, with their (start, end)."""
    found = []
    for rx in QUOTE_RES:
        for m in rx.finditer(line):
            inner = re.sub(r"\[[^\]]*\]", " ", m.group(1))
            if len(norm(inner).split()) >= MIN_QUOTE_WORDS:
                found.append((m.start(), m.end(), m.group(1)))
    return found


def _canon(raw, mult_word, pct):
    """Numeric value of a matched figure, or None if it is not a plain number."""
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", raw):          # 250,000 / 250.000
        value = float(re.sub(r"[.,]", "", raw))
    elif re.fullmatch(r"\d+[.,]\d+", raw):                   # 5.5 / 5,5
        value = float(raw.replace(",", "."))
    elif re.fullmatch(r"\d+", raw):
        value = float(raw)
    else:                                                    # 2.1.302, 1,2,3 ...
        return None
    if mult_word:
        value *= _MULT[mult_word.lower()]
    return round(value, 6), bool(pct)


def parse_numbers(text):
    """[(raw, (value, is_percent), start)] for every figure in the text."""
    out = []
    for m in _NUM.finditer(text):
        dollar, raw, suffix = m.group(1), m.group(2), (m.group(3) or "")
        low = suffix.lower()
        pct = low in ("%", "percent")
        canon = _canon(raw, low if low in _MULT else "", pct)
        if canon is None:
            continue
        out.append((m.group(0).strip(), canon, m.start(), bool(dollar)))
    return out


def transcript_numbers(text):
    """Set of (value, is_percent) present in the transcript, digits or words."""
    text = _TS_PREFIX.sub("", text)
    found = {canon for _, canon, _, _ in parse_numbers(text)}
    return found | _word_numbers(re.findall(r"[a-z]+", text.lower()))


def _word_numbers(words):
    """Values spelled out in English: 'nine', 'twenty five', 'two hundred and fifty
    thousand', 'a million'. Sloppy by design (adjacent number words may merge);
    the error direction is a missed alarm, never a false one."""
    def is_num(w):
        return w in _UNITS or w in _TENS or w in _BIG

    found, i, n = set(), 0, len(words)
    while i < n:
        if words[i] == "a" and i + 1 < n and words[i + 1] in _BIG:
            j, total, cur = i + 1, 0, 1
        elif is_num(words[i]):
            j, total, cur = i, 0, 0
        else:
            i += 1
            continue
        while j < n:
            w = words[j]
            if w in _UNITS:
                cur += _UNITS[w]
            elif w in _TENS:
                cur += _TENS[w]
            elif w == "hundred":
                cur = (cur or 1) * 100
            elif w in ("thousand", "million", "billion"):
                total += (cur or 1) * _BIG[w]
                cur = 0
            elif w == "and" and j + 1 < n and is_num(words[j + 1]) and (cur or total):
                pass
            else:
                break
            j += 1
        value = float(total + cur)
        found.add((value, False))
        if j < n and words[j] == "percent":
            found.add((value, True))
        i = max(j, i + 1)
    return found


def _worth_checking(raw, canon, dollar):
    """Skip bare single digits (list counts, 'step 3'); keep everything specific."""
    value, pct = canon
    if pct or dollar or re.search(r"[.,]", raw) or re.search(r"[kKmMbB]$|million|billion|thousand|\bmil", raw):
        return True
    return len(re.sub(r"\D", "", raw)) >= 2


def check(draft_text, transcript_text):
    lines, first_no = strip_frontmatter(draft_text.splitlines())
    t_norm = norm(_TS_PREFIX.sub("", transcript_text))
    t_nums = transcript_numbers(transcript_text)

    quotes, numbers = [], []
    seen_nums = {}
    section = ""
    for offset, line in enumerate(lines):
        no = first_no + offset
        if line.startswith("#"):
            section = line.lstrip("#").strip().lower()
            continue
        if re.match(r"^\s*\|[\s:|-]+\|\s*$", line):
            continue

        scan = line
        for start, end, inner in sorted(extract_quotes(line), reverse=True):
            parts = [p for p in re.split(r"\.\.\.|…", re.sub(r"\[[^\]]*\]", " ", inner))
                     if len(norm(p).split()) >= 1]
            statuses = [check_fragment(p, t_norm) for p in parts]
            status = ("missing" if "missing" in statuses
                      else "near" if "near" in statuses else "exact")
            quotes.append({"line": no, "status": status, "text": inner.strip()})
            scan = scan[:start] + " " * (end - start) + scan[end:]
        quotes.sort(key=lambda q: q["line"])

        if any(section.startswith(s) for s in SKIP_SECTIONS):
            continue
        scan = re.sub(r"^\s*(?:[-*>]\s*)?(?:\[[ xX]\]\s*)?\d+[.)]\s+", " ", scan)   # list numbering
        scan = _TS_INLINE.sub(" ", scan)
        for raw, canon, pos, dollar in parse_numbers(scan):
            if not _worth_checking(raw, canon, dollar):
                continue
            key = canon
            if key in seen_nums:
                continue
            ctx = scan[max(0, pos - 40):pos + len(raw) + 30].strip()
            seen_nums[key] = True
            numbers.append({"line": no, "value": raw, "status": "matched" if canon in t_nums else "unmatched",
                            "context": ctx})
    return quotes, numbers


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--draft", required=True)
    ap.add_argument("--cleaned-transcript", required=True)
    ap.add_argument("--report", help="write the full result as JSON")
    args = ap.parse_args()
    try:
        draft = open(args.draft, encoding="utf-8").read()
        transcript = open(args.cleaned_transcript, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    if not transcript.strip():
        print("ERROR: transcript is empty", file=sys.stderr)
        sys.exit(2)

    quotes, numbers = check(draft, transcript)
    q = {s: sum(1 for x in quotes if x["status"] == s) for s in ("exact", "near", "missing")}
    n_bad = [x for x in numbers if x["status"] == "unmatched"]
    summary = {"quotes": len(quotes), **{f"quotes_{k}": v for k, v in q.items()},
               "numbers": len(numbers), "numbers_unmatched": len(n_bad)}
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "quotes": quotes, "numbers": numbers}, f,
                      ensure_ascii=False, indent=2)

    print(f"Quotes:  {len(quotes)} checked | {q['exact']} exact | {q['near']} near | {q['missing']} MISSING")
    print(f"Numbers: {len(numbers)} distinct checked | {len(n_bad)} UNMATCHED")
    for x in quotes:
        if x["status"] == "missing":
            print(f"  MISSING quote (draft line {x['line']}): {x['text'][:140]}")
        elif x["status"] == "near":
            print(f"  near    quote (draft line {x['line']}): {x['text'][:140]}")
    for x in n_bad:
        print(f"  UNMATCHED number {x['value']!r} (draft line {x['line']}): ...{x['context']}...")
    sys.exit(0 if q["missing"] == 0 and not n_bad else 1)


if __name__ == "__main__":
    main()
