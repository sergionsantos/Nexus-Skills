# Playbook SYNTHESIZE — de findings a N melhorias

> Objectivo da fase: transformar 30-60 factos soltos em N melhorias-cluster com quotas das 3 fontes. É a fase mais "de julgamento" — por isso está aqui reduzida a procedimento mecânico com pontos de decisão explícitos.

## Passo 1 — Pool único de findings

Junta TODOS os findings (GROUND + todos os agentes) numa lista única. Cada linha: `finding · evidência · lente de origem`. Não filtres ainda — filtrar cedo perde clusters.

## Passo 2 — Etiquetar cada finding: P / L / T

Perguntas-teste (aplica por ordem; primeira que der SIM decide):

- **P (Partido):** "Se nada mudar, isto falha ou já está a falhar?" — app down, bug de invalidação, secrets demo, zero error boundaries. Inclui *vai partir* (divergência que rebenta no próximo arranque).
- **L (Latente):** "O custo de construir já foi pago e falta só expor/colher?" — tabela com RLS sem UI, campo filtrável sem picker, config sem página. Teste mecânico: existe no schema/backend E grep-zero na UI.
- **T (Transformação):** "Isto muda QUEM usa o sistema ou PARA QUÊ?" — novo tipo de utilizador (agentes AI via MCP), nova categoria de uso. Perguntas-guia para gerar T (não esperes que venha dos agentes — no traço, a transformação nasceu aqui, na síntese):
  - Que utilizador/uso este sistema ainda não serve mas devia, dado o ecossistema do dono?
  - O que é que o dono faz hoje FORA do sistema que devia acontecer dentro?
  - Se este sistema falasse com os outros sistemas do dono, o que ficava possível?
  - **Fonte concreta de T (calibração 2026-07-20, serviço Node/MCP):** lê as checklists/wraps FECHADAS (`phase: complete`) do próprio projecto à procura de capacidades já validadas mas nunca embarcadas na superfície pública (ex.: `synth_answer` validado em eval, nunca promovido a MCP tool). Não é grep — é leitura de vereditos; rende T com evidência de que o custo de validação já foi pago.

Finding que não é P, L nem T → provavelmente ruído; marca DESCARTE com razão de 3 palavras.

## Passo 3 — Clustering (o hábito que separa relatório rico de lista rasa)

**Cada melhoria numerada é um cluster temático, não um finding.** Procedimento:
1. Agrupa findings que partilham tema E seriam resolvidos pelo mesmo tipo de trabalho (ex.: due_date + estimate + templates + initiatives = todos "schema pronto sem UI" = 1 melhoria).
2. Dentro do cluster, ordena sub-itens por rácio ganho/diff; o de maior alavancagem lidera a Acção.
3. Cluster de 1 finding só sobrevive se for grande sozinho (app down = cluster de 1, e é #1).
4. Anti-teste: se dois clusters teriam a MESMA acção, funde-os; se um cluster precisa de duas acções sem relação, parte-o.

Resultado esperado: N slots a conter 2-4× N findings (traço: 7 slots ≈ 20+ achados).

## Passo 4 — Scoring e selecção dos N

Para cada cluster, estima em escala grossa (não finjas precisão):
- **Ganho** (1-3): 3 = destrava uso/produto; 2 = melhora uso diário; 1 = QoL
- **Diff** (1-3): 1 = horas; 2 = 1-3 dias; 3 = >3 dias
- **Rácio** = ganho/diff — ordena por ele DENTRO do contexto real do dono (single-user em rede instável sobe error-handling; sistema que vai receber agentes sobe API+escala — o contexto pode mover 1-2 posições e deves dizê-lo no racional)

Quotas obrigatórias nos N seleccionados: **≥1 P, ≥1 L, ≥1 T.** Se não tens T, volta às perguntas-guia do passo 2 — quase nunca "não há"; há "não procurei".

**N não se enche honestamente?** Entregar N-1 sólidos vence encher com um fraco ("evidência ou não entra" > bater o número) — MAS o descarte do último candidato tem de ficar ESCRITO no relatório (sub-secção `### Nota de calibração — porquê N-1` dentro da secção de verificação: candidato, evidência que tinha, razão do descarte). Prometer a nota no cabeçalho e não a escrever é referência forward quebrada — foi um MAJOR real apanhado em review (calibração 2026-07-20). Usa `###` (não `##`) para não quebrar a contagem do check mecânico.

## Passo 5 — Registo de descartes (adição de método; não vem do traço)

1 linha por cluster descartado: nome + razão ("sem evidência de dor", "ganho não cabe numa frase", "prematuro antes de #1"). Vai para notas da checklist, não para o relatório — mas tem de existir: descarte não registado é descarte não pensado.

## Erros típicos

| Erro | Correcção |
|---|---|
| N melhorias = os N findings mais gritantes | Passo 3 — clustering primeiro, selecção depois |
| Tudo P (relatório = QA) | Quotas do passo 4; L é onde vive o maior ganho/diff |
| T inventada sem âncora no ecossistema | Perguntas-guia + evidência de desconexão real (ex.: tasks em markdown fora do gestor de tarefas) |
| Score com falsa precisão (7.3/10) | Escala 1-3; o racional em texto vale mais que o número |
| Descartar em silêncio | Passo 5 — 1 linha por descarte |
