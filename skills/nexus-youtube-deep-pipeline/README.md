# nexus-youtube-deep-pipeline

Análise **profunda** de um vídeo do YouTube: lê a transcrição completa, remove artefactos de transcrição (janelas sobrepostas), gera um documento de conhecimento (conceitos, biografia reconstruída, citações literais, timeline), exclui anúncios/patrocínios e **verifica mecanicamente** cada citação e número contra a transcrição.

## Quando usar
- Pedes explicitamente "processa com profundidade" / "deep process" num vídeo que vale o custo (~12 min, ~0,30 $ por vídeo).
- Entrevistas longas, convidados ricos em frameworks ou com história de vida.
- Para um resumo rápido, não uses esta skill.

## Instalação
```bash
ln -s ~/Nexus-Skills/skills/nexus-youtube-deep-pipeline ~/.claude/skills/nexus-youtube-deep-pipeline   # Claude Code
ln -s ~/Nexus-Skills/skills/nexus-youtube-deep-pipeline ~/.codex/skills/nexus-youtube-deep-pipeline    # Codex CLI
```
No Windows, copia a pasta para `%USERPROFILE%\.claude\skills\`. A pasta de saída é tua: define `OUT=...` (ver "Setup" no `SKILL.md`); nada é escrito noutro sítio.

## Dependências (a instalar por ti)
- Python 3.12 (só biblioteca padrão) e bash (Git Bash no Windows). No Windows define `PYTHONUTF8=1`.
- CLI `claude` (Claude Code) com sessão iniciada: é o único gerador configurado.
- Um extractor de transcrições à tua escolha, p.ex. `yt-dlp` (não vem incluído).
- Sem dependência de outras skills; os testes `test_fact_check.py` e `test_finalize_doc.py` correm no Windows (`test_generate_deep_doc.py` só em Linux/macOS).

## Conteúdo
`SKILL.md` · `scripts/` (dedup, gerador, fact-check, finalize, poller, testes) · `templates/` · `references/`.
