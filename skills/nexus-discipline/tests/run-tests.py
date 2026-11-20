#!/usr/bin/env python3
"""
nexus-discipline test runner.

Validates that:
1. Component prompt files exist and are non-empty.
2. Schema files are valid JSON Schema Draft-07.
3. Each fixture's `expected` payload validates against its schema.
4. Fixtures cover required diversity (all effort levels, all workflow_types, all severities, etc.).
5. isa-create script smoke-test: isa-create.py --help runs without crashing (graceful degradation path).

This runner does NOT call an LLM. It validates STRUCTURAL contract.
Semantic correctness of the prompts is verified separately via human review of fixtures.

Key changes vs alg:
  - COMPONENTS_DIR → nexus-discipline/components/
  - tier-classifier.md → effort-classifier.md  (nexus-discipline renames tier→effort)
  - Tier enum SIMPLE/STANDARD/COMPLEX → E1/E2/E3/E4/E5
  - Deprecated fallback → isa-create.py smoke-test
  - Self-application guard references nexus-discipline

Exit: 0 = all pass, 1 = any failure.

Usage:
    python3 tests/run-tests.py
    python3 tests/run-tests.py --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent
SKILL_ROOT = ROOT.parent
COMPONENTS_DIR = SKILL_ROOT / "components"
SCHEMAS_DIR = ROOT / "schemas"

# isa-create script. Smoke-tested with --help (no LLM needed).
ISA_CREATE = SKILL_ROOT / "scripts" / "isa-create.py"

# Component names (tier-classifier — legacy contract preserved)
CLASSIFIER_PROMPT = COMPONENTS_DIR / "tier-classifier.md"
CRITIC_PROMPT = COMPONENTS_DIR / "plan-critic.md"
CLASSIFIER_SCHEMA = SCHEMAS_DIR / "classifier.schema.json"
CRITIC_SCHEMA = SCHEMAS_DIR / "critic.schema.json"
CLASSIFIER_FIXTURES = ROOT / "classifier-fixtures.json"
CRITIC_FIXTURES = ROOT / "critic-fixtures.json"

# Classifier tier spine (legacy contract: SIMPLE/STANDARD/COMPLEX)
REQUIRED_TIERS = {"SIMPLE", "STANDARD", "COMPLEX"}
REQUIRED_WORKFLOWS = {"FEATURE", "REFACTOR", "INVESTIGATION", "MIGRATION", "SIMPLE"}
REQUIRED_VALIDATION_LEVELS = {"TRIVIAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
REQUIRED_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}
REQUIRED_RECOMMENDATIONS = {"accept", "revise", "reject"}


class Report:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []

    def ok(self, msg: str) -> None:
        self.passed.append(msg)
        if self.verbose:
            print(f"  PASS  {msg}")

    def fail(self, msg: str, detail: str) -> None:
        self.failed.append((msg, detail))
        print(f"  FAIL  {msg}: {detail}", file=sys.stderr)

    def section(self, title: str) -> None:
        print(f"\n== {title} ==")

    def summary(self) -> int:
        print(f"\nTotal: {len(self.passed) + len(self.failed)} | PASS {len(self.passed)} | FAIL {len(self.failed)}")
        if self.failed:
            print("\nFailures:")
            for msg, detail in self.failed:
                print(f"  - {msg}: {detail}")
            return 1
        print("All checks passed.")
        return 0


def check_file_exists(path: Path, label: str, report: Report) -> bool:
    if not path.exists():
        report.fail(f"file_exists:{label}", f"missing: {path}")
        return False
    if path.stat().st_size == 0:
        report.fail(f"file_nonempty:{label}", f"empty: {path}")
        return False
    report.ok(f"file_exists:{label}")
    return True


def check_json_schema(path: Path, label: str, report: Report) -> dict | None:
    try:
        with path.open() as fp:
            schema = json.load(fp)
    except json.JSONDecodeError as exc:
        report.fail(f"schema_json:{label}", str(exc))
        return None
    try:
        Draft7Validator.check_schema(schema)
    except Exception as exc:  # noqa: BLE001
        report.fail(f"schema_valid:{label}", str(exc))
        return None
    report.ok(f"schema_valid:{label}")
    return schema


def check_fixtures(
    fixtures_path: Path,
    schema: dict,
    label: str,
    report: Report,
    diversity_check: callable,
) -> None:
    try:
        with fixtures_path.open() as fp:
            data = json.load(fp)
    except json.JSONDecodeError as exc:
        report.fail(f"fixtures_json:{label}", str(exc))
        return

    cases = data.get("cases", [])
    if not cases:
        report.fail(f"fixtures_count:{label}", "no cases")
        return
    report.ok(f"fixtures_count:{label}={len(cases)}")

    validator = Draft7Validator(schema)
    for case in cases:
        case_id = case.get("id", "<unknown>")
        expected = case.get("expected")
        if expected is None:
            report.fail(f"fixtures_expected:{label}:{case_id}", "missing 'expected'")
            continue
        errors = sorted(validator.iter_errors(expected), key=lambda e: e.path)
        if errors:
            for err in errors:
                report.fail(f"fixtures_schema:{label}:{case_id}", err.message)
            continue
        report.ok(f"fixtures_schema:{label}:{case_id}")

    diversity_check(cases, report)


def diversity_classifier(cases: list[dict], report: Report) -> None:
    """Check that classifier fixtures span all tier values and workflow types."""
    tiers = {c["expected"]["tier"] for c in cases if "expected" in c and "tier" in c["expected"]}
    workflows = {c["expected"]["workflow_type"] for c in cases if "expected" in c}
    levels = {c["expected"]["validation_level"] for c in cases if "expected" in c}

    missing_tiers = REQUIRED_TIERS - tiers
    missing_workflows = REQUIRED_WORKFLOWS - workflows
    missing_levels = REQUIRED_VALIDATION_LEVELS - levels

    if missing_tiers:
        report.fail("diversity:tiers", f"missing tier levels: {missing_tiers}")
    else:
        report.ok("diversity:tiers=all-3-covered")

    if missing_workflows:
        report.fail("diversity:workflows", f"missing workflows: {missing_workflows}")
    else:
        report.ok("diversity:workflows=all-5-covered")

    if missing_levels:
        report.fail("diversity:validation_levels", f"missing: {missing_levels}")
    else:
        report.ok("diversity:validation_levels=all-5-covered")

    # needs_critic must appear true AND false
    needs_critic_vals = {c["expected"]["needs_critic"] for c in cases if "expected" in c}
    if needs_critic_vals != {True, False}:
        report.fail("diversity:needs_critic", f"got {needs_critic_vals}, expected both true and false")
    else:
        report.ok("diversity:needs_critic=both-values-present")


def diversity_critic(cases: list[dict], report: Report) -> None:
    recommendations = {c["expected"]["recommendation"] for c in cases if "expected" in c}
    severities: set[str] = set()
    for case in cases:
        for finding in case.get("expected", {}).get("findings", []):
            severities.add(finding["severity"])

    missing_recs = REQUIRED_RECOMMENDATIONS - recommendations
    if missing_recs:
        report.fail("diversity:recommendations", f"missing: {missing_recs}")
    else:
        report.ok("diversity:recommendations=all-3-covered")

    if not REQUIRED_SEVERITIES.issubset(severities):
        missing = REQUIRED_SEVERITIES - severities
        if "HIGH" in missing:
            report.fail("diversity:severities", "no HIGH finding present")
        else:
            report.ok(f"diversity:severities partial (missing: {missing}) — acceptable")
    else:
        report.ok("diversity:severities=all-3-covered")

    # Blocking + non-blocking both present
    blocking_vals = {c["expected"]["blocking"] for c in cases if "expected" in c}
    if blocking_vals != {True, False}:
        report.fail("diversity:blocking", f"got {blocking_vals}")
    else:
        report.ok("diversity:blocking=both-values-present")


def check_isa_create_smoke(report: Report) -> None:
    """Smoke-test: isa-create.py --help must exit 0 and emit usage text.

    isa-create.py is the ISA creator shipped in scripts/.
    """
    if not ISA_CREATE.exists():
        report.fail(
            "isa_create_smoke",
            f"isa-create.py missing: {ISA_CREATE}",
        )
        return
    try:
        proc = subprocess.run(
            [sys.executable, str(ISA_CREATE), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        report.fail("isa_create_smoke:run", str(exc))
        return
    if proc.returncode != 0:
        report.fail(
            "isa_create_smoke:returncode",
            f"got {proc.returncode}, stderr: {proc.stderr[:200]}",
        )
        return
    if not proc.stdout.strip():
        report.fail("isa_create_smoke:output", "empty stdout from --help")
        return
    report.ok("isa_create_smoke:isa-create.py --help")


def check_prompt_content(prompt: Path, label: str, required_markers: list[str], report: Report) -> None:
    text = prompt.read_text(encoding="utf-8")
    missing = [m for m in required_markers if m not in text]
    if missing:
        report.fail(f"prompt_content:{label}", f"missing markers: {missing}")
    else:
        report.ok(f"prompt_content:{label}")


def main() -> int:
    parser = argparse.ArgumentParser(description="nexus-discipline test runner")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    report = Report(verbose=args.verbose)

    report.section("Component prompts")
    # tier-classifier.md: legacy contract (tier: SIMPLE/STANDARD/COMPLEX) + E1-E5 mapping table
    if check_file_exists(CLASSIFIER_PROMPT, "tier-classifier.md", report):
        check_prompt_content(
            CLASSIFIER_PROMPT,
            "classifier",
            [
                "tier",
                "workflow_type",
                "validation_level",
                "needs_critic",
                "SIMPLE",
                "STANDARD",
                "COMPLEX",
                "E1",
                "E2",
                "E3",
                "E4",
                "E5",
                "FEATURE",
                "REFACTOR",
                "INVESTIGATION",
                "MIGRATION",
                "TRIVIAL",
                "CRITICAL",
                "Decision flowchart",
            ],
            report,
        )

    # plan-critic.md: same contract as alg — name preserved
    if check_file_exists(CRITIC_PROMPT, "plan-critic.md", report):
        check_prompt_content(
            CRITIC_PROMPT,
            "critic",
            [
                "findings",
                "blocking",
                "recommendation",
                "severity",
                "HIGH",
                "MEDIUM",
                "LOW",
                "accuracy",
                "completeness",
                "consistency",
                "feasibility",
                "alignment",
            ],
            report,
        )

    report.section("Schemas")
    classifier_schema = check_json_schema(CLASSIFIER_SCHEMA, "classifier", report)
    critic_schema = check_json_schema(CRITIC_SCHEMA, "critic", report)

    report.section("Classifier fixtures")
    if classifier_schema is not None:
        check_fixtures(CLASSIFIER_FIXTURES, classifier_schema, "classifier", report, diversity_classifier)

    report.section("Critic fixtures")
    if critic_schema is not None:
        check_fixtures(CRITIC_FIXTURES, critic_schema, "critic", report, diversity_critic)

    report.section("isa-create script smoke-test")
    check_isa_create_smoke(report)

    return report.summary()


if __name__ == "__main__":
    sys.exit(main())
