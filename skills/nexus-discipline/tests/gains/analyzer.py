#!/usr/bin/env python3
"""
Session-History Discipline Analyzer
Computes behavioral discipline metrics from Claude Code JSONL session transcripts.

Metrics (per session, then aggregated as mean over K most-recent sessions):
  1. reasoning_density         — chars of text+thinking before first Edit/Write / n tool_use calls before first Edit/Write
  2. verify_after_edit         — fraction of Edit/Write calls followed within 5 tool_use by a verification action
  3. real_test_after_edit      — fraction of code-file Edit/Write calls followed by an actual test/build runner Bash command
  4. read_region_before_edit   — fraction of Edit tool_use preceded by a Read on the same file_path
  5. unverified_flag_usage     — count of UNVERIFIED/por rever/não verificado patterns in assistant text per session
  6. context_budget            — mean assistant output chars per turn
  7. task_success_proxy        — fraction of sessions whose last assistant message lacks unresolved error markers

Usage:
  python3 analyzer.py [--sessions-dir DIR] [--k 30] [--json OUT]
"""

import argparse
import json
import pathlib
import re
import statistics
import sys
from typing import Any, Optional

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

CODE_EXTENSIONS = {
    ".py", ".ts", ".js", ".go", ".rs", ".java", ".rb", ".mjs", ".cjs",
    ".tsx", ".jsx", ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt",
}

VERIFY_TOOL_NAMES = {"Bash", "Grep", "Read"}

REAL_TEST_PATTERN = re.compile(
    r"pytest|npm\s+(run\s+)?(test|build|lint)|jest|vitest|"
    r"go\s+test|cargo\s+(test|build)|tsc|ruff|eslint|mvn|gradle",
    re.IGNORECASE,
)

UNVERIFIED_PATTERN = re.compile(
    r"UNVERIFIED|por\s+rever|n[ãa]o[- ]verificad",
    re.IGNORECASE,
)

ERROR_MARKER_PATTERN = re.compile(
    r"\bError\b|\bFailed\b|\bTraceback\b|\bException\b|\bfailed\b|\berror\b",
    re.IGNORECASE,
)

EDIT_WRITE_TOOLS = {"Edit", "Write"}
VERIFY_TOOLS = {"Bash", "Grep", "Read"}


# ──────────────────────────────────────────────────────────────────────────────
# JSONL parsing
# ──────────────────────────────────────────────────────────────────────────────

