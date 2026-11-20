#!/usr/bin/env python3
"""
Claim-Support Verification — deterministic red-flag filter over stored evidence.

CLI subcommands:
  verify       Check all claims against evidence, update support_status
  report       Generate a support verification summary

Deterministic and cheap: entity, number, date, lexical-overlap, clause-level
negation and antonym checks over stored evidence. No LLM calls. It is a
red-flag filter, not semantic verification: semantic verdicts come from
independent fresh-context verifier votes resolved by claim_ledger.py
(see reference/adversarial-verification.md).

Statuses: supported, partial, contradicted (negation mismatch on shared
content), needs_review (weak overlap, numeric conflict, no captured
evidence), unsupported (no or only empty evidence).

Only factual claims hard-fail (--strict): on unsupported, contradicted or
needs_review until layer 4 has finished on the claim (votes in votes.jsonl
and claim_ledger needs no more); the ledger gate then enforces the outcome.
Thresholds are validated as in claim_ledger. Synthesis/recommendation need
traceability, softer thresholds.

Numbers compare by value and kind (4.0% == 4 percent, 1.5 million ==
1,500,000, $4bn == $4 billion, 3x == 3 times; 3x != 3% != 3); decimal
commas (4,5%) and dot-grouped thousands (1.500.000) are read; citation
markers ([3], [^7]) are stripped; digits hyphenated onto a name (COVID-19,
GPT-4) are identifier tokens. Every claim number must be stated, with its
kind, by some on-topic quote; a quote that states another number of the
same kind instead of a claim number is a numeric conflict.

Provenance: the negation engine (negation_lexicon.json, clause splitting,
antonym pairs, Portuguese "no" contraction handling) is taken from the
FFV47/claude-deep-research-skill fork (MIT, as upstream), commit ba31604.
nexus changes: 'contradicted' status, empty quotes = unsupported, numeric
conflict detection, thousands separators, one agreeing quote wins but
conflicts are surfaced, de/es/fr/it/ja/ko negation cues.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claim_ledger import _cfg as ledger_cfg, votes_still_needed  # noqa: E402


# ---------------------------------------------------------------------------
# JSONL helpers
# ---------------------------------------------------------------------------

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


def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, 'w') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


# ---------------------------------------------------------------------------
# Support verification logic
# ---------------------------------------------------------------------------

# Extract numbers: integers and decimals ("1,847" as one number), with an
# optional scale word or suffix ("1.5 million", "$4bn") and a kind
# (percent: "4%", "4 percent"; multiplier: "3x", "3 times", "3-fold").
# nexus: decimal commas ("4,5%"), dot-grouped thousands ("1.500.000") and
# both together ("1.234,56" = 1234.56) are read too; "1,500" and "1.500"
# keep their English reading (1500, 1.5).
# Digits glued to letters (H100) or hyphenated onto a word (COVID-19, GPT-4)
# are part of an identifier, not a figure: identifiers are compared as tokens.
NUMBER_RE = re.compile(
    r'(?<![\w.,])(?<![^\W\d_]-)'
    r'(?P<whole>\d{1,3}(?:,\d{3})+|\d{1,3}(?:\.\d{3}){2,}|\d{1,3}(?:\.\d{3})+(?=,\d)|\d+)'
    r'(?:(?P<sep>[.,])(?P<frac>\d+))?(?!\d)(?![.,]\d)'
    r'(?:\s(?i:(?P<word>thousand|million|billion|trillion|bn|mn|tn|mil\s+milh(?:ões|oes|ão|ao)|mil|milhão|milhões'
    r'|milhao|milhoes))\b'
    r'|(?i:(?P<suffix>bn|mn|tn|k|m|b))\b)?'
    r'(?P<kind>\s?%|\s(?i:percent|per\s?cent|pct|por\s+cento)\b|(?i:x)\b'
    r'|\s(?i:times)\b(?!\s+(?i:(?:per|each|every)\s+\w+|(?:a|an)\s+(?:day|week|month|year|hour|minute|second|night|'
    r'quarter|season|decade|shift|cycle|session|visit|game|match|round|term|semester|lifetime)s?\b|'
    r'daily|weekly|monthly|yearly|annually|nightly|hourly)\b)'
    r'|\s(?i:fold)\b|-(?i:fold)\b)?')
_SCALES = {'thousand': 3, 'k': 3, 'mil': 3, 'million': 6, 'mn': 6, 'm': 6, 'milhão': 6,
           'milhões': 6, 'milhao': 6, 'milhoes': 6,
           'billion': 9, 'bn': 9, 'b': 9, 'trillion': 12, 'tn': 12}
# nexus: Portuguese scale words ("2.000 milhões", "1,5 mil milhões"): with
# them "." groups thousands and "," is the decimal mark; "mil milhões" = 10^9
_PT_SCALES = frozenset(['mil', 'milhão', 'milhões', 'milhao', 'milhoes'])
# nexus: a kindless number joined to a percent/multiplier by a range word
# shares its kind ("10-12%", "between 10 and 12%", "10 to 12 percent"); a
# year never does ("In 2023 - 12%", "in 2023 and 12%")
_RANGE_JOIN_RE = re.compile(r'\s*(?:-|\u2013|\u2014|to|and|a|e|até|ate)\s*', re.I)

# Identifiers with a hyphenated number (COVID-19, GPT-4, SARS-CoV-2)
IDENTIFIER_RE = re.compile(r'(?<![\w-])[^\W\d_][\w]*(?:-[^\W_]+)*-\d+(?:\.\d+)?(?![\w-])')

# Citation markers ([3], [1][2], [1, 4], [^7]) are not part of a claim
CITATION_MARKER_RE = re.compile(
    r'\[\s*\^?\s*\d+(?:\s*[-\u2013,;]\s*\^?\s*\d+)*\s*\]|\[\^[^\]\s]+\]')

# The word right after a number (its unit: "300 jobs"), and words that are
# not units
_NEXT_WORD_RE = re.compile(r'\s*%?\s*([^\W\d_]+)')
_NOT_UNITS = frozenset(['of', 'the', 'to', 'in', 'and', 'or', 'a', 'an', 'per', 'percent',
                        'per', 'cent', 'from', 'at', 'by', 'on', 'for', 'with', 'than', 'is',
                        'was', 'were', 'are', 'times', 'more', 'less', 'de', 'do', 'da', 'e'])

# Extract year-like numbers
YEAR_RE = re.compile(r'\b(?:19|20)\d{2}\b')

# Extract capitalized entities (naive NER)
ENTITY_RE = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')

# Common words that ENTITY_RE catches when they start a sentence (en, pt).
# ENTITY_RE only matches unaccented letters, so accented words are absent.
STOP_ENTITIES = frozenset([
    'The', 'This', 'That', 'These', 'Those', 'However', 'Furthermore',
    'Moreover', 'Additionally', 'Therefore', 'Nevertheless', 'According',
    'It', 'Its', 'He', 'She', 'We', 'They', 'You', 'There', 'Here',
    'My', 'Our', 'Your', 'His', 'Her', 'Their', 'What', 'Which', 'Who',
    'Some', 'None', 'No', 'Not', 'Nobody', 'Nothing', 'Neither', 'Never',
    'All', 'Any', 'Each', 'Every', 'Many', 'Most', 'Few', 'Several', 'Both',
    'Such', 'Only', 'Also', 'Even', 'Then', 'Now', 'An', 'In', 'On', 'At',
    'By', 'For', 'From', 'With', 'As', 'If', 'When', 'While', 'Since',
    'After', 'Before', 'During', 'And', 'But', 'Or', 'So',
    'Isso', 'Isto', 'Este', 'Esta', 'Estes', 'Estas', 'Esse', 'Essa',
    'Esses', 'Essas', 'Aquele', 'Aquela', 'Aquilo', 'Nenhum', 'Nenhuma',
    'Ele', 'Ela', 'Eles', 'Elas', 'Dele', 'Dela', 'Um', 'Uma', 'Uns',
    'Umas', 'Os', 'Meu', 'Minha', 'Meus', 'Minhas', 'Seu', 'Sua', 'Seus',
    'Suas', 'Nosso', 'Nossa', 'Nossos', 'Nossas', 'Qual', 'Quais', 'Quem',
    'Onde', 'Algum', 'Alguma', 'Alguns', 'Algumas', 'Todos', 'Todas',
    'Cada', 'Muitos', 'Muitas', 'Nunca', 'Apenas', 'Somente', 'Ainda',
    'Hoje', 'Depois', 'Antes', 'Durante', 'Segundo', 'Em', 'Na', 'Nos',
    'Nas', 'De', 'Do', 'Da', 'Dos', 'Das', 'Ao', 'Aos', 'Pelo', 'Pela',
    'Pelos', 'Pelas', 'Para', 'Por', 'Com', 'Sem', 'Se', 'Quando', 'Como',
    'Mas',
])


# Han ideographs: CJK Unified Ideographs and Extension A. Chinese has no
# spaces between words, so runs are split into character bigrams.
CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]+')


def normalize_text(text: str) -> str:
    """NFC-normalize and lowercase, so composed and decomposed accents match."""
    return unicodedata.normalize('NFC', text).lower()


# Negation markers and the phrases that contain one without negating live
# in a data file next to this script, so they change without code edits.
# A claim and a quote that disagree on negation are treated as a
# contradiction, not as support.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'negation_lexicon.json'), encoding='utf-8') as _f:
    _LEXICON = json.load(_f)


def _lexicon_words(key: str) -> list[str]:
    """Return a lexicon list, NFC-normalized and lowercased."""
    return [normalize_text(w) for w in _LEXICON[key]]


NEGATION_WORDS = frozenset(_lexicon_words('negation_words'))
CJK_NEGATIONS = frozenset(_lexicon_words('negation_chars'))

# Words that mark a text as Portuguese, and the negation words that, in
# such a text, are contractions ("no" = "em" + "o") and do not negate
PT_MARKERS = frozenset(_lexicon_words('pt_markers'))
PT_CONTRACTIONS = frozenset(_lexicon_words('pt_contractions'))

# Words found in Portuguese and in English ("da Vinci", "do not"), which
# count only in a text that swaps "no" for one of them
PT_WEAK_MARKERS = frozenset(_lexicon_words('pt_weak_markers'))

# Words that mark a text as English, and letters that mark a word as
# Portuguese, for texts without a Portuguese marker word
EN_MARKERS = frozenset(_lexicon_words('en_markers'))
PT_LETTERS = frozenset(_lexicon_words('pt_letters'))

# Portuguese phrases that contain an English marker word ("on-line"),
# matched as whole words in any case. Longer phrases are tried first.
EN_MARKER_EXCEPTION_RE = re.compile('|'.join(
    rf'\b{re.escape(e)}\b'
    for e in sorted(_lexicon_words('en_marker_exceptions'), key=len, reverse=True)
), re.IGNORECASE)

# Exceptions match as whole words, except Han compounds, which have no
# word boundaries. Longer phrases are tried first.
NEGATION_EXCEPTION_RE = re.compile('|'.join(
    re.escape(e) if CJK_RE.search(e) else rf'\b{re.escape(e)}\b'
    for e in sorted(_lexicon_words('exceptions'), key=len, reverse=True)
))

# Antonym pairs, each side a set of word forms: a negated word equals its
# antonym, so "not closed" agrees with "open".
ANTONYM_PAIRS = [
    tuple(frozenset(normalize_text(w) for w in side) for side in pair)
    for pair in _LEXICON['antonyms']
]

# Extract words in any alphabetic script
WORD_RE = re.compile(r'[^\W\d_]+')

# Extract whole words with their inner apostrophes, so "o" inside
# "O'Brien" is not read as the Portuguese article
PT_MARKER_WORD_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*")

# Text before a word that starts a sentence: nothing, or a sentence end,
# with optional quotes or brackets in between
SENTENCE_START_RE = re.compile(r'(?:^|[.!?])\W*$')

# Extract whole words with an optional "'t" suffix, so "no" inside "NO2"
# is not a negation
NEGATION_WORD_RE = re.compile(r"\b[^\W\d_]+(?:'t)?\b")

# Clause boundaries: commas, semicolons, colons, brackets, dashes between
# spaces, sentence ends (en, pt and zh punctuation), and the separator
# words in the lexicon ("but", "mas"). A period inside a number ("2.5")
# is not a boundary. The zh enumeration comma 、 is not a boundary, since
# it joins items of one clause.
CLAUSE_SPLIT_RE = re.compile(
    r'[,;:()\[\]，；：（）。！？]|[.!?](?=\s|$)|\s[-–—]\s|'
    + '|'.join(rf'\b{re.escape(w)}\b' for w in _lexicon_words('clause_separators')),
    re.IGNORECASE,
)

# Score thresholds: at or above SUPPORTED is supported, at or above
# PARTIAL is partial, below it needs review
SUPPORTED_THRESHOLD = 0.6
PARTIAL_THRESHOLD = 0.35


def has_en_marker_word(text: str) -> bool:
    """Return True if the text contains an English marker word, in any case."""
    return any(w.lower() in EN_MARKERS for w in WORD_RE.findall(text))


def has_standalone_en_marker_word(text: str) -> bool:
    """Return True if the text contains an English marker word outside the
    Portuguese phrases that contain one ("on-line"), in lowercase or at the
    start of a sentence ("The café"). Elsewhere a capitalized or all-caps
    word is a name or an acronym in any language ("The Mall").

    This looser check applies only to a text with a second Portuguese
    signal: it opens a sentence with a Portuguese marker word ("O Globo"),
    or, in the accented-letter rule, the text it is compared with reads as
    Portuguese on its own. In other text, "Shoppers bought no açaí bowls
    on-line." stays English."""
    text = EN_MARKER_EXCEPTION_RE.sub(' ', unicodedata.normalize('NFC', text))
    return any(
        match.group().lower() in EN_MARKERS
        and (match.group().islower() or SENTENCE_START_RE.search(text[:match.start()]))
        for match in WORD_RE.finditer(text))


