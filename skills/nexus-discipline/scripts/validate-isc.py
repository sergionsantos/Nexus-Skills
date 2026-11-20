#!/usr/bin/env python3
"""
nexus-discipline — ISC Validator
Parses ISA files and reports pass/total for ISC checkboxes.

PRIMARY dialect (contract-frozen; see templates/ISA.md):
    - [ ]   unchecked item  → OPEN
    - [x]   checked item    → DONE
    Format: ### ISC-[CATEGORIA]-[N]: description
            - [ ] criterion text
            - [x] criterion text (with optional evidence)

SECONDARY dialect (MoSCoW — legacy dialect; also-supported, not primary):
    ### C{N} — {Name}
    **Prioridade:** Must|Should|Could
    **Pass:** ... / **Fail:** ...
    This dialect is parsed when no checkbox ISCs are found, or when --dialect moscow
    is passed explicitly. It does NOT override the checkbox dialect.

Decision note (audit gap #3):
    The contract frozen by isa-convention.contract.md mandates the checkbox dialect
    (- [ ] / - [x]) because that is what the unattended gate hooks read.  The MoSCoW
    dialect is an also-supported legacy path for backwards compatibility with older
    ISA files written against the legacy dialect.  New ISAs created by isa-create.py
    always use the checkbox dialect.  If both dialects are present in the same file,
    the checkbox dialect wins (--dialect checkbox is the default).

Exit codes:
    0  all checked (DONE) out of total found — or no criteria found (warn)
    1  one or more criteria still OPEN, or parse error

Word-boundary slug safety note (nexus-discipline):
    This script uses re.findall with anchored patterns rather than bare string
    find-and-replace, so there is no risk of the \\bword\\b false-positive class
    (e.g. 'edge' inside 'Ledger').  Patterns are regex-anchored to line structure.
"""

import argparse
import re
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class CheckboxCriterion:
    """A single ISC checkbox item (contract-frozen dialect)."""

    def __init__(self, section_id: str, section_name: str, text: str, done: bool):
        self.section_id = section_id    # e.g. "ISC-FUNC-01"
        self.section_name = section_name  # e.g. "Funcionalidade principal"
        self.text = text                # criterion text
        self.done = done                # True = [x], False = [ ]

    @property
    def status(self) -> str:
        return "DONE" if self.done else "OPEN"

    def to_dict(self) -> Dict:
        return {
            "section": self.section_id,
            "section_name": self.section_name,
            "text": self.text,
            "status": self.status,
        }


class MoscowCriterion:
    """A single ISC criterion in the legacy MoSCoW dialect."""

    def __init__(self, cid: str, name: str, description: str,
                 test: str, pass_cond: str, fail_cond: str, priority: str):
        self.cid = cid
        self.name = name
        self.description = description
        self.test = test
        self.pass_cond = pass_cond
        self.fail_cond = fail_cond
        self.priority = priority  # Must | Should | Could
        self.status: Optional[str] = None  # PASS | FAIL | SKIP

    def to_dict(self) -> Dict:
        return {
            "id": self.cid,
            "name": self.name,
            "priority": self.priority,
            "status": self.status,
            "test": self.test,
            "pass_condition": self.pass_cond,
            "fail_condition": self.fail_cond,
        }


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

# ISC section header: ### ISC-CATEGORIA-N: description
# Anchored to start of line; section ID is word-boundary safe because the
# pattern requires the literal prefix 'ISC-' followed by word chars only.
_ISC_HEADER_RE = re.compile(
    r'^#{2,4}\s+(ISC-[A-Z0-9]+-\d+):\s*(.*)$',
    re.MULTILINE
)

# Any markdown heading (##, ###, ####) — used to bound ISC section bodies so
# that checkboxes in non-ISC sections (Features, Verification, etc.) are never
# attributed to the last ISC header.
_ANY_HEADING_RE = re.compile(r'^#{2,}\s+', re.MULTILINE)

# Checkbox item lines: "- [ ] text" or "- [x] text" (case-insensitive x)
# Anchored to line start; will not match mid-line occurrences.
_CHECKBOX_RE = re.compile(
    r'^\s*-\s+\[([ xX])\]\s+(.+)$',
    re.MULTILINE
)

# MoSCoW block pattern (legacy dialect)
_MOSCOW_BLOCK_RE = re.compile(
    r'^#{2,4}\s+(C\d+)\s+[—-]\s+(.+?)\n'
    r'.*?\*\*Descri[çc][ãa]o:\*\*\s*(.+?)\n'
    r'.*?\*\*Teste:\*\*\s*(.+?)\n'
    r'.*?\*\*Pass:\*\*\s*(.+?)\n'
    r'.*?\*\*Fail:\*\*\s*(.+?)\n'
    r'.*?\*\*Prioridade:\*\*\s*(Must|Should|Could)',
    re.MULTILINE | re.DOTALL
)