def _content_blocks(message_obj: dict) -> list[dict]:
    """Extract content block list from a message dict (inner message.content)."""
    content = message_obj.get("content", [])
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def parse_session(path: pathlib.Path) -> Optional[dict]:
    """
    Parse one JSONL file and return a structured session dict, or None on
    total failure.  Skips malformed lines; logs a count.

    Returns:
      {
        "path": str,
        "assistant_turns": [   # ordered list of assistant API calls
          {
            "text_chars": int,      # chars of text+thinking in this turn
            "tool_uses": [          # tool_use blocks in order
              {"name": str, "input": dict}
            ]
          }
        ],
        "last_assistant_text": str,  # text of last assistant turn (for success proxy)
        "skipped_lines": int,
      }
    """
    skipped = 0
    assistant_turns: list[dict] = []
    last_assistant_text = ""

    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw_lines = fh.readlines()
    except OSError:
        return None

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue

        entry_type = obj.get("type")
        if entry_type != "assistant":
            continue

        message = obj.get("message")
        if not isinstance(message, dict):
            skipped += 1
            continue

        blocks = _content_blocks(message)
        if not blocks:
            continue

        text_chars = 0
        tool_uses: list[dict] = []
        turn_text_parts: list[str] = []

        for blk in blocks:
            btype = blk.get("type")
            if btype in ("text", "thinking"):
                chunk = blk.get("text") or blk.get("thinking") or ""
                text_chars += len(chunk)
                turn_text_parts.append(chunk)
            elif btype == "tool_use":
                tool_uses.append({
                    "name": blk.get("name", ""),
                    "input": blk.get("input") or {},
                })

        turn_text = "\n".join(turn_text_parts)
        assistant_turns.append({
            "text_chars": text_chars,
            "tool_uses": tool_uses,
            "turn_text": turn_text,
        })
        if turn_text_parts:
            last_assistant_text = turn_text

    if not assistant_turns:
        return None

    return {
        "path": str(path),
        "assistant_turns": assistant_turns,
        "last_assistant_text": last_assistant_text,
        "skipped_lines": skipped,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Per-session metric computation
# ──────────────────────────────────────────────────────────────────────────────

def _flatten_tool_uses(session: dict) -> list[dict]:
    """Return a flat ordered list of all tool_use calls across all turns."""
    out = []
    for turn in session["assistant_turns"]:
        for tu in turn["tool_uses"]:
            # annotate with turn index for context
            out.append(tu)
    return out


def compute_reasoning_density(session: dict) -> Optional[float]:
    """
    Chars of assistant text+thinking BEFORE the first Edit/Write tool_use,
    divided by number of tool_use calls BEFORE the first Edit/Write.
    None if no Edit/Write exists (session had no edits — skip contribution).
    None if 0 tool_use calls before first Edit/Write (pure-text preamble edge case → return text_chars as-is / 1).
    """
    text_so_far = 0
    tool_calls_so_far = 0

    for turn in session["assistant_turns"]:
        # Walk through this turn's content in order:
        # text_chars come before tool_uses (Claude emits text then tools)
        text_so_far += turn["text_chars"]
        for tu in turn["tool_uses"]:
            if tu["name"] in EDIT_WRITE_TOOLS:
                # found first edit — compute density
                denominator = max(tool_calls_so_far, 1)
                return text_so_far / denominator
            tool_calls_so_far += 1

    # No Edit/Write found in session
    return None


def compute_verify_after_edit(session: dict) -> Optional[float]:
    """
    Of all Edit/Write tool_use, fraction followed within next 5 tool_use
    by: any Bash/Grep/Read tool, OR Bash with test/build/lint command.
    """
    flat = _flatten_tool_uses(session)
    if not flat:
        return None

    edit_indices = [i for i, tu in enumerate(flat) if tu["name"] in EDIT_WRITE_TOOLS]
    if not edit_indices:
        return None

    verified_count = 0
    for ei in edit_indices:
        window = flat[ei + 1: ei + 6]  # next 5 tool_use
        for tu in window:
            if tu["name"] in VERIFY_TOOLS:
                verified_count += 1
                break
        # if Bash in window, also check command
        # (already counted above if name==Bash is in VERIFY_TOOLS — it is)

    return verified_count / len(edit_indices)


def _is_code_file(file_path: str) -> bool:
    return pathlib.Path(file_path).suffix.lower() in CODE_EXTENSIONS


def _is_real_test_command(bash_input: dict) -> bool:
    cmd = bash_input.get("command") or bash_input.get("cmd") or ""
    if not isinstance(cmd, str):
        cmd = str(cmd)
    return bool(REAL_TEST_PATTERN.search(cmd))


def compute_real_test_after_edit(session: dict) -> Optional[float]:
    """
    Of Edit/Write on code files, fraction followed within next 5 tool_use
    by a Bash call matching a real test/build/lint runner.
    """
    flat = _flatten_tool_uses(session)
    if not flat:
        return None

    code_edit_indices = [
        i for i, tu in enumerate(flat)
        if tu["name"] in EDIT_WRITE_TOOLS
        and _is_code_file(str(tu["input"].get("file_path") or tu["input"].get("path") or ""))
    ]
    if not code_edit_indices:
        return None

    tested_count = 0
    for ei in code_edit_indices:
        window = flat[ei + 1: ei + 6]
        for tu in window:
            if tu["name"] == "Bash" and _is_real_test_command(tu["input"]):
                tested_count += 1
                break

    return tested_count / len(code_edit_indices)


def compute_read_region_before_edit(session: dict) -> Optional[float]:
    """
    Fraction of Edit tool_use preceded ANYWHERE earlier in session by a
    Read tool_use on the same file_path.
    """
    flat = _flatten_tool_uses(session)
    edit_indices = [i for i, tu in enumerate(flat) if tu["name"] == "Edit"]
    if not edit_indices:
        return None

    preceded_count = 0
    for ei in edit_indices:
        edit_path = str(flat[ei]["input"].get("file_path") or flat[ei]["input"].get("path") or "")
        if not edit_path:
            continue
        prior = flat[:ei]
        for tu in prior:
            if tu["name"] == "Read":
                read_path = str(tu["input"].get("file_path") or tu["input"].get("path") or "")
                if read_path == edit_path:
                    preceded_count += 1
                    break

    return preceded_count / len(edit_indices)


def compute_unverified_flag_usage(session: dict) -> float:
    """Count of UNVERIFIED/por rever/não verificado matches in all assistant text."""
    count = 0
    for turn in session["assistant_turns"]:
        count += len(UNVERIFIED_PATTERN.findall(turn["turn_text"]))
    return float(count)


def compute_context_budget(session: dict) -> float:
    """Mean assistant output chars per turn."""
    chars = [turn["text_chars"] for turn in session["assistant_turns"]]
    if not chars:
        return 0.0
    return statistics.mean(chars)


def compute_task_success_proxy(session: dict) -> float:
    """
    1.0 if last assistant message lacks unresolved error markers, else 0.0.
    Heuristic: checks last non-empty assistant turn text for ERROR_MARKER_PATTERN.
    Note: this is a pessimistic proxy — error markers in explanatory text will
    lower the score even when the task succeeded. Documented limitation.
    """
    text = session["last_assistant_text"]
    if not text:
        return 1.0  # no text = no error
    # If we find error-like words, check if they appear to be unresolved
    # (not in a past-tense "fixed the error" context — rough heuristic)
    lines = text.strip().split("\n")
    last_lines = "\n".join(lines[-10:])  # focus on closing lines
    if ERROR_MARKER_PATTERN.search(last_lines):
        return 0.0
    return 1.0


def compute_session_metrics(session: dict) -> dict:
    return {
        "reasoning_density": compute_reasoning_density(session),
        "verify_after_edit": compute_verify_after_edit(session),
        "real_test_after_edit": compute_real_test_after_edit(session),
        "read_region_before_edit": compute_read_region_before_edit(session),
        "unverified_flag_usage": compute_unverified_flag_usage(session),
        "context_budget": compute_context_budget(session),
        "task_success_proxy": compute_task_success_proxy(session),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Aggregation
# ──────────────────────────────────────────────────────────────────────────────

def aggregate_metrics(per_session: list[dict]) -> dict:
    """
    Compute mean over all sessions, skipping None values per metric
    (None means the metric was not applicable to that session).
    """
    keys = [
        "reasoning_density", "verify_after_edit", "real_test_after_edit",
        "read_region_before_edit", "unverified_flag_usage", "context_budget",
        "task_success_proxy",
    ]
    result = {}
    for k in keys:
        vals = [s[k] for s in per_session if s.get(k) is not None]
        result[k] = statistics.mean(vals) if vals else None
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Display
# ──────────────────────────────────────────────────────────────────────────────

def print_table(metrics: dict, sessions_analyzed: int, sessions_skipped: int, k: int) -> None:
    METRIC_LABELS = {
        "reasoning_density":       ("Reasoning Density",         "chars-of-text÷tool-calls before first edit"),
        "verify_after_edit":       ("Verify After Edit",         "fraction of Edit/Write followed by Bash/Grep/Read in next 5"),
        "real_test_after_edit":    ("Real Test After Edit",      "fraction of code edits followed by real test/build runner"),
        "read_region_before_edit": ("Read Before Edit",          "fraction of Edit preceded by Read on same file"),
        "unverified_flag_usage":   ("Unverified Flags (mean)",   "mean count of UNVERIFIED/por-rever per session"),
        "context_budget":          ("Context Budget (mean)",     "mean assistant output chars per turn"),
        "task_success_proxy":      ("Task Success Proxy",        "fraction of sessions ending without error markers"),
    }

    print()
    print("=" * 72)
    print(f"  DISCIPLINE BASELINE  —  K={k}  sessions={sessions_analyzed}")
    print("=" * 72)
    print(f"  Sessions skipped (parse error / empty): {sessions_skipped}")
    print()
    print(f"  {'Metric':<28} {'Value':>10}  Description")
    print(f"  {'-'*28} {'-'*10}  {'-'*30}")

    for key, (label, desc) in METRIC_LABELS.items():
        val = metrics.get(key)
        if val is None:
            val_str = "     N/A"
        elif key in ("reasoning_density", "unverified_flag_usage", "context_budget"):
            val_str = f"{val:>10.1f}"
        else:
            val_str = f"{val:>9.1%} "
        print(f"  {label:<28} {val_str}  {desc}")

    print()
    print("  Notes:")
    print("  - reasoning_density: higher = more text-reasoning per tool call before acting")
    print("  - verify_after_edit: target > 70%")
    print("  - real_test_after_edit: target > 50% (many edits are config/docs, not code)")
    print("  - read_region_before_edit: target > 80% (read before edit)")
    print("  - unverified_flag_usage: lower is better (0 = no hedged claims left open)")
    print("  - task_success_proxy: heuristic — error words in closing lines = 0; document limitation")
    print("=" * 72)
    print()


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discipline analyzer for Claude Code session transcripts."
    )
    parser.add_argument(
        "--sessions-dir",
        default=str(pathlib.Path.home() / ".claude" / "projects"),
        help="Root directory containing project subdirs with *.jsonl files (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=30,
        help="Number of most-recent sessions to analyze (default: 30)",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        default=None,
        help="If set, write the baseline JSON to this path",
    )
    args = parser.parse_args()

    sessions_dir = pathlib.Path(args.sessions_dir).expanduser()
    if not sessions_dir.exists():
        print(f"ERROR: sessions-dir not found: {sessions_dir}", file=sys.stderr)
        sys.exit(1)

    # Gather all JSONL files, sort by mtime descending, take K
    all_files = list(sessions_dir.glob("*/*.jsonl"))
    if not all_files:
        print(f"ERROR: no *.jsonl files found under {sessions_dir}", file=sys.stderr)
        sys.exit(1)

    all_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    selected = all_files[: args.k]

    print(f"Found {len(all_files)} JSONL files; analyzing most-recent {len(selected)}...", file=sys.stderr)

    sessions_skipped = 0
    per_session_metrics: list[dict] = []
    sessions_analyzed = 0

    for f in selected:
        session = parse_session(f)
        if session is None:
            sessions_skipped += 1
            continue
        metrics = compute_session_metrics(session)
        per_session_metrics.append(metrics)
        sessions_analyzed += 1

    if not per_session_metrics:
        print("ERROR: zero sessions successfully parsed — cannot produce baseline.", file=sys.stderr)
        sys.exit(1)

    aggregated = aggregate_metrics(per_session_metrics)

    # Approximation notes
    notes = (
        "reasoning_density: text chars BEFORE first Edit/Write divided by tool_use calls before first Edit/Write; "
        "thinking blocks counted if non-empty (many are empty/redacted). "
        "task_success_proxy: heuristic — error-word regex on last 10 lines; false positives likely when agent "
        "discusses past errors or references error types by name. "
        "real_test_after_edit: only counts explicit test runner commands, not manual curl/echo checks."
    )

    baseline = {
        "k_sessions": args.k,
        "sessions_analyzed": sessions_analyzed,
        "sessions_skipped": sessions_skipped,
        "metrics": aggregated,
        "notes": notes,
    }

    print_table(aggregated, sessions_analyzed, sessions_skipped, args.k)

    if args.json_out:
        out_path = pathlib.Path(args.json_out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(baseline, fh, indent=2)
        print(f"Baseline written to: {out_path}", file=sys.stderr)

    # Always print JSON to stdout as well (useful for piping)
    # (only if --json not given; otherwise would duplicate)
    if not args.json_out:
        print(json.dumps(baseline, indent=2))


if __name__ == "__main__":
    main()
