#!/usr/bin/env python3
"""
Quote Verification — evidence counts only if the quote is really in the source.

Every `direct_quote` / `data_point` evidence row claims to be text taken from a
source. LLMs paraphrase, "tidy up" and occasionally invent quotes. This script
checks each stored quote against a saved text snapshot of the source.

Inspired by Hermes `grounded-citations` (verbatim quote acceptance) and by
B143KC47/deep-research-skill ("log evidence from opened sources only — never
from search-result snippets").

Snapshots:
  snapshots/<source_id>.txt   plain text of the opened source (fetched page,
                              extracted PDF text, transcript ...)
  snapshots.jsonl             append-only registry: source_id, sha256, chars,
                              origin, captured_at

CLI:
  snapshot   save source text (from --file or stdin) for a source_id
  verify     check evidence quotes against snapshots

Match levels (after normalisation: NFKC, curly quotes/dashes folded, ellipsis
removed, whitespace collapsed, case-folded):
  verbatim     normalised quote is a substring of the normalised snapshot
  near         >= 85% of the quote's 6-word shingles line up in one source
               passage (tolerates line-break hyphenation, small edits)
               or alphanumeric fingerprints match (OCR / PDF text layers:
               hyphenation, ligatures, collapsed spaces). Never tolerated:
               a number of the quote missing (as a whole number) from the
               matched passage, a negation cue (negation_lexicon.json,
               English n't) in the quote but not the passage or vice versa,
               or any word-level edit (quote aligned with the passage) that
               changes a number or a negation cue — so a number swapped for
               another number of the passage, or a negation moved to another
               clause, is missing.
               Elided quotes ("...") are near when every segment matches in
               source order, within 400 chars of the previous one, with no
               negation in the omitted text and no hidden sentence break
               (abbreviations such as "Dr." are not breaks). Han/kana quotes
               may start or end mid-run (no word spaces).
  missing      none of the above — the quote is not supported by the saved
               source (quote_checks.jsonl rows carry a `reason`)
  no_snapshot  the source has no saved text (cannot check)

`verify --strict` exits 1 when any checkable quote (direct_quote, data_point)
is `missing`, or when the share of checkable quotes without snapshot exceeds
--max-no-snapshot (default 0.2).
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from datetime import datetime, timezone

CHECKABLE_TYPES = ('direct_quote', 'data_point')
SHINGLE = 6
FINGERPRINT_MIN = 40
NEAR_THRESHOLD = 0.85

_FOLD = {
    '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",
    '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u00ab': '"', '\u00bb': '"',
    '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-', '\u2014': '-', '\u2212': '-',
    '\u00a0': ' ', '\u2009': ' ', '\u202f': ' ',
}
_ELLIPSIS_RE = re.compile(r'\.\.\.|\u2026|\[\s*\.\.\.\s*\]|\[…\]')
_HYPHEN_BREAK_RE = re.compile(r'(\w)-\s*\n\s*(\w)')
_WS_RE = re.compile(r'\s+')
_SID_RE = re.compile(r'^[A-Za-z0-9_\-]{1,64}$')


def normalize(text: str) -> str:
    text = unicodedata.normalize('NFKC', text or '')
    text = _HYPHEN_BREAK_RE.sub(r'\1\2', text)
    text = ''.join(_FOLD.get(ch, ch) for ch in text)
    text = _ELLIPSIS_RE.sub(' ', text)
    text = text.replace('"', ' ').replace("'", "'")
    return _WS_RE.sub(' ', text).strip().casefold()


def _words(text: str) -> list[str]:
    return re.findall(r'\w+', text)


def _number_edge_problem(hay: str, start: int, end: int) -> bool:
    """nexus: R15-C3 — a match edge cuts through a number at a decimal or
    group separator ('5%' inside '2.5%', 'hired 12' inside '12,000')."""
    if start >= 2 and hay[start].isdigit() and hay[start - 1] in '.,' and hay[start - 2].isdigit():
        return True
    # nexus: R16 — nor drop a minus sign ("5%" inside "-5%"); a hyphen after a
    # word or digit ("COVID-19", "10-12") is no sign
    if start >= 1 and hay[start].isdigit() and hay[start - 1] in '-\u2212' and (
            start == 1 or not hay[start - 2].isalnum()):
        return True
    if end + 1 < len(hay) and hay[end - 1].isdigit() and hay[end] in '.,' and hay[end + 1].isdigit():
        return True
    return False


def _contains_bounded(needle: str, haystack: str) -> bool:
    """Substring match that does not start/end in the middle of a word."""
    start = haystack.find(needle)
    while start != -1:
        end = start + len(needle)
        before_ok = start == 0 or not (_word_char(haystack[start - 1]) and _word_char(needle[0]))
        after_ok = end == len(haystack) or not (_word_char(haystack[end]) and _word_char(needle[-1]))
        if (before_ok and after_ok and not _cjk_edge_problem(haystack, start, end)
                and not _number_edge_problem(haystack, start, end)):
            return True
        start = haystack.find(needle, start + 1)
    return False


_NUM_RE = re.compile(r'\d+(?:[.,]\d+)*')
# nexus: R17 — a figure with its minus sign ("-5" is not "5"); a hyphen after a
# word or digit ("COVID-19", "10-12") is no sign
_SIGNED_NUM_RE = re.compile(r'(?:(?<!\w)-)?\d+(?:[.,]\d+)*')

# ---------------------------------------------------------------------------
# Guards for 'near': a near match tolerates small edits, never a changed
# number, a flipped negation, or an elision that changes what the source says.
# ---------------------------------------------------------------------------

MAX_ELISION_GAP = 400        # normalised chars allowed between elided segments
INDEL_SLACK = 3              # words of drift tolerated inside one near passage
MAX_CANDIDATES = 50          # source locations considered per segment

_FALLBACK_NEGATIONS = ['not', 'no', 'never', 'cannot', 'none', 'nobody', 'neither']
# English forms that mean "not"; folded so "did not" == "didn't" == "cannot".
_NOT_FORMS = {'not', 'cannot', 'cant'}
_NT_RE = re.compile(r"(?<=\w)n't(?!\w)")
# nexus: any token before . ! ? and whitespace ends a sentence ("20%.",
# "(2019).", "plan 3."), not only a word of 2+ letters.
_SENTENCE_END_RE = re.compile(r'(\S+?)([.!?])(?=\s)')
# Abbreviations whose period does not end a sentence ("Dr. Smith"). Only
# title-like ones: "etc.", "Inc.", "Co." or month names often end a
# sentence, so they count as a break (the source is casefolded, so the
# capital of the next word cannot tell them apart).
_ABBREVIATIONS = frozenset([
    'dr', 'mr', 'mrs', 'ms', 'prof', 'sr', 'jr', 'st', 'mt', 'vs', 'al', 'fig', 'figs', 'eq',
    'vol', 'pp', 'approx', 'dept', 'univ', 'gen', 'gov', 'sen', 'rep', 'sra', 'srs', 'eng',
    'av', 'cf', 'resp'])


def _has_sentence_break(text: str) -> bool:
    """True if text holds a sentence end that is not an abbreviation, an
    initial ("J. Smith") or a dotted abbreviation ("e.g.", "U.S.").
    nexus: a figure with a decimal point ("$4.5bn.", "2.5%.") ends a sentence."""
    for m in _SENTENCE_END_RE.finditer(text):
        token = re.sub(r'^\W+', '', m.group(1)).casefold()
        if m.group(2) != '.':
            return True
        if token in _ABBREVIATIONS or _DOTTED_ABBREV_RE.fullmatch(token) \
                or (len(token) == 1 and token.isalpha()):
            continue
        return True
    return False


_DOTTED_ABBREV_RE = re.compile(r'(?:[^\W\d_]{1,3}\.)+[^\W\d_]{1,3}')


# Han ideographs, kana and CJK compatibility ideographs: scripts written
# without spaces between words, so a quote may start or end mid-run.
def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return 0x3040 <= o <= 0x30FF or 0x3400 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF


def _word_char(ch: str) -> bool:
    return ch.isalnum() and not _is_cjk(ch)


_HAN_NUMERALS = frozenset('〇零一二三四五六七八九十百千万萬亿億兆两兩')


def _cjk_negation_in(src: str, i: int, j: int, edge: int) -> bool:
    """nexus: negation cue in src[i:j] (just outside a quote whose edge is at
    `edge`). Lexicon exceptions (非常) are masked on a wider window so a
    window cut cannot fake a negation, but only exceptions lying wholly
    outside the quote: one that straddles the edge (从未|来过 -> 未来) means the
    quote cut a real negation off."""
    lo, hi = max(0, i - 4), min(len(src), j + 4)
    wide = list(src[lo:hi])
    if _NEG_EXCEPTIONS_RE is not None:
        for e in _NEG_EXCEPTIONS_RE.finditer(src, lo, hi):
            if not (e.start() < edge < e.end()):
                wide[e.start() - lo:e.end() - lo] = ' ' * (e.end() - e.start())
    return bool(negation_cues(''.join(wide)[i - lo:j - lo]))


def _cjk_edge_problem(src: str, start: int, end: int) -> bool:
    """nexus: a CJK quote may start or end mid-run, but not by cutting off a
    negation right before or after it (不会增加 -> 会增加; 報告されなかった ->
    報告され) or by splitting a Han numeral (一百五十万 -> 五十万)."""
    if 0 < start < len(src) and _is_cjk(src[start - 1]) and _is_cjk(src[start]):
        k = start
        while k > max(0, start - 2) and _is_cjk(src[k - 1]):
            k -= 1
        if _cjk_negation_in(src, k, start, start) or (src[start - 1] in _HAN_NUMERALS and src[start] in _HAN_NUMERALS):
            return True
    if 0 < end < len(src) and _is_cjk(src[end]) and _is_cjk(src[end - 1]):
        k = end
        while k < min(len(src), end + 4) and _is_cjk(src[k]):
            k += 1
        if _cjk_negation_in(src, end, k, end) or (src[end] in _HAN_NUMERALS and src[end - 1] in _HAN_NUMERALS):
            return True
    return False


def _load_negation_lexicon() -> tuple[frozenset, tuple, re.Pattern | None]:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'negation_lexicon.json')
    try:
        with open(path, encoding='utf-8') as f:
            lex = json.load(f)
    except (OSError, ValueError):
        lex = {}
    words = {normalize(w) for w in lex.get('negation_words') or _FALLBACK_NEGATIONS} | {'nor'}
    chars = tuple(normalize(c) for c in lex.get('negation_chars', []) if c.strip())
    parts = []
    for ex in sorted({normalize(e) for e in lex.get('exceptions', []) if e.strip()}, key=len, reverse=True):
        # Han/kana/hangul phrases have no word spaces; others match on word boundaries.
        cjk = any(ord(ch) >= 0x2E80 for ch in ex)
        parts.append(re.escape(ex) if cjk else r'(?<!\w)' + re.escape(ex) + r'(?!\w)')
    return frozenset(words), chars, (re.compile('|'.join(parts)) if parts else None)


_NEG_WORDS, _NEG_CHARS, _NEG_EXCEPTIONS_RE = _load_negation_lexicon()


def _load_antonyms() -> dict[str, tuple[int, int]]:
    """word -> (pair index, side) from the lexicon's antonym pairs."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'negation_lexicon.json')
    try:
        with open(path, encoding='utf-8') as f:
            pairs = json.load(f).get('antonyms', [])
    except (OSError, ValueError):
        pairs = []
    out: dict[str, tuple[int, int]] = {}
    for i, pair in enumerate(pairs):
        for side, forms in enumerate(pair[:2]):
            for w in forms:
                out[normalize(w)] = (i, side)
    return out