def parse_checkbox_criteria(content: str) -> List[CheckboxCriterion]:
    """Parse contract-frozen checkbox dialect from ISA content.

    Strategy: find each ISC-* section header, then collect all - [ ]/- [x]
    items that follow it, bounded by the NEXT markdown heading of any kind
    (##, ###, ####).  This prevents checkboxes in non-ISC sections (Features,
    Verification, Out-of-Scope, etc.) from being attributed to the last ISC
    header — which would inflate the open count with skeleton placeholders.
    """
    criteria: List[CheckboxCriterion] = []

    # Find all ISC section header positions
    headers = list(_ISC_HEADER_RE.finditer(content))
    if not headers:
        return criteria

    # Build sorted list of ALL heading start positions so we can find the
    # next heading (ISC or non-ISC) after each ISC header.
    all_heading_starts = sorted(m.start() for m in _ANY_HEADING_RE.finditer(content))

    def next_heading_after(pos: int) -> int:
        """Return the start of the first heading whose start > pos, or len(content)."""
        for h in all_heading_starts:
            if h > pos:
                return h
        return len(content)

    for header_match in headers:
        section_id = header_match.group(1).strip()
        section_name = header_match.group(2).strip()
        # Body ends at the next heading after this header's end (not its start,
        # because the header line itself is a heading we already matched).
        body_start = header_match.end()
        body_end = next_heading_after(header_match.end())
        body = content[body_start:body_end]

        for cb_match in _CHECKBOX_RE.finditer(body):
            marker = cb_match.group(1)  # ' ' or 'x'/'X'
            text = cb_match.group(2).strip()
            done = marker.lower() == 'x'
            criteria.append(CheckboxCriterion(
                section_id=section_id,
                section_name=section_name,
                text=text,
                done=done,
            ))

    return criteria


def parse_moscow_criteria(content: str) -> List[MoscowCriterion]:
    """Parse legacy MoSCoW dialect from ISA content."""
    criteria: List[MoscowCriterion] = []
    for m in _MOSCOW_BLOCK_RE.finditer(content):
        cid, name, desc, test, pass_cond, fail_cond, priority = (
            g.strip() for g in m.groups()
        )
        criteria.append(MoscowCriterion(
            cid=cid, name=name, description=desc,
            test=test, pass_cond=pass_cond, fail_cond=fail_cond,
            priority=priority,
        ))
    return criteria


