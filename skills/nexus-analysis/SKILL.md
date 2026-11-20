---
name: nexus-analysis
description: >-
  Playbook de análise de melhorias para um sistema/app/projecto EXISTENTE: produz N melhorias substanciais priorizadas (default 7), cada uma com evidência ficheiro:linha, cobrindo três fontes — o que está partido, o valor latente (construído mas não exposto) e as transformações (o que muda a categoria do produto). Usar quando o pedido é "encontra N melhorias", "analisa a app e diz o que melhorar", "como tornar X extraordinário", "nexus-analysis". NÃO usar para: debug de um bug concreto (systematic-debugging), plano de build executável passo-a-passo (nexus-plan-spec — a análise ALIMENTA o plano, não o substitui), review de diff/PR (code-review), audit de repo externo, triagem de feature requests de clientes.
version: 1.0.0
status: active
---

# nexus-analysis — análise de melhorias que vai além do que está mal

> **Contrato:** transforma "melhora isto" num relatório de N melhorias priorizadas onde cada claim tem evidência verificável, a ordem tem racional explícito, e uma revisão independente correu antes de o chamar final. Custo: 4-5 agentes de exploração + 1-2 passes de review (revisão corrige, passe fresh confirma); horas, não minutos. Origem: destilado de análises reais de aplicações (casos internos do autor, não incluídos nesta skill); nelas a revisão independente apanhou erros que o autor tinha por certos.

## Operating mode (obrigatório para qualquer modelo que execute isto)

- **Evidência ou não entra.** Cada claim aponta para `ficheiro:linha`, output de comando, ou grep. **Grep-zero é evidência** ("0 hits de `due_date` em issue-detail.tsx" prova ausência de UI). "Parece que falta X" sem grep não entra no relatório.
- **Docs mentem; runtime também sabe mentir.** Estado documentado (LOGs, READMEs, backlogs) é hipótese até confirmação viva. Mas runtime só é evidência depois de confirmar **identidade, freshness, semântica e exit status** — falsos-verdes típicos: gate que imprime FAIL e sai 0; porta que responde 200 com o SERVIÇO ERRADO no payload; mtime recente com dados antigos dentro. Divergência doc-vs-realidade é finding de topo; falso-verde do runtime também.
- **Predict-then-run nos checks:** escreve o esperado (contagem, exit code) antes de correr.
- **Não arredondar para cima:** claim não-verificado fica etiquetado como tal, nunca promovido a facto.

## Custo (para o dono decidir se vale a pena)

- **Análise a frio** (ordem de grandeza observada em casos internos do autor, não incluídos): 1 sessão orquestradora + 4-5 agentes EXPLORE (paralelos) + 1 agente revisor fresh + 0-1 re-review = **6-8 agentes**, wall-time 2-4h, tokens ordem de grandeza "sessão longa" (centenas de k). GROUND/SYNTHESIZE/STRUCTURE correm na sessão orquestradora.
- **Re-análise (delta)** (observado num caso interno do autor, não incluído): reconciliação + lentes delegadas + reviews até convergir = **<1h wall-time** para um sistema médio. Nesse caso a REVIEW custou mais que o explore (7 passes fresh até zero-findings; os 6 primeiros com findings reais) — orçamenta a convergência, não só a análise. Ver `references/playbook-delta.md`.
- Executor solo sem subagentes (modelo único): mesmas fases sequenciais, wall-time maior. A review independente não desaparece: ou corres o prompt do revisor numa sessão nova/segundo modelo (ver passo 5), ou o relatório fica `mechanically-verified` / "por rever" em vez de "final".

## Workflow

> **Projecto já analisado antes por este skill?** Usa o modo delta — `references/playbook-delta.md` (reconciliação do relatório anterior + explore dirigido às zonas que mudaram + 1 lente fresh). O workflow abaixo é a análise a frio.

> **Cada fase tem um playbook detalhado em `references/playbook-<fase>.md`** — com prompts prontos, comandos, exemplos anotados do exemplo trabalhado e tabela de erros típicos. **Lê o playbook da fase ANTES de a executar** (obrigatório na 1ª utilização do skill; depois, sempre que hesitares). O resumo abaixo é o mapa, não o território. **Caso completo fase-a-fase (com proveniência marcada): `references/worked-example-task-tracker.md`** — lê-o uma vez antes da 1ª análise. **Scripts:** `scripts/scaffold.sh` (arranque: checklist+esqueleto) e `scripts/verify-report.sh` (check mecânico) — testados com negative control.

### 0. SCOPE (2 min)
Fixa: N melhorias (default 7 — força selecção; 3 é raso, 15 é lista de compras), superfície (que dirs/stack/docs contam), e o **standard de comparação** se existir (uma app de tarefas compara-se a um produto de referência maduro; um CRM compara-se ao seu spec). Superfície ambígua → pergunta ao dono AGORA (1 pergunta), não a meio. Abre checklist de controlo com ISCs binários (ISC = critério de conclusão: uma condição que só pode estar cumprida ou não, sem meio-termo, e se marca só com evidência) — ex.: análise cobre lentes X, N recomendações com problema+evidência+acção+impacto, review independente corrida.

