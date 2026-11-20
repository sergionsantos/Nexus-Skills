# Final-mutation and pointer Truth Gates

Reusable verification lessons from a long spec→implementation→relocation→wrap workflow.

## 1. Same-turn completion means after the last mutation

A PASS earlier in the turn is stale if any file is patched, generated, renamed, committed, or auto-regenerated afterwards.

Required order:

1. finish every mutation;
2. run canonical checks;
3. capture literal exit codes;
4. make no further mutation;
5. only then use completion language.

If a gate complains again in a later turn, run a fresh check in that later turn or report only observed state without completion wording.

## 2. Git cleanliness is content, not exit status

`git status` normally exits 0 with dirty or untracked files. Require:

```sh
porcelain=$(git status --porcelain)
test -z "$porcelain"
```

This caught an untracked ISA that an exit-code-only gate had missed.

## 3. Verify the verifier before blaming the implementation

A custom probe can false-fail by passing an unsupported CLI option or reading the wrong path. On failure:

- compare the probe command with the exact contract/spec command;
- inspect `--help` or the canonical test;
- repeat with the exact supported invocation;
- label the first result as verifier error when proven.

## 4. Wrapper exit 0 is not agent completion

For gateway delegation, distinguish:

- shell/HTTP process exit;
- HTTP status;
- agent envelope (`completed`, `failed`, `finish_reason`);
- actual artifacts and tests.

A process exit 0 with `completed=false` requires a closeout delegation and fresh verification.

## 5. Wrap pointer search may miss top-N semantically

After a distiller reports pointer creation:

1. search the semantic topic;
2. if absent from visible top-N, search exact canonical filename and absolute path;
3. require returned pointer ID and path;
4. document filename as the robust re-entry key when semantic ranking is weak;
5. never claim the semantic query passed if only filename/path did.

## 6. Curated artifacts can still be stale

`--isa` prevents stream mixing but older ISAs may retain resolved blockers or superseded counts. Manually reconcile wrap drafts against live state for:

- paths after rename/move;
- current Git/tool versions;
- final decision/artifact/risk counts;
- latest tests and milestone;
- next unstarted milestone.
