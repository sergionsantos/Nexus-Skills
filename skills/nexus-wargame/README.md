# nexus-wargame

Transforma um objectivo com **terreno adversarial** (lead-gen, migração, campanha, lançamento — tudo o que uma plataforma, concorrente ou algoritmo pode fazer falhar) em **war-games** executáveis: planos acção → reacção → contra-acção, com falhas antecipadas. Gastas o modelo forte uma vez; modelos baratos executam depois com o julgamento já nos ficheiros.

## Quando usar
- "Faz um war-game de X" / caminho incerto e cheio de excepções → esta skill.
- Plano linear sem adversário → `nexus-plan`; spec de build de código → `nexus-plan-spec`; lição da sessão → `nexus-learner`.

Cada movimento tem 8 elementos (acção, observação se funcionar/falhar, causa, sinal, contra-movimento, bifurcação, abort). Workflow em 7 fases com red-team até convergir.

## Instalação
```bash
ln -s ~/Nexus-Skills/skills/nexus-wargame ~/.claude/skills/nexus-wargame   # Claude Code
ln -s ~/Nexus-Skills/skills/nexus-wargame ~/.codex/skills/nexus-wargame    # Codex CLI
```
No Windows, copia a pasta para `%USERPROFILE%\.claude\skills\`.

## Dependências
Nenhuma (só markdown). Pressupõe agentes que suportem subagentes em paralelo; sem eles, faz as waves em sessões distintas.

## Conteúdo
`SKILL.md` · `templates/wargame-order.md` (inclui prompt de red-team) · `references/leadgen-avatars-case.md` (caso de origem, anonimizado).