def starts_sentence_with_pt_marker(text: str) -> bool:
    """Return True if a capitalized Portuguese marker word opens a sentence
    of the text ("O museu", "O Globo")."""
    text = unicodedata.normalize('NFC', text).replace('’', "'")
    return any(
        match.group().istitle() and match.group().lower() in PT_MARKERS
        and SENTENCE_START_RE.search(text[:match.start()])
        for match in PT_MARKER_WORD_RE.finditer(text))


def is_portuguese(text: str, other: str = '') -> bool:
    """Return True if the text contains a Portuguese marker word that
    counts, given other, the text it is compared with.

    A marker counts in lowercase, or capitalized at the start of a
    sentence ("O museu"). Elsewhere a capitalized or all-caps word is a
    name or an acronym in any language ("São Paulo", "type O", "NAS").

    At the start of a sentence, a marker followed by a capitalized word
    may open a name ("Uma Thurman", "O Globo"). It counts only if the text
    has no standalone English marker word, and other reads as Portuguese
    on its own or swaps "no" for weak Portuguese marker words.
    So "O Brasil fica no centro" reads as Portuguese against "O Brasil
    não fica no centro". "O Globo publicou no Natal" reads as Portuguese
    against "O Globo publicou na véspera do Natal". "Uma Thurman won no
    Oscar" reads as English against "Uma Thurman won Oscar"."""
    text = unicodedata.normalize('NFC', text).replace('’', "'")
    for match in PT_MARKER_WORD_RE.finditer(text):
        word = match.group()
        if word.lower() not in PT_MARKERS:
            continue
        if word.islower():
            return True
        if word.istitle() and SENTENCE_START_RE.search(text[:match.start()]):
            next_word = PT_MARKER_WORD_RE.search(text, match.end())
            opens_name = next_word is not None and next_word.group()[0].isupper()
            if not opens_name or (not has_standalone_en_marker_word(text)
                                  and (is_portuguese(other) or swaps_no_for_pt_weak_marker(text, other))):
                return True
    return False


