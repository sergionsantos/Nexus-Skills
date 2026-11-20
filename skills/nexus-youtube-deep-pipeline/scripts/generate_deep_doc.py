#!/usr/bin/env python3
"""
Generate a deep knowledge document from a cleaned transcript.

Calls the LLM with a content-type-specific deep prompt, reads the cleaned
transcript in 4 chunks, and writes the result to the output path.

This is a SKELETON — the LLM call implementation depends on the runtime
environment (available providers, API keys). Customise the provider chain
(`PROVIDERS`) for your environment.

Usage:
    python3 generate_deep_doc.py \
        --cleaned-transcript TRANSCRIPT \
        --video-meta '{"url": "...", "title": "...", ...}' \
        --content-type personal-development \
        --output /tmp/draft.md
"""

import argparse
import collections
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


def _load_env():
    """Optionally load KEY=VALUE lines from the file named by YTDEEP_ENV_FILE
    (e.g. API keys for an extra HTTP provider). Variables already set in the
    environment win. No file configured -> nothing happens."""
    path = os.environ.get("YTDEEP_ENV_FILE")
    if not path:
        return
    env_file = pathlib.Path(path).expanduser()
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()

LLM_TIMEOUT_SECS = int(os.environ.get("PROCESS_TIMEOUT", "300"))

# Retry budget. The whole chain is retried while errors look transient, up to
# this many seconds in total. Keep it BELOW the poller's budget
# (wait_for_status.sh defaults to 90 x 20s = 1800s) so a hopeless run ends as
# state=error with a real message, instead of the poller reporting a timeout.
LLM_MAX_RETRY_SECS = int(os.environ.get("LLM_MAX_RETRY_SECS", "900"))
LLM_RETRY_BASE_SECS = int(os.environ.get("LLM_RETRY_BASE_SECS", "5"))
LLM_RETRY_MAX_SLEEP = int(os.environ.get("LLM_RETRY_MAX_SLEEP", "120"))

# Local `claude -p` link. YTDEEP_CLAUDE_BIN pins the binary (tests point it at
# a missing path so the chain never reaches a real, billed CLI). The timeout
# is generous: a 30KB document takes 2-12 minutes through the CLI.
CLAUDE_BIN_ENV = "YTDEEP_CLAUDE_BIN"
CLAUDE_TIMEOUT_SECS = int(os.environ.get("CLAUDE_TIMEOUT", "1200"))

# Provider chain — the local `claude -p` CLI only.
# Only the local `claude` CLI is configured. Any other provider (an HTTP
# OpenAI-compatible endpoint) can be added as a further link below.
# The claude link (kind "cli") uses the machine's own Claude login, no API
# key; `--model claude-sonnet` (the default) names it. A link with no
# credential is SKIPped. The generic OpenAI-compatible HTTP path
# (`_post_chat`, kind "http", needs "key_envs"/"base_url"/"temperature"/
# "extra_headers") is kept for adding a link later; no HTTP link is configured
# now, and test_generate_deep_doc.py injects stub HTTP links into a sandbox copy.
# ponytail: a list of dicts, not a provider class hierarchy. Add a link by
# appending a dict; only a non-HTTP provider would need new code.
PROVIDERS = [
    {
        "name": "claude-sonnet",
        "kind": "cli",
        # CLAUDE_CLI_MODEL: any alias `claude --model` accepts (opus, sonnet, full id).
        "model": os.environ.get("CLAUDE_CLI_MODEL", "sonnet"),
    },
]


def load_template(content_type):
    """Load the deep prompt template for a given content type."""
    type_map = {
        "personal-development": "deep_personal_development.md",
        "trader-biography": "deep_biography.md",
        "business": "deep_business.md",
        "ai-tech": "deep_business.md",
        "health": "deep_business.md",
        "real-estate": "deep_business.md",
    }
    fname = type_map.get(content_type, "deep_personal_development.md")
    template_path = TEMPLATES_DIR / fname
    if not template_path.exists():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        sys.exit(1)
    # The whole file, not just the "Generation prompt" block: the output
    # structure (section order, per-section fields) lives above it, and the
    # prompt's "sections in the order above" points at it.
    return template_path.read_text(encoding="utf-8")


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def size_profile(chars):
    """Output budget derived from the cleaned transcript length.

    Depth is chosen by whoever invokes the pipeline, never by video length: a
    10-minute video can be processed deep. What scales is HOW MUCH the source
    can support. Ratios are calibrated so a ~500KB transcript lands on the
    template ceilings (100KB doc, 15 concepts, 40 quotes...) and a ~26KB one
    (19 min) on a ~34KB doc with 12 concepts and 29 quotes.
    """
    return {
        "doc_kb": _clamp(round(chars * 1.3 / 1000), 12, 100),
        "concepts": _clamp(round(chars / 2200), 5, 15),
        "frameworks": _clamp(round(chars / 8000), 2, 5),
        "traps": _clamp(round(chars / 2500), 4, 13),
        "tools": _clamp(round(chars / 2500), 4, 11),
        "quotes": _clamp(round(chars / 900), 10, 40),
        "rows": _clamp(round(chars / 1000), 8, 25),
        "timeline": _clamp(round(chars / 3000), 4, 15),
        "links": _clamp(round(chars / 1800), 8, 20),
    }


