#!/usr/bin/env python3
"""
Atomic Claim Extractor — decomposes report sections into typed claims.

CLI subcommands:
  extract      Parse a markdown report into atomic claims (claims.jsonl)
  add          Manually add a single claim
  list         List claims, optionally filtered by section or type
  stats        Show claim statistics (counts by type/status)

Claim identity:
  claim_id = sha256(section_id + normalized_text)[:16]

Claim types (per GPT Pro's refinement of Codex's proposal):
  - factual: hard-fails on lack of support
  - synthesis: needs traceability, softer threshold
  - recommendation: needs traceability, softer threshold
  - speculation: labeled, no support gate
"""

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Claim ID computation
# ---------------------------------------------------------------------------

_WHITESPACE_RE = re.compile(r'\s+')


def normalize_text(text: str) -> str:
    """Normalize for stable hashing."""
    return _WHITESPACE_RE.sub(' ', text.strip()).lower()


def compute_claim_id(section_id: str, text: str) -> str:
    """sha256(section_id + normalized_text)[:16] hex."""
    payload = section_id + normalize_text(text)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]


# ---------------------------------------------------------------------------
# JSONL helpers
# ---------------------------------------------------------------------------

def append_jsonl(path: str, obj: dict) -> None:
    with open(path, 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Report parsing helpers
# ---------------------------------------------------------------------------

# Section header patterns
SECTION_PATTERNS = [
    (re.compile(r'^##\s+Executive\s+Summary', re.I), 'executive_summary'),
    (re.compile(r'^##\s+Introduction', re.I), 'introduction'),
    (re.compile(r'^##\s+Finding\s+(\d+)', re.I), lambda m: f'finding_{m.group(1)}'),
    (re.compile(r'^##\s+Synthesis', re.I), 'synthesis'),
    (re.compile(r'^##\s+Limitations', re.I), 'limitations'),
    (re.compile(r'^##\s+Recommendations', re.I), 'recommendations'),
    (re.compile(r'^##\s+Conclusion', re.I), 'conclusion'),
    (re.compile(r'^##\s+(.+)', re.I), lambda m: re.sub(r'\W+', '_', m.group(1).strip().lower())[:30]),
]

# Citation markers: [N], [N, M], [N; M], [N-M] (range), [^N] (footnote)
CITATION_RE = re.compile(r'\[\s*\^?\s*(\d+(?:\s*[-\u2013,;]\s*\^?\s*\d+)*)\s*\]')
MAX_CITATION_RANGE = 50


def citation_numbers(sentence: str) -> list[int]:
    """nexus: display numbers cited in a sentence, ranges expanded."""
    out: list[int] = []
    for m in CITATION_RE.finditer(sentence):
        for part in re.split(r'\s*[,;]\s*', m.group(1)):
            ends = [int(x) for x in re.findall(r'\d+', part)]
            if len(ends) == 2 and 0 <= ends[1] - ends[0] <= MAX_CITATION_RANGE:
                ends = list(range(ends[0], ends[1] + 1))
            out.extend(n for n in ends if n not in out)
    return out


# nexus: sections that hold references or the method, not findings
NON_CLAIM_SECTIONS = ('bibliograph', 'references', 'works_cited', 'further_reading',
                      'methodology', 'appendix', 'claim_ledger', 'report_metadata')
NON_CLAIM_EXACT = ('sources', 'reference')


def section_kind(section_id: str) -> str:
    """nexus: section id without leading numbering ("7_references" ->
    "references"), so numbered headings match like plain ones. The
    section_id itself (part of claim_id) is unchanged."""
    return re.sub(r'^(?:\d+[._-]?)+_*', '', section_id or '') or section_id


def _kind_is(kind: str, *names: str) -> bool:
    """nexus: the section kind is one of names, alone or followed by a
    qualifier when the name is one SECTION_PATTERNS also matches as a
    heading prefix ("recommendations_for_policymakers",
    "conclusion_and_outlook"), so a numbered heading classifies like the
    same heading unnumbered. "recommendation_algorithms" is not
    Recommendations (the pattern needs the plural)."""
    return any(kind == n or (n in _QUALIFIABLE_KINDS and kind.startswith(n)) for n in names)


# nexus: the kinds SECTION_PATTERNS recognises by heading prefix
_QUALIFIABLE_KINDS = frozenset(['recommendations', 'synthesis', 'conclusion', 'conclusions', 'limitations'])


def is_non_claim_section(section_id: str) -> bool:
    kind = section_kind(section_id)
    return section_id == 'preamble' or kind in NON_CLAIM_EXACT \
        or kind.startswith(NON_CLAIM_SECTIONS)

# Sections whose uncited prose without figures is scope/meta text
META_SECTIONS = ('introduction', 'limitations')
_YEAR_RE = re.compile(r'\b(?:19|20)\d{2}\b')


def is_meta_sentence(sentence: str, section_id: str) -> bool:
    """Uncited sentence without a figure in the introduction or limitations:
    scope or method text, not a claim to verify."""
    # nexus: a numbered label ("Assumption 1:") is not a figure, and the
    # template's "Confidence Level:" line is a self-assessment (R12-F4)
    if (not CITATION_RE.search(sentence) and _CONFIDENCE_LABEL_RE.match(sentence)
            and _plain(section_kind(section_id)).startswith(('executive_summary', 'summary', 'resumo', 'sumario'))):
        return True
    body = _NUMBERED_LABEL_RE.sub(' ', sentence)
    return (section_kind(section_id).startswith(META_SECTIONS) and not CITATION_RE.search(sentence)
            and not re.search(r'\d', _YEAR_RE.sub(' ', body)))


def _plain(text: str) -> str:
    """nexus: text without diacritics ("sumário" -> "sumario") (R14-C1)."""
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


_NUMBERED_LABEL_RE = re.compile(r'^\W*[^\W\d_]+(?: [^\W\d_]+)? \d{1,2}\s*:')
_CONFIDENCE_LABEL_RE = re.compile(r'^\W*(?:confidence(?: level)?|n[ií]vel de confian[cç]a|confian[cç]a)\s*:', re.I)

# Sentence splitting (basic but handles abbreviations)
SENTENCE_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')


_RECOMMENDATION_RE = re.compile(
    r"\b(?:should|ought to|recommend(?:s|ed|ing|ation)?|we (?:advise|suggest|propose))\b"
    r"|^\W*(?:consider|avoid|prefer)\b", re.I)
_SPECULATION_RE = re.compile(
    r"\b(?:might|could potentially|it is possible|may eventually|hypothetically|speculatively)\b",
    re.I)
_SYNTHESIS_RE = re.compile(
    r"\b(?:overall|taken together|collectively|the evidence suggests|this implies)\b", re.I)


def classify_claim(text: str, section_id: str) -> str:
    """Heuristic claim type classification.

    nexus: keywords match whole words ("suggests" and "considered" are not
    recommendations), and a sentence that cites a source and states a
    figure other than a year is factual outside Recommendations, whatever
    its hedging: the cited figure must be checked against the source."""
    kind = section_kind(section_id)  # nexus: "9_recommendations_for_x" -> "recommendations_for_x"
    # nexus: R15-D4 — the figure override holds for uncited sentences too: an
    # uncited figure hedged with "might"/"should" is still a figure to check
    if (not _kind_is(kind, 'recommendations', 'recommendation')
            and re.search(r'\d', _YEAR_RE.sub(' ', CITATION_RE.sub(' ', text)))):
        return 'factual'
    if _kind_is(kind, 'synthesis', 'conclusion', 'conclusions', 'limitations') and _SYNTHESIS_RE.search(text):
        return 'synthesis'
    if _RECOMMENDATION_RE.search(text):
        return 'recommendation'
    if _SPECULATION_RE.search(text):
        return 'speculation'
    return 'factual'


def parse_sections(markdown: str) -> list[tuple[str, str]]:
    """Parse markdown into (section_id, content) pairs."""
    lines = markdown.split('\n')
    sections = []
    current_id = 'preamble'
    current_lines = []

    for line in lines:
        matched = False
        for pattern, id_or_fn in SECTION_PATTERNS:
            m = pattern.match(line)
            if m:
                if current_lines:
                    sections.append((current_id, '\n'.join(current_lines)))
                current_id = id_or_fn(m) if callable(id_or_fn) else id_or_fn
                current_lines = []
                matched = True
                break
        if not matched:
            current_lines.append(line)

    if current_lines:
        sections.append((current_id, '\n'.join(current_lines)))

    return sections


# nexus: markdown block structure for extraction (R11-F1, R12-C1/C6/F2/F4/F5)
_FENCE_RE = re.compile(r'^[ \t]*(`{3,}|~{3,}).*?(?:^[ \t]*\1[^\n]*$|\Z)', re.M | re.S)
# nexus: an inline comment is a space; one on lines of its own leaves a blank line (R13-C2)
_INLINE_COMMENT_RE = re.compile(r'[ \t]*<!--.*?-->[ \t]*', re.S)
_ATX_HEADING_RE = re.compile(r'^[ \t]{0,3}#{1,6}(?:[ \t]|$)')
_THEMATIC_BREAK_RE = re.compile(r'^[ \t]{0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$')
_HTML_BLOCK_LINE_RE = re.compile(r'^[ \t]*</?[a-zA-Z][\w-]*(?:\s[^<>]*)?/?>[ \t]*$')
_LIST_ITEM_RE = re.compile(r'^[ \t]*(?:[-*+]|(\d{1,9})[.)])[ \t]+')
_BLOCKQUOTE_RE = re.compile(r'^[ \t]*(?:>[ \t]?)+')
_MONTHS = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b\.?"
# nexus: figures that do not make a short sentence a claim: a reference to a
# table/figure/section/version/page, a date, a bare year
_NON_FIGURE_RE = re.compile(
    r'\b(?:table|tab|figure|fig|section|sec|chapter|ch|appendix|version|v|page|pp?|item|step|no|n[.ºo])\.?\s*\d[\d.]*'
    r'|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:de\s+)?' + _MONTHS + r'(?:\s+(?:de\s+)?\d{4})?'
    r'|\b' + _MONTHS + r'\s+\d{1,2}(?:st|nd|rd|th)?\b(?:,?\s+\d{4})?'
    r'|\b(?:19|20)\d{2}\b(?![.,]?\d|\s*%)', re.I)
_WORD_RE = re.compile(r'[^\W\d_]{2,}')


def _blocks(text: str) -> list[str]:
    """nexus: paragraphs, list items and blockquote paragraphs of a markdown
    section. HTML comments, fenced code, headings, table rows, thematic
    breaks and HTML block lines are not text and end the block they
    interrupt, so a sentence next to them is neither lost (R11-F1) nor merged
    with its neighbours (R12-F5); each list item is its own block without
    its marker (R12-C1)."""
    text = '\n'.join(_BLOCKQUOTE_RE.sub('', line) for line in text.split('\n'))
    text = _INLINE_COMMENT_RE.sub(' ', text)   # a comment on its own lines leaves a blank line
    text = _FENCE_RE.sub('\n\n', text)
    blocks: list[str] = []
    cur: list[str] = []

    def flush():
        if cur:
            blocks.append('\n'.join(cur))
            cur.clear()

    last_num = None     # number of the current ordered-list item
    for line in text.split('\n'):
        if (not line.strip() or _ATX_HEADING_RE.match(line) or line.lstrip().startswith('|')
                or _THEMATIC_BREAK_RE.match(line) or _HTML_BLOCK_LINE_RE.match(line)):
            flush()
            last_num = None
            continue
        m = _LIST_ITEM_RE.match(line)
        # nexus: inside a paragraph only a bullet or "1." starts a list; "2023. Margins"
        # on a wrapped line continues the sentence (R13-C1)
        # nexus: inside a paragraph or list item a bullet, "1." or the next
        # number of the current list starts an item; "2023. Margins" on a
        # wrapped line continues the sentence (R13-C1, R14-C3)
        num = int(m.group(1)) if m and m.group(1) else None
        if m and (not cur or num in (None, 1) or (last_num is not None and num == last_num + 1)):
            flush()
            last_num = num
            line = line[m.end():]
        cur.append(line.strip())
    flush()
    return blocks


def is_claim_sentence(s: str) -> bool:
    """nexus: a sentence is a claim candidate when it has at least 2 words
    besides citation markers and figures, and is longer than 30 characters,
    or shorter but states a figure — not only a table/figure/section/version
    reference, a date or a year — or cites a source with at least 3 words
    (R11-F2, R12-C2/C3/F1). Label lines such as "Sources: [1], [2]",
    "See also [5]." or "Ibid. [4]" are not claims."""
    bare = CITATION_RE.sub(' ', s)
    words = len(_WORD_RE.findall(bare))
    figure = bool(re.search(r'\d', _NON_FIGURE_RE.sub(' ', bare)))
    if figure and CITATION_RE.search(s):
        return True     # "Slowdown: 8% [2]", "2023: 19% [4]" (R13-C3, R14-C2)
    if words < 2 or len(bare.split()) < 3:
        return False
    if len(s) > 30 or figure:
        return True
    return bool(CITATION_RE.search(s)) and words >= 3


def extract_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering noise."""
    result = []
    for block in _blocks(text):
        block = re.sub(r'\*\*([^*]+)\*\*', r'\1', block)  # bold
        block = re.sub(r'\*([^*]+)\*', r'\1', block)  # italic
        for s in SENTENCE_RE.split(block):
            s = s.strip()
            if s and is_claim_sentence(s):
                result.append(s)
    return result


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_extract(args: argparse.Namespace) -> None:
    """Extract atomic claims from a markdown report."""
    report_path = args.report
    if not os.path.exists(report_path):
        print(json.dumps({'error': f'Report not found: {report_path}'}), file=sys.stderr)
        sys.exit(1)

    with open(report_path) as f:
        markdown = f.read()

    claims_path = os.path.join(args.dir, 'claims.jsonl')
    existing_ids = {r['claim_id'] for r in read_jsonl(claims_path)}
    # nexus: [N] markers link to the N-th distinct source in sources.jsonl
    # (the numbering of citation_manager.py assign-display-numbers and
    # export-bibliography)
    by_number = display_numbers(args.dir)
    unlinked: set[int] = set()

    sections = parse_sections(markdown)
    added = 0
    skipped = 0

    for section_id, content in sections:
        if is_non_claim_section(section_id):
            continue
        sentences = extract_sentences(content)
        for sentence in sentences:
            if is_meta_sentence(sentence, section_id):
                continue
            claim_id = compute_claim_id(section_id, sentence)
            if claim_id in existing_ids:
                skipped += 1
                continue

            # Link citation numbers in the sentence to source_ids
            cited = []
            for n in citation_numbers(sentence):
                sid = by_number.get(n)
                if sid is None:
                    unlinked.add(n)
                elif sid not in cited:
                    cited.append(sid)

            claim = {
                'claim_id': claim_id,
                'section_id': section_id,
                'text': sentence,
                'claim_type': classify_claim(sentence, section_id),
                'cited_source_ids': cited,
                'evidence_ids': [],  # optional: verify_claim_support also reads the cited sources' evidence
                'support_status': 'unverified',
                'extracted_at': datetime.now(timezone.utc).isoformat(),
            }
            append_jsonl(claims_path, claim)
            existing_ids.add(claim_id)
            added += 1

    print(json.dumps({
        'status': 'ok',
        'claims_added': added,
        'claims_skipped': skipped,
        'total_claims': len(existing_ids),
        'unlinked_citation_numbers': sorted(unlinked),
    }))


def display_numbers(run_dir: str) -> dict[int, str]:
    """Display number -> source_id, in registration order of distinct sources."""
    out: dict[int, str] = {}
    seen: set[str] = set()
    for src in read_jsonl(os.path.join(run_dir, 'sources.jsonl')):
        sid = src.get('source_id')
        if sid and sid not in seen:
            seen.add(sid)
            out[len(seen)] = sid
    return out


def cmd_add(args: argparse.Namespace) -> None:
    """Manually add a single claim."""
    data = json.loads(args.json)
    section_id = data.get('section_id', 'unknown')
    text = data.get('text', '')
    if not text:
        print(json.dumps({'error': 'text is required'}), file=sys.stderr)
        sys.exit(1)

    claim_id = compute_claim_id(section_id, text)
    claims_path = os.path.join(args.dir, 'claims.jsonl')

    existing = read_jsonl(claims_path)
    for row in existing:
        if row.get('claim_id') == claim_id:
            print(json.dumps({'status': 'duplicate', 'claim_id': claim_id}))
            return

    valid_types = {'factual', 'synthesis', 'recommendation', 'speculation'}
    claim_type = data.get('claim_type', 'factual')
    if claim_type not in valid_types:
        claim_type = 'factual'

    claim = {
        'claim_id': claim_id,
        'section_id': section_id,
        'text': text,
        'claim_type': claim_type,
        'cited_source_ids': data.get('cited_source_ids', []),
        'evidence_ids': data.get('evidence_ids', []),
        'support_status': 'unverified',
        'extracted_at': datetime.now(timezone.utc).isoformat(),
    }
    append_jsonl(claims_path, claim)
    print(json.dumps({'status': 'added', 'claim_id': claim_id}))


def cmd_list(args: argparse.Namespace) -> None:
    """List claims with optional filters."""
    claims_path = os.path.join(args.dir, 'claims.jsonl')
    rows = read_jsonl(claims_path)

    if args.section:
        rows = [r for r in rows if r.get('section_id') == args.section]
    if args.type:
        rows = [r for r in rows if r.get('claim_type') == args.type]
    if args.status:
        rows = [r for r in rows if r.get('support_status') == args.status]

    # Deduplicate
    seen = set()
    unique = []
    for r in rows:
        cid = r.get('claim_id')
        if cid not in seen:
            seen.add(cid)
            unique.append(r)

    print(json.dumps({'count': len(unique), 'claims': unique}, indent=2, ensure_ascii=False))


def cmd_stats(args: argparse.Namespace) -> None:
    """Show claim statistics."""
    claims_path = os.path.join(args.dir, 'claims.jsonl')
    rows = read_jsonl(claims_path)

    # Deduplicate
    seen = set()
    unique = []
    for r in rows:
        cid = r.get('claim_id')
        if cid not in seen:
            seen.add(cid)
            unique.append(r)

    by_type = {}
    by_status = {}
    by_section = {}
    for r in unique:
        t = r.get('claim_type', 'unknown')
        s = r.get('support_status', 'unknown')
        sec = r.get('section_id', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
        by_section[sec] = by_section.get(sec, 0) + 1

    print(json.dumps({
        'total': len(unique),
        'by_type': by_type,
        'by_status': by_status,
        'by_section': by_section,
    }, indent=2))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog='extract_claims',
        description='Atomic claim extraction and ledger for deep-research v3.0',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # extract
    p_ext = sub.add_parser('extract', help='Extract claims from markdown report')
    p_ext.add_argument('--report', required=True, help='Path to report.md')
    p_ext.add_argument('--dir', required=True, help='Run directory containing claims.jsonl')

    # add
    p_add = sub.add_parser('add', help='Manually add a single claim')
    p_add.add_argument('--json', required=True, help='JSON with section_id, text, claim_type')
    p_add.add_argument('--dir', required=True, help='Run directory')

    # list
    p_list = sub.add_parser('list', help='List claims')
    p_list.add_argument('--dir', required=True, help='Run directory')
    p_list.add_argument('--section', default=None, help='Filter by section_id')
    p_list.add_argument('--type', default=None, help='Filter by claim_type')
    p_list.add_argument('--status', default=None, help='Filter by support_status')

    # stats
    p_stats = sub.add_parser('stats', help='Claim statistics')
    p_stats.add_argument('--dir', required=True, help='Run directory')

    args = parser.parse_args()
    dispatch = {
        'extract': cmd_extract,
        'add': cmd_add,
        'list': cmd_list,
        'stats': cmd_stats,
    }
    dispatch[args.command](args)


if __name__ == '__main__':
    main()