def swaps_no_for_pt_weak_marker(text: str, other: str) -> bool:
    """Return True if other has a weak Portuguese marker word ("na", "do")
    where the text has the contraction "no", after the same word and
    before a lowercase word. Other must also have at least two weak marker
    words in lowercase and no English marker word in any case.

    These words also appear in English, before a name ("da Vinci") or in
    a set phrase ("do not", "de facto"), so one of them alone does not
    make other Portuguese. "O Globo publicou na véspera do Natal" swaps
    "no" in "O Globo publicou no Natal"; "O Globo cited da Vinci, de
    Gaulle letters" does not, against "O Globo cited no letters"."""
    if has_en_marker_word(other):
        return False
    words = WORD_RE.findall(unicodedata.normalize('NFC', text))
    other_words = WORD_RE.findall(unicodedata.normalize('NFC', other))
    if sum(w in PT_WEAK_MARKERS for w in other_words) < 2:
        return False
    before_no = {prev for prev, w in zip(words, words[1:]) if w in PT_CONTRACTIONS}
    return any(prev in before_no and w in PT_WEAK_MARKERS and following.islower()
               for prev, w, following in zip(other_words, other_words[1:], other_words[2:]))


def has_pt_letter_word(clause: str, text: str, other: str) -> bool:
    """Return True if the clause has a lowercase word with a Portuguese
    letter ("histórico") and the text it comes from has no English marker
    word, in any case. If the text opens a sentence with a Portuguese
    marker word ("O Globo"), or other, the text it is compared with, reads
    as Portuguese on its own ("A loja não vende on-line."),
    only a standalone English marker word counts.

    This reads a text without a Portuguese marker word as Portuguese. The
    word must sit in the clause itself, so a Portuguese note in another
    clause ("Sales showed no growth (relatório anual).") leaves the
    English "no" negating. Capitalized words do not count, since names
    keep their accents in any language ("São Paulo")."""
    en_marker_check = (
        has_standalone_en_marker_word
        if starts_sentence_with_pt_marker(text) or is_portuguese(other)
        else has_en_marker_word)
    if en_marker_check(text):
        return False
    return any(w.islower() and PT_LETTERS & set(w)
               for w in WORD_RE.findall(unicodedata.normalize('NFC', clause)))


def has_negation(text: str, *, portuguese: bool) -> bool:
    """Return True if the text contains a negation marker.

    portuguese says whether the clause reads as Portuguese, from the whole
    text it comes from or from its own words; there, the contraction "no"
    does not negate."""
    # Fold the typographic apostrophe so "doesn’t" matches like "doesn't"
    text = normalize_text(text).replace('’', "'")
    text = NEGATION_EXCEPTION_RE.sub(' ', text)
    if any(ch in text for ch in CJK_NEGATIONS):
        return True
    negation_words = NEGATION_WORDS - PT_CONTRACTIONS if portuguese else NEGATION_WORDS
    words = NEGATION_WORD_RE.findall(text)
    return any(w in negation_words or w.endswith("n't") for w in words)


