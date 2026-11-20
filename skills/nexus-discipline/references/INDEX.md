# Índice das references — nexus-discipline

44 ficheiros, cada um com uma linha única. Regra: nunca deixar uma reference fora deste índice; cada row aponta para um ficheiro existente.
Adicionar lição nova = ficheiro novo em `references/` + 1 linha aqui (ver SKILL.md §8).

## Verificação e provas (16)

| Ficheiro | Tema |
|---|---|
| `verify-probe-anti-patterns.md` | Verify Probe Anti-Patterns — 4 padrões novos (M15-M18 projecto X) |
| `shell-probe-false-fails.md` | Shell + DB + Cron Probe False-Fails — 16 padrões que parecem system failures mas são bugs do probe |
| `probe-cleanup-ordering.md` | Pattern: Cleanup-before-invariants em verify scripts |
| `probe-grep-escape-hell.md` | Pattern: grep regex escape hell em bash heredoc |
| `probe-hook-contract.md` | Pattern: Hook contract probing — don't search for `data: T[]` literal |
| `source-aware-negative-controls.md` | Source-Aware Negative Controls |
| `gate-calibration-and-runtime-probes.md` | GATE Calibration + Runtime Probe Patterns |
| `generated-artifact-reproducibility-gate.md` | Generated-artifact reproducibility gate |
| `final-mutation-and-pointer-truth-gates.md` | Final-mutation and pointer Truth Gates |
| `dump-real-values-on-smoke-tests.md` | Dump Real Values on Smoke Tests |
| `verify-your-own-tool-before-blaming-inputs.md` | VERIFY-YOUR-OWN-TOOL-BEFORE-BLAMING-INPUTS (2026-07-05, CRM) |
| `false-alarm-from-partial-evidence.md` | Falso alarme a partir de evidência parcial |
| `systemic-bug-detection.md` | Schema-level systemic-bug detection (for execution) |
| `mock-theater-rewrite-recipe.md` | Mock-Theater Test Rewrite Recipe |
| `verification-closeout-and-background-agent-integrity.md` | Verification closeout and background-agent integrity |
| `count-based-proof.md` | Done-language + count-based proof |

## Linguagem de conclusão e gates (6)

| Ficheiro | Tema |
|---|---|
| `done-language-and-status-vocabulary.md` | Done-Language Trap + Status Vocabulary |
| `done-language-gate-for-creative-artifacts.md` | DONE-LANGUAGE gate — bash specifics |
| `alg-enforcement-3-gates.md` | ALG Enforcement — Padrão Determinístico de 3 Gates |
| `loop-detection-case-studies.md` | Loop Detection — Case Studies |
| `approval-gated-commands-remote-channels.md` | Approval-gated commands on remote chat channels (bots, API servers, messaging gateways) |
| `isa-retroactivo.md` | ISA Retroactivo — Recovery Procedure |

## Revisão independente (3)

| Ficheiro | Tema |
|---|---|
| `fresh-context-verifier-protocol.md` | Fresh-Context Verifier Protocol (Rule 0 operacionalizada) |
| `independent-code-review-calls.md` | Independent Code-Review CALL — orquestrador ↔ revisor playbook |
| `cold-eyes-review-findings.md` | Cold-Eyes Review — Findings Patterns from Independent Lens Sessions (2026-07-04) |

## Multi-agente, worktrees e planos (6)

| Ficheiro | Tema |
|---|---|
| `multi-agent-sibling-edits-detector.md` | Pattern: Sibling-edits clobber em multi-agent |
| `worktree-shared-race-conditions.md` | Worktree-Shared Race Conditions (sibling subagents mid-call) |
| `pre-flight-collision-check.md` | Pre-Flight Collision Check — "Cria X em path Y" tasks |
| `ground-truth-drift-between-sessions.md` | Ground truth drift between execution windows — when yesterday's "verified ✅" is today's empty |
| `spike-read-only-dry-run-pattern.md` | Spike READ-ONLY dry-run pattern — reusar o contrato real + input sintético + chain discipline |
| `product-decision-gap-protocol.md` | Product-Decision Gap Protocol (DIV-GUARD) |

## Comunicação com o dono e bloqueios (6)

| Ficheiro | Tema |
|---|---|
| `rule-0-11-explain-then-recommend.md` | Explain-Then-Recommend (detailed support doc) |
| `multi-path-options-compact.md` | Multi-path options → compact output, not narrative sections |
| `auth-blocked-redirect-first.md` | AUTH-BLOCKED-REDIRECT-FIRST (2026-07-05, CRM session) |
| `pivot-to-auth-free-hardened.md` | Pivot-to-Auth-Free Protocol (HARDENED) |
| `structured-ask-owner-for-secret.md` | Structured ask — owner tem o segredo, tu não consegues chegar a ele |
| `grounded-source-only.md` | grounded-source-only — verbatim citation discipline for identity/memory blocks |

## Dados, schemas e ferramentas (5)

| Ficheiro | Tema |
|---|---|
| `psql-dryrun-rollback-discipline-2026-07-19.md` | psql-dryrun-rollback-discipline-2026-07-19.md |
| `postgres-runtime-probe-gotchas.md` | Postgres + PostgREST runtime probe gotchas (pitfall 2026-07-02 / 2026-07-04, executor) |
| `sqlite-python-execution-pitfalls.md` | sqlite3-python execution pitfalls |
| `write-file-api-key-sanitization-corrupts-disk.md` | write_file/patch sanitization can corrupt `apiKey:` literals on disk |
| `read-file-display-vs-disk-sanitization.md` | read_file display sanitization vs on-disk reality |

## Núcleo (playbooks e esforço) (2)

| Ficheiro | Tema |
|---|---|
| `playbooks.md` | Playbooks — decision-trees executáveis |
| `effort-and-process.md` | Esforço e processo — system prompt de execução |
