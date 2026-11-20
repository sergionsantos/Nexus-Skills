---
name: nexus-youtube-deep-pipeline
description: Process a YouTube video with maximum depth — read the full transcript, deduplicate transcription artefacts, fact-check claims, reconstruct biography from dispersed fragments, preserve verbatim quotes, identify and patch gaps. Produces a knowledge document sized to the transcript (about 12KB for a short video, up to 100KB for a long interview) with concepts, frameworks, citations, fact-check coverage, and zero sponsor-read content. Depth is the caller's choice: any video length can use it when the user asks for deep.

**Trigger on ANY of these signals:**
- User says "process with depth", "deep process", "deep pipeline", "processa com profundidade", "processamento profundo", "extract everything", "extrai tudo", "faz um doc completo", "knowledge doc completo"
- User complains the surface process missed content ("surface only got X%", "missed half", "same level of depth you did before")
- Video is high-signal: long-form interview (90min+), framework-rich guest (Naval, Hormozi, Thiel, Dalio, etc.), or content described as "dense", "densíssimo", "deep", "wisdom", "in-depth"
- User explicitly contrasts with surface ("not the surface one", "not the standard", "não precisa de ser standard")

**Do NOT trigger on:**
- Short videos (tutorials, news, summaries) when the user did NOT ask for deep: use a lighter standard summary workflow instead. If the user asks for deep on a short video, run it. Depth is chosen at invocation, never by duration.
- Quick summaries ("resumo", "summary", "sumário", "quick", "brief")
- Different actions: PDF generation, transcript-only export, editing existing docs
- Explicit "surface" or "standard" requests
- Pure transcript extraction without analysis

This skill is a high-investment mode (~12min, ~$0.30 per video) — only use when the user signals the content is worth the cost.
---

# YouTube Deep Pipeline

Process a YouTube video with maximum rigor. Goes beyond the standard extract-then-summarise flow to: deduplicate transcription artefacts, read the full transcript in chunks, verify every claim against the raw text, reconstruct biographical threads, preserve verbatim quotes, identify and patch missing facts.

**When to use this skill:**
- User explicitly asks for deep processing ("processa com profundidade", "deep process", "extract everything")
- Video is long-form (90min+) with a framework-rich guest (Hormozi, Naval, Thiel, Dalio, etc.)
- Video has biographical material (guest tells life stories, family history, business trajectory)
- Surface processing missed significant content (user already complained "se mais detalhado")
- Cost is acceptable: ~$0.30 and ~12min per video, vs ~$0.05/3min for surface

**When NOT to use:**
- Short routine videos (tutorials, news, opinions) when the user did not ask for deep → use a lighter standard summary workflow instead. An explicit deep request on a short video is honoured; the output is sized to the transcript.
- Videos without transcripts (private, region-locked, no captions)
- Pure entertainment / off-topic content
- When user just wants a quick summary and is not in "deep mode"

**Announce at start:** "Vou usar o skill nexus-youtube-deep-pipeline para processar [URL] com profundidade máxima."

**Terminology.** "surface" / "standard" = the lighter, normal summary of a video (not included in this repo); this skill is the deep alternative.

**Setup (once per session).** Two variables are used by every command below; paths are yours to choose:
```bash
SKILL=~/.claude/skills/nexus-youtube-deep-pipeline   # where this skill is installed (or ~/.codex/skills/...)
OUT=~/youtube-knowledge                               # YOUR output folder; nothing is written elsewhere
mkdir -p "$OUT/raw" "$OUT/raw-processed" "$OUT/digests" "$OUT/people"
```
`/tmp/...` in the examples is only a scratch folder; use any writable folder. `$META_JSON` is the video metadata, e.g. `{"url": "...", "title": "...", "channel": "...", "date": "YYYY-MM-DD", "duration": "mm:ss"}` (`yt-dlp --dump-single-json URL` gives these values).

---

## Workflow

The skill orchestrates these steps via the bundled scripts:

1. **Extract** transcript (bring your own extractor, e.g. `yt-dlp`; see Step 1)
2. **Deduplicate** transcription artefact (sliding-window overlap)
3. **Read in chunks** (split by sentence count, ~4 chunks)
4. **Generate** with LLM using the deep template for the content type, sized to the transcript (bio, timeline, ad reads excluded)
5. **Fact-check** every quote and number in the draft against the cleaned transcript (mechanical, not sampled)
6. **Patch gaps** if any check fails
7. **Write final** knowledge document to `$OUT/digests/...` (your output folder)

