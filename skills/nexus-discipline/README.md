# nexus-discipline

**ISA** = Ideal State Artifact: ficheiro de spec/estado de uma tarefa por fases (`.isa/ISA-<nome>.md`, ver `templates/ISA.md`). **ISC** = critério de aceitação binário `- [ ]` dentro dele.

Disciplina de execução e verificação para agentes de código (Claude Code, Codex, etc.): **verificar antes de afirmar** (prever o resultado, corrigir com controlos negativos, revisão independente), **linguagem de conclusão honesta** (só «done» com prova deste turno), tríade por fase (ISA + status file + script de verify), cadência de milestones e gates antes de acções irreversíveis.

## Quando usar
- Execução de trabalho não trivial (código, migrações, scripts) em que não queres «parece certo» como prova.
- Quando vais declarar «concluído», fechar um milestone ou lançar subagentes.
- Para planos produzidos por `nexus-plan-spec` / `nexus-plan` (define o VERIFY-PREFLIGHT-GATE e a MILESTONE-CADENCE).

## Conteúdo
- `SKILL.md` — doutrina (§1-§6), routing por problema (§7), regra anti-drift (§8).
- `references/` — playbooks P1-P15, casos e receitas; índice em `references/INDEX.md`.
- `templates/`, `examples/`, `components/`, `scripts/` — ISA (artefacto de spec/estado), classificador de esforço, `isa-create.py`, `validate-isc.py`.

## Instalação
Copia (ou faz symlink) da pasta para `~/.claude/skills/nexus-discipline` ou `~/.codex/skills/nexus-discipline` (Windows: `%USERPROFILE%\.claude\skills\`).

## Dependências
Nenhuma obrigatória. Scripts em Python 3 (`PYTHONUTF8=1` no Windows); `tests/run-tests.py` precisa de `pip install jsonschema`. Skills irmãs opcionais: `nexus-plan-spec`, `nexus-plan`, `session-resume`, `nexus-learner`, `nexus-skill-creator`, `session-wrap`.