_ANTONYMS = _load_antonyms()


def _antonym_swap(edited_q: list[str], edited_p: list[str]) -> bool:
    """nexus: an edit that replaces a word with its antonym (increased ->
    decreased) flips the meaning like a negation does."""
    q = {_ANTONYMS[w] for w in edited_q if w in _ANTONYMS}
    return any((i, 1 - side) in q for i, side in (_ANTONYMS[w] for w in edited_p if w in _ANTONYMS))


def negation_cues(text: str) -> Counter:
    """Multiset of negation cues in normalised text (lexicon words, CJK
    negation characters, English n't), ignoring non-negating exceptions
    such as "not only" or "no doubt"."""
    if _NEG_EXCEPTIONS_RE is not None:
        text = _NEG_EXCEPTIONS_RE.sub(' ', text)
    cues: Counter = Counter()
    n_nt = len(_NT_RE.findall(text))
    if n_nt:
        cues['not'] += n_nt
        text = _NT_RE.sub(' ', text)
    for w in _words(text):
        if w in _NEG_WORDS:
            cues['not' if w in _NOT_FORMS else w] += 1
    for ch in _NEG_CHARS:
        n = text.count(ch)
        if n:
            cues[ch] += n
    return cues


@lru_cache(maxsize=8)
def _source_index(normalized_source: str) -> tuple[list, dict, list]:
    """Word char spans, shingle -> word positions, and fingerprint -> char map."""
    spans = [(m.start(), m.end(), m.group()) for m in re.finditer(r'\w+', normalized_source)]
    words = [w for _, _, w in spans]
    positions: dict[tuple, list[int]] = {}
    for i in range(len(words) - SHINGLE + 1):
        positions.setdefault(tuple(words[i:i + SHINGLE]), []).append(i)
    fp_map = [i for i, ch in enumerate(normalized_source) if ch.isalnum()]
    return spans, positions, fp_map