---

## Step 1: Extract transcript

The bundled scripts do **not** include an extractor: bring your own (e.g. `yt-dlp`, or any tool that exports the transcript with timestamps). The pipeline only needs a UTF-8 text/markdown file: optional frontmatter, then paragraphs of transcript text (ideally `### [mm:ss]` headings every ~45 s). Save it under `$OUT/raw/`.

```bash
yt-dlp --skip-download --write-auto-subs --sub-langs "en.*" --sub-format vtt -o "$OUT/raw/%(id)s" "URL"   # suggestion; convert the .vtt to plain text
```

Capture the raw path from stdout. It will be the input to Step 2.

---

## Step 2: Deduplicate transcription artefact

**Why this matters:** YouTube auto-transcription (and many extractors) produces transcripts with sliding-window overlap. For DOAC Clips and similar channels, every line has 3 overlapping copies of the same content with variable stride — **NOT a clean period-3 repetition** (so naive `s[:n//3] * 3` fails). The artefact must be detected and removed before the LLM sees the transcript, otherwise it processes 3x more text and produces no extra value.

The full algorithm is in `references/transcript-triplication-dedup.md`. Read it first time you encounter a transcript with this artefact. **Use `scripts/dedup_transcript_v3.py` by default** — it's a state-machine chunk-match dedup that works on transcripts with or without terminal punctuation. The older `dedup_transcript.py` (v1) assumes `.!?` tokenization and silently under-reduces (~1% instead of ~60%) on punctuation-less auto-caption transcripts — this once caused an LLM hallucination in production. Kept only for reference; do not use it going forward.

```bash
python3 "$SKILL/scripts/dedup_transcript_v3.py" --raw "RAW_PATH" --output /tmp/cleaned_transcript.txt
```

Check the stderr reduction line: if reduction is well below ~30-60%, the transcript has an unusual artefact shape — inspect manually before proceeding, don't trust a low-reduction run.

---

## Step 3: Read in chunks and generate with LLM

The cleaned transcript can be 15KB (a short video) to 500KB. Sending it whole to the LLM risks losing the middle. Read in 4 chunks of roughly equal sentence count, then call the LLM with a deep-specific prompt that asks for:

Counts and sizes below are ceilings for a 90+ minute source. `generate_deep_doc.py` appends a SIZING block (`size_profile`) that scales them to the transcript length and tells the model to omit sections the source cannot support rather than pad (about: 5KB transcript → 12KB doc, 5 concepts, 10 quotes; 26KB → 34KB, 12 concepts, 29 quotes; 500KB → 100KB, 15 concepts, 40 quotes).

- Sumário (3 paragraphs, both axes articulated)
- 12-15 Conceitos Centrais (each with **O que é / Como se manifesta / Por que importa / Aplicação paradoxal** structure)
- 10-13 Armadilhas e Auto-sabotagem (each with **Trigger / Manifestação / Impacto / Antídoto** structure)
- 10-11 Ferramentas & Técnicas Práticas (each with **Descrição / Como aplicar / Quando usar**)
- Mudanças de Mindset (table De→Para with 25+ rows)
- Sinais de Alarme (25+ bullets)
- Aplicação Prática (3 sub-levels: Esta Semana / Prática Contínua / On Specific Topic)
- **A Linha Pessoal** (10 sub-sections reconstructing biography from dispersed fragments)
- Citações Relevantes (40+ verbatim quotes, grouped by theme)
- Timeline Emocional (8+ entries with date + event + operational response)
- Estrutura por Capítulo (Timestamps Aproximados)
- Conceitos-Âncora (wikilinks to existing notes — optional: if you have no notes vault, leave the links as plain text)
- Metadados Internos (quality score, extraction notes)

The deep prompt template is in `templates/deep_personal_development.md` (and analogues for other content types). The script `scripts/generate_deep_doc.py` calls the LLM and writes the result.

**This step runs in the background by default** — the LLM call takes 2-10 minutes and any foreground caller (the Claude Code harness cuts at 120s) will kill it mid-flight. The script detaches itself and returns immediately; you poll a status file. Do not add `&`, `nohup` or a timeout wrapper, and do not pass `--foreground` in the pipeline.