# Three-letter function words (en, pt). Other lowercase three-letter words
# carry the claim's predicate ("won", "big"), so they count as tokens.
# Negation words are left out, since the negation check handles them.
SHORT_FUNCTION_WORDS = frozenset([
    'the', 'and', 'for', 'are', 'was', 'but', 'nor', 'yet', 'you', 'all',
    'any', 'can', 'had', 'has', 'her', 'his', 'its', 'our', 'who', 'how',
    'why', 'may', 'did', 'per', 'via', 'she', 'him', 'own', 'too',
    'que', 'uma', 'uns', 'com', 'por', 'dos', 'das', 'nos', 'nas', 'aos',
    'mas', 'ele', 'ela', 'seu', 'sua', 'foi', 'são', 'sao', 'tem', 'era',
    'ser', 'sem', 'até', 'ate', 'lhe', 'num',
]) | NEGATION_WORDS


def extract_tokens(text: str) -> set[str]:
    """Extract significant tokens: in alphabetic scripts, words of 4+
    letters and lowercase three-letter words other than function words; in
    Han text, character bigrams. A capitalized three-letter word ("Tim",
    "GDP") names the subject, which entities cover, so it is no token."""
    tokens = {
        w.lower() for w in WORD_RE.findall(CJK_RE.sub(' ', unicodedata.normalize('NFC', text)))
        if len(w) >= 4 or (len(w) == 3 and w.islower() and w not in SHORT_FUNCTION_WORDS)
    }
    # nexus: identifiers carry their number (GPT-4 is not GPT-5)
    tokens.update(i.lower() for i in IDENTIFIER_RE.findall(text))
    text = normalize_text(text)
    for run in CJK_RE.findall(text):
        if len(run) == 1:
            tokens.add(run)
        else:
            tokens.update(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


def _canonical_number(m: re.Match) -> str:
    """Numeric value of a NUMBER_RE match as a plain decimal string plus
    its kind ('%' percent, 'x' multiplier, '' other), so equivalent forms
    compare equal ("4.0%" == "4 percent", "1.5 million" == "1,500,000",
    "$4bn" == "$4 billion", "3x" == "3 times") and kinds do not ("3x" !=
    "3%" != "3")."""
    whole = m.group('whole')
    frac, sep = m.group('frac'), m.group('sep')
    scale = re.sub(r'\s+', ' ', (m.group('word') or m.group('suffix') or '').lower())
    pt = scale.split(' ')[-1] in _PT_SCALES
    if pt and whole.count(',') == 1 and not frac:     # nexus: "1,250 milhões" = 1.25 million
        whole, frac = whole.split(',')
    elif pt and ',' in whole:
        whole = whole.replace(',', '')
    elif pt or '.' in whole:
        whole = whole.replace('.', '')
    else:
        whole = whole.replace(',', '')
    if pt and sep == '.' and frac and len(frac) == 3:   # nexus: "2.000 milhões"
        whole, frac = whole + frac, None
    value = Decimal(whole + ('.' + frac if frac else ''))
    if scale:
        value = value.scaleb(9 if scale.startswith('mil milh') else _SCALES[scale])
    kind = (m.group('kind') or '').strip().lower()
    suffix = '%' if kind and kind[0] in '%p' else 'x' if kind else ''
    return format(value.normalize(), 'f') + suffix


def number_kind(n: str) -> str:
    """'%', 'x' or '' for a canonical number."""
    return n[-1] if n and n[-1] in '%x' else ''


def strip_citation_markers(text: str) -> str:
    """Remove citation markers ([3], [1][2], [^7]): they are not claim content."""
    return CITATION_MARKER_RE.sub(' ', text or '')


def number_matches(text: str) -> list[tuple[re.Match, str]]:
    """nexus: NUMBER_RE matches with their canonical value; a kindless number
    joined to the next one by a range word takes that number's kind."""
    ms = list(NUMBER_RE.finditer(text))
    vals = [_canonical_number(m) for m in ms]
    for i in range(len(ms) - 2, -1, -1):
        gap = text[ms[i].end():ms[i + 1].start()]
        if (not number_kind(vals[i]) and number_kind(vals[i + 1]) and _RANGE_JOIN_RE.fullmatch(gap)
                and not YEAR_RE.fullmatch(ms[i].group(0))):
            vals[i] += number_kind(vals[i + 1])
    return list(zip(ms, vals))


def extract_numbers(text: str) -> set[str]:
    """Extract numeric values. nexus: thousands separators are dropped so
    "1,847" and "1847" compare equal (upstream read "1,847" as 1 and 847);
    values are canonical (see _canonical_number), ranges share their kind."""
    return {v for _, v in number_matches(text)}


def number_units(text: str) -> dict[str, set[str]]:
    """Map each number to the words right after it ("300 jobs" -> jobs)."""
    out: dict[str, set[str]] = {}
    for m, value in number_matches(text):
        word = _NEXT_WORD_RE.match(text, m.end())
        if word and word.group(1).lower() not in _NOT_UNITS:
            out.setdefault(value, set()).add(word.group(1).lower())
    return out


def numbers_swapped(claim_text: str, quote: str, claim_numbers: set[str]) -> bool:
    """nexus: the quote has the claim's numbers, but attached to each
    other's units ("300 jobs across 12 plants" vs "12 jobs across 300
    plants")."""
    claim_units, quote_units = number_units(claim_text), number_units(quote)
    for n, words in claim_units.items():
        if n not in claim_numbers or not quote_units.get(n) or words & quote_units[n]:
            continue
        if any(m != n and m in claim_numbers and words & ws for m, ws in quote_units.items()):
            return True
    return False


def extract_years(text: str) -> set[str]:
    """Extract year mentions."""
    return set(YEAR_RE.findall(text))


def extract_non_year_numbers(text: str) -> set[str]:
    """nexus: numeric values other than years. Years score in their own
    component; counting them as numbers too let a shared year carry a
    claim whose real figure (\"12%\") the evidence never states."""
    return extract_numbers(text) - extract_years(text)


def extract_entities(text: str) -> set[str]:
    """Extract capitalized entity mentions, without leading stop words,
    so "Some Tesla" yields "Tesla" and "It" yields nothing."""
    ents = set()
    for match in ENTITY_RE.findall(text):
        words = match.split()
        while words and words[0] in STOP_ENTITIES:
            words.pop(0)
        if words:
            ents.add(' '.join(words))
    return ents


# Scored components: (name, extractor, weight, mismatch threshold, note).
# A component scores the share of the claim's items found in the quote.
# A component the claim lacks is left out of the score instead of counting
# as a full match.
SCORE_COMPONENTS = (
    ('tokens', extract_tokens, 0.4, 0.3, 'low lexical overlap'),
    ('numbers', extract_non_year_numbers, 0.25, 0.5, 'number mismatch'),
    ('years', extract_years, 0.15, 1.0, 'year mismatch'),
    ('entities', extract_entities, 0.2, 0.3, 'entity mismatch'),
)


def claim_components(claim_text: str) -> list[tuple]:
    """Return the scored components the claim actually has, with its items."""
    return [
        (name, extract, claim_items, weight, threshold, note)
        for name, extract, weight, threshold, note in SCORE_COMPONENTS
        if (claim_items := extract(claim_text))
    ]


def score_quote(components: list[tuple], quote: str) -> tuple[float, list[tuple]]:
    """Score one quote against the claim components.

    Returns (score, matches), where matches holds
    (name, match, weight, threshold, note) per component.

    A word the claim and the quote share as an entity scores once, in the
    entities component, and is left out of the tokens. Otherwise a shared
    subject would also match as a token, and the quote "Tesla lost" would
    support the claim "Tesla won"."""
    claim_entities = next(
        (items for name, _, items, *_ in components if name == 'entities'), set())
    shared_entity_words = {
        w for e in claim_entities & extract_entities(quote) for w in normalize_text(e).split()
    }
    matches = []
    for name, extract, claim_items, weight, threshold, note in components:
        if name == 'tokens':
            claim_items = claim_items - shared_entity_words
            if not claim_items:
                continue
        matches.append(
            (name, len(claim_items & extract(quote)) / len(claim_items), weight, threshold, note))
    total_weight = sum(weight for _, _, weight, _, _ in matches)
    score = (
        sum(match * weight for _, match, weight, _, _ in matches) / total_weight
        if total_weight else 0.0
    )
    return score, matches


def content_items(text: str) -> set[str]:
    """Return the items scoring compares: tokens, numbers and entities."""
    return extract_tokens(text) | extract_numbers(text) | extract_entities(text)


def split_clauses(text: str) -> list[str]:
    """Split text at clause punctuation (en, pt and zh) and separator words.

    NFC-normalized, so a decomposed "porém" still matches, but not
    lowercased, since entity extraction needs the original case."""
    return [c for c in CLAUSE_SPLIT_RE.split(unicodedata.normalize('NFC', text)) if c.strip()]


def relevant_clauses(text: str, other: str, *, text_is_claim: bool) -> list[str]:
    """Return the clauses of text that carry content shared with other.

    A clause is relevant if, on its own, it partially matches the other
    text (scored claim against evidence), or if it holds shared content
    that the rest of text lacks. A negation in any other clause does not
    touch what the claim and the evidence have in common."""
    clauses = split_clauses(text)
    other_items = content_items(other)
    relevant = []
    for i, clause in enumerate(clauses):
        claim, quote = (clause, other) if text_is_claim else (other, clause)
        rest = ' '.join(clauses[:i] + clauses[i + 1:])
        shared_here = content_items(clause) & other_items
        if (score_quote(claim_components(claim), quote)[0] >= PARTIAL_THRESHOLD
                or shared_here - content_items(rest)):
            relevant.append(clause)
    return relevant


# nexus: R16 — "up to 70%" is a bound, not a direction
_UP_TO_RE = re.compile(r'\bup to\b')
# nexus: R17 — direction nouns/particles, weaker than a verb of the same pair
DIRECTION_NOUNS = frozenset({
    'up', 'down', 'growth', 'crescimento', 'aumento', 'aumentos', 'subida', 'subidas', 'queda', 'quedas',
    'descida', 'descidas', 'diminuição', 'redução', 'baixa'})


def uses_opposite_antonyms(text_a: str, text_b: str, verbs_over_nouns: bool = False) -> bool:
    """Return True if the texts take opposite sides of an antonym pair:
    one uses only one side, the other only the opposite side. A text that
    uses both sides ("not open ... closed on holidays") takes neither."""
    words_a = set(WORD_RE.findall(_UP_TO_RE.sub(' ', normalize_text(text_a))))
    words_b = set(WORD_RE.findall(_UP_TO_RE.sub(' ', normalize_text(text_b))))
    for forms_x, forms_y in ANTONYM_PAIRS:
        # nexus: R17 — nouns and particles ("growth", "queda", "set up") only
        # give a direction when the text has no verb of the pair: in "Wage
        # growth fell" the direction is "fell", not "growth". R18: only without
        # a negation — "no growth ... fell" keeps the negated noun in the XOR
        verbs = (forms_x | forms_y) - DIRECTION_NOUNS
        wa = words_a - DIRECTION_NOUNS if verbs_over_nouns and words_a & verbs else words_a
        wb = words_b - DIRECTION_NOUNS if verbs_over_nouns and words_b & verbs else words_b
        a_x, a_y = bool(wa & forms_x), bool(wa & forms_y)
        b_x, b_y = bool(wb & forms_x), bool(wb & forms_y)
        if (a_x and not a_y and b_y and not b_x) or (a_y and not a_x and b_x and not b_y):
            return True
    return False


def negation_mismatch(claim_text: str, quote: str) -> bool:
    """Return True if claim and quote disagree on negating shared content.

    Each negation and each switch to an antonym flips the meaning once, so
    "not closed" agrees with "open" and "not open" disagrees with "not
    closed". Without a negation, opposite antonyms alone are a mismatch
    ("rose 12%" vs "fell 12%"), judged against the quote clause that best
    matches the claim, so another clause's direction ("..., while costs
    rose") neither hides nor causes a flip."""
    claim_clauses = relevant_clauses(claim_text, quote, text_is_claim=True)
    quote_clauses = relevant_clauses(quote, claim_text, text_is_claim=False)
    claim_pt, quote_pt = is_portuguese(claim_text, quote), is_portuguese(quote, claim_text)
    claim_negated = any(
        has_negation(c, portuguese=claim_pt or has_pt_letter_word(c, claim_text, quote))
        for c in claim_clauses)
    quote_negated = any(
        has_negation(c, portuguese=quote_pt or has_pt_letter_word(c, quote, claim_text))
        for c in quote_clauses)
    if not (claim_negated or quote_negated):
        # nexus: R15-C1 — without a negation, opposite antonyms on shared
        # content ("rose 12%" vs "fell 12%") are a contradiction too.
        # R16: compare with the quote clause that best matches the claim
        # ("Sales fell 12%, while costs rose" against "Sales rose 12%").
        if not quote_clauses:
            return False
        components = claim_components(claim_text)
        claim_words = set(WORD_RE.findall(_UP_TO_RE.sub(' ', normalize_text(' '.join(claim_clauses)))))
        pair_words = set().union(*(x | y for x, y in ANTONYM_PAIRS if claim_words & (x | y)))
        directed = [c for c in quote_clauses
                    if set(WORD_RE.findall(_UP_TO_RE.sub(' ', normalize_text(c)))) & pair_words]
        if not directed:
            return False
        best_clause = max(directed, key=lambda c: score_quote(components, c)[0])
        return uses_opposite_antonyms(' '.join(claim_clauses), best_clause, verbs_over_nouns=True)
    flipped = uses_opposite_antonyms(' '.join(claim_clauses), ' '.join(quote_clauses))
    return claim_negated ^ quote_negated ^ flipped


def compute_support_score(claim_text: str, evidence_quotes: list[str]) -> tuple[str, float, str]:
    """
    Compute support status for a claim given its linked evidence quotes.

    Returns (status, score, notes).
    Score range: 0.0 (no overlap) to 1.0 (strong support).
    """
    if not evidence_quotes:
        return ('unsupported', 0.0, 'no evidence linked')
    # nexus: an empty quote is no evidence (issue #14 scored it 0.6)
    evidence_quotes = [strip_citation_markers(q) for q in evidence_quotes if q and q.strip()]
    if not evidence_quotes:
        return ('unsupported', 0.0, 'only empty evidence quotes')

    # nexus: citation markers ([3], [1][2]) are not figures of the claim
    claim_text = strip_citation_markers(claim_text)
    components = claim_components(claim_text)
    # Years have their own component; the numeric checks are for the rest
    claim_numbers = extract_non_year_numbers(claim_text)
    claim_years = extract_years(claim_text)

    best_score = -1.0  # below any real score, so the first quote sets notes
    best_notes = []
    contradicting = 0
    numeric_conflicts = 0
    year_conflicts = 0
    qualifier_conflicts: list[str] = []
    best_agreeing = -1.0
    agreeing_notes: list[str] = []
    # nexus: claim numbers stated by on-topic quotes without a negation
    # mismatch. Figures may come from different quotes ("10% ... [1]",
    # "12% ... [2]"), but each must be stated with its kind (12% != 12).
    backed_numbers: set[str] = set()

    for quote in evidence_quotes:
        score, matches = score_quote(components, quote)

        conflict = False
        if score >= PARTIAL_THRESHOLD and negation_mismatch(claim_text, quote):
            contradicting += 1
            conflict = True
        elif score >= PARTIAL_THRESHOLD:
            backed_numbers |= claim_numbers & extract_non_year_numbers(quote)
            if (numbers_conflict(claim_numbers, quote, matches)
                    or numbers_swapped(claim_text, quote, claim_numbers)):
                numeric_conflicts += 1
                conflict = True
            elif numbers_conflict(claim_years, quote, matches, extract=extract_years):
                year_conflicts += 1
                conflict = True
            elif (qualifier_note := qualifier_conflict(claim_text, quote)):
                qualifier_conflicts.append(qualifier_note)
                conflict = True
        quote_notes = ['no shared content with evidence'] if score == 0.0 else []
        quote_notes += [
            note for name, match, _, threshold, note in matches
            # At score 0, "no shared content" replaces the lexical note
            if match < threshold and not (score == 0.0 and name == 'tokens')
        ]
        if not conflict and score > best_agreeing:
            best_agreeing, agreeing_notes = score, quote_notes

        if score > best_score:
            best_score, best_notes = score, quote_notes

    # nexus: one quote that agrees on polarity and numbers is enough support,
    # but disagreeing quotes are surfaced so the verifiers look at them.
    # Every claim number must be stated by some on-topic quote: a quote that
    # omits the figure ("grew" vs "grew 12%") does not back it.
    numbers_backed = claim_numbers <= backed_numbers
    if best_agreeing >= SUPPORTED_THRESHOLD and numbers_backed:
        notes = '; '.join(agreeing_notes) or 'adequate overlap'
        conflicts = contradicting + numeric_conflicts + year_conflicts + len(qualifier_conflicts)
        if conflicts:
            notes += (f'; {conflicts} other quote(s) conflict '
                      '(negation mismatch or numeric conflict) — check for disagreeing sources')
        return ('supported', round(best_agreeing, 3), notes)

    if contradicting:
        return ('contradicted', 0.0, 'negation mismatch with evidence')
    if numeric_conflicts:
        return ('needs_review', round(best_score, 3),
                'numeric conflict: a claim number differs from the evidence or is attached to another unit')
    if year_conflicts:
        return ('needs_review', round(best_score, 3),
                'year mismatch: a claim year differs from the evidence')
    if qualifier_conflicts:
        return ('needs_review', round(min(best_score, SUPPORTED_THRESHOLD - 0.01), 3),
                f'{qualifier_conflicts[0]} (currency, quarter, month or named subject differs from the evidence)')
    if not numbers_backed and best_agreeing >= PARTIAL_THRESHOLD:
        # Capped below the support threshold: the overlap is not support
        return ('needs_review',
                round(min(best_agreeing, SUPPORTED_THRESHOLD - 0.01), 3),
                'claim number not found in evidence')

    # Threshold decision
    if best_score >= SUPPORTED_THRESHOLD:
        status = 'supported'
    elif best_score >= PARTIAL_THRESHOLD:
        status = 'partial'
    else:
        status = 'needs_review'

    if best_notes:
        notes = '; '.join(best_notes)
    elif status == 'supported':
        notes = 'adequate overlap'
    else:
        notes = 'overlap below support threshold'
    return (status, round(best_score, 3), notes)


# ---------------------------------------------------------------------------
# nexus: R15 — qualifiers that change what a figure means: currency, quarter
# or half-year, month, and the named subject (entity substitution). Each is
# compared only when both texts state one; a quote that names another
# currency/period/subject than the claim is a conflict, not support.
# ---------------------------------------------------------------------------

_CURRENCY_RE = re.compile(
    r'US\$|\$|€|£|¥|\b(?:USD|EUR|GBP|JPY|CHF)\b|\b(?:dollars?|d[óo]lares|euros?|pounds?|libras?)\b', re.I)
_CURRENCY_CANON = {'us$': 'USD', '$': 'USD', 'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD',
                   'dólares': 'USD', 'dolares': 'USD', '€': 'EUR', 'eur': 'EUR', 'euro': 'EUR',
                   'euros': 'EUR', '£': 'GBP', 'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP',
                   'libra': 'GBP', 'libras': 'GBP', '¥': 'JPY', 'jpy': 'JPY', 'chf': 'CHF'}
_QUARTER_RE = re.compile(r'\b([QH][1-4])\b|\b([1-4])T\b', re.I)
_MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6,
    'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
}
_PROPER_WORD_RE = re.compile(r"[^\W\d_][^\W\d_]*")