# Appended to every prompt. Without it the model sometimes treats the task as "create a
# file", finds no write tool and replies with an apology around (or instead of) the doc.
OUTPUT_CONTRACT = (
    "\n\nOUTPUT CONTRACT — your entire reply IS the document. "
    "Start with the YAML frontmatter (---) and end with the last section. "
    "There is no file to write and no tool to call: never mention files, tools, permissions, "
    "saving, or offers to do anything after the document. "
    "Do not wrap the document in a code fence. Quote every frontmatter string that contains "
    "a colon, and write tema_principal as ONE double-quoted line.\n"
)


def sizing_block(chars):
    """Prompt text that overrides the template's fixed counts and sizes."""
    s = size_profile(chars)
    return (
        "\n\nSIZING — this OVERRIDES every count and size in the template above; "
        "the template numbers are ceilings for a 90+ minute source. "
        f"The cleaned transcript is {chars:,} characters. Size the document to what it supports:\n"
        f"- Document size: about {s['doc_kb']}KB (never above 100KB)\n"
        f"- Main concepts / lessons: up to {s['concepts']}\n"
        f"- Frameworks / strategy elements: up to {s['frameworks']}\n"
        f"- Traps / errors: up to {s['traps']}\n"
        f"- Tools and techniques: up to {s['tools']}\n"
        f"- Verbatim quotes: up to {s['quotes']}\n"
        f"- Table rows / bullets (De→Para, Sinais de Alarme): up to {s['rows']}\n"
        f"- Timeline entries: up to {s['timeline']}\n"
        f"- Wikilinks: up to {s['links']}\n"
        "Fewer well-supported items beat padding: never invent, repeat or stretch "
        "material to reach a count. Omit a section (biography, timeline, mindset "
        "table) when the source gives it no material, and say so in Metadados Internos.\n"
    )


def split_into_chunks(transcript, n_chunks=4):
    """Split transcript by sentence count into n_chunks roughly equal parts."""
    sentences = [s for s in transcript.split("\n") if s.strip()]
    chunk_size = len(sentences) // n_chunks
    chunks = []
    for i in range(n_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < n_chunks - 1 else len(sentences)
        chunks.append("\n".join(sentences[start:end]))
    return chunks


# Info strings the LLM has been seen using on the spurious wrapper fence.
# (`markdown` was observed on a spurious wrapper fence, 2026-08-10, live probe.)
_WRAP_FENCE = r'```(?:yaml|markdown|md)'


# Conversational noise the model sometimes writes AROUND the document when it believes
# it must "save a file" it has no tool for (observed on 40 of 48 runs for one channel): a preamble ("I have no write tool, so here is the document"), the document
# inside a ```markdown fence, and a closing offer ("If you want, I can save it...").
_POSTAMBLE = re.compile(
    r'^(se (quiser|preferir|reativar)|note:|\*\*note|done\s*[—-]|if you.d like|'
    r'o documento é|- se quiser|nota:|(não|nao) (consegui gravar|gravei)|i did not save|'
    r'i couldn.t save|\*\*o que fazer agora|diz(-me)? se queres|tell me a path|'
    r'duas notas sobre o documento|o documento tem cerca de)', re.I)
_FM_FENCE = re.compile(r'^```(?:yaml|markdown|md)\s*$')


def _extract_document(content):
    """Return only the document when the model wrapped it in chatter.

    No-op for a clean response (starts with frontmatter or an H1, no stray text).
    Cases handled:
      - preamble text before the document;
      - a ```markdown fence around the whole document, with text after the close;
      - an H1 line emitted before a ```yaml-fenced frontmatter (the H1 is dropped:
        the document's own H1 follows the frontmatter);
      - trailing offers/notes after the last section.
    A fence whose closing line sits right after the frontmatter's closing '---'
    is left for _strip_wrapping_fence (variant 1)."""
    lines = content.split("\n")
    n = len(lines)
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is None:
        return content
    start = None
    for i in range(first, min(n, first + 40)):
        # A wrapper is a fence whose body starts with frontmatter ('---'), or a ```markdown/md
        # fence that opens on an H1. A ```yaml block starting with a '# comment' is real code.
        info = lines[i].strip()[3:].strip()
        if _FM_FENCE.match(lines[i].strip()) and i + 1 < n and (
                lines[i + 1].strip() == "---" or (info in ("markdown", "md") and lines[i + 1].startswith("# "))):
            start = i
            break
    if start is not None and start > first:
        lines = lines[start:]
    elif start is None and not (lines[first].strip() == "---" or lines[first].startswith("# ")):
        # preamble without a fence: the document starts at the first frontmatter or H1
        for i in range(first, n):
            if lines[i].strip() == "---" or lines[i].startswith("# "):
                lines = lines[i:]
                break
    # whole-document ```markdown wrap that is closed before EOF: cut at the close
    if lines and _FM_FENCE.match(lines[0].strip()):
        fm_end = None
        if len(lines) > 1 and lines[1].strip() == "---":
            fm_end = next((i for i in range(2, len(lines)) if lines[i].strip() == "---"), None)
        right_after_fm = fm_end is not None and fm_end + 1 < len(lines) and lines[fm_end + 1].strip() == "```"
        if not right_after_fm:
            bare = [i for i in range(1, len(lines)) if lines[i].strip() == "```"]
            close = bare[-1] if bare and bare[-1] > len(lines) // 2 and not any(
                l.startswith("#") for l in lines[bare[-1] + 1:]) else None
            lines = lines[1:close] if close is not None else lines[1:]
    # A closing offer can span several lines ("I did not save the file. ... Tell me a path"):
    # cut from its first line when it sits in the last 12 lines and no heading follows it.
    tail_from = max(0, len(lines) - 12)
    for k in range(tail_from, len(lines)):
        if _POSTAMBLE.match(lines[k].strip()) and not any(l.startswith("#") for l in lines[k:]):
            lines = lines[:k]
            break
    # Orphan closing fence followed by a short free-text offer, whatever its wording:
    # unbalanced fences, the last fence within 12 lines of the end, no heading after it.
    if sum(1 for l in lines if l.strip().startswith("```")) % 2 == 1:
        bare = [i for i, l in enumerate(lines) if l.strip() == "```"]
        if bare and len(lines) - bare[-1] <= 12 and not any(l.startswith("#") for l in lines[bare[-1]:]):
            lines = lines[:bare[-1]]
    # A trailing ``` is popped only when fences are unbalanced (an orphan wrapper
    # close); a balanced one closes a real code block at the end of the document.
    def _orphan_fence():
        return lines[-1].strip() == "```" and sum(1 for l in lines if l.strip().startswith("```")) % 2 == 1
    while lines and (not lines[-1].strip() or lines[-1].strip() == "---"
                     or _POSTAMBLE.match(lines[-1].strip()) or _orphan_fence()):
        lines.pop()
    return "\n".join(lines) + "\n"


