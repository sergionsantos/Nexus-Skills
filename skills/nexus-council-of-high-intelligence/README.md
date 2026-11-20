# nexus-council-of-high-intelligence

Conselho de 18 pensadores fixos (Sócrates, Feynman, Sun Tzu, Ada Lovelace, Taleb, Kahneman, Munger, Meadows, Torvalds, Rams, …) que debate uma decisão real em rondas: análise cega, contra-interrogatório anónimo, posição final, votação ponderada pela confiança e veredicto estruturado (critérios de falha, próximo passo, relatório de minoria). Cada membro corre como subagente independente.

## Quando usar
Decisões com risco material, valores em conflito, evidência incompleta ou irreversibilidade ("convoca o conselho", "stress-test a esta decisão"). Não serve para factos nem escolhas baratas e reversíveis.

## Diferença face a `nexus-persona-council`
- Esta skill: **membros fixos** (os 18 em `agents/`), já incluídos, sem preparação; protocolo único e rígido.
- `nexus-persona-council`: **personas definidas por ti** (ficheiros `LENS.md` à tua escolha, p.ex. um especialista concreto do teu domínio); modos solo/counsel/battle/lens.
- Pensadores históricos genéricos → esta; "o que diria a pessoa X" → a outra.

## Instalação
Copia (ou faz symlink de) esta pasta para `~/.claude/skills/nexus-council-of-high-intelligence` ou `~/.codex/skills/nexus-council-of-high-intelligence`. Abre sessão nova.

## Dependências
- Capacidade de lançar subagentes em paralelo. Nada mais; não precisa de serviços externos.
- Opcional (não usado por omissão): `configs/` e `scripts/detect-providers.sh` (bash + perl) para encaminhar membros para outros fornecedores de modelos.

## Origem e licença
Projecto `0xNyk/council-of-high-intelligence` (MIT, © 2026 nyk) — ver `LICENSE`. `references/protocol.md` é o protocolo derivado, com os caminhos adaptados a esta pasta e duas modificações locais (revisão de objecções suportadas no STEP 4 e o prompt da Ronda 2); os `configs/provider-model-slots*.example.yaml` reflectem essas modificações. Os 18 agentes e `detect-providers.sh` são idênticos ao original.
