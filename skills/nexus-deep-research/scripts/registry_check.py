#!/usr/bin/env python3
"""
Registry Check — verify that cited academic identifiers exist, match the
claimed metadata, and are not retracted.

LLMs fabricate plausible DOIs, attach real DOIs to the wrong paper, and cite
retracted work. This script resolves every DOI / arXiv / PubMed identifier in
sources.jsonl against the authoritative registry and compares title and year.

Inspired by the Hermes `citation-guard` plugin (DOI/PMID/arXiv resolution,
retraction detection, no API keys) and K-Dense `verify_citations.py`.

Registries (no keys needed):
  DOI    https://doi.org/<doi> with Accept: application/vnd.citationstyles.csl+json
         (works for Crossref and DataCite DOIs; Crossref records carry
         `updated-by` entries from Retraction Watch: type retraction /
         withdrawal / removal / expression_of_concern / correction)
         fallback: https://api.crossref.org/works/<doi>
  arXiv  https://export.arxiv.org/api/query?id_list=<id>
  PubMed https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi (pubtype
         "Retracted Publication")

Result statuses:
  verified          identifier resolves and title/year agree
  metadata_mismatch identifier resolves to a DIFFERENT title (or year off by >1)
  retracted         registry marks the work retracted / withdrawn / removed
  concern           expression of concern on record
  not_found         identifier does not resolve (likely fabricated): a registry
                    answered 404 and no lookup failed transiently
  error             network / registry error — status unknown, NOT a pass
                    (timeout, 408/429/5xx on any lookup, or doi.org resolves
                    without metadata and Crossref has no record)
  skipped           not an academic identifier (plain URL)

CLI:
  check    check every source in a run directory (writes registry_checks.jsonl)
  lookup   check one identifier (doi:..., arxiv:..., pmid:...)

`check --strict` exits 1 on retracted, not_found or metadata_mismatch.
"""

import argparse
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib import error, request
from urllib.parse import quote

USER_AGENT = 'nexus-deep-research/1.0 (registry_check; fork of 199-biotechnologies/claude-deep-research-skill)'
RETRACTION_TYPES = frozenset(['retraction', 'withdrawal', 'removal', 'retracted', 'withdrawn'])
CONCERN_TYPES = frozenset(['expression_of_concern', 'expression-of-concern', 'concern'])
FAILING = ('retracted', 'not_found', 'metadata_mismatch')

_DOI_RE = re.compile(r'(10\.\d{4,9}/[^\s"<>]+)', re.IGNORECASE)
_ARXIV_RE = re.compile(r'(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)', re.IGNORECASE)


# ---------------------------------------------------------------------------
# HTTP (injectable for tests)
# ---------------------------------------------------------------------------

class Fetcher:
    """Minimal GET client. Returns (status_code, body_text). Never raises."""

    def __init__(self, timeout: float = 15.0, pause: float = 0.35):
        self.timeout = timeout
        self.pause = pause
        self._last = 0.0

    def get(self, url: str, accept: str = 'application/json') -> tuple[int, str]:
        wait = self.pause - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()
        req = request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': accept})
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode('utf-8', errors='replace')
        except error.HTTPError as e:
            return e.code, ''
        except Exception as e:  # network, TLS, timeout
            return 0, str(e)


# ---------------------------------------------------------------------------
# Identifier parsing
# ---------------------------------------------------------------------------

def parse_identifier(locator: str) -> tuple[str, str] | None:
    """Return (kind, id) for doi:/arxiv:/pmid: locators or recognisable URLs."""
    loc = (locator or '').strip()
    low = loc.lower()
    if low.startswith('doi:'):
        return ('doi', loc[4:].strip())
    if low.startswith('arxiv:'):
        return ('arxiv', loc[6:].strip())
    if low.startswith('pmid:'):
        return ('pmid', loc[5:].strip())
    m = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', low)
    if m:
        return ('pmid', m.group(1))
    if 'arxiv.org/' in low:
        m = re.search(r'arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:\.pdf)?(?:[?#]|$)', loc, re.IGNORECASE)
        if m:
            return ('arxiv', m.group(1))
    m = _DOI_RE.search(loc)
    if m and ('doi.org/' in low or low.startswith('10.')):
        return ('doi', m.group(1).rstrip('.,;)'))
    return None