def _currencies(text: str) -> set[str]:
    return {_CURRENCY_CANON[m.group(0).lower()] for m in _CURRENCY_RE.finditer(text)}


def _quarters(text: str) -> set[str]:
    out = {(m.group(1) or 'Q' + m.group(2)).upper() for m in _QUARTER_RE.finditer(text)}
    for m in _QUARTER_WORDS_RE.finditer(unicodedata.normalize('NFC', text)):   # nexus: R16 "third quarter"
        out.add(('H' if m.group(2).lower() in ('half', 'semestre') else 'Q') + _ORDINALS[m.group(1).lower()])
    return out


_ORDINALS = {'first': '1', '1st': '1', 'second': '2', '2nd': '2', 'third': '3', '3rd': '3', 'fourth': '4',
             '4th': '4', 'primeiro': '1', 'segundo': '2', 'terceiro': '3', 'quarto': '4',
             '1.º': '1', '2.º': '2', '3.º': '3', '4.º': '4', '1º': '1', '2º': '2', '3º': '3', '4º': '4'}
_QUARTER_WORDS_RE = re.compile(
    r'(?<!\w)(first|second|third|fourth|1st|2nd|3rd|4th|primeiro|segundo|terceiro|quarto|[1-4]\.?º)'
    r'[\s-]+(quarter|half|trimestre|semestre)\b', re.I)   # nexus: R17 "third-quarter"