def _passage_problem(q: str, passage: str) -> str | None:
    """Why `passage` cannot stand behind a near match of quote segment `q`.

    nexus: besides the multiset checks, the quote is aligned word by word
    with the passage, and every edit (a word replaced, added or dropped)
    must avoid numbers and negation cues. So a number swapped for another
    number of the same passage, or a negation moved to another clause, is
    never a near match. Extra passage words before the quote's first or
    after its last word are only window slack and are ignored."""
    if not set(_SIGNED_NUM_RE.findall(q)) <= set(_SIGNED_NUM_RE.findall(passage)):
        return 'number_not_in_passage'
    if negation_cues(q) != negation_cues(passage):
        return 'negation_mismatch'
    a, b = _cue_words(q), _cue_words(passage)
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    for k, (tag, i1, i2, j1, j2) in enumerate(ops):
        if tag == 'equal':
            continue
        if tag == 'insert' and ((k == 0 and i1 == 0) or (k == len(ops) - 1 and i1 == len(a))):
            continue
        edited_q, edited_p = ' '.join(a[i1:i2]), ' '.join(b[j1:j2])
        if Counter(_NUM_RE.findall(edited_q)) != Counter(_NUM_RE.findall(edited_p)):
            return 'number_not_in_passage'
        if negation_cues(edited_q) != negation_cues(edited_p):
            return 'negation_mismatch'
        if _antonym_swap(a[i1:i2], b[j1:j2]):
            return 'antonym_mismatch'
    return None


