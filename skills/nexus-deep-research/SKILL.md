---
name: nexus-deep-research
description: Use when the user needs multi-source research with citation tracking, evidence persistence, adversarial claim verification, and structured report generation. Triggers on "deep research", "comprehensive analysis", "research report", "compare X vs Y", "analyze trends", or "state of the art". Not for simple lookups, debugging, or questions answerable with 1-2 searches.
---

# Nexus Deep Research

## Core Purpose

Deliver citation-tracked research reports through a structured pipeline with evidence persistence, source identity management, perspective-guided coverage, adversarial claim-level verification, and progressive context management.

**Verification principle:** the writer never verifies their own claims. Mechanical checks are scripts; semantic checks are fresh-context verifiers that vote; the delivery gate reads their files. "Could not check" is reported as unverified, never as supported.

**Autonomy Principle:** Operate independently. Infer assumptions from context. Only stop for critical errors or incomprehensible queries. Surface high-materiality assumptions explicitly in the Introduction and Methodology rather than silently defaulting.

---

## Decision Tree

```
Request Analysis
+-- Simple lookup? --> STOP: Use WebSearch
+-- Debugging? --> STOP: Use standard tools
+-- Complex analysis needed? --> CONTINUE

Mode Selection
+-- Initial exploration --> quick (3 phases, 2-5 min)
+-- Standard research --> standard (6 phases, 5-10 min) [DEFAULT]
+-- Critical decision --> deep (8 phases, 10-20 min)
+-- Comprehensive review --> ultradeep (8+ phases, 20-45 min)
```

**Default assumptions:** Technical query = technical audience. Comparison = balanced perspective. Trend = recent 1-2 years.

---

## Workflow Overview

| Phase | Name | Quick | Std | Deep | Ultra |
|-------|------|-------|-----|------|-------|
| 1 | SCOPE | Y | Y | Y | Y |
| 2 | PLAN | - | Y | Y | Y |
| 3 | RETRIEVE | Y | Y | Y | Y |
| 4 | TRIANGULATE | - | Y | Y | Y |
| 4.5 | OUTLINE REFINEMENT | - | Y | Y | Y |
| 5 | SYNTHESIZE | - | Y | Y | Y |
| 6 | CRITIQUE | - | - | Y | Y |
| 7 | REFINE | - | - | Y | Y |
| 8 | PACKAGE | Y | Y | Y | Y |

**Note:** Phases 3-5 operate as an evidence loop per section (retrieve → evidence store → refine outline → draft → verify claims → delta-retrieve if needed), not as strict sequential gates.

---

## Execution

**On invocation, load relevant reference files:**

1. **Phase 1-7:** Load [methodology.md](./reference/methodology.md) for detailed phase instructions
2. **Phase 2-3 (Std+):** Load [retrieval-and-stopping.md](./reference/retrieval-and-stopping.md) — query types, STORM perspectives, facets and coverage, search ladder, stop rules
3. **Phase 4-7 (Std+):** Load [adversarial-verification.md](./reference/adversarial-verification.md) — 6 verification layers, verifier brief, failure patterns, red team, delivery gate
4. **Phase 8 (Report):** Load [report-assembly.md](./reference/report-assembly.md) for progressive generation
5. **HTML/PDF output:** Load [html-generation.md](./reference/html-generation.md)
6. **Quality checks:** Load [quality-gates.md](./reference/quality-gates.md)
7. **Long reports (>18K words):** Load [continuation.md](./reference/continuation.md)

**Templates:**
- Report structure: [report_template.md](./templates/report_template.md)
- HTML styling: [mckinsey_report_template.html](./templates/mckinsey_report_template.html)