def _months(text: str) -> set[int]:
    out = {_MONTHS[w.lower()] for w in WORD_RE.findall(text) if w.lower() in _MONTHS}
    if re.search(r'\bMay\b', text):           # "may" the modal verb is lowercase
        out.add(5)
    return out


def _proper_words(text: str, *, sentence_initial: bool) -> set[str]:
    """Capitalized words that name something (casefolded). A word that opens
    a sentence counts only with sentence_initial=True or a possessive
    ("France's"), since a sentence-initial capital is usually a common word."""
    out = set()
    for m in _PROPER_WORD_RE.finditer(text):
        w = m.group(0)
        if not w[0].isupper() or w in STOP_ENTITIES or w.lower() in _MONTHS or w == 'May':
            continue
        if len(w) < 3 and not w.isupper():
            continue
        initial = bool(SENTENCE_START_RE.search(text[:m.start()]))
        possessive = text[m.end():m.end() + 2] in ("'s", "’s")
        if initial and not (sentence_initial or possessive):
            continue
        out.add(w.casefold())
    return out


def qualifier_conflict(claim_text: str, quote: str) -> str | None:
    """Note naming the qualifier the quote states differently, else None."""
    for extract, note in ((_currencies, 'currency mismatch'), (_quarters, 'quarter mismatch'),
                          (_months, 'month mismatch')):
        c, q = extract(claim_text), extract(quote)
        if c and q and not c <= q:
            return note
    # identifiers (COVID-19, GPT-4) are compared as tokens, not as names
    claim_text, quote = IDENTIFIER_RE.sub(' ', claim_text), IDENTIFIER_RE.sub(' ', quote)
    claim_names = _proper_words(claim_text, sentence_initial=True)
    quote_words = {w.casefold() for w in WORD_RE.findall(unicodedata.normalize('NFC', quote))}
    claim_words = {w.casefold() for w in WORD_RE.findall(unicodedata.normalize('NFC', claim_text))}
    missing = claim_names - quote_words
    other = _proper_words(unicodedata.normalize('NFC', quote), sentence_initial=False) - claim_words
    if missing and other:
        return 'entity mismatch: the evidence names another subject'
    return None


