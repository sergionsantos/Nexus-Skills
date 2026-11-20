# nexus-learner

Transforma uma lição aprendida numa sessão (um bug difícil, uma descoberta não-óbvia) num skill reutilizável — mas só se houver evidência real.

## Quando usar
- No fim de um debug/descoberta que custou esforço real e vai repetir-se.
- Dizendo «extrai um skill disto», «aprende isto» ou `/nexus-learner`.
- Não serve para notas rápidas nem para conhecimento que se encontra numa pesquisa.

## O que faz
Gate (vale a pena?) → dedup contra skills existentes → recolha de evidência verbatim → escrita com template → validação mecânica → relatório honesto (`draft` até ao 1.º uso real).

## Instalação
Copia (ou faz symlink) da pasta `nexus-learner/` para `~/.claude/skills/` (Claude Code) ou `~/.codex/skills/` (Codex).

## Dependências
- Python 3 (só biblioteca standard) para os scripts em `scripts/`:
  - `validate-learned-skill.py <skill.md>` — valida forma e evidência.
  - `sweep-draft-skills.py [--days N]` — lista drafts estagnados.
- No Windows, corre com `PYTHONUTF8=1`. Variável opcional `SKILLS_DIR` muda a pasta de skills analisada (por omissão `~/.claude/skills`).
- Opcional: uma pesquisa semântica/memória persistente para o passo de dedup (o grep chega para começar).