### 1. GROUND — estado real vs estado documentado
Lê os LOGs/docs do projecto E confirma ao vivo o que eles afirmam (processos, portas, configs, migrações). Output: secção "Estado real verificado" no topo do relatório com (a) o que está de facto a correr, (b) onde os docs estão desactualizados, (c) divergências críticas novas. Este passo costuma render o finding #1 (ex.: app em baixo + segredo JWT desalinhado) antes de qualquer agente de exploração arrancar. **Playbook: `references/playbook-ground.md`** (tabela claim→check, comandos por tipo de claim, 3 classes de divergência).

### 2. EXPLORE — multi-lens paralelo
Lança **4-5 agentes read-only em paralelo** (Explore), cada um com uma lente DIFERENTE — lentes distintas encontram o que redundância não encontra. **Sem subagentes, ou delegação a falhar/timeout → modo EXPLORE-SOLO** (lentes sequenciais + tabela-prova; pre-flight de delegação antes do fan-out — ver playbook-explore):

| Lente | Procura |
|---|---|
| Arquitectura/código | Camadas críticas sem testes, bugs latentes, estado derivado frágil, trilhas de fixes em comentários (= fragilidade), padrões N+1/round-trips |
| Infra/deploy/segurança | Secrets, persistência de processos, configs divergentes, RLS/auth, o que parte num reboot |
| Gap funcional vs standard | **Schema/backend pronto sem UI** (valor latente nº1), features do standard em falta, capacidades enterradas |
| UX/robustez | Error states, offline, loading, mobile, consistência de design, operações-de-dono que exigem SQL |
| (opcional) Integração/ecossistema | Como é que o sistema serve os OUTROS sistemas do dono — ajuda a fonte-3 do passo 3, mas a transformação nasce na síntese, não exige esta lente |

Contrato de output por agente: findings com `ficheiro:linha`, greps com resultado (incl. zeros), sem recomendações — só factos. Máx 5 agentes por wave; spot-check de 2-3 claims por report à chegada. **Playbook: `references/playbook-explore.md`** (prompt template copy-paste + checklist concreta por lente) **+ `references/explore-checklists-by-stack.md`** (greps prontos: Next/Supabase, API Python, serviço Node/MCP, launchd macOS).

### 3. SYNTHESIZE — três fontes de melhoria (o coração do método)
Gera candidatos das **três fontes** — quem só olha para a 1ª faz QA, não análise:

1. **Partido** — o que falha ou vai falhar (env divergente, bug de invalidação, zero error boundaries).
2. **Latente** — o que já está construído mas não exposto (tabelas com RLS sem UI, campos filtráveis sem picker). É onde vive o maior rácio ganho/diff: o custo já foi pago, falta colher.
3. **Transformação** — o que muda a categoria do produto no contexto do dono (gestor de tarefas → superfície programável para agentes via API/MCP). Pergunta-guia: "que utilizador/uso este sistema ainda não serve mas devia?"

**Cada melhoria numerada é um *cluster* temático de sub-findings relacionados, não um único item** — agrupa (ex.: todos os campos schema-sem-UI numa só melhoria; toda a dívida admin/design noutra) e ordena os sub-itens internos por rácio ganho/diff, com o de maior alavancagem a liderar a Acção. É isto que deixa 7 slots conter ~20 achados em vez de 7 itens rasos.

Selecção dos N: por **alavancagem no contexto real** (single-user em rede instável valoriza offline-handling; sistema que vai receber agentes valoriza API+escala), não por best-practice genérica. Descarta: nice-to-haves sem evidência de dor, refactors sem ganho visível, tudo o que não couber numa frase de impacto — 1 linha de razão por descarte. **Playbook: `references/playbook-synthesize.md`** (etiquetagem P/L/T com perguntas-teste, procedimento de clustering, scoring 1-3, quotas ≥1 por fonte).

### 4. STRUCTURE — formato do relatório
Usa `templates/report-template.md`. Por melhoria: **Problema** (bullets com evidência) → **Acção** (passos concretos, ordenados por rácio ganho/diff, com a opção mínima nomeada — "`<input type=date>` chega") → **Impacto** (porquê importa + esforço). Depois: **tabela de ordem com racional por posição** (1 linha cada) + sequência prática. Regras de ordenação observadas no exemplo trabalhado: pré-condição primeiro (app tem de correr) · maior ganho/diff cedo · seguro-de-vida (testes) antes de mexer na camada que protege · transformação depois do núcleo estar seguro · coerência/QoL no fim. **Trade-off deliberado = nota explícita** ("quem preferir rigor máximo troca #4 para segundo lugar") — mostrar o julgamento, não escondê-lo. **Liga as melhorias entre si:** dependências e reforços mútuos por número ("#5 herda um núcleo testado por #4"; "com #2, agentes criam issues padronizadas") — a sequência prática nasce daí. **Playbook: `references/playbook-structure.md`** (item exemplar anotado linha-a-linha, regras por campo, heurísticas de ordem por ordem de aplicação).