def numbers_conflict(claim_numbers: set[str], quote: str, matches: list[tuple],
                     extract=extract_non_year_numbers) -> bool:
    """nexus: the quote is on the same topic but, instead of one of the
    claim's numbers, states another number of the same kind ("from 10% to
    12%" vs "from 10% to 15%"; "fell 12%" vs "fell 3%"). Sharing one number
    does not excuse another that differs; a number of another kind ("$5
    billion" next to a claimed "12%") is a different quantity, not a
    conflict. With extract=extract_years, the same check for years ("in
    2024" vs "in 2019")."""
    if not claim_numbers:
        return False
    quote_numbers = extract(quote)
    token_match = next((m for name, m, *_ in matches if name == 'tokens'), 0.0)
    if token_match < 0.5:
        return False
    missing, extra = claim_numbers - quote_numbers, quote_numbers - claim_numbers
    return any(number_kind(n) == number_kind(m) for n in missing for m in extra)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def factual_claims(claims: list[dict], *statuses: str) -> list[dict]:
    """Return the factual claims whose support_status is one of statuses."""
    return [
        c for c in claims
        if c.get('claim_type') == 'factual' and c.get('support_status') in statuses
    ]


def append_claim_section(lines: list[str], heading: str, claims: list[dict]) -> None:
    """Append a report section listing claims with their status and notes."""
    lines.append(f'## {heading}')
    lines.append('')
    for c in claims:
        lines.append(f'- [{c["support_status"]}] `{c["section_id"]}`: {c["text"][:100]}...')
        if c.get('_support_notes'):
            lines.append(f'  Notes: {c["_support_notes"]}')
    lines.append('')