# What a finished document must contain. A refusal ("I cannot write files") is a
# 200 OK of a few hundred chars to a few KB and passes every size check.
_DOC_START = re.compile(r'\A(---\n|```(?:yaml|markdown|md)\n---\n|# )')
_HAS_SUMARIO = re.compile(r'^#{1,3}\s*Sum[aá]rio\b', re.M)


def _strip_wrapping_fence(content):
    """Strip a spurious wrapper fence the LLM sometimes puts around the response.
    Three observed variants (info string is yaml, markdown or md):
      1. ```yaml ... --- frontmatter --- ``` (closed right after frontmatter)
      2. ```yaml ... --- frontmatter --- (never closed, straight into the H1)
      3. no opening fence at all, but a bare trailing ``` orphaned at EOF
         (LLM closes a wrap it never opened, or appends one out of habit)
    Only strips at the document boundaries — never touches fences elsewhere
    in the body (a real closing fence of a code block always has a matching
    opening fence, keeping the total count even).

    Variant 3 runs on the content AFTER 1/2 stripped any opening fence: a
    whole-document wrap (```markdown at line 0, ``` at EOF) is an EVEN fence
    count while the opener is still there, which is exactly what disarmed the
    odd-count heuristic before. Dropping the opener first makes the orphan
    trailing fence odd, so variant 3 then removes it. Order matters here.

    The parity count is only a tie-breaker for the no-opener case: once an
    opening wrap HAS been stripped, a bare trailing fence closes that wrap and
    goes regardless of parity (an unclosed ```python inside the body would
    otherwise make the count even again and strand the wrapper fence).

    Known ceilings (deliberate, not oversights): a four-backtick wrap
    (````markdown … ````) and info strings outside the alternation (```mdx)
    are left untouched. Four backticks is the correct way to wrap a document
    that itself contains fences, so it is the likeliest next variant to
    appear — extend _WRAP_FENCE when it does.

    The third ceiling is the consequential one, and it is a genuine ambiguity
    rather than a bug: `opener, body, ```python, code, ``` ` is the SAME token
    sequence whether that last fence closes the inner code block or closes an
    unclosed wrap. This code assumes it closes the wrap, so a document wrapped
    in an unclosed ```markdown whose last block is real code loses that block's
    closing fence. No local rule can satisfy both readings; a four-backtick
    wrap is what disambiguates them at the source."""
    stripped_opener = False
    if re.match(_WRAP_FENCE, content):
        # Variant 1: closing fence right after frontmatter's closing '---'
        m = re.match(_WRAP_FENCE + r'\s*\n(---\n.*?\n---\n)```\s*\n(.*)$', content, flags=re.DOTALL)
        if m:
            content = m.group(1) + "\n" + m.group(2)
        else:
            # Variant 2: no closing fence here — drop the opening fence line.
            # If the wrap IS closed at EOF, variant 3 below takes that half.
            m = re.match(_WRAP_FENCE + r'\s*\n(.*)$', content, flags=re.DOTALL)
            if m:
                content = m.group(1)
                # Variant 1 consumes its own closing fence; variant 2 does not,
                # so a trailing fence below belongs to THIS wrap.
                stripped_opener = True
    # Variant 3: bare trailing ``` at EOF. Certain when we just removed the
    # matching opener; otherwise decided by parity (unbalanced — a real fenced
    # code block always pairs, so an odd count means that last fence is the
    # spurious wrapper rather than a legit code block).
    lines = content.split("\n")
    trailing_idx = len(lines) - 1
    while trailing_idx >= 0 and lines[trailing_idx].strip() == "":
        trailing_idx -= 1
    if trailing_idx >= 0 and lines[trailing_idx].strip() == "```":
        fence_count = sum(1 for l in lines if l.strip().startswith("```"))
        if stripped_opener or fence_count % 2 == 1:
            content = "\n".join(lines[:trailing_idx]).rstrip() + "\n"
    return content


