# session-resume

Protocolo para **retomar trabalho longo a meio** (projecto, migração, plano de build, investigação) numa sessão nova, sem redescobrir nada nem assumir estado errado. Inclui a disciplina de "done" (nada de «concluído» sem verificação corrida nesse turno).

## Quando usar
- «Retoma o projecto X», «continua onde ficámos», «volta ao X».
- A sessão abre num projecto com README-EXECUTOR, LOG de wrap, ISA ou ficheiro de estado.
- O agente vai declarar «feito/verificado» sem prova.

## Instalação
Copia (ou faz symlink) da pasta `session-resume/` para `~/.claude/skills/` ou `~/.codex/skills/`.

## Conteúdo
- `SKILL.md` — checklist de 5 passos + anti-padrões.
- `templates/reentry-readme.md` — folha de re-entrada para novos projectos.
- `scripts/recover-from-failed-patch.sh` — confirma se uma edição realmente persistiu.
- `references/pitfalls-avancados.md` — pitfalls técnicos específicos.
- `references/self-report-fabrication.md` — caso de estudo.

## Dependências
Nenhuma obrigatória. Usa git e, opcionalmente, uma memória persistente, um issue tracker e a skill `session-wrap` e a skill irmã `nexus-discipline` (`../nexus-discipline`, opcional: sem ela, o ISA é qualquer ficheiro de estado).