### 5. VERIFY — mecânico + independente
1. **Check mecânico** com predição: N+3 secções `##`, N problemas, N acções, N impactos, exit 0 (`grep -c` por marcador).
2. **Review independente** (regra de revisão independente, lente ≠ autor): agente NOVO pós-relatório — os agentes de exploração e os teus próprios spot-checks NÃO contam (auto-confirmação; desvio nº1 observado em modelos médios). Sessão/agente fresh spot-checka os claims mais citados contra o código real — paths, linhas, greps-zero, estado vivo. Findings → corrige e re-verifica. Só depois de **zero findings** o relatório é "final".
   **Sem subagentes?** Duas saídas: (a) abre uma sessão nova (ou outro modelo) sem a tua conversa, cola VERBATIM o prompt do revisor de `references/playbook-verify.md` (secção «Prompt pronto para o revisor») com o path do relatório e do código, e traz os findings de volta; (b) se não houver essa possibilidade, não tickes o ISC: marca o relatório `mechanically-verified` ("por rever — pedir review independente") em vez de `final`, e di-lo no fecho. A secção `## Verificação independente` tem de existir na mesma (o `verify-report.sh` exige-a) e deve dizer «por rever».
3. Fecha checklist (ISCs ticked com evidência), commit+push se o projecto é repo, session-wrap se o tema fecha. **Playbook: `references/playbook-verify.md`** (script mecânico pronto com negative control, prompt pronto para o revisor, regras de contaminação, loop de convergência, DONE-language).

## Heurísticas de julgamento (o que separa isto de uma lista)

- **Rácio ganho/diff** manda na ordem dentro de cada melhoria e entre melhorias.
- **Histórico é evidência:** trilha de fixes em comentários (FIX F3/F14/…) sem testes = camada frágil → melhoria "seguro de vida".
- **Contexto > genérico:** cada impacto justifica-se no ambiente REAL do dono, não em abstracto.
- **Cada melhoria cabe numa frase de impacto.** Se precisa de parágrafo para justificar, é fraca — corta.
- **Esforço sempre declarado** (horas/dias) — sem estimativa não há priorização honesta.
- **A análise alimenta o /nexus-plan (ou /nexus-plan-spec):** se o dono quiser executar, cada melhoria vira input de um plano — não detalhar steps de build aqui.

## Quando NÃO usar
- Bug concreto reportado → `systematic-debugging` (se instalada). · Plano executável de UMA melhoria → `nexus-plan` (com supervisão) ou `nexus-plan-spec` (executor sem juízo). · Review de diff → `code-review` (se instalada). · Ideias de negócio sem sistema existente → brainstorming/venture skills.

## Verificação (deste skill)
Relatório produzido passa: N melhorias com os 3 campos · ≥1 melhoria de cada uma das 3 fontes (partido/latente/transformação) · toda a claim com evidência · tabela de ordem com racional · review independente registada com resultado. Check mecânico (prova as secções obrigatórias, não só a contagem): `grep -c "^## " relatorio.md` = N+3 (+1 se o relatório incluir a secção opcional "Resumo executivo", +1 pela secção "Reconciliação" em modo delta — `scripts/verify-report.sh` já ajusta sozinho e falha duplicados) **E** `grep -c "^## Estado real verificado" relatorio.md` = 1 **E** `grep -c "^## Ordem" relatorio.md` = 1 **E** `grep -c "^## Verificação independente" relatorio.md` = 1 — um relatório sem a secção de review falha aqui, não passa verde.

## Anti-padrões

| Anti-padrão | Correcção |
|---|---|
| Só encontrar o que está partido | Passo 3 — forçar as 3 fontes; latente e transformação são o valor |
| Claims sem ficheiro:linha | Operating mode — evidência ou não entra |
| Confiar no LOG/README | Passo 1 — ground vivo primeiro; divergência é finding |
| Ordem sem racional | Passo 4 — tabela posição→porquê + trade-offs explícitos |
| Declarar final sem review fresh | Passo 5 — zero findings antes de "final" |
| Agentes redundantes (mesma lente ×4) | Passo 2 — lentes distintas, contrato só-factos |
| Relatório vira plano de build | Heurísticas — análise alimenta nexus-plan-spec, não o substitui |
| Anunciar artefacto ("checklist criada", "relatório escrito") antes do write confirmado no disco | Confirma o ficheiro existe (`ls`/output da própria tool) antes de o narrar como feito |

## Changelog
- v1.0.0: versão partilhável (adaptada de uma skill interna e saneada de contexto privado). Método inalterado: GROUND → EXPLORE multi-lente → SYNTHESIZE (3 fontes) → STRUCTURE → VERIFY (mecânico + revisão independente); modo delta; checklists por stack; scripts `scaffold.sh` e `verify-report.sh`; exemplo trabalhado anonimizado.