def cmd_verify(args: argparse.Namespace) -> None:
    """Verify all claims against evidence, update claims.jsonl."""
    claims_path = os.path.join(args.dir, 'claims.jsonl')
    evidence_path = os.path.join(args.dir, 'evidence.jsonl')
    sources_path = os.path.join(args.dir, 'sources.jsonl')

    claims = read_jsonl(claims_path)
    evidence = read_jsonl(evidence_path)
    sources = read_jsonl(sources_path)

    # Build evidence index by source_id
    ev_by_source: dict[str, list[str]] = {}
    ev_by_id: dict[str, dict] = {}
    for ev in evidence:
        sid = ev.get('source_id', '')
        eid = ev.get('evidence_id', '')
        ev_by_source.setdefault(sid, []).append(ev.get('quote', ''))
        ev_by_id[eid] = ev

    # Deduplicate claims
    seen = set()
    unique_claims = []
    for c in claims:
        cid = c.get('claim_id')
        if cid not in seen:
            seen.add(cid)
            unique_claims.append(c)

    verified = 0
    updated_claims = []

    for claim in unique_claims:
        claim_type = claim.get('claim_type', 'factual')

        # Gather evidence for this claim
        cited_ids = claim.get('cited_source_ids', [])
        evidence_ids = claim.get('evidence_ids', [])

        # Collect evidence quotes from linked evidence_ids
        quotes = []
        for eid in evidence_ids:
            if eid in ev_by_id:
                quotes.append(ev_by_id[eid].get('quote', ''))

        # Also gather from cited sources
        for sid in cited_ids:
            if sid in ev_by_source:
                quotes.extend(ev_by_source[sid])

        if not quotes and not cited_ids and not evidence_ids:
            # No links at all
            if claim_type == 'speculation':
                claim['support_status'] = 'supported'  # Speculation doesn't need evidence
            else:
                claim['support_status'] = 'unsupported'
        elif not quotes:
            # Has cited sources but no evidence captured yet
            claim['support_status'] = 'needs_review'
        else:
            status, score, notes = compute_support_score(claim['text'], quotes)
            claim['support_status'] = status
            claim['_support_score'] = score
            claim['_support_notes'] = notes

        verified += 1
        updated_claims.append(claim)

    # Rewrite claims.jsonl with updated statuses
    write_jsonl(claims_path, updated_claims)

    # nexus: a layer-1 red flag (unsupported, needs_review, contradicted) is
    # a question for the layer-4 verifiers, not a final verdict. Once layer
    # 4 has finished on a flagged claim (it has votes and claim_ledger needs
    # no more: decided, or the verifier budget is spent), --strict hands it
    # to the ledger gate, which enforces the outcome: refuted text removed,
    # contested/unverified ids listed, the unverified-rate cap. The
    # deterministic status stays in claims.jsonl so the ledger can see it.
    cfg = ledger_cfg(args)
    votes_by_claim: dict[str, list[dict]] = {}
    for v in read_jsonl(os.path.join(args.dir, 'votes.jsonl')):
        votes_by_claim.setdefault(v.get('claim_id'), []).append(v)
    resolved_ids = set()
    for c in factual_claims(updated_claims, 'unsupported', 'needs_review', 'contradicted'):
        votes = votes_by_claim.get(c.get('claim_id'), [])
        if votes and votes_still_needed(votes, cfg) == 0:
            resolved_ids.add(c.get('claim_id'))

    # Compute summary
    status_counts = Counter(c.get('support_status') for c in updated_claims)
    factual_unsupported = len(factual_claims(updated_claims, 'unsupported'))
    factual_needs_review = len(factual_claims(updated_claims, 'needs_review'))
    factual_contradicted = len(factual_claims(updated_claims, 'contradicted'))
    total_factual = sum(1 for c in updated_claims if c.get('claim_type') == 'factual')
    unresolved = [c.get('claim_id') for c in factual_claims(
        updated_claims, 'unsupported', 'needs_review', 'contradicted')
        if c.get('claim_id') not in resolved_ids]

    # Strict mode: fail if any factual claim is unsupported, or contradicted
    # / needs review without a verifier resolution
    passed = not (args.strict and unresolved)

    print(json.dumps({
        'status': 'pass' if passed else 'fail',
        'verified': verified,
        'support_status_counts': dict(status_counts),
        'factual_unsupported': factual_unsupported,
        'factual_needs_review': factual_needs_review,
        'factual_contradicted': factual_contradicted,
        'resolved_by_verifiers': len(resolved_ids),
        'unresolved_claim_ids': unresolved,
        'total_factual': total_factual,
        'unsupported_rate': round((factual_unsupported + factual_contradicted) / max(total_factual, 1), 3),
        'note': 'deterministic red-flag filter only; semantic verdicts come from claim_ledger.py',
    }, indent=2))

    if not passed:
        sys.exit(1)


def cmd_report(args: argparse.Namespace) -> None:
    """Generate human-readable support verification report."""
    claims_path = os.path.join(args.dir, 'claims.jsonl')
    claims = read_jsonl(claims_path)

    # Deduplicate
    seen = set()
    unique = []
    for c in claims:
        cid = c.get('claim_id')
        if cid not in seen:
            seen.add(cid)
            unique.append(c)

    lines = ['# Claim Support Verification Report', '']

    # Summary
    status_counts = Counter(c.get('support_status') for c in unique)
    type_counts = Counter(c.get('claim_type') for c in unique)
    lines.append(f'**Total claims:** {len(unique)}')
    lines.append(f'**By type:** {dict(type_counts)}')
    lines.append(f'**By status:** {dict(status_counts)}')
    lines.append('')

    # Unsupported factual claims (the failures)
    unsupported_factual = factual_claims(unique, 'contradicted', 'unsupported', 'needs_review')
    if unsupported_factual:
        append_claim_section(lines, 'Contradicted/Unsupported/Review-needed Factual Claims', unsupported_factual)

    # Partial factual claims: some overlap, below the support threshold
    partial_factual = factual_claims(unique, 'partial')
    if partial_factual:
        append_claim_section(lines, 'Partially Supported Factual Claims', partial_factual)

    if not unsupported_factual and not partial_factual:
        lines.append('## All factual claims passed the lexical support check.')
        lines.append('')

    lines.append(
        '_Support status comes from a lexical heuristic (shared words, '
        'numbers, years, entities and negation). It is not semantic '
        'verification: a claim marked supported can still misstate its source. '
        'Semantic verdicts come from independent verifier votes resolved by '
        '`claim_ledger.py`._'
    )

    print('\n'.join(lines))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog='verify_claim_support',
        description='Claim-support red-flag filter for nexus-deep-research',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # verify
    p_ver = sub.add_parser('verify', help='Verify claims against evidence')
    p_ver.add_argument('--dir', required=True, help='Run directory')
    p_ver.add_argument('--strict', action='store_true',
                       help='Exit 1 if a factual claim is unsupported, contradicted or needs review '
                            'and layer 4 has not finished on it (votes.jsonl; claim_ledger.py pending '
                            'asks for no more). Once layer 4 has finished, the outcome is enforced '
                            'by claim_ledger.py gate')
    p_ver.add_argument('--support-threshold', type=int, dest='support_threshold',
                       help='as in claim_ledger.py (default 2)')
    p_ver.add_argument('--refute-threshold', type=int, dest='refute_threshold',
                       help='as in claim_ledger.py (default 2)')
    p_ver.add_argument('--max-verifiers', type=int, dest='max_verifiers',
                       help='as in claim_ledger.py (default 3)')

    # report
    p_rep = sub.add_parser('report', help='Generate verification report')
    p_rep.add_argument('--dir', required=True, help='Run directory')

    args = parser.parse_args()
    dispatch = {
        'verify': cmd_verify,
        'report': cmd_report,
    }
    dispatch[args.command](args)


if __name__ == '__main__':
    main()