# ---------------------------------------------------------------------------
# Registry lookups -> normalised metadata dict
#   {found: bool, title: str|None, year: int|None, flags: set[str], source: str}
#   found None => registry error (unknown)
# ---------------------------------------------------------------------------

def _year_from_parts(obj: dict | None) -> int | None:
    try:
        return int(obj['date-parts'][0][0])
    except Exception:
        return None


def _flags_from_updates(updates) -> set[str]:
    flags = set()
    for u in updates or []:
        t = str(u.get('type', '')).lower()
        if t in RETRACTION_TYPES:
            flags.add('retracted')
        elif t in CONCERN_TYPES:
            flags.add('concern')
    return flags


def _transient(status: int) -> bool:
    """Network failure, timeout, rate limit, server error or access wall
    (401/403 bot walls): says nothing about existence."""
    return status in (0, 401, 403, 408, 429) or status >= 500


def lookup_doi(doi: str, fetcher: Fetcher) -> dict:
    status, body = fetcher.get(f'https://doi.org/{quote(doi, safe="/()._-;:")}',
                               accept='application/vnd.citationstyles.csl+json')
    source = 'doi.org'
    data = None
    # nexus: `not_found` needs an authoritative "does not exist" (HTTP 404) and no
    # transient error on any lookup. A Crossref 404 alone is not enough when doi.org
    # timed out / 5xx'd (DataCite DOIs such as Zenodo are absent from Crossref), nor
    # when doi.org answered 200 without CSL JSON (the DOI resolves).
    absent = status == 404
    unknown = []
    if _transient(status):
        unknown.append(f'doi.org HTTP {status}')
    if status == 200:
        try:
            data = json.loads(body)
        except ValueError:
            data = None
            unknown.append('doi.org resolves but returned no CSL metadata')
    if data is None and status != 404:
        # Fallback: Crossref REST API
        s2, b2 = fetcher.get(f'https://api.crossref.org/works/{quote(doi, safe="/()._-;:")}')
        source = 'crossref'
        if s2 == 200:
            try:
                data = json.loads(b2).get('message')
            except ValueError:
                data = None
        elif s2 == 404:
            absent = True
        if _transient(s2):
            unknown.append(f'crossref HTTP {s2}')
        if data is None:
            status = s2
    if data is None:
        if absent and not unknown:
            return {'found': False, 'title': None, 'year': None, 'flags': set(), 'source': source}
        return {'found': None, 'title': None, 'year': None, 'flags': set(), 'source': source,
                'error': '; '.join(unknown) or f'HTTP {status}'}
    title = data.get('title')
    if isinstance(title, list):
        title = title[0] if title else None
    # nexus: Crossref keeps the subtitle in its own field
    subtitle = data.get('subtitle')
    if isinstance(subtitle, list):
        subtitle = subtitle[0] if subtitle else None
    if title and subtitle and isinstance(subtitle, str) and subtitle.strip():
        title = f'{title}: {subtitle}'
    year = _year_from_parts(data.get('issued')) or _year_from_parts(data.get('published-print')) \
        or _year_from_parts(data.get('published-online'))
    flags = _flags_from_updates(data.get('updated-by'))
    if title and re.match(r'^\s*(retracted|withdrawn)\b', title, re.IGNORECASE):
        flags.add('retracted')
    return {'found': True, 'title': title, 'year': year, 'flags': flags, 'source': source}


_ATOM = '{http://www.w3.org/2005/Atom}'


