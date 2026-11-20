# Sub-rotinas de execução

Quatro sub-rotinas aprendidas em sessões reais de planeamento/execução.

## 1. Verify literal fresh com exit code visível

**Quando** o contexto exige "verify real corrido neste turno" ou "exit code visível":

1. Corre o verify numa shell que mantenha o `cwd` correcto (alguns sandboxes de execução de código perdem o `cwd` em subprocessos e dão falsas falhas de colecção nos testes).
2. Captura stdout/stderr para ficheiro; se for pytest, faz parse do `--junitxml` (ver `verify-evidence-patterns.md`).
3. Imprime sempre o exit code como número (`PYTEST_EXIT=<código>`).
4. Antes de responder ao utilizador, confirma o exit=0 de todos os comandos que vais citar.
5. Se exit != 0, não discutas: começa a resposta pelo exit e pelo dump.

A regra geral (exit code visível + dump antes de citar resultado) é doutrina e vive no §0.10 do SKILL.md.

## 2. Tocar no schema da DB

Sempre que o plano tocar o schema (nova migration, alargar um CHECK, RLS nova):

1. Inspecciona a migration anterior mais recente (para nomear a seguinte em sequência).
2. Verifica CHECK constraints (ex.: valores permitidos de uma coluna `kind`) na DB ACTUAL, não no código-fonte.
3. Patch forward-only (sem DROP); ao alargar valores permitidos, usa `RESERVED` ou equivalente.
4. Dry-run antes de aplicar (`migrate plan` ou equivalente da tua ferramenta).
5. ⛔ `GATE PRÉ-APLICAÇÃO` (irreversível sem migration inversa): preparar, PARAR, review forte + aprovação humana explícita.

## 3. Seleção de worktree

Com várias worktrees em paralelo:

1. Cada peça de trabalho **nova** cria a sua própria worktree + branch `feat/<slug>`; não a mistures com outra branch em curso.
2. Confirma o `cwd` de qualquer daemon/processo de longa duração contra a branch fonte de verdade (`lsof -p <pid> -d cwd`).
3. Antes de `kill && restart`, confirma que o `cwd` do daemon tem as migrations mais recentes — senão é a classe de bug "worktree errada".

## 4. Probes persistidas em disco

Toda a probe (in-process ou subprocesso) persiste num ficheiro (`probes/probe-<id>.py` ou pasta equivalente do projecto), não só na conversa:

1. `id` curto (ex.: `f33-e2e`).
2. Docstring: o quê, porquê, output esperado, o que foi realmente observado.
3. A sessão seguinte reproduz com `python <ficheiro> --rerun`.