def _cue_words(text: str) -> list[str]:
    """Words of normalised text, with English n't split off as 'not', so
    'didn't' aligns with 'did not'."""
    return _words(_NT_RE.sub(' not', text))


def _expand_to_words(src: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and src[start - 1].isalnum():
        start -= 1
    while end < len(src) and src[end].isalnum():
        end += 1
    return start, end


def _match_segment(q: str, normalized_source: str) -> tuple[str, float, list, str | None]:
    """Return (level, coverage, candidate char spans in the source, reason)."""
    src = normalized_source
    spans, positions, fp_map = _source_index(src)
    q_words = _words(q)
    found = []
    start = src.find(q)
    while start != -1 and len(found) < MAX_CANDIDATES:
        end = start + len(q)
        if ((start == 0 or not (_word_char(src[start - 1]) and _word_char(q[0])))
                and (end == len(src) or not (_word_char(src[end]) and _word_char(q[-1])))
                and not _cjk_edge_problem(src, start, end)
                and not _number_edge_problem(src, start, end)):
            found.append((start, end))
        start = src.find(q, start + 1)
    if found:
        return ('verbatim', 1.0, found, None)
    if len(q_words) < SHINGLE:
        # Too short for shingles: the same word sequence must occur in the
        # source (punctuation ignored), on whole-word boundaries.
        n = len(q_words)
        for i in range(len(spans) - n + 1):
            if (n and spans[i][2] == q_words[0] and [s[2] for s in spans[i:i + n]] == q_words
                    and not _number_edge_problem(src, spans[i][0], spans[i + n - 1][1])):
                found.append((spans[i][0], spans[i + n - 1][1]))
                if len(found) >= MAX_CANDIDATES:
                    break
        return ('verbatim', 1.0, found, None) if found else ('missing', 0.0, [], 'segment_not_found')

    # Shingle path: locate passages where the quote's shingles line up
    # (same relative offsets, small drift), not shingles scattered anywhere.
    q_sh = [tuple(q_words[i:i + SHINGLE]) for i in range(len(q_words) - SHINGLE + 1)]
    hits = [(i, p) for i, sh in enumerate(q_sh) for p in positions.get(sh, ())]
    best_cov, reason = 0.0, 'segment_not_found'
    cands = []
    for anchor in sorted({p - i for i, p in hits}):
        aligned = [(i, p) for i, p in hits if abs(p - i - anchor) <= INDEL_SLACK]
        cov = len({i for i, _ in aligned}) / len(q_sh)
        if cov < NEAR_THRESHOLD:
            best_cov = max(best_cov, cov)
            continue
        i0, p0 = min(aligned)
        i1, p1 = max(aligned)
        w_start = max(0, p0 - i0)
        w_end = min(len(spans) - 1, p1 + SHINGLE - 1 + (len(q_words) - (i1 + SHINGLE)))
        cands.append((cov, spans[w_start][0], spans[w_end][1]))
    good = []
    for cov, s, e in sorted(cands, key=lambda c: (-c[0], c[1])):
        problem = ('number_not_in_passage' if _number_edge_problem(src, s, e)
                   else _passage_problem(q, src[s:e]))
        if problem is None:
            if (s, e) not in [g[1:] for g in good]:
                good.append((cov, s, e))
        elif reason == 'segment_not_found':
            reason = problem
    if good:
        return ('near', round(good[0][0], 3), [(s, e) for _, s, e in good[:MAX_CANDIDATES]], None)
    if cands:
        best_cov = max(c[0] for c in cands)

    # OCR/PDF fallback: alphanumeric fingerprint, checked against the located passage.
    fp = ''.join(ch for ch in q if ch.isalnum())
    if len(fp) >= FINGERPRINT_MIN and numbers_in_source(q, src):
        src_fp = _source_fingerprint(src)[0]
        idx = src_fp.find(fp)
        while idx != -1 and len(found) < MAX_CANDIDATES:
            s, e = _expand_to_words(src, fp_map[idx], fp_map[idx + len(fp) - 1] + 1)
            problem = ('number_not_in_passage' if _number_edge_problem(src, s, e)
                       else _passage_problem(q, src[s:e]))
            if problem is None:
                found.append((s, e))
            elif reason == 'segment_not_found':
                reason = problem
            idx = src_fp.find(fp, idx + 1)
        if found:
            return ('near', 1.0, found, None)
    elif not numbers_in_source(q, src) and reason == 'segment_not_found':
        reason = 'number_not_in_passage'
    return ('missing', round(best_cov, 3), [], reason)


@lru_cache(maxsize=64)
def _source_fingerprint(normalized_source: str) -> tuple[str, frozenset]:
    return (''.join(ch for ch in normalized_source if ch.isalnum()),
            frozenset(_NUM_RE.findall(normalized_source)))


def fingerprint_match(q: str, normalized_source: str) -> bool:
    """OCR/PDF fallback (from necopinus): compare lowercase alphanumeric-only
    fingerprints, so line-wrap hyphens, ligatures and collapsed spaces do not
    cause false misses. Guarded: the quote needs >= FINGERPRINT_MIN chars and
    every number in it must exist as a whole number in the source, so "23%"
    cannot match inside "123%"."""
    fp = ''.join(ch for ch in q if ch.isalnum())
    if len(fp) < FINGERPRINT_MIN:
        return False
    return fp in _source_fingerprint(normalized_source)[0] and numbers_in_source(q, normalized_source)


def numbers_in_source(q: str, normalized_source: str) -> bool:
    return set(_NUM_RE.findall(q)) <= _source_fingerprint(normalized_source)[1]


def match_quote(quote: str, normalized_source: str, source_words: set[tuple] | None = None) -> tuple[str, float]:
    """Return (level, coverage) for a quote against an already-normalised source.
    `source_words` is accepted for backward compatibility and ignored."""
    level, coverage, _ = match_quote_detail(quote, normalized_source)
    return (level, coverage)


def _elision_problem(src: str, prev_end: int, start: int, prev_raw: str) -> str | None:
    """Why the source text omitted between two elided segments breaks the quote."""
    if start < prev_end:
        return 'elision_out_of_order'
    if start - prev_end > MAX_ELISION_GAP:
        return 'elision_gap_too_long'
    gap = src[prev_end:start]
    if negation_cues(gap):
        return 'negation_in_elided_gap'
    # Stitching the end of one sentence onto another ("Smoking ... reduces
    # risk") is only allowed when the quote itself marks the sentence end.
    w = max(0, prev_end - 2)
    while w > 0 and src[w - 1].isalnum():
        w -= 1
    if _has_sentence_break(src[w:start]) and not prev_raw.rstrip().endswith(('.', '!', '?')):
        return 'elision_crosses_sentence'
    return None


def match_quote_detail(quote: str, normalized_source: str) -> tuple[str, float, str | None]:
    """Return (level, coverage, reason) for a quote against a normalised source.

    Quotes with elisions ("...", "…", "[...]") are split; every segment must
    match on its own, in source order, within MAX_ELISION_GAP chars of the
    previous segment, and the omitted source text must not hold a negation or
    a sentence break the quote hides. An elided quote is at best `near`.
    `reason` explains a `missing` result (None otherwise).
    """
    raw = [s for s in _ELLIPSIS_RE.split(unicodedata.normalize('NFKC', quote or '')) if _words(normalize(s))]
    segments = [normalize(s) for s in raw]
    if not segments:
        return ('missing', 0.0, 'empty_quote')
    results = [_match_segment(s, normalized_source) for s in segments]
    coverage = round(sum(r[1] for r in results) / len(results), 3)
    for level, _, _, reason in results:
        if level == 'missing':
            return ('missing', coverage, reason)
    if len(results) == 1:
        level = results[0][0]
        return (level, 1.0 if level == 'verbatim' else coverage, None)

    # Chain the segments through the source: depth-first over candidate spans.
    cands = [sorted(r[2]) for r in results]
    problems: set[str] = set()
    dead: set[tuple[int, int]] = set()

    def chain(k: int, prev_end: int) -> bool:
        if k == len(cands):
            return True
        if (k, prev_end) in dead:
            return False
        for s, e in cands[k]:
            problem = _elision_problem(normalized_source, prev_end, s, raw[k - 1])
            if problem is None and chain(k + 1, e):
                return True
            if problem:
                problems.add(problem)
        dead.add((k, prev_end))
        return False

    if any(chain(1, e) for _, e in cands[0]):
        return ('near', coverage, None)
    # Report the most meaning-relevant problem seen.
    for reason in ('negation_in_elided_gap', 'elision_crosses_sentence',
                   'elision_gap_too_long', 'elision_out_of_order'):
        if reason in problems:
            return ('missing', coverage, reason)
    return ('missing', coverage, 'elision_out_of_order')


def shingles(words: list[str]) -> set[tuple]:
    return {tuple(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1)}


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: str, obj: dict) -> None:
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def snapshot_path(run_dir: str, source_id: str) -> str:
    return os.path.join(run_dir, 'snapshots', f'{source_id}.txt')


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_snapshot(args: argparse.Namespace) -> None:
    if not _SID_RE.match(args.source_id):
        print(json.dumps({'status': 'error', 'error': 'invalid source_id'}))
        sys.exit(2)
    if args.file:
        with open(args.file, encoding='utf-8', errors='replace') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    if not text.strip():
        print(json.dumps({'status': 'error', 'error': 'empty snapshot text'}))
        sys.exit(2)
    path = snapshot_path(args.dir, args.source_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    append_jsonl(os.path.join(args.dir, 'snapshots.jsonl'), {
        'source_id': args.source_id, 'sha256': digest, 'chars': len(text),
        'origin': args.origin or '', 'captured_at': datetime.now(timezone.utc).isoformat(),
    })
    print(json.dumps({'status': 'ok', 'source_id': args.source_id, 'chars': len(text), 'sha256': digest[:16]}))


def verify_run(run_dir: str) -> list[dict]:
    evidence = read_jsonl(os.path.join(run_dir, 'evidence.jsonl'))
    cache: dict[str, str | None] = {}
    results = []
    for ev in evidence:
        etype = ev.get('evidence_type', 'direct_quote')
        sid = ev.get('source_id', '')
        row = {'evidence_id': ev.get('evidence_id'), 'source_id': sid, 'evidence_type': etype}
        if etype not in CHECKABLE_TYPES:
            row.update(level='not_checked', coverage=None)
            results.append(row)
            continue
        if sid not in cache:
            path = snapshot_path(run_dir, sid) if _SID_RE.match(sid or '') else ''
            if path and os.path.exists(path):
                with open(path, encoding='utf-8', errors='replace') as f:
                    cache[sid] = normalize(f.read())
            else:
                cache[sid] = None
        cached = cache[sid]
        if cached is None:
            row.update(level='no_snapshot', coverage=None)
        else:
            level, cov, reason = match_quote_detail(ev.get('quote', ''), cached)
            row.update(level=level, coverage=cov)
            if reason:
                row['reason'] = reason
        results.append(row)
    return results


def cmd_verify(args: argparse.Namespace) -> None:
    results = verify_run(args.dir)
    with open(os.path.join(args.dir, 'quote_checks.jsonl'), 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    checkable = [r for r in results if r['level'] != 'not_checked']
    counts: dict[str, int] = {}
    for r in results:
        counts[r['level']] = counts.get(r['level'], 0) + 1
    missing = [r['evidence_id'] for r in checkable if r['level'] == 'missing']
    no_snap = sum(1 for r in checkable if r['level'] == 'no_snapshot')
    no_snap_rate = no_snap / len(checkable) if checkable else 0.0

    problems = []
    if missing:
        problems.append(f'{len(missing)} quote(s) not found in their source snapshot')
    if no_snap_rate > args.max_no_snapshot:
        problems.append(f'{no_snap}/{len(checkable)} checkable quotes have no source snapshot')
    passed = not (args.strict and problems)
    print(json.dumps({'status': 'pass' if passed else 'fail', 'counts': counts,
                      'missing_evidence_ids': missing, 'no_snapshot_rate': round(no_snap_rate, 3),
                      'problems': problems}, indent=2))
    if not passed:
        sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(prog='verify_quotes', description='Check evidence quotes against source snapshots')
    sub = p.add_subparsers(dest='command', required=True)

    ps = sub.add_parser('snapshot', help='Save source text for a source_id')
    ps.add_argument('--dir', required=True)
    ps.add_argument('--source-id', required=True)
    ps.add_argument('--file', help='text file (default: stdin)')
    ps.add_argument('--origin', help='how the text was obtained, e.g. web_extract URL')

    pv = sub.add_parser('verify', help='Verify evidence quotes')
    pv.add_argument('--dir', required=True)
    pv.add_argument('--strict', action='store_true')
    pv.add_argument('--max-no-snapshot', type=float, default=0.2)

    args = p.parse_args()
    {'snapshot': cmd_snapshot, 'verify': cmd_verify}[args.command](args)


if __name__ == '__main__':
    main()
