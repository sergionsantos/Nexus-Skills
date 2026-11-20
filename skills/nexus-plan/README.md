# nexus-plan

Planeamento **rápido e económico** (~140-300k tokens) de uma melhoria média/grande, com juízo humano/orquestrador no loop: arquitecto forte escreve o plano, um critic revê-o num passe, um executor de tier médio executa e um verificador independente fecha.

## Quando usar
- Queres um plano curto e executá-lo com supervisão → esta skill.
- Queres uma spec exaustiva para um modelo executar sozinho, sem ninguém a supervisionar → `nexus-plan-spec`.
- Ainda não sabes O QUE melhorar → `nexus-analysis` primeiro.

Dois regimes: PLAN-v2 (trabalho médio) e Decision-Spec JIT (trabalho grande, faseado).

## Instalação
Copia ou faz symlink desta pasta:
```bash
ln -s ~/Nexus-Skills/skills/nexus-plan ~/.claude/skills/nexus-plan   # Claude Code
ln -s ~/Nexus-Skills/skills/nexus-plan ~/.codex/skills/nexus-plan    # Codex CLI
```
No Windows, copia a pasta para `%USERPROFILE%\.claude\skills\`.

## Dependências
Nenhuma (só markdown). Funciona melhor com agentes que suportem subagentes; sem eles, separa os papéis em sessões distintas. Skills relacionadas: `nexus-plan-spec`, `nexus-analysis`.

## Conteúdo
`SKILL.md` · `templates/` (decision-spec, plan-v2, prompts de critic/executor/verify) · `references/patterns.md`.
