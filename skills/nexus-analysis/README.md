# nexus-analysis

Análise priorizada de melhorias para um sistema, app ou projecto **já existente**: produz N melhorias (por omissão 7), cada uma com evidência `ficheiro:linha`, a cobrir três fontes — o que está partido, o valor latente (já construído mas não exposto) e as transformações (o que muda a categoria do produto).

## Quando usar
- «Encontra 7 melhorias para esta app», «analisa isto e diz o que melhorar», «como tornar X extraordinário».
- Não serve para: debug de um bug concreto, plano de build passo-a-passo (usa `nexus-plan-spec`), review de diff/PR, audit de repo externo.

## Como funciona
GROUND (estado real vs documentado) → EXPLORE (4-5 lentes em paralelo) → SYNTHESIZE → STRUCTURE (relatório) → VERIFY (check mecânico + revisão independente). Existe também um modo delta para re-análises (`references/playbook-delta.md`). Começa por ler `SKILL.md` e o exemplo `references/worked-example-task-tracker.md`.

## Instalação
Copia (ou faz symlink) da pasta `nexus-analysis/` para `~/.claude/skills/` ou `~/.codex/skills/`.

## Dependências
- Bash, `grep`, `sed` (os scripts em `scripts/` são `scaffold.sh` e `verify-report.sh`; no Windows usa Git Bash ou WSL).
- Idealmente um runtime com subagentes (exploração paralela e revisão fresh); sem eles o método corre em modo solo e o relatório fica «por rever».
- Skills relacionadas (opcionais): `nexus-plan-spec`, `nexus-discipline`, `session-wrap`.
