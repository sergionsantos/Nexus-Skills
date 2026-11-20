# nexus-plan-spec

Skill para escrever um **plano/spec de build exaustivo** (10-20k linhas, 10+ milestones), verificado contra o ambiente real e pensado para ser executado por um modelo médio ou por um executor literal que não toma decisões próprias.

## Quando usar
- "Faz um plano completo para X", "spec para outro modelo executar", "build plan de um produto".
- O output vai ser executado por um agente sem juízo crítico.
- Para um plano rápido/médio usa antes **`nexus-plan`** (mais barato); esta skill custa muitos tokens (milhões num plano grande).

## O que inclui
- `SKILL.md`: modo de operação (§0), pipeline de 10 fases, formato de step, red-team.
- `references/example-mini-plan.md`: spec completo mínimo, validável.
- `references/`: protocolo do critic, prompts de red-team, template de state-snapshot, padrões de evidência, roadmap pós-conclusão, autoria paralela e custos.
- `scripts/validate-plan-spec.sh`: validador mecânico (`bash scripts/validate-plan-spec.sh plano.md`; precisa de bash — Git Bash no Windows).

## Instalação
```bash
ln -s ~/Nexus-Skills/skills/nexus-plan-spec ~/.claude/skills/nexus-plan-spec   # Claude Code
ln -s ~/Nexus-Skills/skills/nexus-plan-spec ~/.codex/skills/nexus-plan-spec    # Codex CLI
```
Alternativa sem symlink (qualquer SO, incl. Windows): copia a pasta `skills/nexus-plan-spec` para `~/.claude/skills/` (Claude Code) ou `~/.codex/skills/` (Codex CLI); no Windows `~` é `%USERPROFILE%`. Cópia não acompanha `git pull`: volta a copiar ao actualizar.

## Dependências
Nenhuma obrigatória. Funciona melhor com `nexus-discipline` (execução com gates: VERIFY-PREFLIGHT-GATE e MILESTONE-CADENCE) e `nexus-plan` (versão rápida). `session-wrap` é opcional para fechar a sessão.
