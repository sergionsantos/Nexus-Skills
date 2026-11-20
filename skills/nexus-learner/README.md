# nexus-learner

Transforma uma lição aprendida numa sessão (um bug difícil, uma descoberta não-óbvia) num skill reutilizável — mas só se houver evidência real.

## Quando usar
- No fim de um debug/descoberta que custou esforço real e vai repetir-se.
- Dizendo «extrai um skill disto», «aprende isto» ou `/nexus-learner`.
- Não serve para notas rápidas nem para conhecimento que se encontra numa pesquisa.

## O que faz
Gate (vale a pena?) → dedup contra skills existentes → recolha de evidência verbatim → escrita com template → validação mecânica → relatório honesto (`draft` até ao 1.º uso real).

## Termos
- **Update-over-create**: antes de criar um skill, procura skills existentes sobre o tema; se houver, actualiza-o em vez de criar um duplicado.
- **Passing check**: o teste/comando que provou o caminho (exit 0, repro reproduzido, build verde) registado no bloco Evidência; «pareceu funcionar» não conta. O validador só procura uma marca textual disso (exit 0 / PASS / comando em backticks), não executa nem confirma o check.

## Instalação
Copia (ou faz symlink) da pasta `nexus-learner/` para `~/.claude/skills/` (Claude Code) ou `~/.codex/skills/` (Codex).

## Dependências
- Python 3 (só biblioteca standard) para os scripts em `scripts/`:
  - `validate-learned-skill.py [--skills-dir PASTA] <skill.md>` — valida só a FORMA (frontmatter, secções, evidência presente), **não a verdade da claim**; a correcção exige revisão independente antes de promover. Considera também a pasta `.claude/skills` ancestral (skills de projecto).
  - `sweep-draft-skills.py [--days N] [--skills-dir PASTA]` — lista drafts estagnados.
- No Windows, corre com `PYTHONUTF8=1`. Variável opcional `SKILLS_DIR` muda a pasta de skills analisada (por omissão `~/.claude/skills`).
- Opcional: uma pesquisa semântica/memória persistente para o passo de dedup (o grep chega para começar).
