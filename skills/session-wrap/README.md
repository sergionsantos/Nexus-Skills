# session-wrap

Fecha um tema de trabalho: escreve uma nota durável (estado, decisões, pendências e limitações, ficheiros, lições) para que possas limpar a sessão e retomar o tema mais tarde sem recomeçar do zero.

## Quando usar
- No fim de um tema a que vais voltar, ou antes de `/clear`.
- Quando dizes "wrap this up", "fecha o tema" ou `/wrap`.
- A maioria das sessões não precisa de wrap.

## O que faz
- Delimita primeiro o âmbito (workspace, spec/plano, sessão).
- Escreve `Wraps/wrap-<slug>-<AAAA-MM-DD>.md` (pasta configurável) marcado como DRAFT.
- Opcional: grava um apontador curto numa memória persistente, se tiveres uma.

## Instalação
Copia a pasta para `~/.claude/skills/session-wrap` (Claude Code) ou `~/.codex/skills/session-wrap` (Codex), ou cria um symlink.

## Dependências
Nenhuma. A memória persistente é opcional.