def lookup_arxiv(arxiv_id: str, fetcher: Fetcher) -> dict:
    status, body = fetcher.get(f'https://export.arxiv.org/api/query?id_list={quote(arxiv_id)}',
                               accept='application/atom+xml')
    if status != 200:
        return {'found': None, 'title': None, 'year': None, 'flags': set(), 'source': 'arxiv',
                'error': f'HTTP {status}'}
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {'found': None, 'title': None, 'year': None, 'flags': set(), 'source': 'arxiv',
                'error': 'unparseable Atom'}
    entry = root.find(f'{_ATOM}entry')
    if entry is None:
        return {'found': False, 'title': None, 'year': None, 'flags': set(), 'source': 'arxiv'}
    title = ' '.join((entry.findtext(f'{_ATOM}title') or '').split())
    eid = entry.findtext(f'{_ATOM}id') or ''
    if not title or title.lower() == 'error' or '/api/errors' in eid:
        return {'found': False, 'title': None, 'year': None, 'flags': set(), 'source': 'arxiv'}
    published = entry.findtext(f'{_ATOM}published') or ''
    year = int(published[:4]) if published[:4].isdigit() else None
    summary = (entry.findtext(f'{_ATOM}summary') or '').strip().lower()
    flags = {'retracted'} if summary.startswith(('this paper has been withdrawn', 'withdrawn')) else set()
    return {'found': True, 'title': title, 'year': year, 'flags': flags, 'source': 'arxiv'}


