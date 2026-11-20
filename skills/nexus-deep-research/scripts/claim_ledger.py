#!/usr/bin/env python3
"""
Claim Ledger — multi-verifier voting, resolution and delivery gate.

Semantic verification of claims is done by independent verifier agents that
run in FRESH context (they see the claim, the cited evidence and the failure
patterns — never the writer's reasoning or other verifiers' votes). Each
verifier records one vote per claim here. This script resolves the votes into
a final status, tells the orchestrator which claims still need verifiers
(early exit), checks source-family independence, and gates delivery.

Design sources:
  * Claude Code /deep-research: vote per claim; claims that could not be
    checked are "unverified", NOT refuted.
  * math-olympiad (anthropics/claude-plugins-official): asymmetric thresholds
    and pigeonhole early exit; verifiers blind to each other.
  * clinical-trial-forecast (anthropics/life-sciences): a claim ledger that is
    applied back to the report.
  * math-proof:siege: explicit proved / refuted / open bookkeeping.

Files (in the run directory):
  claims.jsonl         claims (from extract_claims.py), read-only here
  sources.jsonl        sources (from citation_manager.py), read-only here
  votes.jsonl          append-only verifier votes
  claim_ledger.jsonl   resolved ledger (rewritten by `resolve`)

Final statuses:
  supported    >= support_threshold "supported" votes, refutations below threshold
  refuted      >= refute_threshold "refuted" votes and support below threshold
  contested    both thresholds reached, or votes support a claim the
               deterministic layer flagged as contradicted
  unverified   not decided (no votes, too few, or verifiers could not check),
               including claims layer 1 flagged as contradicted

CLI:
  vote      record one verifier vote
  pending   list claims that still need verifier votes (with how many)
  resolve   compute the ledger
  gate      fail delivery on refuted claims / unacknowledged gaps
  table     print the ledger as a Markdown table for the report appendix
"""

import argparse
import functools
import html
from decimal import Decimal
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

VERDICTS = ('supported', 'refuted', 'unverifiable')
FINAL_STATUSES = ('supported', 'refuted', 'contested', 'unverified')

# Failure-pattern codes a verifier may cite (see reference/adversarial-verification.md)
FAILURE_PATTERNS = frozenset([
    'quote-mismatch', 'out-of-context', 'scope-inflation', 'number-error',
    'unit-or-base-error', 'stale', 'causal-leap', 'cherry-pick', 'circular-source',
    'secondary-misreport', 'vendor-claim', 'preprint-as-settled', 'benchmark-caveat',
    'sample-or-population', 'definition-drift', 'missing-counterevidence',
    'misattribution', 'fabricated-source', 'other',
])

DEFAULTS = {'support_threshold': 2, 'refute_threshold': 2, 'max_verifiers': 3}

# Second-level labels under 2-letter ccTLDs (example.co.uk, example.gov.pt ...)
_SECOND_LEVEL = frozenset(['co', 'com', 'org', 'net', 'gov', 'ac', 'edu', 'or', 'ne', 'go', 'mil', 'nhs'])


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


def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def append_jsonl(path: str, obj: dict) -> None:
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def _claims(run_dir: str) -> dict[str, dict]:
    out = {}
    for c in read_jsonl(os.path.join(run_dir, 'claims.jsonl')):
        out.setdefault(c['claim_id'], c)
    return out


def _fail(msg: str) -> None:
    print(json.dumps({'status': 'error', 'error': msg}))
    sys.exit(2)


# ---------------------------------------------------------------------------
# Source families (independence)
# ---------------------------------------------------------------------------

def registrable_domain(host: str) -> str:
    host = (host or '').lower().strip('.')
    if host.startswith('www.'):
        host = host[4:]
    labels = host.split('.')
    if len(labels) >= 3 and len(labels[-1]) == 2 and labels[-2] in _SECOND_LEVEL:
        return '.'.join(labels[-3:])
    return '.'.join(labels[-2:]) if len(labels) >= 2 else host


# Scholarly identifiers, either in canonical form (doi:..., arxiv:...) or as URLs.
_DOI_RE = re.compile(r'^(?:doi:|https?://(?:dx\.)?doi\.org/)(10\.\d{4,}/\S+)$', re.IGNORECASE)
_ARXIV_RE = re.compile(
    r'^(?:arxiv:|https?://(?:www\.)?(?:export\.)?arxiv\.org/(?:abs|pdf)/)'
    r'(\d{4}\.\d{4,5}|[a-z][a-z.\-]*/\d{7})(?:v\d+)?(?:\.pdf)?/?$', re.IGNORECASE)
