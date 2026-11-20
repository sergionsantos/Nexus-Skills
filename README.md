# Nexus-Skills

Repositório privado com as skills de agente (Claude Code / Codex) do Sérgio Santos, partilhadas com família e amigos.

## Skills

| Skill | Para que serve |
|---|---|
| [`nexus-deep-research`](skills/nexus-deep-research) | Pesquisa aprofundada com citações verificadas, red team e gate de entrega. Guia PT-PT em `docs/`. |
| [`nexus-discipline`](skills/nexus-discipline) | Doutrina de execução: verificar antes de declarar «feito», linguagem de evidência, gates e marcos. |
| [`nexus-plan`](skills/nexus-plan) | Plano rápido e económico, com humano ou orquestrador no loop. |
| [`nexus-plan-spec`](skills/nexus-plan-spec) | Plano/spec exaustivo para ser executado por agentes sem supervisão. |
| [`nexus-analysis`](skills/nexus-analysis) | Análise de um sistema existente com melhorias priorizadas e evidência ficheiro:linha. |
| [`nexus-wargame`](skills/nexus-wargame) | War-games de planos em terreno adversarial (draft: v0.1, sem uso real). |
| [`nexus-learner`](skills/nexus-learner) | Extrai lições de uma sessão e transforma-as em skills reutilizáveis. |
| [`nexus-skill-creator`](skills/nexus-skill-creator) | Cria e disponibiliza skills novas (Claude Code e Codex). |
| [`nexus-persona-council`](skills/nexus-persona-council) | Pareceres de personas reais (24 incluídas) sobre uma decisão, com ronda cega. |
| [`nexus-council-of-high-intelligence`](skills/nexus-council-of-high-intelligence) | Conselho de 18 membros fixos para decisões difíceis (fork MIT de `0xNyk`). |
| [`nexus-youtube-deep-pipeline`](skills/nexus-youtube-deep-pipeline) | Processamento profundo de vídeos YouTube: transcrição, fact-check, citações. Precisa do CLI `claude`. |
| [`session-resume`](skills/session-resume) | Retoma um projecto sem perder o estado nem repetir trabalho. |
| [`session-wrap`](skills/session-wrap) | Fecho de sessão: estado, decisões, pendentes e lições, num ficheiro. |

## Instalação

```bash
git clone <este repo> ~/Nexus-Skills
ln -s ~/Nexus-Skills/skills/<skill> ~/.claude/skills/<skill>     # Claude Code
ln -s ~/Nexus-Skills/skills/<skill> ~/.codex/skills/<skill>      # Codex CLI
```

No Windows, copia a pasta da skill para `%USERPROFILE%\.claude\skills\` (ou define `PYTHONUTF8=1` para correr os scripts Python).

## Convenções

- Uma pasta por skill em `skills/`, com `SKILL.md` e, se existirem, `references/`, `scripts/`, `tests/`.
- Sem caminhos, máquinas, chaves ou dados pessoais do autor.
- Skills de terceiros mantêm a licença e a atribuição originais (`nexus-deep-research`, `nexus-council-of-high-intelligence`: MIT).
