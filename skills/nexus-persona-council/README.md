# nexus-persona-council

Motor de juizo por persona. Dado um caso real (com factos e numeros), produz um parecer escrito do ponto de vista de uma ou varias pessoas-expert cujo "motor de julgamento" (`LENS.md`) tu forneces. Quatro modos:

- `solo` — uma persona, decisao concreta.
- `counsel` — mesa de 3-5 personas, ronda cega + arbitro externo.
- `battle` — pre-mortem adversarial contra um plano ja decidido.
- `lens` — ver uma situacao pelos olhos de uma ou varias personas (exploracao, sem decisao formal).

Inclui gates anti-conselho-generico (cheque numerico, teste de remocao de voz, "swap de sector").

## Quando usar
Decisao importante com factos na mesa, ou plano escrito que queres atacar. **Nao** serve para perguntas do tipo "o que pensa X sobre Y" nem para escrever texto na voz de alguem.

## Instalacao
Copia (ou faz symlink de) esta pasta para `~/.claude/skills/nexus-persona-council` ou `~/.codex/skills/nexus-persona-council`. Abre sessao nova.

## Dependencias
- Nenhuma ferramenta externa. O `counsel` exige poder lancar subagentes/sessoes independentes (ronda cega); sem isso, nao corre.
- **Personas:** inclui 24 em `personas/` (lista e limitacoes em `personas/README.md`). Para acrescentar mais, cria `<Nome>/LENS.md` nessa pasta (formato em `references/lens-format.md`) ou aponta `PERSONAS_DIR` para a tua.