# arXiv's DataCite DOIs: 10.48550/arXiv.<id> is the same paper as arxiv:<id>.
_ARXIV_DOI_RE = re.compile(r'^10\.48550/arxiv\.(.+?)(?:v\d+)?$', re.IGNORECASE)


def _scholarly_family(loc: str) -> str | None:
    """`arxiv:<id>` (version-less) / `doi:<doi>` / `pmid:<id>` for scholarly locators, else None."""
    loc = loc.strip()
    m = _ARXIV_RE.match(loc)
    if m:
        return 'arxiv:' + m.group(1).lower()
    m = _DOI_RE.match(loc)
    if m:
        doi = m.group(1).rstrip('.').lower()
        a = _ARXIV_DOI_RE.match(doi)
        return 'arxiv:' + a.group(1) if a else 'doi:' + doi
    if loc.lower().startswith('pmid:'):
        return loc.lower()
    return None


def source_family(source: dict) -> str:
    """Independence family. Explicit `source_family` wins; else derived.

    Derived families are a floor, not a proof of independence: two outlets
    repeating one press release are one family in reality. Verifiers flag
    that case with the `circular-source` pattern.

    A paper is one voice: all arXiv versions (v1, v2 ...), its arXiv DataCite
    DOI (10.48550/arXiv.<id>) and its abs/pdf URLs are one family.
    """
    if source.get('source_family'):
        explicit = str(source['source_family']).strip()
        return _scholarly_family(explicit) or explicit.lower()
    loc = source.get('canonical_locator') or source.get('raw_url') or ''
    scholarly = _scholarly_family(loc)
    if scholarly:
        return scholarly
    parsed = urlparse(loc if '://' in loc else 'https://' + loc)
    return registrable_domain(parsed.hostname or loc)


# ---------------------------------------------------------------------------
# Report text normalisation (refuted-claim detection)
# ---------------------------------------------------------------------------

SHINGLE_SIZE = 3
REFUTED_OVERLAP_THRESHOLD = 0.8

