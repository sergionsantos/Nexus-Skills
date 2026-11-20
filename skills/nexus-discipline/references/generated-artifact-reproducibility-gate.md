# Generated-artifact reproducibility gate

## Trigger

Use whenever a milestone commits reports, snapshots, CSV/JSON/Markdown, fixtures, lock-like manifests, screenshots metadata, or other files produced by a script/probe/generator.

## Failure class

A generator can pass all functional tests yet leave a non-reproducible repository:

- UUIDs, random ports, temporary paths, timestamps, host paths or traceback locations are serialized;
- the committed artifact reflects one run, but the next real run changes bytes;
- tests validate shape/content but never verify rerun stability;
- independent verification runs the generator and discovers a dirty tree.

This is not housekeeping. A generator whose canonical output changes without semantic input change is not verified.

## Mandatory gate

1. Start from clean tree.
2. Run the real generator once.
3. Hash every generated canonical artifact.
4. Run the real generator again with identical semantic inputs.
5. Hash again and require equality.
6. Require `git status --porcelain` empty after the second run.
7. Add an automated determinism test when the artifacts are versioned or release-gating.

Example gate:

```bash
test -z "$(git status --porcelain)"
python scripts/generate_report.py   # exemplo — script do teu projecto
h1=$(shasum -a 256 docs/report.md docs/report.csv | shasum -a 256 | cut -d' ' -f1)
python scripts/generate_report.py   # exemplo — script do teu projecto
h2=$(shasum -a 256 docs/report.md docs/report.csv | shasum -a 256 | cut -d' ' -f1)
test "$h1" = "$h2"
test -z "$(git status --porcelain)"
```

## Normalization discipline

Normalize only volatile representation, never semantic evidence:

- `/tmp/run-<uuid>` → `<workspace>`;
- random loopback port → `<loopback-port>`;
- temporary profile filename → `<profile>`;
- host-specific traceback prefix → `<runtime-path>`;
- timestamps → fixed/frozen clock only when time is not the subject under test.

Preserve actual exit codes, classifications, allow/deny outcomes and meaningful stderr. A stable fabricated report is worse than an unstable truthful one.

## Truthfulness rule for probes

Name the invariant at the strength actually proved. Example:

- writing outside `/Users` is blocked does **not** prove exact-workspace confinement;
- writing in one `/tmp` directory succeeds does **not** prove sibling `/tmp` directories are blocked;
- exit non-zero does not prove no side effect — check the filesystem/network/process side effect directly.

Unproved stronger invariants become explicit later-milestone requirements, not optimistic wording in the current milestone.

## Session reference

Caso real: functional sandbox probes and 40 tests passed, but independent rerun dirtied `docs/sandbox-spike.{md,csv}` through UUIDs and ports. Repair normalized volatile tokens, added a two-run SHA-256 test, required post-rerun clean tree, and downgraded exact-workspace confinement to an honest follow-up requirement. Final gate: two equal hashes + clean tree + 41 tests.