**Scripts** (all in `scripts/` of this skill's directory — run as `python <skill_dir>/scripts/<name>.py`, e.g. `~/.claude/skills/nexus-deep-research/scripts/…` in Claude Code; `[run]` is the output folder in the working directory):

| Stage | Script |
|---|---|
| Sources / evidence | `citation_manager.py`, `evidence_store.py`, `source_evaluator.py evaluate --url U --title T [--date YYYY-MM-DD]` (credibility prior 0-100, JSON) |
| Office/PDF inputs | `extract_office_text.py SRC --out [run]/source_material` |
| Coverage / stop | `verify_coverage.py --dir [run] --require-stop`, `retrieval_health.py --dir [run]` |
| Claims (lexical red-flags) | `extract_claims.py extract --dir [run] --report [md]` (links `[N]`, `[N, M]`, `[N-M]`, `[^N]` markers to the N-th distinct source in `sources.jsonl`, the bibliography numbering; skips Bibliography, Methodology and Appendix sections), `verify_claim_support.py verify --dir [run] --strict` |
| Quotes vs saved text | `verify_quotes.py snapshot` / `verify --dir [run] --strict` |
| DOI / arXiv / PMID, retractions | `registry_check.py check --dir [run] --strict` |
| Verifier votes + gate | `claim_ledger.py pending` / `vote` / `resolve` / `gate` / `table --dir [run]` |
| Report | `validate_report.py --report [path]`, `verify_citations.py --report [path]`, `md_to_html.py [md]` (HTML preview), `verify_pdf_text.py --pdf [pdf]` |

All gates in [adversarial-verification.md, Layer 6](./reference/adversarial-verification.md#layer-6--delivery-gate) must exit 0 before PACKAGE, or the report is delivered as a qualified partial with the failing gate named.

---

## Output Contract

**Required sections:**
- Executive Summary (200-400 words)
- Introduction (scope, methodology, assumptions)
- Main Analysis (4-8 findings, 600-2,000 words each, cited)
- Synthesis & Insights (patterns, implications)
- Limitations & Caveats
- Recommendations
- Bibliography (COMPLETE - every citation, no placeholders), headed exactly `## Bibliography` (no number, no "References": `validate_report.py`, `verify_citations.py` and `md_to_html.py` find it by that heading)
- Methodology Appendix

**Output files (all to `./[topic]_[YYYYMMDD]/` — a subdirectory of the working directory where the skill was invoked):**
- Markdown (primary source of truth)
- `sources.jsonl` — stable source registry with canonical IDs
- `evidence.jsonl` — append-only evidence store with quotes and locators
- `claims.jsonl` — atomic claims with deterministic support status
- `votes.jsonl` / `claim_ledger.jsonl` — verifier votes and resolved claim statuses
- `coverage.json`, `queries.jsonl`, `retrievals.jsonl` — facets, query provenance, fetch attempts, retrieval stop
- `snapshots/` — raw text of quoted sources (for quote verification)
- `run_manifest.json` — query, mode, assumptions, provider config
- HTML (McKinsey style, auto-opened)
- PDF (professional print, auto-opened)

**Quality standards:**
- 10+ sources, 3+ per major claim (cluster-independent, not just count)
- All factual claims cited immediately [N] with evidence backing in `evidence.jsonl`
- Claim-support verification mandatory: no unsupported or refuted factual claims pass delivery; contested claims show both readings
- A refuted claim is removed or rewritten **without restating it**: the ledger gate fails on its text (exact, or ≥ 80% of its 3-word shingles in one report sentence or a window of consecutive report sentences) even when negated or framed ("it is not true that …") — write what the source supports instead
- Supported claims should rest on ≥ 2 independent source families (circular sourcing flagged): a warning in Standard (state single-family claims in Limitations), a gate failure with `--strict-independence` in Deep/UltraDeep
- Every high-priority facet has a recorded counter-evidence search
- Retracted papers are cited only as retracted
- No placeholders, no fabricated citations
- Prose-first (>=80%), bullets sparingly

---

## When to Use / NOT Use

**Use:** Comprehensive analysis, technology comparisons, state-of-the-art reviews, multi-perspective investigation, market analysis.

**Do NOT use:** Simple lookups, debugging, 1-2 search answers, quick time-sensitive queries.

---

## Provenance

Fork of [199-biotechnologies/claude-deep-research-skill](https://github.com/199-biotechnologies/claude-deep-research-skill) (MIT). Adopted with attribution: negation engine from the FFV47 fork; coverage-led retrieval, stop rules and retrieval health from the alepar fork; Office/PDF extraction, search ladder, red team and claim corrections from necopinus/hermes-skill-deep-research. Design references: Anthropic multi-agent research system, Claude Code `/deep-research`, `math-olympiad`, `clinical-trial-forecast`, STORM (Shao et al., 2024). Details in each script's docstring.