_QUOTES = str.maketrans({c: '"' for c in '\u201c\u201d\u201e\u201f\u00ab\u00bb\u2033'}
                        | {c: "'" for c in '\u2018\u2019\u201a\u201b\u2032\u00b4'}
                        | {c: '-' for c in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212'})
_HTML_SUP = re.compile(r'<sup>.*?</sup>', re.IGNORECASE | re.DOTALL)
# nexus: an HTML tag: a known element name (or a custom element with "-"),
# then attributes (name, or name=value with quoted or unquoted value; a
# quoted value may be followed directly by the next attribute), within one
# line. Prose such as "<half of the target ... >10%", "<<quoted words>>" or
# "<higher for group A than B>" is kept (R10-A4, R12-C4); unlisted real tags
# such as <time>, <var>, <font> are markup (R11-F3, R12-C5).
_HTML_ELEMENTS = (
    'a|abbr|address|area|article|aside|audio|b|bdi|bdo|big|blockquote|body|br|button|canvas|caption|center|'
    'cite|code|col|colgroup|data|datalist|dd|del|details|dfn|dialog|div|dl|dt|em|embed|fieldset|figcaption|'
    'figure|font|footer|form|h[1-6]|head|header|hgroup|hr|html|i|iframe|img|input|ins|kbd|label|legend|li|'
    'link|main|map|mark|math|menu|meta|meter|nav|nobr|noscript|object|ol|optgroup|option|output|p|param|'
    'picture|pre|progress|q|rp|rt|ruby|s|samp|script|search|section|select|slot|small|source|span|strike|'
    'strong|style|sub|summary|sup|svg|table|tbody|td|template|textarea|tfoot|th|thead|time|title|tr|track|'
    'tt|u|ul|var|video|wbr')
_HTML_TAG = re.compile(
    r'(?<!<)</?(?:(?:' + _HTML_ELEMENTS + r')|[a-zA-Z][a-zA-Z0-9]*-[a-zA-Z0-9-]*)'
    r'''(?:(?:[ \t]+|(?<=["']))[a-zA-Z_:@][-\w:.@]*(?:[ \t]*=[ \t]*(?:"[^"\n]*"|'[^'\n]*'|[^\s"'<>`]+))?)*'''
    r'[ \t]*/?>', re.IGNORECASE)
_BARE_ATTR = re.compile(r'''(?:^|[ \t])[a-zA-Z_:@][-\w:.@]*(?=[ \t]|/?>$)''')
_HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)


def _tag_or_prose(m: 're.Match') -> str:
    """nexus: a run of bare words is prose, not attributes: "<a quarter of
    SMEs ... >60%" (R13-C6); a real tag has at most one bare (boolean)
    attribute (<td nowrap>, <details open>)."""
    inner = m.group(0)[1:].lstrip('/')
    inner = inner[re.match(r'[a-zA-Z][\w-]*', inner).end():]
    return m.group(0) if len(_BARE_ATTR.findall(inner)) > 1 else ' '
_IMAGE_OR_LINK = re.compile(r'!?\[([^\]]*)\](?:\([^)]*\)|\[[^\]]*\])')
_NUM_CITE = re.compile(r'\[\s*\^?\s*\d+(?:\s*[-,;]\s*\^?\s*\d+)*\s*\](?:\([^)\s]*\))?')
_NAMED_CITE = re.compile(r'\[(?:\^|@)[^\]]*\]')
_YEAR = r'(?:19|20)\d{2}[a-z]?'
# nexus: an author-year citation is names (capitalised words, initials,
# "et al.", "and"/"&", name particles) then a year. A parenthetical sentence
# such as "(Acme Holdings went bankrupt in 2019)" is report text, not a citation.
_CITE_NAME = (r"(?:[A-Z][\w'\u2019.\-]*|et\s+al\.?|and|&|von|van|der|den|de|da|del|della|di|du|"
              r"dos|la|le|y)")
_CITE_ONE = _CITE_NAME + r'(?:\s*,?\s+' + _CITE_NAME + r')*\s*,?\s*' + _YEAR
_AUTHOR_YEAR_CITE = re.compile(r'\(\s*' + _CITE_ONE + r'(?:\s*[;,]\s*' + _CITE_ONE + r')*\s*\)')
_SUPERSCRIPT = re.compile('[\u00b9\u00b2\u00b3\u2070\u2074-\u2079]+')
_EMPHASIS = re.compile(r'[*_~`]+')
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+|\n\s*\n|\n(?=\s*(?:[#>|]|[-*+]\s|\d+[.)]\s))')
_TOKEN = re.compile(r"\w+(?:[.,']\w+)*%?")  # nexus: keep '%' so 12% != 12


def _strip_markup(text: str) -> str:
    # Superscript citation digits first: NFKC would turn '¹' into a plain '1'.
    # nexus: character references are text (&nbsp; &ndash; &ldquo; &amp;) (R12-F3)
    s = unicodedata.normalize('NFKC', _SUPERSCRIPT.sub(' ', html.unescape(text or ''))).translate(_QUOTES)
    s = _MD_ESCAPE.sub(r'\1', s)
    s = _HTML_SUP.sub(' ', s)
    s = _HTML_TAG.sub(_tag_or_prose, _HTML_COMMENT.sub(' ', s))   # R13-C8: comments are not text
    s = _NUM_CITE.sub(' ', s)       # before links: '[1](#ref-1)' is a citation, not text
    s = _NAMED_CITE.sub(' ', s)
    s = _IMAGE_OR_LINK.sub(r'\1', s)
    s = _NUM_CITE.sub(' ', s)
    s = _AUTHOR_YEAR_CITE.sub(' ', s)
    return _EMPHASIS.sub('', s)


# nexus: R15-C6 — markdown backslash escapes render as the bare character ("12\%" = "12%")
_MD_ESCAPE = re.compile(r'\\([\\`*_{}\[\]()#+\-.!|%$<>~])')


def _tokens(stripped: str) -> list[str]:
    return _TOKEN.findall(stripped.casefold())


def match_form(text: str) -> list[str]:
    """nexus: R15-D1 — the tokens the gate compares: normalise_text tokens,
    each stemmed (_stem)."""
    return [_stem(t) for t in normalise_text(text).split()]


# nexus: R15-D1 — light English stemming so an inflection change is no
# rewording: "banned" / "did not ban", "fell" / "did not fall" share a stem.
# Normalisation only (both sides alike); the gate still interprets nothing.
_IRREGULAR = {
    'fell': 'fall', 'fallen': 'fall', 'rose': 'rise', 'risen': 'rise', 'grew': 'grow', 'grown': 'grow',
    'shrank': 'shrink', 'shrunk': 'shrink', 'sank': 'sink', 'sunk': 'sink', 'won': 'win', 'lost': 'lose',
    'sold': 'sell', 'bought': 'buy', 'paid': 'pay', 'spent': 'spend', 'built': 'build', 'made': 'make',
    'took': 'take', 'taken': 'take', 'gave': 'give', 'given': 'give', 'went': 'go', 'gone': 'go',
    'saw': 'see', 'seen': 'see', 'led': 'lead', 'began': 'begin', 'begun': 'begin', 'kept': 'keep',
    'left': 'leave', 'met': 'meet', 'ran': 'run', 'held': 'hold', 'found': 'find', 'got': 'get',
    'brought': 'bring', 'became': 'become', 'came': 'come', 'said': 'say', 'told': 'tell',
    'thought': 'think', 'wrote': 'write', 'written': 'write', 'drove': 'drive', 'driven': 'drive',
    'beat': 'beat', 'beaten': 'beat', 'hit': 'hit', 'cut': 'cut', 'set': 'set', 'put': 'put',
}


@functools.lru_cache(maxsize=65536)
def _stem(token: str) -> str:
    if token.endswith("'s"):
        token = token[:-2]
    if not token.isalpha():
        return token
    token = _IRREGULAR.get(token, token)
    for suffix in ('ing', 'ed', 'es', 's'):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[:-len(suffix)]
            break
    if len(token) >= 4 and token[-1] == token[-2] and token[-1] not in 'aeiouls':
        token = token[:-1]
    if len(token) >= 4 and token.endswith('e'):
        token = token[:-1]
    return token


def _canonical_numbers(stripped: str) -> str:
    """nexus: replace each figure by its canonical value and kind
    (verify_claim_support), so "1500" / "1.5 thousand" and "12.0%" /
    "12 percent" are one token. The reading does not depend on the language
    of the text. A figure written with a single separator before a 3-digit
    group ("1,500", "1.500") reads 1500 in English and 1.5 in Portuguese (or
    the reverse); it becomes one token holding both readings ("1.5'1500"),
    the same token for both spellings, which _figures_kept matches against
    either reading."""
    from verify_claim_support import number_kind, number_matches  # lazy: it imports this module
    out, last = [], 0
    for m, value in number_matches(stripped):
        out.append(stripped[last:m.start()])
        raw = m.group('whole') + (m.group('sep') or '') + (m.group('frac') or '')
        if _AMBIGUOUS_FIGURE.fullmatch(raw) and not (m.group('word') or m.group('suffix')):
            head, group = raw[:-4], raw[-3:]
            readings = sorted({format(Decimal(head + group).normalize(), 'f'),
                               format(Decimal(head + '.' + group).normalize(), 'f')}, key=Decimal)
            value = "'".join(readings) + number_kind(value)
        out.append(f' {value} ')
        last = m.end()
    out.append(stripped[last:])
    return ''.join(out)


_AMBIGUOUS_FIGURE = re.compile(r'[1-9]\d{0,2}[.,]\d{3}')


def _figure_readings(token: str) -> tuple[set[str], str] | None:
    """nexus: (readings, kind) of a canonical figure token, None for words."""
    if not token[:1].isdigit():
        return None
    kind = token[-1] if token[-1] in '%x' else ''
    body = token[:-1] if kind else token
    return set(body.split("'")), kind


@functools.lru_cache(maxsize=65536)
def _token_keys(token: str, report_side: bool = False) -> frozenset:
    """nexus: the readings a token stands for: itself for a word, each
    reading (with its kind) for a figure, so "1.500" (token "1.5'1500")
    matches both "1500" and "1.5". On the report side a figure also offers
    its bare value: a range can give a report figure a kind its claim copy
    lacks ("fell to 25 and 30%" reads "25%"), so a bare claim figure matches
    the same value of any kind; a claim figure with a kind still needs it
    (R10-A1)."""
    r = _figure_readings(token)
    if not r:
        return frozenset((token,))
    readings, kind = r
    keys = {x + kind for x in readings}
    if report_side:
        keys |= readings
    return frozenset(keys)


def _shingle_keys(shingle: tuple[str, ...], report_side: bool = False) -> set[tuple[str, ...]]:
    keys: set[tuple[str, ...]] = {()}
    for tok in shingle:
        keys = {k + (x,) for k in keys for x in _token_keys(tok, report_side)}
    return keys


@functools.lru_cache(maxsize=65536)
def _keyed_shingles(tokens: tuple[str, ...]) -> frozenset:
    """nexus: every reading of every shingle of report tokens (cached)."""
    out: set[tuple[str, ...]] = set()
    for sh in _shingles(list(tokens)):
        out |= _shingle_keys(sh, report_side=True)
    return frozenset(out)


def _overlap(claim_tokens: list[str], sentence_tokens: list[str]) -> float:
    """nexus: share of the claim's shingles found in the sentence, a figure
    matching any of its readings (same kind)."""
    c = _shingles(claim_tokens)
    if not c:
        return 0.0
    s = _keyed_shingles(tuple(sentence_tokens))
    return sum(1 for sh in c if _shingle_keys(sh) & s) / len(c)


@functools.lru_cache(maxsize=8)
def _report_keys(report_norm: str) -> tuple:
    return tuple(_token_keys(_stem(t), True) for t in report_norm.split())


def _contains(claim_tokens: list[str], report_norm: str) -> bool:
    """nexus: the claim's tokens occur contiguously in the normalised report,
    a figure matching any of its readings."""
    want = [_token_keys(t) for t in claim_tokens]
    n = len(want)
    if not n:
        return False
    have = _report_keys(report_norm)
    first = want[0]
    return any(first & have[i] and all(want[k] & have[i + k] for k in range(1, n))
               for i in range(len(have) - n + 1))


def normalise_text(text: str) -> str:
    """Formatting-insensitive form: no markdown emphasis/code/link syntax, no
    citation markers ([1], [1, 2], [^1], (Author, 2020)), unified quotes and
    dashes, casefolded, punctuation dropped, whitespace collapsed, figures
    in canonical form."""
    return ' '.join(_tokens(_canonical_numbers(_strip_markup(text))))


def _shingles(tokens: list[str]) -> set[tuple[str, ...]]:
    if len(tokens) < SHINGLE_SIZE:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i:i + SHINGLE_SIZE]) for i in range(len(tokens) - SHINGLE_SIZE + 1)}


def shingle_overlap(claim: str, sentence: str) -> float:
    """Share of the claim's word shingles that appear in `sentence` (0..1)."""
    return _overlap(match_form(claim), match_form(sentence))


def report_sentences(report: str) -> list[str]:
    stripped = _strip_markup(report)
    return [s.strip() for s in _SENTENCE_SPLIT.split(stripped) if s and s.strip()]


def refuted_in_report(claim_text: str, report_norm: str, sentences: list[tuple[str, set]]) -> str | None:
    """Problem description if a refuted claim survives in the report, else None.

    nexus: strict gate (design decision 2026-11-19). The claim's normalised
    text (normalise_text: no markdown, no citation markers, figures by value
    and kind, quotes/dashes/spaces unified, casefolded) is present if it
    occurs anywhere in the normalised report, or if a report sentence or a
    window of consecutive report sentences (_best_window) covers
    >= REFUTED_OVERLAP_THRESHOLD of its 3-word shingles. Then the gate fails,
    always. Nothing is interpreted: negations, frames ("not true that", "no
    evidence that", "Não é verdade que"), "but"/"mas" and corrections that
    repeat the refuted wording all fail. Write the correction without
    restating the refuted claim ("sales grew 3%", not "it is not true that
    sales grew 12%"). A figure written with one separator before a 3-digit
    group ("1,500", "1.500") matches both its readings, so switching
    convention is not a correction. `sentences` gives the report sentences
    (raw text first; the second item is ignored)."""
    claim_tokens = match_form(claim_text)
    if not claim_tokens:
        return None
    if _contains(claim_tokens, report_norm):
        return ('refuted claim still present in the report (ignoring formatting/citation markers; '
                'a correction must not restate the refuted claim, even negated)')
    best, best_text = _best_window(claim_text, claim_tokens, [s for s, _ in sentences])
    if best >= REFUTED_OVERLAP_THRESHOLD:
        return (f'refuted claim near-duplicated in the report (shingle overlap {best:.2f} >= '
                f'{REFUTED_OVERLAP_THRESHOLD}; rewrite it without restating the refuted claim): '
                f'"{best_text[:160]}"')
    return None


_CLAIM_PIECES = re.compile(r'(?<=[.!?])\s+|\n')
_MAX_WINDOW = 8


@functools.lru_cache(maxsize=65536)
def _sentence_tokens(raw: str) -> tuple[str, ...]:
    return tuple(match_form(raw))


def _best_window(claim_text: str, claim_tokens: list[str], sentences: list[str]) -> tuple[float, str]:
    """nexus: best shingle coverage of the claim by a window of consecutive
    report sentences (R10-A2/A3). A claim can span several report sentences:
    the claim extractor and the gate split text differently (a sentence
    starting with a digit or an accented capital, joined bullet lines, an
    abbreviation such as "Inc." or "U.S."). Windows hold up to one sentence
    more than the claim has pieces; shingles crossing a sentence boundary
    count, as they do in the claim."""
    c = _shingles(claim_tokens)
    if not c or not sentences:
        return 0.0, ''
    ckeys = [(sh, _shingle_keys(sh)) for sh in c]
    pieces = len([p for p in _CLAIM_PIECES.split(_strip_markup(claim_text)) if p.strip()])
    width = min(_MAX_WINDOW, max(2, pieces + 1))
    toks = [_sentence_tokens(s) for s in sentences]
    # claim shingles found inside each sentence, and across each boundary
    inside = [frozenset(sh for sh, k in ckeys if k & _keyed_shingles(t)) for t in toks]
    across = [frozenset(sh for sh, k in ckeys
                        if k & _keyed_shingles(toks[i][-(SHINGLE_SIZE - 1):] + toks[i + 1][:SHINGLE_SIZE - 1]))
              if inside[i] or inside[i + 1] else frozenset()
              for i in range(len(toks) - 1)]
    best, best_i, best_j = 0.0, 0, 0
    for i in range(len(toks)):
        if not inside[i] and not (i < len(across) and across[i]):
            continue
        found: set = set(inside[i])
        for j in range(i, min(len(toks), i + width)):
            if j > i:
                found |= inside[j] | across[j - 1]
            score = len(found) / len(c)
            if score > best:
                best, best_i, best_j = score, i, j
    return best, ' '.join(sentences[best_i:best_j + 1])

# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_claim(votes: list[dict], deterministic: str | None, cfg: dict) -> dict:
    counts = Counter(v['verdict'] for v in votes)
    s, r, u = counts['supported'], counts['refuted'], counts['unverifiable']
    st, rt = cfg['support_threshold'], cfg['refute_threshold']

    if s >= st and r >= rt:
        status, why = 'contested', 'both support and refutation thresholds reached'
    elif r >= rt:
        status, why = 'refuted', f'{r} independent refutations'
    elif s >= st and deterministic == 'contradicted':
        status, why = 'contested', 'verifiers support it but stored evidence has opposite polarity'
    elif s >= st:
        status, why = 'supported', f'{s} independent confirmations'
    else:
        # nexus: undecided votes leave a claim unverified even when layer 1
        # flagged it as contradicted, so it counts toward --max-unverified-rate
        status = 'unverified'
        why = 'no votes yet' if not votes else (
            'verifiers could not check it' if u and not (s or r) else 'votes below thresholds')
        if deterministic == 'contradicted':
            why += '; deterministic layer found opposite-polarity evidence'

    patterns = Counter(p for v in votes for p in v.get('failure_patterns', []))
    corrections = [v['correction'] for v in votes if v.get('correction')]
    return {
        'corrections': corrections,
        'final_status': status,
        'reason': why,
        'votes': {'supported': s, 'refuted': r, 'unverifiable': u},
        'dissent': (r if status == 'supported' else s if status == 'refuted' else 0),
        'failure_patterns': dict(patterns),
    }


def votes_still_needed(votes: list[dict], cfg: dict) -> int:
    """Pigeonhole early exit: 0 when the outcome is decided or the budget is spent."""
    counts = Counter(v['verdict'] for v in votes)
    s, r = counts['supported'], counts['refuted']
    st, rt, mx = cfg['support_threshold'], cfg['refute_threshold'], cfg['max_verifiers']
    if r >= rt or (s >= st and r == 0):
        return 0
    remaining = mx - len(votes)
    if remaining <= 0:
        return 0
    # Can any outcome still be reached with the remaining votes?
    can_support = s + remaining >= st
    can_refute = r + remaining >= rt
    if not (can_support or can_refute):
        return 0
    need_s = max(st - s, 0) if can_support else remaining
    need_r = max(rt - r, 0) if can_refute else remaining
    return max(1, min(need_s, need_r, remaining))


def _cfg(args: argparse.Namespace) -> dict:
    cfg = dict(DEFAULTS)
    for k in cfg:
        v = getattr(args, k, None)
        if v is not None:
            cfg[k] = v
    if cfg['support_threshold'] < 1 or cfg['refute_threshold'] < 1:
        _fail('thresholds must be >= 1')
    if cfg['max_verifiers'] < max(cfg['support_threshold'], cfg['refute_threshold']):
        _fail('max_verifiers must be >= both thresholds')
    return cfg


def _votes_by_claim(run_dir: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for v in read_jsonl(os.path.join(run_dir, 'votes.jsonl')):
        out.setdefault(v['claim_id'], []).append(v)
    return out


def _wanted(claim: dict, types: list[str]) -> bool:
    return claim.get('claim_type', 'factual') in types


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_vote(args: argparse.Namespace) -> None:
    claims = _claims(args.dir)
    if args.claim_id not in claims:
        _fail(f'unknown claim_id {args.claim_id}')
    patterns = [p.strip() for p in (args.failure_patterns or '').split(',') if p.strip()]
    bad = [p for p in patterns if p not in FAILURE_PATTERNS]
    if bad:
        _fail(f'unknown failure pattern(s): {bad}; allowed: {sorted(FAILURE_PATTERNS)}')
    if args.verdict == 'refuted' and not patterns:
        _fail('a refutation must name at least one failure pattern')
    if args.correction and args.verdict != 'refuted':
        _fail('--correction is only valid with verdict refuted')
    existing = _votes_by_claim(args.dir).get(args.claim_id, [])
    if any(v['verifier_id'] == args.verifier_id for v in existing):
        _fail(f'verifier {args.verifier_id} already voted on {args.claim_id} (one vote per verifier)')
    row = {
        'claim_id': args.claim_id,
        'verifier_id': args.verifier_id,
        'verdict': args.verdict,
        'rationale': args.rationale or '',
        'evidence_ids': [e for e in (args.evidence_ids or '').split(',') if e],
        'failure_patterns': patterns,
        'correction': args.correction or None,
        'voted_at': datetime.now(timezone.utc).isoformat(),
    }
    append_jsonl(os.path.join(args.dir, 'votes.jsonl'), row)
    print(json.dumps({'status': 'recorded', 'claim_id': args.claim_id, 'verifier_id': args.verifier_id}))


def cmd_pending(args: argparse.Namespace) -> None:
    cfg = _cfg(args)
    votes = _votes_by_claim(args.dir)
    pending = []
    for cid, c in _claims(args.dir).items():
        if not _wanted(c, args.types):
            continue
        need = votes_still_needed(votes.get(cid, []), cfg)
        if need:
            pending.append({'claim_id': cid, 'section_id': c.get('section_id'),
                            'text': c.get('text'), 'votes_cast': len(votes.get(cid, [])),
                            'launch_verifiers': need})
    print(json.dumps({'pending': len(pending), 'config': cfg, 'claims': pending},
                     indent=2, ensure_ascii=False))


def build_ledger(run_dir: str, cfg: dict, types: list[str]) -> list[dict]:
    claims = _claims(run_dir)
    votes = _votes_by_claim(run_dir)
    sources = {s['source_id']: s for s in read_jsonl(os.path.join(run_dir, 'sources.jsonl'))}
    rows = []
    for cid, c in claims.items():
        if not _wanted(c, types):
            continue
        res = resolve_claim(votes.get(cid, []), c.get('support_status'), cfg)
        fams = sorted({source_family(sources[s]) for s in c.get('cited_source_ids', []) if s in sources})
        rows.append({
            'claim_id': cid,
            'section_id': c.get('section_id'),
            'claim_type': c.get('claim_type', 'factual'),
            'text': c.get('text'),
            'deterministic_status': c.get('support_status'),
            'source_families': fams,
            **res,
        })
    return rows


def cmd_resolve(args: argparse.Namespace) -> None:
    cfg = _cfg(args)
    rows = build_ledger(args.dir, cfg, args.types)
    write_jsonl(os.path.join(args.dir, 'claim_ledger.jsonl'), rows)
    print(json.dumps({
        'status': 'ok',
        'claims': len(rows),
        'final_status_counts': dict(Counter(r['final_status'] for r in rows)),
        'config': cfg,
    }, indent=2))


def cmd_gate(args: argparse.Namespace) -> None:
    cfg = _cfg(args)
    rows = build_ledger(args.dir, cfg, args.types)
    report = ''
    if args.report:
        with open(args.report, encoding='utf-8') as f:
            report = f.read()

    report_norm = normalise_text(report) if report else ''
    sentences = [(s, _shingles(normalise_text(s).split())) for s in report_sentences(report)] if report else []

    problems, warnings = [], []
    for r in rows:
        cid = r['claim_id']
        if r['final_status'] == 'refuted':
            if report:
                hit = refuted_in_report(r['text'] or '', report_norm, sentences)
                if hit:
                    problems.append(f'{cid}: {hit}')
            else:
                problems.append(f'{cid}: refuted — remove or rewrite it, then re-extract claims')
        if r['final_status'] in ('unverified', 'contested') and report and cid not in report:
            problems.append(f'{cid}: {r["final_status"]} but not listed in the report claim ledger')
        if r['final_status'] == 'supported' and len(r['source_families']) < args.min_families:
            msg = f'{cid}: supported by {len(r["source_families"])} source family(ies) (< {args.min_families})'
            (problems if args.strict_independence else warnings).append(msg)

    total = len(rows)
    unverified = sum(1 for r in rows if r['final_status'] == 'unverified')
    if total and unverified / total > args.max_unverified_rate:
        problems.append(f'unverified rate {unverified}/{total} exceeds {args.max_unverified_rate:.0%}')

    passed = not problems
    print(json.dumps({'status': 'pass' if passed else 'fail', 'problems': problems,
                      'warnings': warnings,
                      'final_status_counts': dict(Counter(r['final_status'] for r in rows))},
                     indent=2, ensure_ascii=False))
    if not passed:
        sys.exit(1)


def _md(s: str) -> str:
    return (s or '').replace('|', '\\|').replace('\n', ' ')


def cmd_table(args: argparse.Namespace) -> None:
    cfg = _cfg(args)
    rows = build_ledger(args.dir, cfg, args.types)
    order = {'refuted': 0, 'contested': 1, 'unverified': 2, 'supported': 3}
    rows.sort(key=lambda r: (order[r['final_status']], r['section_id'] or ''))
    print('| Claim | Section | Status | Votes S/R/U | Source families | Notes |')
    print('|---|---|---|---|---|---|')
    for r in rows:
        v = r['votes']
        # nexus: a refuted claim's text is never printed, so pasting this
        # table as the report appendix cannot trip the refuted-text gate
        text = ('_(refuted claim text withheld; see claim_ledger.jsonl)_' if r['final_status'] == 'refuted'
                else _md(r['text'])[:140])
        notes = _md(r['reason'])
        if r['failure_patterns']:
            notes += '; patterns: ' + ', '.join(sorted(r['failure_patterns']))
        if r['corrections']:
            notes += f'; {len(r["corrections"])} correction(s) proposed'
        print(f'| `{r["claim_id"]}` {text} | {r["section_id"]} | **{r["final_status"]}** | '
              f'{v["supported"]}/{v["refuted"]}/{v["unverifiable"]} | {len(r["source_families"])} | {notes} |')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(prog='claim_ledger', description='Claim ledger: verifier votes, resolution and delivery gate')
    sub = p.add_subparsers(dest='command', required=True)

    def common(sp, with_types=True):
        sp.add_argument('--dir', required=True, help='Run directory')
        sp.add_argument('--support-threshold', type=int, dest='support_threshold')
        sp.add_argument('--refute-threshold', type=int, dest='refute_threshold')
        sp.add_argument('--max-verifiers', type=int, dest='max_verifiers')
        if with_types:
            sp.add_argument('--types', nargs='+', default=['factual'],
                            help='claim types to verify (default: factual)')

    sv = sub.add_parser('vote', help='Record one verifier vote')
    sv.add_argument('--dir', required=True)
    sv.add_argument('--claim-id', required=True)
    sv.add_argument('--verifier-id', required=True, help='unique per verifier agent, e.g. v1')
    sv.add_argument('--verdict', required=True, choices=VERDICTS)
    sv.add_argument('--rationale')
    sv.add_argument('--evidence-ids', help='comma-separated evidence_ids the verifier checked')
    sv.add_argument('--failure-patterns', help='comma-separated pattern codes (required for refuted)')
    sv.add_argument('--correction', help='refuted only: what the source actually supports. The orchestrator '
                    'adds it as a NEW claim, which needs its own fresh verifiers (never self-validating)')

    common(sub.add_parser('pending', help='Claims that still need verifier votes'))
    common(sub.add_parser('resolve', help='Resolve votes into claim_ledger.jsonl'))
    sg = sub.add_parser('gate', help='Delivery gate (exit 1 on problems)')
    common(sg)
    sg.add_argument('--report', help='Final report markdown; refuted text must be gone and gaps listed')
    sg.add_argument('--min-families', type=int, default=2)
    sg.add_argument('--strict-independence', action='store_true',
                    help='fail (not warn) when a supported claim has < min-families')
    sg.add_argument('--max-unverified-rate', type=float, default=0.25)
    common(sub.add_parser('table', help='Markdown ledger table'))

    args = p.parse_args()
    {'vote': cmd_vote, 'pending': cmd_pending, 'resolve': cmd_resolve,
     'gate': cmd_gate, 'table': cmd_table}[args.command](args)


if __name__ == '__main__':
    main()