class ProviderOutputError(Exception):
    """A 200 OK whose body is unusable: truncated, or stuck in a repeat loop."""


# A degenerate line is one long line made almost entirely of one character —
# counting only characters that carry meaning. Markdown layout (spaces, table
# pipes, rules, padding) is legitimately repetitive: a 6-column aligned table
# row measures 0.83 and a separator row 0.97, so counting raw characters would
# throw away good documents. SKILL.md Step 3 asks for a 25-row table, so this
# is not hypothetical.
# Measured on real docs, non-layout chars only: worst legitimate line is 0.18;
# the observed failure was 0.999 (20328 x '底' in a 20342-char line).
_LOOP_MIN_LINE = 200
_LOOP_CHAR_RATIO = 0.5
_LAYOUT_CHARS = set(" \t-|=_*#.:+")

# A whole document that repeats itself: measured uniqueness on real artefacts is
# 0.887-0.972, while a doc looping one line sits near 0. Only applied to docs
# long enough for the ratio to mean anything.
_DUP_MIN_LINES = 50
_DUP_UNIQUE_RATIO = 0.5

# Real deep docs are 30-100KB. Anything this short is not a document; the case
# that motivated it is a completion that was all <think> and nothing else,
# which the reasoning-block strip turns into the empty string.
_MIN_DOC_CHARS = 500


def _reject_bad_completion(content, finish_reason):
    """Raise unless the completion actually looks like a finished document.

    A 200 OK is not success. On 2026-08-10 a run wrote a doc whose last line
    was 20342 chars of one Chinese ideograph and which stopped at 7 of the 13
    required sections — and every check downstream passed it (size matched the
    status, first line was ---, no stray fences, state=done), because nothing
    ever looked at the response itself. Truncation and repeat loops are the two
    failures a provider signals cheaply, so check exactly those two here, where
    the next link in the chain can still rescue the run.

    ponytail: cheap signals, not a quality model. This catches "the model
    broke", not "the model wrote something mediocre" — judging content is the
    fact-check step's job (SKILL.md Step 4).

    Named ceiling: this covers repetition at LINE granularity — one degenerate
    line, or a document made of duplicate lines. A loop that repeats a word or
    phrase WITHIN one line of otherwise varied text is not seen, because no
    single character dominates it. Catching that needs n-gram counting, which
    is more machinery than the failures actually observed justify. It also says
    nothing about whether the 13 sections SKILL.md asks for are present.
    """
    # Absent or empty finish_reason counts as not-clean: treating a missing
    # field as success silently disarms the check for any provider that omits
    # it, which is the failure mode this whole function exists to prevent.
    if finish_reason != "stop":
        # "length" = hit max_tokens mid-document. Anything else the vendor
        # invents (content_filter, ...) is likewise not a clean ending.
        raise ProviderOutputError(
            f"completion did not finish cleanly (finish_reason={finish_reason!r}); "
            f"got {len(content)} chars")
    if len(content.strip()) < _MIN_DOC_CHARS:
        raise ProviderOutputError(
            f"completion is too short to be a document: {len(content.strip())} chars")
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        if len(line) < _LOOP_MIN_LINE:
            continue
        signal = [c for c in line if c not in _LAYOUT_CHARS]
        if len(signal) < _LOOP_MIN_LINE // 2:
            continue  # mostly layout: a table row, a rule, an indented block
        char, count = collections.Counter(signal).most_common(1)[0]
        if count / len(signal) > _LOOP_CHAR_RATIO:
            raise ProviderOutputError(
                f"repeat loop on line {i}: {count}/{len(signal)} non-layout chars are {char!r}")
    body = [l for l in lines if l.strip()]
    if len(body) >= _DUP_MIN_LINES:
        distinct = len(set(body))
        if distinct / len(body) < _DUP_UNIQUE_RATIO:
            raise ProviderOutputError(
                f"document repeats itself: only {distinct} distinct of {len(body)} lines")


