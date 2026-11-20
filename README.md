# Nexus-Skills

Repositório privado com as skills de agente (Claude Code / Codex) do Sérgio Santos, partilhadas com família e amigos.

## Skills

| Skill | O que faz | Estado |
|---|---|---|
| [`nexus-deep-research`](skills/nexus-deep-research) | Pesquisa aprofundada com citações verificadas, red team e gate de entrega. Guia PT-PT em `docs/`. | pronta para partilha |

(Mais skills a caminho; vários nomes serão renomeados para serem auto-explicativos.)

## Instalação

```bash
git clone <este repo> ~/Nexus-Skills
ln -s ~/Nexus-Skills/skills/<skill> ~/.claude/skills/<skill>     # Claude Code
ln -s ~/Nexus-Skills/skills/<skill> ~/.codex/skills/<skill>      # Codex CLI
```

No Windows, copia a pasta da skill para `%USERPROFILE%\.claude\skills\`.

## Convenções

- Uma pasta por skill em `skills/`, com `SKILL.md` e, se existirem, `reference/`, `scripts/`, `tests/`.
- Sem caminhos, máquinas, chaves ou dados pessoais do autor.
- Skills de terceiros mantêm a licença e a atribuição originais.
