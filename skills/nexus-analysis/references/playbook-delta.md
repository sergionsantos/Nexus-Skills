# Playbook DELTA — re-análise de um projecto já analisado

> Objectivo: 2ª (ou N-ésima) análise do MESMO projecto sem re-descobrir tudo do zero. O que muda: o GROUND ganha um passo de reconciliação contra a análise anterior, o EXPLORE encolhe para as zonas que mudaram + 1 lente NOVA, e o relatório declara explicitamente o destino de cada melhoria antiga. O que NÃO muda: standard de evidência, 3 fontes, review independente. Caso-âncora: uma análise de 7 melhorias seguida, no dia seguinte, de uma re-análise com 3 milestones já aplicados e 4 pendentes — uma re-análise a frio teria re-gastado 4-5 agentes para redescobrir 3 milestones já fechados.

## Quando usar delta vs análise a frio

| Situação | Modo |
|---|---|
| Existe relatório anterior deste skill + checklist/LOG da execução | **Delta** |
| Relatório anterior existe mas >6 meses OU o sistema mudou de stack/arquitectura | A frio (o mapa antigo mente mais do que ajuda) |
| Análise anterior foi de outro método (audit externo, review avulsa) | A frio, mas lê o artefacto antigo como fonte documentada do GROUND |
| Dono pede lente NOVA que a análise anterior não cobriu | Delta + essa lente como a lente NOVA obrigatória |

Regra de fronteira: delta exige o RELATÓRIO anterior + rasto de execução (checklist `phase:`, LOG, commits). Sem rasto de execução, não sabes o que foi aplicado — corre o passo 1 na mesma, mas espera classificar quase tudo como "estado desconhecido" e o custo aproxima-se da análise a frio.

## Passo 1 — Reconciliação: destino de cada melhoria antiga (20-30 min)

Para CADA melhoria do relatório anterior, determina o estado com evidência viva (não com o LOG — o LOG é claim, o código/runtime é veredicto):

| Estado | Critério | Evidência exigida |
|---|---|---|
| **APLICADA** | Execução registada E verificação viva confirma | commit/checklist + check vivo (grep do símbolo novo, curl, teste a passar) |
| **PARCIAL** | Alguns sub-itens do cluster aplicados | lista sub-item a sub-item (o cluster de 5 pode ter 3 feitos) |
| **NÃO APLICADA** | Sem rasto de execução | grep-zero do que a Acção mandava criar |
| **OBSOLETA** | O contexto mudou e a melhoria já não faz sentido | 1 linha de racional (ex.: feature removida, standard mudou) |
| **REGREDIDA** | Foi aplicada e voltou a partir | evidência da aplicação + evidência da regressão — candidato automático a melhoria de topo na nova análise |

Output: **tabela de reconciliação** (vai inteira para o relatório novo). Exemplo do caso-âncora:

| # antiga | Melhoria | Estado | Evidência |
|---|---|---|---|
| 1 | App down + JWT | APLICADA | M30 fechado no checklist; `curl :<porta>/login` → 200 |
| 3 | Error boundaries/offline | APLICADA | M32 fechado; `find src/app -name "error.tsx"` → 3 hits |
| 4 | Testes sync layer | NÃO APLICADA | M33 pendente; `ls src/lib/sync/*.test.ts` → vazio |

Predict-then-run mantém-se: antes de cada check escreve o esperado a partir do LOG — divergência LOG-vs-vivo é finding (classe 1-3 do playbook-ground, tabela igual).

## Passo 2 — GROUND abreviado (10-15 min)

Não repitas o inventário completo. Verifica só:
1. Os claims do relatório anterior que a reconciliação marcou APLICADA (já feito no passo 1 — não dupliques).
2. Factos de ambiente da análise anterior que têm data (portas, versões, processos) — ambiente é estado vivo, re-check obrigatório.
3. Docs novos desde a análise anterior (`ls -lt` nos dirs de docs/checklists/wraps; `git log --oneline --since=<data-análise>` se é repo).

## Passo 3 — EXPLORE dirigido (2-3 agentes, não 4-5)

- **1-2 agentes nas zonas QUENTES**: dirs/ficheiros tocados desde a análise anterior (`git diff --stat <commit-da-análise>..HEAD` dá a lista; sem git, mtime). Lente: "o que a execução das melhorias antigas partiu ou deixou a meio" — fixes introduzem regressões (observado no caso-âncora: fix de review introduziu edge-case novo apanhado na ronda 2).
- **1 agente com lente NOVA** (ângulo que a análise anterior NÃO usou ou usou fraco — ex.: se a anterior era código-pesada, manda integração/ecossistema). Anti-cegueira: o delta herda os pontos cegos do mapa antigo; a lente nova é o antídoto — não é opcional. **Nota de vocabulário:** "fresh/independente" fica reservado para o REVISOR do VERIFY — este agente de exploração NÃO conta como review (desvio nº1 dos modelos médios).
- **NUNCA** re-correr as 4-5 lentes completas sobre zonas não tocadas — é o desperdício que este modo existe para evitar. Excepção: reconciliação encontrou ≥2 REGREDIDAS → o sistema está a degradar por baixo dos fixes; escala para análise a frio. (O threshold "≥2" é adição de método, não do exemplo trabalhado — ajusta com uso real.)

## Passo 4 — SYNTHESIZE com regras extra

Igual ao playbook-synthesize (3 fontes, clustering, quotas), mais:
- **PARCIAL/NÃO APLICADA não transita automaticamente.** Re-avalia contra o contexto ACTUAL: a prioridade de há 3 meses pode ter caído (então relega ou marca OBSOLETA com racional) ou subido (então cita a evidência nova). Copiar a lista antiga para a frente é o anti-padrão nº1 do delta.
- **REGREDIDA entra no topo** salvo racional explícito em contrário — regressão prova que a zona é frágil E importante.
- N pode ser menor (5 em vez de 7) se o sistema encolheu de superfície problemática — declara o N escolhido e porquê no SCOPE.

## Passo 5 — STRUCTURE/VERIFY

Template normal + **secção "Reconciliação com análise de {data}"** (a tabela do passo 1) logo a seguir a "Estado real verificado" — o título TEM de começar por `## Reconciliação` (o `verify-report.sh` conta-a por esse nome; esperado passa a N+3+resumo+recon automaticamente). VERIFY igual no resto (check mecânico + review fresh) com um item extra para o revisor: **spot-check de 2-3 estados da tabela de reconciliação** (é a secção onde o autor mais confia no LOG em vez do vivo — desvio previsível).

## Erros típicos nesta variante

| Erro | Correcção |
|---|---|
| Copiar melhorias NÃO APLICADAS para a frente sem re-avaliar | Passo 4 — prioridade re-justificada no contexto actual ou corta |
| Confiar no LOG/checklist para "APLICADA" sem check vivo | Passo 1 — LOG é claim; grep/curl/teste é veredicto |
| Delta sem lente NOVA (herda pontos cegos do mapa antigo) | Passo 3 — 1 lente NOVA obrigatória |
| Re-explorar tudo "para garantir" | Passo 3 — zonas frias ficam frias; ≥2 REGREDIDAS é o único gatilho de escalação |
| Esquecer a tabela de reconciliação no relatório | Passo 5 — secção obrigatória, o revisor spot-checka |