def lookup_pmid(pmid: str, fetcher: Fetcher) -> dict:
    if not pmid.isdigit():
        return {'found': False, 'title': None, 'year': None, 'flags': set(), 'source': 'pubmed'}
    status, body = fetcher.get(
        f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json')
    if status != 200:
        return {'found': None, 'title': None, 'year': None, 'flags': set(), 'source': 'pubmed',
                'error': f'HTTP {status}'}
    try:
        rec = json.loads(body).get('result', {}).get(pmid)
    except ValueError:
        rec = None
    if not rec or rec.get('error'):
        return {'found': False, 'title': None, 'year': None, 'flags': set(), 'source': 'pubmed'}
    pubdate = rec.get('pubdate') or ''
    year = int(pubdate[:4]) if pubdate[:4].isdigit() else None
    types = {t.lower() for t in rec.get('pubtype', [])}
    flags = set()
    if 'retracted publication' in types:
        flags.add('retracted')
    if 'expression of concern' in types:
        flags.add('concern')
    return {'found': True, 'title': rec.get('title'), 'year': year, 'flags': flags, 'source': 'pubmed'}


LOOKUPS = {'doi': lookup_doi, 'arxiv': lookup_arxiv, 'pmid': lookup_pmid}


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _norm_title(t: str | None) -> str:
    t = unicodedata.normalize('NFKC', t or '').casefold()
    t = re.sub(r'^\s*(retracted|withdrawn)\s*[:\-]\s*', '', t)
    t = re.sub(r'<[^>]+>', ' ', t)  # JATS/HTML tags in registry titles
    return ' '.join(re.findall(r'\w+', t))


_SUBTITLE_SEP_RE = re.compile(r':|\s[-\u2013\u2014]\s|\?|\.')


def _subtitle_omitted(short: str | None, full: str | None) -> bool:
    """True if `short` (>= 3 words) is exactly `full` up to a subtitle separator."""
    ns = _norm_title(short)
    if len(ns.split()) < 3:
        return False
    full = full or ''
    return any(_norm_title(full[:m.start()]) == ns for m in _SUBTITLE_SEP_RE.finditer(full))


def title_similarity(a: str | None, b: str | None) -> float:
    """Similarity of claimed title `a` to registry title `b` (0..1).

    nexus: a claimed title that omits the registry's subtitle is a full
    match. The reverse — the claimed title adds a subtitle the registry
    record lacks — is only a partial match (SUBTITLE_ADDED_SCORE): the
    added part is unchecked and may be invented."""
    na, nb = _norm_title(a), _norm_title(b)
    if not na or not nb:
        return 0.0
    # nexus: a bare prefix ('De' for 'Deep learning ...') is not a match; only a
    # title of >= 3 words that ends where the other side's subtitle begins.
    if na == nb or _subtitle_omitted(a, b):
        return 1.0  # subtitle omitted in the citation
    if _subtitle_omitted(b, a):
        return SUBTITLE_ADDED_SCORE
    return round(difflib.SequenceMatcher(None, na, nb).ratio(), 3)


SUBTITLE_ADDED_SCORE = 0.8


def assess(kind: str, ident: str, meta: dict, claimed_title: str | None, claimed_year) -> dict:
    out = {'kind': kind, 'id': ident, 'registry': meta.get('source'),
           'registry_title': meta.get('title'), 'registry_year': meta.get('year')}
    if meta.get('found') is None:
        out.update(status='error', detail=meta.get('error', 'registry error'))
        return out
    if not meta['found']:
        out.update(status='not_found', detail='identifier does not resolve')
        return out
    if 'retracted' in meta['flags']:
        out.update(status='retracted', detail='registry marks the work retracted/withdrawn')
        return out
    details = []
    status = 'verified'
    if claimed_title:
        sim = title_similarity(claimed_title, meta.get('title'))
        out['title_similarity'] = sim
        if sim < 0.6:
            status = 'metadata_mismatch'
            details.append('identifier resolves to a different title')
        elif sim < 0.85:
            details.append('title only partially matches')
    try:
        cy = int(str(claimed_year)[:4]) if claimed_year else None
    except ValueError:
        cy = None
    if cy and meta.get('year') and abs(cy - meta['year']) > 1:
        status = 'metadata_mismatch'
        details.append(f'year {cy} vs registry {meta["year"]}')
    if status == 'verified' and 'concern' in meta['flags']:
        status = 'concern'
        details.append('expression of concern on record')
    out.update(status=status, detail='; '.join(details) or 'resolves; metadata agrees')
    return out


def check_locator(locator: str, title: str | None, year, fetcher: Fetcher) -> dict:
    parsed = parse_identifier(locator)
    if not parsed:
        return {'status': 'skipped', 'detail': 'not an academic identifier', 'locator': locator}
    kind, ident = parsed
    res = assess(kind, ident, LOOKUPS[kind](ident, fetcher), title, year)
    res['locator'] = locator
    return res


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def read_jsonl(path: str) -> list[dict]:
    rows = []
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            rows = [json.loads(line) for line in f if line.strip()]
    return rows


def cmd_check(args: argparse.Namespace, fetcher: Fetcher | None = None) -> int:
    fetcher = fetcher or Fetcher()
    results = []
    for s in read_jsonl(os.path.join(args.dir, 'sources.jsonl')):
        loc = s.get('canonical_locator') or s.get('raw_url') or ''
        r = check_locator(loc, s.get('title'), s.get('year'), fetcher)
        r['source_id'] = s.get('source_id')
        r['checked_at'] = datetime.now(timezone.utc).isoformat()
        results.append(r)
    with open(os.path.join(args.dir, 'registry_checks.jsonl'), 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    counts: dict[str, int] = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    failing = [{'source_id': r['source_id'], 'status': r['status'], 'detail': r.get('detail')}
               for r in results if r['status'] in FAILING]
    passed = not (args.strict and failing)
    print(json.dumps({'status': 'pass' if passed else 'fail', 'counts': counts, 'failing': failing,
                      'note': "'error' means unknown (network), not verified"}, indent=2, ensure_ascii=False))
    return 0 if passed else 1


def cmd_lookup(args: argparse.Namespace, fetcher: Fetcher | None = None) -> int:
    r = check_locator(args.identifier, args.title, args.year, fetcher or Fetcher())
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 1 if r['status'] in FAILING else 0


def main(argv=None, fetcher: Fetcher | None = None) -> int:
    p = argparse.ArgumentParser(prog='registry_check', description='Verify DOI/arXiv/PMID citations against registries')
    sub = p.add_subparsers(dest='command', required=True)
    pc = sub.add_parser('check', help='Check all sources in a run directory')
    pc.add_argument('--dir', required=True)
    pc.add_argument('--strict', action='store_true')
    pl = sub.add_parser('lookup', help='Check one identifier')
    pl.add_argument('identifier', help='doi:10.x/..., arxiv:2305.14251, pmid:123, or URL')
    pl.add_argument('--title')
    pl.add_argument('--year')
    args = p.parse_args(argv)
    return {'check': cmd_check, 'lookup': cmd_lookup}[args.command](args, fetcher)


if __name__ == '__main__':
    import sys as _sys
    for _s in (_sys.stdin, _sys.stdout, _sys.stderr):
        if hasattr(_s, 'reconfigure'):
            _s.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