```bash
python3 "$SKILL/scripts/generate_deep_doc.py" \
  --cleaned-transcript /tmp/cleaned_transcript.txt \
  --video-meta '{"url": "...", "title": "...", "channel": "...", "date": "...", "duration": "..."}' \
  --content-type personal-development \
  --output /tmp/draft_doc.md || exit 1   # check the exit code BEFORE polling
# returns in <1s, printing the log / status / output paths
```

Then wait with the bundled poller — **never** with a bare `until grep …; do sleep; done`:

```bash
"$SKILL/scripts/wait_for_status.sh" \
  /tmp/draft_doc.md.status.json       # defaults: 90 polls x 20s
case $? in
  0) : ;;                                              # done
  1) echo "run failed";        tail -20 /tmp/draft_doc.md.log; exit 1 ;;
  2) echo "worker died";       tail -20 /tmp/draft_doc.md.log; exit 1 ;;  # SIGKILL/OOM
  3) echo "timed out, or bad max_polls/interval argument"; exit 1 ;;
  *) echo "waiter did not run (rc=$?)"; exit 1 ;;      # 127 = wrong path, etc.
esac
# The generator itself exits 3 if another run is still working on this
# --output; the `|| exit 1` above catches that before the poll ever starts.
tail -20 /tmp/draft_doc.md.log        # per-provider TRY/FAIL/SKIP lines
```

Use the **absolute** path, and keep the `*)` branch. Without them a mistyped or non-executable waiter returns 127, no `case` branch matches, `case` itself exits 0 — and the pipeline walks into step 4 fact-checking a draft that was never written. The old `grep` loop at least hung visibly; a missing default turns the same failure into a silent success.

Only the live child writes the status file, so a `grep` loop waits **for ever** if that child is SIGKILLed, OOM-killed or lost to a reboot — the status stays frozen at `running` and nothing ever writes `done`. `wait_for_status.sh` checks the recorded pid with `kill -0` and is bounded, so it always returns.

Three side files sit next to `--output`: `.status.json` (state `starting|running|done|error`, pid, byte count or error), `.log` (all stderr of the run), and the output doc itself. `--cleaned-transcript` must be a real path — process substitution (`<(echo ...)`) breaks, because the detached child outlives the fd.

`--foreground` blocks instead of detaching. Use it only for interactive debugging, never from the pipeline.

---

## Step 4: Fact-check every quote and number

The draft is high-volume and a model wrote it: trust nothing that is not checked. `scripts/fact_check.py` looks up **every** quoted passage and **every** figure of the draft in the cleaned transcript. Nothing is sampled.

```bash
python3 "$SKILL/scripts/fact_check.py" \
  --draft /tmp/draft_doc.md \
  --cleaned-transcript /tmp/cleaned_transcript.txt \
  --report /tmp/fact_check.json
```

Exit 0 = everything found. Exit 1 = findings, each printed with its draft line:
- **Quotes** (text in `"..."`, `“...”` or `«...»`, 4+ words): `exact` = verbatim in the transcript (case, punctuation and accents ignored); `near` = at least 80% of its 4-word runs are present (ASR drift, one dropped word) — passes but is listed; `MISSING` = not in the transcript. A quote split with `...` is checked fragment by fragment.
- **Numbers** (2+ digits, or `%`, `$`, a decimal, a k/M/B suffix): compared by value, so `250k` = `250,000` = `250 mil`, `1M` = `a million`, `93%` = `93 percent`, `20` = `twenty`. Anything the transcript does not contain is `UNMATCHED`. Bare single digits, list numbering, timestamps, frontmatter and the Metadados/Capítulos sections are skipped.

A report line in `/tmp/fact_check.json` has `line`, `status` and the text, so findings can be fixed without re-reading the whole draft.