def _reject_not_a_document(content):
    """Shape check, kept apart from _reject_bad_completion (which is only about
    truncation and loops): a refusal or a reply that talks about files is a 200 OK
    that passes every size check, so the chain must see it as a provider failure."""
    if not _DOC_START.match(content.lstrip()):
        raise ProviderOutputError(
            "completion does not start with frontmatter or an H1 (preamble or refusal): "
            + content.strip()[:120].replace("\n", " "))
    if not _HAS_SUMARIO.search(content):
        raise ProviderOutputError("completion has no Sumário section: not a knowledge document")


def _finish_completion(content, finish_reason):
    """Shared tail of every provider: strip reasoning/wrapper noise, then reject
    a truncated or degenerate completion."""
    # ponytail: strip <think>...</think>. Reasoning models prefix the completion
    # with it; harmless for claude, kept for any future reasoning-model link.
    content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)
    content = re.split(r'<think>', content)[0]
    content = _strip_wrapping_fence(_extract_document(content))
    _reject_bad_completion(content, finish_reason)
    _reject_not_a_document(content)
    return content


def _post_chat(provider, api_key, full_prompt):
    """POST one OpenAI-compatible /chat/completions request. Raises on failure."""
    payload = json.dumps({
        "model": provider["model"],
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": provider["temperature"],
        "max_tokens": 32000,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    headers.update(provider["extra_headers"])

    req = urllib.request.Request(
        f"{provider['base_url']}/chat/completions",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SECS) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    choice = data["choices"][0]
    content = choice["message"]["content"]
    return _finish_completion(content, choice.get("finish_reason"))


def _find_claude_cli():
    """Path of a runnable claude binary, or None.

    The fallback paths matter: the generator re-execs itself detached, and a
    cron/launchd/ssh shell often lacks ~/.local/bin on PATH."""
    override = os.environ.get(CLAUDE_BIN_ENV)
    if override:
        return override if os.access(override, os.X_OK) else None
    found = shutil.which("claude")
    if found:
        return found
    for cand in (Path.home() / ".local/bin/claude", Path("/opt/homebrew/bin/claude"),
                 Path("/usr/local/bin/claude")):
        if os.access(cand, os.X_OK):
            return str(cand)
    return None


# Only genuinely transient CLI failures are retried. A usage limit is not: it
# resets in hours, so waiting out the 900s budget would just burn it.
_CLI_TRANSIENT = re.compile(r"overloaded|api error: ?5\d\d|timed? ?out|econn|socket hang up", re.I)


def _run_claude(provider, binary, full_prompt):
    """One `claude -p` call. The prompt goes in on stdin (30KB+ is too large
    for argv); --output-format json is what exposes stop_reason, the only
    truncation signal the CLI gives. Tools are off: this is pure generation.

    Maps failures onto call_llm's classes: TimeoutError/ConnectionError are
    transient, RuntimeError (auth, usage limit, bad output) is not."""
    env = dict(os.environ)
    env.setdefault("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "32000")  # parity with the HTTP links' max_tokens
    # Pure generation must not inherit the user's Claude setup. Two leaks were observed:
    #  - MCP connectors (Claude Docs, Drive): the model answered "I have no permission to
    #    save a file" -> --strict-mcp-config.
    #  - a Stop HOOK (an agent plugin's autopilot) that forces a follow-up turn after the
    #    document: `result` is the LAST turn ("the document above is the deliverable..."),
    #    not the document -> --setting-sources project + a neutral cwd drops user/local
    #    settings, hooks and plugins. Verified 2026-10-20: 222-char hook reply before,
    #    33 KB document after, same prompt.
    cmd = [binary, "-p", "--model", provider["model"], "--tools", "",
           "--strict-mcp-config", "--setting-sources", "project", "--disable-slash-commands",
           "--no-session-persistence", "--output-format", "json"]
    try:
        p = subprocess.run(cmd, input=full_prompt, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env=env, timeout=CLAUDE_TIMEOUT_SECS, cwd=tempfile.gettempdir())
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"claude -p exceeded {CLAUDE_TIMEOUT_SECS}s")
    data = None
    for line in reversed(p.stdout.strip().splitlines()):
        if line.startswith("{"):
            try:
                data = json.loads(line)
            except ValueError:
                pass
            break
    if data is None or p.returncode != 0 or data.get("is_error"):
        detail = ((data or {}).get("result") or p.stderr or p.stdout)[:300].replace("\n", " ")
        msg = f"claude -p exit {p.returncode}: {detail}"
        if _CLI_TRANSIENT.search(detail):
            raise ConnectionError(msg)
        raise RuntimeError(msg)
    stop = data.get("stop_reason")
    return _finish_completion(data.get("result") or "", "stop" if stop == "end_turn" else stop)


def _provider_chain(preferred=None):
    """PROVIDERS, with `preferred` (a provider name) moved to the front.

    No special case for preferred=None/unknown: no provider name equals it, so
    every sort key is True and the stable sort returns PROVIDERS untouched.
    (The removed `if not preferred` shortcut was unreachable from the CLI —
    --model always defaults to a real name — i.e. untestable dead code.)"""
    return sorted(PROVIDERS, key=lambda p: p["name"] != preferred)


def _retry_after_secs(headers):
    """Seconds from a Retry-After header, which is either a delta or an HTTP date."""
    value = (headers or {}).get("Retry-After") if headers else None
    if not value:
        return None
    value = str(value).strip()
    try:
        # OverflowError: float("inf") parses fine but int(inf) raises, which
        # would otherwise kill a retryable 429 on a single malformed header.
        return max(0, int(float(value)))
    except (ValueError, OverflowError):
        pass
    try:
        when = parsedate_to_datetime(value)
        return max(0, int((when - datetime.now(when.tzinfo)).total_seconds()))
    except Exception:
        return None


def call_llm(prompt, transcript_chunks, model=None):
    """
    Call the LLM, retrying the whole chain while the failures look transient.

    One round tries every link once (fast: a model-specific overload is rescued
    immediately by the next model, with no waiting). Only when the round ends
    with nothing but transient failures does it sleep and go round again —
    honouring Retry-After when the server sends one, otherwise exponential
    backoff capped at LLM_RETRY_MAX_SLEEP, and never past LLM_MAX_RETRY_SECS in
    total. With a single vendor this retry IS the 429 mitigation; there is no
    second vendor left to fall through to.

    Retryable: 429, 5xx, socket timeout, connection error. NOT retryable: 401,
    400 and other 4xx (repeating a bad key or a bad payload only burns budget),
    and malformed responses. A link with no API key is skipped, not fatal.
    Raises RuntimeError with every link's last error once the budget is gone.
    """
    chunk_text = "\n\n---\n\n".join(
        f"CHUNK {i+1}/{len(transcript_chunks)}:\n{c}" for i, c in enumerate(transcript_chunks)
    )
    full_prompt = f"{prompt}\n\nTRANSCRIPT CHUNKS:\n{chunk_text}"

    chain = _provider_chain(model)
    deadline = time.monotonic() + LLM_MAX_RETRY_SECS
    attempt = 0
    while True:
        errors = []
        retry_after = None
        transient = False
        for i, provider in enumerate(chain):
            name = provider["name"]
            nxt = chain[i + 1]["name"] if i + 1 < len(chain) else "(end of round)"
            kind = provider.get("kind", "http")
            if kind == "cli":
                credential = _find_claude_cli()
                missing = f"claude CLI not found ({CLAUDE_BIN_ENV} unset or not executable, none on PATH)"
            else:
                credential = next((os.environ[e] for e in provider["key_envs"] if os.environ.get(e)), "")
                missing = f"no API key ({'/'.join(provider['key_envs'])} unset)"
            if not credential:
                print(f"SKIP provider={name}: {missing} -> next={nxt}", file=sys.stderr)
                errors.append(f"{name}: {missing}")
                continue

            print(f"TRY provider={name} model={provider['model']}", file=sys.stderr)
            try:
                if kind == "cli":
                    return _run_claude(provider, credential, full_prompt)
                return _post_chat(provider, credential, full_prompt)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:300].replace("\n", " ")
                reason = f"HTTP {e.code}: {body}"
                if e.code == 429 or 500 <= e.code < 600:
                    transient = True
                    header_wait = _retry_after_secs(e.headers)
                    if header_wait is not None:
                        retry_after = max(retry_after or 0, header_wait)
            except (TimeoutError, ConnectionError, urllib.error.URLError) as e:
                reason = f"{type(e).__name__}: {e}"
                transient = True
            except Exception as e:  # malformed JSON, unexpected shape
                reason = f"{type(e).__name__}: {e}"
            print(f"FAIL provider={name}: {reason} -> next={nxt}", file=sys.stderr)
            errors.append(f"{name}: {reason}")

        if not transient:
            break  # nothing here gets better by waiting

        if retry_after is not None:
            wait, why = retry_after, "Retry-After"
        else:
            wait, why = min(LLM_RETRY_BASE_SECS * 2 ** attempt, LLM_RETRY_MAX_SLEEP), "backoff"
        # Floor the wait. Retry-After legitimately arrives as 0 — an absolute
        # HTTP date already in the past (clock skew, transit time) parses to
        # zero seconds — and sleep(0) turns "back off" into a tight loop:
        # measured 523 requests/s, which against a server that is already
        # rate-limiting us is how a temporary block becomes a permanent one.
        # A hostile or malformed header must never be worse than no header.
        wait = max(wait, LLM_RETRY_BASE_SECS)
        remaining = deadline - time.monotonic()
        if wait >= remaining:
            print(f"GIVE UP after {attempt + 1} round(s): next wait {wait}s exceeds the "
                  f"{LLM_MAX_RETRY_SECS}s retry budget ({int(remaining)}s left)", file=sys.stderr)
            break
        attempt += 1
        print(f"RETRY round {attempt + 1} in {wait}s ({why}), "
              f"{int(remaining)}s of budget left", file=sys.stderr)
        time.sleep(wait)

    raise RuntimeError(
        f"all LLM providers failed after {attempt + 1} round(s):\n  " + "\n  ".join(errors)
    )


def _write_status(path, **fields):
    """Overwrite the status file atomically. Only the running process writes it.

    Plain open(path, "w") truncates first and the JSON only lands on close, so
    a poller reading in that window sees an empty or half-written file. Write
    to a sibling temp and os.replace() — atomic rename on POSIX, so a reader
    sees either the whole old file or the whole new one.
    """
    fields["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    # Unique temp name in the same dir (same filesystem, so os.replace stays
    # atomic). A fixed "<path>.tmp" breaks with two runs on one --output: each
    # replaces the temp the other is still writing, and the resulting
    # FileNotFoundError lands in main()'s handler, which then fails to write
    # the status too — bare traceback, status lost.
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)),
                               prefix=os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(fields, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        # Never leave the temp behind on a serialisation/IO failure.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _adopt_child_pid(status_file, pid, output, log_path):
    """Record the child's pid in the status, but only while it still says
    "starting".

    Why write it at all: the child can die during interpreter startup, imports
    or _load_env(), i.e. before it writes "running" itself. A "starting" status
    with no pid leaves the poller with nothing to check liveness against, so it
    burns its whole budget and reports a timeout instead of a death.

    Why guarded: from the child's first write onwards the child owns this file,
    and pushing a newer state back to "starting" would make a poller read a
    finished run as dead.

    ponytail: read-then-write, NOT atomic. There is a sub-millisecond window
    where the child could advance between the read and the write, and the
    parent would then revert it. Left as-is because the failure direction is
    safe — the poller reports a live run as dead (exit 2, pipeline stops on a
    good draft) and never reports a dead run as done — and closing it properly
    means a lock file, which is more machinery than the window deserves. The
    concurrent-run case that made this reachable is handled upstream instead,
    by refusing to start a second run on the same --output at all.
    """
    try:
        if json.loads(Path(status_file).read_text()).get("state") == "starting":
            _write_status(status_file, state="starting", pid=pid,
                          output=output, log=log_path)
    except Exception:
        pass  # child already owns the file, or it is mid-write — leave it alone


def _pid_alive(pid):
    """Is `pid` a running process? Never signals it on Windows, where
    os.kill(pid, 0) would TERMINATE the target (any signal but CTRL_*_EVENT
    goes to TerminateProcess)."""
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(k32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # alive, just not ours — still a reason to refuse
    except OSError:
        return False
    return True


def _live_run_pid(status_file):
    """The pid of a run still working on this status file, or None.

    None also when the status names this very process: the background child
    re-execs with the same --status-file, and the pid recorded there is its own.
    """
    try:
        st = json.loads(Path(status_file).read_text())
    except Exception:
        return None  # missing or unreadable: nothing is running
    if st.get("state") not in ("starting", "running"):
        return None
    pid = st.get("pid")
    if not isinstance(pid, int) or pid == os.getpid():
        return None
    return pid if _pid_alive(pid) else None


def _spawn_background(args):
    """Re-exec self detached and return immediately.

    The LLM call takes minutes; any foreground caller (Claude Code harness at
    120s, a shell with a timeout, an ssh session) will cut it. So background is
    the DEFAULT and the caller polls the status file.
    ponytail: Popen + start_new_session + a status JSON. No job runner, no
    queue, no daemon — one call at a time is all this pipeline ever does.
    """
    log_path = args.output + ".log"
    _write_status(args.status_file, state="starting", output=args.output, log=log_path)
    # A bare traceback here would leave the status stuck at "starting" forever,
    # and a poller waiting on done|error would spin for ever with it.
    try:
        with open(log_path, "w") as log:
            child = subprocess.Popen(
                [sys.executable, os.path.abspath(__file__)] + sys.argv[1:] + ["--foreground"],
                stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except Exception as e:
        _write_status(args.status_file, state="error", output=args.output, log=log_path,
                      error=f"spawn failed: {type(e).__name__}: {e}")
        print(f"ERROR: could not start background run: {e}", file=sys.stderr)
        sys.exit(2)
    _adopt_child_pid(args.status_file, child.pid, args.output, log_path)
    print(f"Started in background: pid={child.pid}")
    print(f"  log:    {log_path}")
    print(f"  status: {args.status_file}")
    print(f"  output: {args.output}")
    print(f"Poll with: cat {args.status_file}   # state: starting|running|done|error")


def main():
    parser = argparse.ArgumentParser(description="Generate deep knowledge doc from cleaned transcript")
    parser.add_argument("--cleaned-transcript", required=True)
    parser.add_argument("--video-meta", required=True, help="JSON string with url, title, channel, date, duration")
    parser.add_argument("--content-type", default="personal-development")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="claude-sonnet",
                        help="provider link tried first (the only link configured: claude-sonnet)")
    parser.add_argument("--n-chunks", type=int, default=4)
    parser.add_argument("--foreground", action="store_true",
                        help="Block until the LLM finishes (default: detach and poll --status-file)")
    parser.add_argument("--status-file", default=None,
                        help="Progress/result JSON (default: <output>.status.json)")
    args = parser.parse_args()

    if not args.status_file:
        args.status_file = args.output + ".status.json"

    # Before the first _write_status: a missing dir used to kill the parent
    # with a bare FileNotFoundError, leaving no status file at all for the
    # caller's poll loop to ever see. --status-file is its own flag and can
    # point somewhere else entirely, so both dirs need this, not just --output.
    # makedirs only fixes "dir absent". A dir that exists but is not writable,
    # or a path component that is a file, still cannot hold a status — there is
    # nowhere to write one, so say so on stderr and exit non-zero rather than
    # dying in a bare traceback the caller has to decode.
    try:
        for path in (args.output, args.status_file):
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    except OSError as e:
        print(f"ERROR: cannot create the directory for {path}: {e}", file=sys.stderr)
        sys.exit(2)
    status_dir = os.path.dirname(os.path.abspath(args.status_file))
    if not os.access(status_dir, os.W_OK):
        # ponytail: os.access, not a probe write — a probe write here would
        # clobber the state the busy check below is about to read. It answers
        # the common case (dir exists, not writable); anything exotic (ACLs, ro
        # remount between here and the write) still surfaces as an error later.
        print(f"ERROR: status directory is not writable: {status_dir}", file=sys.stderr)
        sys.exit(2)

    # One run per --output. The status file is a single slot: a second run
    # would overwrite the first one's state, and a poller waiting on run A
    # would get run B's "done" while A silently rewrites the output afterwards
    # — the fact-checked doc and the doc left on disk would differ.
    busy = _live_run_pid(args.status_file)
    if busy:
        print(f"ERROR: another run (pid {busy}) is still working on {args.output}. "
              f"Wait for it, or use a different --output/--status-file.", file=sys.stderr)
        sys.exit(3)

    if not args.foreground:
        _spawn_background(args)
        return

    _write_status(args.status_file, state="running", pid=os.getpid(),
                  output=args.output, log=args.output + ".log")
    try:
        run(args)
        # Inside the try: if this stat raises, the status must still land on
        # error — never be left at "running" for a poller to wait on for ever.
        _write_status(args.status_file, state="done", pid=os.getpid(),
                      output=args.output, log=args.output + ".log",
                      bytes=os.path.getsize(args.output))
    except Exception as e:
        _write_status(args.status_file, state="error", pid=os.getpid(),
                      output=args.output, log=args.output + ".log",
                      error=f"{type(e).__name__}: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


def run(args):
    with open(args.cleaned_transcript, encoding="utf-8") as f:
        transcript = f.read()

    meta = json.loads(args.video_meta)
    template_prompt = load_template(args.content_type)

    chunks = split_into_chunks(transcript, args.n_chunks)

    # Augment prompt with video metadata
    augmented = f"VIDEO: {meta.get('title', '?')} ({meta.get('url', '?')})\n"
    augmented += f"CHANNEL: {meta.get('channel', '?')}\n"
    augmented += f"DATE: {meta.get('date', '?')}\n"
    augmented += f"DURATION: {meta.get('duration', '?')}\n\n"
    augmented += template_prompt
    augmented += sizing_block(len(transcript))
    augmented += OUTPUT_CONTRACT

    print(f"Calling LLM ({args.model}) with {len(chunks)} chunks ({sum(len(c) for c in chunks)} chars total)...", file=sys.stderr)

    result = call_llm(augmented, chunks, model=args.model)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Wrote {len(result)} chars to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
