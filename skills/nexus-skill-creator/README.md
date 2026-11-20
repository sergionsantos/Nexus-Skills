# nexus-skill-creator

Criação disciplinada de skills novas: 4 perguntas de intent, dedup, escolha de localização,
estrutura por tamanho, secções obrigatórias, smoke com predição e negative control, e estado
`draft` até ao 1º uso real com revisão independente.

## Quando usar
"cria um skill para X", "transforma este workflow num skill", "nova skill".
Não serve para benchmarks pesados (usa o skill-creator oficial) nem para lições da sessão (nexus-learner).

## Instalação
Copia (ou faz symlink) da pasta para `~/.claude/skills/nexus-skill-creator` e/ou `~/.codex/skills/nexus-skill-creator`.

## Script opcional: scripts/bridge-skill.sh
Torna um skill disponível em Claude Code e Codex ao mesmo tempo (symlink; `--copy` para cópia):

    bash scripts/bridge-skill.sh <nome> --dry-run   # só mostra
    bash scripts/bridge-skill.sh <nome>             # ~/.claude/skills <-> ~/.codex/skills
    bash scripts/bridge-skill.sh <nome> --a DIR1 --b DIR2   # pastas à escolha

Idempotente em modo symlink (com `--copy`, uma 2ª corrida dá conflito); falha explicitamente em conflito (pastas reais nos dois lados) ou skill inexistente.
No Windows corre em Git Bash; se o symlink falhar (precisa de Modo de Programador), usa `--copy`.

## Dependências
Bash. Opcional: `python3` + PyYAML para o check de frontmatter.