**What it does NOT check** (named ceilings): proper names, tool names and commands (an ASR error like "Churnney" is copied faithfully and passes — read the extractor's auto-caption warning); who said a quote; whether a number is attached to the right thing (it only has to exist somewhere in the transcript). A quote translated into the draft's language reports `MISSING` by design: remove the quotation marks or replace it with the verbatim passage.

If any finding, proceed to Step 5. Only `scripts/test_fact_check.py` proves the checker can fail (it feeds it an invented quote and an invented number); rerun it after touching the script.

---

## Step 5: Patch gaps

For each `MISSING` quote and each `UNMATCHED` number:

1. Open the draft at the reported line and find the passage in the cleaned transcript that it was meant to reflect
2. Real quote, model altered it → replace it with the verbatim transcript text
3. Paraphrase or translation → remove the quotation marks (or label it a paraphrase); never leave invented words inside quotes
4. Number not in the transcript → correct it from the transcript, or delete the claim. Do not "fix" it by guessing
5. Re-run `fact_check.py` on the whole draft; the file is final only at exit 0, or when each remaining finding is a deliberate, understood exception

---

## Step 6: Write to KB

Do NOT hand-write or copy the model's frontmatter. Run `scripts/finalize_doc.py`: it builds the frontmatter deterministically (fixed key order and formats, valid YAML) from the video metadata, keeps only `tema_principal`/`tags`/`topics` from the model, adds the provenance fields (`pipeline`, `pipeline_run`, `pipeline_generator`, `fact_check`, `video_id`) and refuses a draft that still has a wrapper fence or no H1. Schema: `references/frontmatter-schema.md`.

```bash
python3 "$SKILL/scripts/finalize_doc.py" --draft /tmp/draft_doc.md \
  --video-meta "$META_JSON" --fact-check pass \
  --content-type ai-tech --people-dir "$OUT/people" \
  --output "$OUT/digests/[categoria]/[canal]/[date] [title].md"
```

`--fact-check` takes `pass` or `exceptions:N` (the count left after Step 5; say in the doc why each exception is a false positive, e.g. a number the transcript spells out). `--people-dir` is optional: it creates a stub channel page if `[[People/<canal>]]` (Obsidian-style wikilink) does not exist yet, so the link never dangles; omit it if you do not use wikilinks.

Then move the raw transcript to `$OUT/raw-processed/[categoria]/[canal]/` and write the document to `$OUT/digests/[categoria]/[canal]/[date] [title].md` — **categoria first, then a subfolder per canal** (e.g. `$OUT/digests/Personal-Development/Alex Hormozi/`). Check for an existing canal folder before writing (`ls "$OUT/digests/[categoria]/"`) — don't write flat into `digests/`; create the folder if needed. Before writing, check for an existing digest with the same `video_id` (`grep -rl 'video_id: "ID"' "$OUT/digests"`): one video, one digest; replace it, do not add a second.

After a batch, check the new files yourself (optional): valid YAML frontmatter, no duplicate `video_id`, no assistant chatter in the body.

---

## Pitfalls

### Pitfall 1: Naive period-3 dedup fails
The sliding-window overlap is NOT a clean period-3 repetition. Naive `s[:n//3] * 3` will produce garbled text. **Read** `references/transcript-triplication-dedup.md` before deduping. Use `scripts/dedup_transcript_v3.py` (state-machine, handles punctuation-less transcripts) — not v1.

### Pitfall 2: Ad reads inflate the doc
Long-form interviews have 2-4 sponsor reads (LinkedIn, Flightcast, Fiverr, Athletic Greens, etc.). They occupy 5-10% of the runtime but add zero knowledge. **Always exclude**. The list of known sponsors is in `references/ad-reads-exclusion.md`. For unknown channels, use the heuristic: paragraphs that contain sponsor keywords ("brought to you by", "go to [domain]", "code [WORD]", "today's episode is sponsored") AND no first-person guest content.

### Pitfall 3: LLM invents plausible-looking facts
A dense doc invites fabrication, and quotes and figures are where it shows. **Always run Step 4.** Any `MISSING` quote or `UNMATCHED` number means the model put words or figures in the speaker's mouth: treat the draft as suspect, fix each finding in Step 5, and skim the surrounding section for the same kind of slip.

### Pitfall 4: LLM quota (429) and transient failures
**The chain is the local `claude` CLI alone.** `generate_deep_doc.py` keeps its generic OpenAI-compatible HTTP code path so another link can be added later (append a dict to `PROVIDERS`; API keys can come from the environment or from a `KEY=VALUE` file named by `YTDEEP_ENV_FILE`), but no HTTP link is configured.

`generate_deep_doc.py` therefore does two things:

1. **Model fallback inside one round.** The chain is **claude-sonnet** only: `claude -p` with the machine's own Claude login (see below). With one link there is nothing to fall through to; a failure logs `FAIL provider=<name>: <reason> -> next=(end of round)`. If a link is added later, a failure on one link logs `FAIL provider=<name>: <code> -> next=<name>` and the next is tried **immediately, with no waiting**.
2. **Retry with backoff — this is the real overload/quota mitigation.** With no second link, waiting is the only remaining move. When a whole round ends in transient failures, the run sleeps and goes round again: `Retry-After` when the server sends one, otherwise exponential backoff (`LLM_RETRY_BASE_SECS`, default 5s, doubling, capped by `LLM_RETRY_MAX_SLEEP`, default 120s). Total budget `LLM_MAX_RETRY_SECS`, default **900s**.

**Retryable:** 429, 5xx, socket timeout, connection error. **Not retryable:** 401, 400 and other 4xx, and malformed responses — repeating a bad key or a bad payload only burns the budget. A link whose key is missing logs `SKIP` and is passed over, and that is not transient either: a missing key fails immediately.

Keep `LLM_MAX_RETRY_SECS` **below the poller's budget** (`wait_for_status.sh` defaults to 90 × 20s = 1800s). Otherwise a hopeless run is reported by the poller as a timeout instead of ending as `state=error` with the real reason in it.

Original incident (historical): the then-first vendor returned `429 Token Plan usage limit reached` on 2026-08-03 and the run simply died with no retry and no fallback.

`--model <link-name>` (default and only link: `claude-sonnet`) moves that link to the front; it never disables the others.

**The `claude` link (`claude-sonnet`).** It runs `claude -p --model sonnet --tools "" --no-session-persistence --output-format json`, prompt on stdin. It is the first and only link, on every host. A host where `claude` is not found logs `SKIP` and the run fails immediately. `--output-format json` is what makes it debuggable: `stop_reason` other than `end_turn` (e.g. `max_tokens`) is treated as a truncated completion, and `is_error` carries the failure text. An expired login (`Failed to authenticate`, fix with `claude auth login`) and a usage limit are **not** retried; only overload/5xx/timeout are. Env: `CLAUDE_CLI_MODEL` (alias or full model id, default `sonnet`), `CLAUDE_TIMEOUT` (seconds, default 1200), `YTDEEP_CLAUDE_BIN` (pin the binary; searched on PATH, `~/.local/bin`, `/opt/homebrew/bin`, `/usr/local/bin` otherwise). Like the HTTP links, it cannot detect a loop inside a single line (named ceiling below).

**A 200 OK is not automatically a document.** `_reject_bad_completion` checks two things before the content is accepted, and a failure is treated as a provider failure — so the next link gets a go, exactly like an HTTP error:

- `finish_reason != "stop"` → the model was cut off mid-document (`length` = hit `max_tokens`). (Observed live on the OpenAI-compatible HTTP path: `stop` normally, `length` on truncation.) **Absent or empty counts as not-clean** — treating a missing field as success would silently disarm the check.
- content shorter than 500 chars → not a document. A completion that is all `<think>` strips to the empty string, and an empty file otherwise sails through every downstream check (`bytes` matches `getsize` at 0, `state=done`).
- a long line made almost entirely of one character → repeat loop. Layout characters (spaces, `|`, `-`, padding) are excluded from the count, because an aligned markdown table is legitimately 0.83–0.97 one character and Step 3 explicitly asks for a 25-row table.
- fewer than half the document's lines distinct → the model looped a line or a paragraph.

**Named ceiling:** all of this is repetition at *line* granularity. A loop that repeats a word or phrase *within* one line of otherwise varied text is not detected, and nothing checks that the 13 sections above are actually present.

This exists because of a real artefact from 2026-08-10: a doc that stopped at 7 of the 13 required sections with a last line of 20342 chars of one Chinese ideograph — and **every** downstream check passed it (size matched the status, first line was `---`, no stray fences, `state=done`), because nothing looked at the response itself. Size and shape checks are blind to it. Judging content quality is still Step 4's job; these two only catch "the model broke".

**One run per `--output`.** A second run against a status file that is `starting`/`running` with a live pid refuses with **exit 3**. The status file is a single slot: without this, a poller waiting on run A gets run B's `done` while A rewrites the output afterwards, so the fact-checked doc and the doc on disk differ. If a run is genuinely stuck, kill its pid (the status names it) or point `--output` somewhere else.

`scripts/test_generate_deep_doc.py` locks all of this in (429 → next model with no wait, budget exhaustion, `Retry-After` obeyed over backoff, exponential backoff on 5xx, 401 never retried, missing key fails fast, claude link: fallthrough without an HTTP key, truncation rejected, expired login not retried, size scaling, and that the real chain is `claude-sonnet` alone with zero HTTP calls even if another provider's API key is in the environment). The HTTP-path tests run in a sandbox copy of the script with two stub links injected (`stub-a`, `stub-b`). The claude link is tested against a fake binary; set `YTDEEP_CLAUDE_BIN` to a missing path in any new test so nothing reaches a real `claude`. Run it after touching provider code.

### Pitfall 5: Bio threads get lost
Guest biographical fragments are dispersed throughout the transcript ("my dad", "when I was 26", "I met my wife"). The LLM may miss the thread if asked to summarise linearly. Use the dedicated section "A Linha Pessoal" in the deep prompt, with explicit guidance to reconstruct from dispersed fragments.

### Pitfall 6: Cost runaway
Generation is one LLM call per run (the transcript goes in as chunks inside a single prompt), so cost scales with transcript length and is mostly the generation itself; `fact_check.py` is free. Re-run generation only when a draft is genuinely unusable, not to fix single findings (use Step 5).

### Pitfall 7: Hallucination in emotional timeline
The "Timeline Emocional" section is the most fabrication-prone. Dates are easy to invent. Cross-check every date against the transcript. If a date is not stated explicitly, write "circa 2024" or omit rather than invent.

---

## Quick start (when invoked)

```bash
# 1. Announce
echo "Vou usar o skill nexus-youtube-deep-pipeline para processar [URL] com profundidade máxima."

# 2. Extract
RAW="$OUT/raw/[canal]/[date] [title].md"   # your extractor's output (see Step 1)
echo "Raw: $RAW"

# 3. Dedupe (v3 — handles punctuation-less transcripts; v1 under-reduces silently)
#    Write to a real file: step 4 detaches, and a <(...) fd dies with the parent shell.
python3 "$SKILL/scripts/dedup_transcript_v3.py" \
  --raw "$RAW" --output /tmp/cleaned_transcript.txt
wc -c /tmp/cleaned_transcript.txt

# 4. Generate (backgrounds itself — returns in <1s, then poll)
python3 "$SKILL/scripts/generate_deep_doc.py" \
  --cleaned-transcript /tmp/cleaned_transcript.txt \
  --video-meta "$META_JSON" \
  --content-type personal-development \
  --output /tmp/draft_doc.md || exit 1

"$SKILL/scripts/wait_for_status.sh" \
  /tmp/draft_doc.md.status.json || { tail -20 /tmp/draft_doc.md.log; exit 1; }

# 5. Fact-check
python3 "$SKILL/scripts/fact_check.py" \
  --draft /tmp/draft_doc.md \
  --cleaned-transcript /tmp/cleaned_transcript.txt \
  --report /tmp/fact_check.json

# 6. Fix every MISSING quote / UNMATCHED number it printed (exit 1), re-run until exit 0
# ... see Step 5 ...

# 7. Finalize (deterministic frontmatter + schema check), then move raw to Processed/
python3 "$SKILL/scripts/finalize_doc.py" \
  --draft /tmp/draft_doc.md --video-meta "$META_JSON" --fact-check pass \
  --people-dir "$OUT/people" \
  --output "$OUT/digests/[categoria]/[canal]/[date] [title].md" || exit 1
mv "$RAW" "$OUT/raw-processed/[categoria]/[canal]/[date] [title].md"
```

---

## Known failure: the model answers "I cannot write files" (2026-10-20)

On 40 of 48 runs of one campaign `claude -p` replied with an apology and the document inside a ```markdown block, or only with the apology, because it inherited the user's Claude setup (MCP connectors such as Claude Docs/Drive, and a Stop hook that added a second turn). Three layers now defend against it, and all three are needed:

1. `--strict-mcp-config --setting-sources project --disable-slash-commands` and a neutral cwd on the `claude -p` call: no MCP connectors, and no user hooks. The second leak was the real killer: a Stop hook installed by an agent plugin forced a follow-up turn after the document, and `result` is the LAST turn ("the document above is the deliverable", 222 chars), not the document.
2. `OUTPUT_CONTRACT` appended to every prompt: the reply IS the document, no file, no code fence.
3. `_extract_document()` strips a preamble, a whole-document fence and a closing offer; `_reject_bad_completion()` then rejects anything that does not start with frontmatter/H1 or has no `Sumário`, so the provider chain retries instead of writing a refusal to disk (a 1 KB "I can't proceed" text previously passed the size check and was marked `fact_check: pass`).

`scripts/test_finalize_doc.py` covers the extraction and the finalizer (runs on Windows too). Run it, and `test_generate_deep_doc.py` on Linux/macOS, after touching either.

## Captions blocked (HTTP 429)

yt-dlp subtitle downloads can be IP-blocked for hours after a parallel burst (all machines on one home IP share the block; `--extractor-args player_client=...` does not help). Fetch captions one video at a time with a pause. If it persists, open the watch page in a real browser, click "Show transcript" and read the `ytd-transcript-segment-renderer` rows (timestamp + text): this was used for 48 videos with the end timestamp matching the video duration. Build the raw file as `### [mm:ss]` paragraphs of ~45 s (the format described in Step 1).

## Running on Windows

The generator, `fact_check.py`, `finalize_doc.py` and the dedup run on Windows with Python 3.12. Run the commands from Git Bash.

- **Run the generator with `--foreground`.** Background mode (`start_new_session`) and `wait_for_status.sh` assume POSIX; they are not verified on Windows. Do not start two runs on the same `--output`.
- **Set `PYTHONUTF8=1`** so console and default file encodings are UTF-8 (printing `→` or accents to a cp1252 console would otherwise fail).
- **If the `claude` CLI is not found, point `YTDEEP_CLAUDE_BIN` at the `.exe`** (for example `claude.exe` under `~/.local/bin`). A `.cmd` shim on a path with accented characters can fail with "path not found"; the exe itself works.
- **`claude auth status` can say `loggedIn: true` while the real call fails** with `OAuth session expired`. Trust the generator's log line, not the status command.
- **`test_generate_deep_doc.py` does not run on Windows** (it uses `signal.SIGKILL`, bash and a `#!` fake binary). Run it on Linux or macOS after any change to provider code. `test_fact_check.py` and `test_finalize_doc.py` do run on Windows.
- **Passing `--video-meta` from PowerShell 5** mangles the JSON quotes; use Git Bash, or call the script from a small Python driver.

## Bundled resources

- `references/transcript-triplication-dedup.md` — algorithm for the sliding-window overlap artefact
- `references/deep-processing-checklist.md` — what to look for in chunks (ad reads, bios, etc.)
- `references/ad-reads-exclusion.md` — known sponsor reads by channel + heuristic
- `references/content-types.md` — content-type taxonomy + matching deep templates
- `templates/deep_personal_development.md` — deep template for personal-development
- `templates/deep_biography.md` — deep template for trader-biography / biography
- `templates/deep_business.md` — deep template for business / ai-tech
- `scripts/dedup_transcript_v3.py` — sliding-window dedup (use this; v1 kept only for reference, do not use)
- `scripts/generate_deep_doc.py` — LLM orchestrator (backgrounds by default, provider fallback chain)
- `scripts/wait_for_status.sh` — bounded, liveness-aware poller for the background run (use instead of a `grep` loop)
- `scripts/test_generate_deep_doc.py` — self-check: fallback chain, background default, wrapper-fence stripping, dead-worker poll
- `scripts/fact_check.py` — mechanical check of every quote and number against the transcript
- `scripts/test_fact_check.py` — self-check with negative controls (invented quote / number must be reported)
- `scripts/finalize_doc.py` — deterministic frontmatter + schema check; the only way a final doc is written
- `scripts/test_finalize_doc.py` — self-check for the finalizer and `_extract_document`
- `references/frontmatter-schema.md` — the exact header every digest carries

Read references as needed; templates dictate output structure per content type.