def extract_title(content: str) -> str:
    """Extract ISA title from frontmatter or first H1."""
    # YAML frontmatter title:
    m = re.search(r'^title:\s*["\']?ISA:\s*(.+?)["\']?\s*$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # First H1: "# ISA: ..." or "# ISA — ..."
    m = re.search(r'^#\s+ISA[:\s—-]+(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "Unknown"


def extract_phase(content: str) -> Optional[str]:
    """Extract current phase from YAML frontmatter."""
    m = re.search(r'^phase:\s*(\S+)', content, re.MULTILINE)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------

VALID_PHASES = [
    "observe", "think", "plan", "build", "execute", "verify", "learn", "complete"
]


def report_checkbox(criteria: List[CheckboxCriterion], verbose: bool, quiet: bool,
                    title: str = "Unknown") -> Dict:
    """Build result dict and print report for checkbox dialect."""
    total = len(criteria)
    done_count = sum(1 for c in criteria if c.done)
    open_count = total - done_count
    overall = "PASS" if open_count == 0 and total > 0 else "FAIL"

    result = {
        "dialect": "checkbox",
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "overall": overall,
        "summary": {
            "total": total,
            "done": done_count,
            "open": open_count,
            "ratio": f"{done_count}/{total}",
        },
        "criteria": [c.to_dict() for c in criteria],
    }

    if not quiet:
        sep = "=" * 70
        print(f"\n{sep}")
        print(f"ISC Validation Report (checkbox dialect): {title}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"{sep}")
        status_icon = "PASS" if overall == "PASS" else "FAIL"
        print(f"\nOVERALL: {status_icon}")
        print(f"\nSummary:")
        print(f"  Total criteria : {total}")
        print(f"  Done [x]       : {done_count}")
        print(f"  Open [ ]       : {open_count}")
        print(f"  Ratio          : {done_count}/{total}")

        if verbose or overall == "FAIL":
            print(f"\nDetails:")
            current_section = None
            for c in criteria:
                if c.section_id != current_section:
                    current_section = c.section_id
                    print(f"\n  [{c.section_id}] {c.section_name}")
                icon = "[x]" if c.done else "[ ]"
                print(f"    {icon} {c.text}")
        print(f"\n{sep}")

    return result


def report_moscow(criteria: List[MoscowCriterion], verbose: bool, quiet: bool,
                  title: str = "Unknown") -> Dict:
    """Build result dict and print report for MoSCoW dialect (legacy)."""
    # MoSCoW validation is read-only in this script: status is inferred from
    # interactive input only when --auto is not set. For non-interactive use
    # (unattended gates), all criteria are reported as PENDING.
    for c in criteria:
        if c.status is None:
            c.status = "PENDING"

    must_criteria = [c for c in criteria if c.priority == "Must"]
    must_pass = sum(1 for c in must_criteria if c.status == "PASS")
    must_total = len(must_criteria)
    all_must_pass = must_total > 0 and must_pass == must_total
    overall = "PASS" if all_must_pass else "FAIL"

    total = len(criteria)
    passed = sum(1 for c in criteria if c.status == "PASS")

    result = {
        "dialect": "moscow",
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "overall": overall,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": sum(1 for c in criteria if c.status == "FAIL"),
            "pending": sum(1 for c in criteria if c.status == "PENDING"),
            "must_pass": f"{must_pass}/{must_total}",
        },
        "criteria": [c.to_dict() for c in criteria],
    }

    if not quiet:
        sep = "=" * 70
        print(f"\n{sep}")
        print(f"ISC Validation Report (MoSCoW dialect — legacy): {title}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"{sep}")
        print(f"\nOVERALL: {overall}")
        s = result["summary"]
        print(f"\nSummary:")
        print(f"  Total   : {s['total']}")
        print(f"  Passed  : {s['passed']}")
        print(f"  Failed  : {s['failed']}")
        print(f"  Pending : {s['pending']}")
        print(f"  Must    : {s['must_pass']}")
        if verbose:
            print(f"\nDetails:")
            for c in criteria:
                icon = {"PASS": "[P]", "FAIL": "[F]", "PENDING": "[?]"}.get(c.status, "[?]")
                print(f"  {icon} {c.cid} — {c.name} ({c.priority})")
        print(f"\n{sep}")
        print("NOTE: MoSCoW dialect is legacy. New ISAs should use the checkbox dialect.")

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="nexus-discipline — Validate ISC criteria in an ISA file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dialects:
  checkbox (default, contract-frozen):
    Parses  ### ISC-CAT-N: description / - [ ] text / - [x] text
    Reports done/total and exits 0 if all checked, 1 otherwise.

  moscow (legacy, also-supported):
    Parses  ### C{N} — Name / **Prioridade:** Must|Should|Could blocks
    Used for older (legacy-dialect) ISA files.
    New ISAs from isa-create.py always use the checkbox dialect.

Exit codes:
  0  all criteria DONE (checkbox) or all Must PASS (moscow)
  1  one or more criteria OPEN/FAIL, or no criteria found
""",
    )
    parser.add_argument("isa_file", help="Path to the ISA .md file")
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show details for all criteria (always shown on FAIL)"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Only print PASS or FAIL (machine-readable)"
    )
    parser.add_argument(
        "--dialect", "-d", choices=["checkbox", "moscow", "auto"],
        default="auto",
        help=(
            "ISC dialect to parse. 'auto' tries checkbox first, falls back to moscow. "
            "Default: auto"
        ),
    )
    parser.add_argument(
        "--json", "-j", metavar="FILE",
        help="Export result to JSON file"
    )
    args = parser.parse_args()

    isa_path = Path(args.isa_file)
    if not isa_path.exists():
        print(f"ERROR: File not found: {isa_path}", file=sys.stderr)
        sys.exit(1)

    content = isa_path.read_text(encoding="utf-8")
    title = extract_title(content)
    phase = extract_phase(content)

    if not args.quiet:
        print(f"ISC Validator (nexus-discipline) — {title}")
        if phase:
            phase_warn = (
                " [WARNING: phase not yet 'verify' — criteria may be incomplete]"
                if phase not in ("verify", "learn", "complete")
                else ""
            )
            print(f"Phase: {phase}{phase_warn}")
        else:
            print("WARNING: No 'phase:' field found in frontmatter. "
                  "Unattended gates will not audit this ISA (fail-open). "
                  "Add 'phase: observe' to frontmatter.")

    # --- Dialect selection ---
    result: Optional[Dict] = None
    dialect_used = args.dialect

    if args.dialect in ("checkbox", "auto"):
        checkbox_criteria = parse_checkbox_criteria(content)
        if checkbox_criteria:
            dialect_used = "checkbox"
            result = report_checkbox(checkbox_criteria, args.verbose, args.quiet, title=title)
        elif args.dialect == "checkbox":
            print("ERROR: No checkbox ISC criteria found (### ISC-*: / - [ ] pattern). "
                  "Check the file or use --dialect moscow.", file=sys.stderr)
            sys.exit(1)

    if result is None and args.dialect in ("moscow", "auto"):
        moscow_criteria = parse_moscow_criteria(content)
        if moscow_criteria:
            dialect_used = "moscow"
            result = report_moscow(moscow_criteria, args.verbose, args.quiet, title=title)
        else:
            if not args.quiet:
                print(
                    "WARNING: No ISC criteria found in either dialect.\n"
                    "  Checkbox:  ### ISC-CAT-N: / - [ ] / - [x]\n"
                    "  MoSCoW:    ### C{N} — Name / **Prioridade:** Must|Should|Could",
                    file=sys.stderr,
                )
            sys.exit(1)

    # --- Summary line for quiet mode ---
    if args.quiet:
        print(result["overall"])

    # --- JSON export ---
    if args.json:
        out_path = Path(args.json)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet:
            print(f"\nExported to: {out_path}")

    # --- Exit code ---
    sys.exit(0 if result["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
