# Product-Decision Gap Protocol (DIV-GUARD)

> Origem: sessão CRM 2026-07-01 (Task A — tenant_id scoping). O utilizador deu instrução condicional que funcionou como **gate explícito antes de PLAN**; documenta o protocolo geral.

## 1. O padrão

**Quando o utilizador diz coisas como:**

> *"Inspeciona X, e se Y for verdade, PARA e avisa-me; senão continua com Z"*

> *"Replica o padrão de A, MAS se A for single-tenant, avisa-me antes — nesse caso é decisão minha"*

> *"Investiga se B existe; se não existir, propomos juntos em vez de assumires"*

…o resultado do gate é **a decisão**, não um passo intermédio. O plano só começa a partir do "se não Y" — e essa porção está em aberto até o utilizador escolher.

## 2. O anti-pattern

Cumprir a letra avançando para Z mesmo quando Y disparou:

- "As rotas não têm scoping server-side, mas o utilizador disse 'replica o padrão' → replico o client-side, é o que está lá."
- "A documentação não fala de multi-tenancy, mas isso é decisão dele, eu implemento o caminho mais óbvio."

**Custo:** 1-2h de implementação revertida. **Custo de perguntar:** 30s.

## 3. O protocolo correcto (passo-a-passo)

### Passo 1 — Antes de PLAN, executar o gate

O gate do utilizador (inspecionar X, verificar Y) corre **dentro de OBSERVE/THINK**, não em PLAN. Se a verificação é um `read_file`/`grep`/`git log`/etc., faz essas leituras **antes** de escreveres a primeira linha do ISA ou do plano.

### Passo 2 — Se Y dispara, PARAR

Se Y é verdade (gate disparado), **não continues para PLAN**. Emite um relatório intermédio com:

1. **Paths verificados** (com line numbers) — prova de que inspeccionaste
2. **Estado real encontrado** — cita o TODO / comentário / linha que confirma Y (verbatim, não parafraseado)
3. **N leituras possíveis** — lista de opções, cada uma com trade-off visível (não escondas a "replicar o que está lá" como se fosse a única)
4. **Pergunta directa** — qual das N queres? (sugere a `clarify` tool se aplicável)

### Passo 3 — Se Y NÃO dispara, continuar normalmente

Gate passou (Y é falso) → PLAN com base no que viste → execução normal.

### Passo 4 — Registar o gap no ISA (se for E3+)

Mesmo que a decisão seja "parar e documentar", o trabalho foi substancial. Cria uma mini-ISA (E1) com:
- Goal: documentar o gap sistémico
- ISC: paths verificados + backlog entry + comentários `TODO` em código (se pedido)
- Phase: `complete` se for só registo (não implementação)

## 4. Caso de estudo — Task A

**Input do utilizador:**

> "Task A (SEGURANCA, comeca por esta) - tenant_id scoping: a rota apps/api/src/routes/activities.ts (GET /api/v1/activities) NAO filtra por escritorio/utilizador, qualquer user ve atividades de qualquer contacto (data-leak multi-tenant, 107 angariadores). Fix: scoping por tenant_id do user autenticado (ou so leads atribuidos), ve como outras rotas fazem auth/scoping p/ nao partir o padrao."

**O guard crítico que o utilizador adicionou (via `clarify`):**

> "GUARD CRITICO: se essas rotas NAO tiverem scoping algum (app toda single-tenant hoje), PARA e avisa-me ANTES de implementar - nesse caso o fix muda de forma (seria multi-tenancy global, nao so esta rota) e e decisao do dono."

**Execução do guard:**

1. `read_file` de `apps/api/src/plugins/auth.ts` → encontrei `TODO` explícito em `auth.ts:152-154`: *"single-tenant assumption valid only for the pilot — replace with explicit office membership before multi-tenant"*. **Gate disparou.**
2. `grep` em `leads.ts` e `contacts.ts` → confirmei que o "padrão" é `officeId` como filtro **client-side via query string**, não server-side forçado. Gap sistémico confirmado.
3. **PAREI**. Emiti relatório com paths verificados + 4 leituras (A replicar / B forçar / C documentar / D parar) + pergunta qual.

**Resposta do utilizador:**

> "Opcao D (parar Tarefa A) - correcto: NAO remendes so /api/v/activities (fix falso, inconsistente com as outras 6+ rotas single-tenant). O gap e SISTEMICO e o dono confirmou que o CRM sera multi-escritorio/multi-agencia -> multi-tenancy vira TAREFA PROPRIA (sprint dedicado, todas as rotas + auth.ts:152-154), a agendar."

**Resultado:** zero código de remendo escrito, sprint próprio agendado, gap sistémico documentado em ISA E1 (mini) com backlog entry. 1-2h de reversão poupada.

## 5. Quando é que o guard NÃO se aplica?

- **Decisão puramente técnica, sem trade-off de produto** (ex.: "extrai a função para util partilhado" — não há 4 leituras; é decisão de implementação, não de produto). Mas se o utilizador disse "decide tu", usa a regra de **documentar a decisão** (e não perguntar).
- **Conhecimento prévio sólido** (ex.: padrão da framework X é Y, o utilizador é especialista e confia no teu juízo). Mas isto é raro — e se tens dúvida, perguntar é mais barato.
- **Tarefa E1 trivial** (typo, rename). Não vale a pena sequer detectar o guard.

## 6. Forma rápida de detectar o pattern

Re-lê a última mensagem do utilizador. Procura por:
- "se X, PARA" / "se X, avisa" / "se X, pergunta"
- "MAS se Y for verdade" / "a menos que Y" / "excepto se Y"
- "GUARD CRÍTICO:" / "ATENÇÃO:" / "CUIDADO:"
- "decisão minha" / "decide tu mas confirma"
- "investiga antes" / "verifica primeiro"

Se encontrares, o teu próximo tool call **é o gate**, não o PLAN. Pula a tentação de fazer ambos em simultâneo.

## 7. Anti-pattern: o "fast path" do gate

Existe uma tentação racional de cumprir a letra avançando para a "default" e adicionar a pergunta no fim do output. **Não faças.** Razões:

1. O utilizador pode ter respostas diferentes conforme o que viu. A "default" pode ser a pior escolha.
2. Mesmo que a default seja a escolha correcta, perdeste a oportunidade de confirmar — e o utilizador perde a capacidade de corrigir cedo.
3. A regra de reporte fiel do nexus-discipline exige que a evidência do gate apareça **antes** da decisão, não depois.

## 8. Conflito com Rule 0 (revisão independente, SKILL.md §1)

Nenhum. O DIV-GUARD é uma **paragem para input do utilizador** (P1 gate), não uma revisão técnica por outro agente (P2 gate). São complementares: o DIV-GUARD decide SE o trabalho segue, o Rule 0 decide SE o trabalho já feito está limpo.

## 9. Changelog

- 2026-07-01 — v1 criado. Caso de estudo: scoping por tenant. Pattern abstraído para casos futuros.
- 2026-07-01 — v1.1 (refinamento, sem duplicação). Caso de estudo: Task B ingest activities-first (mesma sessão). O user usou o trigger-phrase *"replica o padrão, consistência > inventar"* sem dar um guard explícito. A correcção: tratar **"match the pattern" como um guard implícito em si mesmo**. Refactor: §5 "anti-pattern do 'match-the-pattern' automático" abaixo.

---

## 10. Refinamento v1.1 — "Match the pattern" é um DIV-GUARD implícito

**Problema observado na mesma sessão 2026-07-01 (Task B):** o user disse *"segue a abordagem da rota irmã /api/v1/leads"* e *"consistência > inventar modelo novo"*. Sem guard explícito tipo *"se a rota for single-tenant, avisa"*. Mas a regra §6 deste protocolo (detecção por trigger-phrase) **também funciona sem guard explícito** — o "match the pattern" é em si um sinal para inspecção prévia.

**Anti-pattern do "fast path":** ouvir "replica o padrão" → ir directo a implementar a versão mais óbvia do match. **Nunca fazer.** Razões:

1. O "padrão" pode ser um stub intencional (single-tenant, MVP, etc.). Match um stub = reproduzir o gap, não corrigi-lo.
2. O "padrão" pode estar em vias de ser substituído (TODO literal na zona).
3. O "padrão" pode ser inconsistente entre siblings (ex.: 3 rotas com 3 abordagens diferentes).

**Protocolo (mesmo que não haja guard explícito):**

1. **Inspecionar 2-3 siblings reais** — não o README, não o schema. `read_file` e cita o que encontras com `file:line`.
2. **Procurar TODO/FIXME/HACK** perto do pattern — se encontrares, o pattern é o problema, não a solução.
3. **Apresentar a opção-matrix (4 leituras)** via `clarify`:
   - (A) Match exactamente + aceita a limitação
   - (B) Força server-side + rejeita se não coincidir
   - (C) Documenta o gap + zero código
   - (D) Escalar para sprint dedicado
4. **Deixar o user escolher.** Se user já tinha implícito um default ("replica, claro!"), a `clarify` ainda assim serve para confirmar — não para atrasar.

**Trigger phrases** (match any → aplicar este protocolo, mesmo sem guard explícito):

- "replica o padrão de X" / "replicate the pattern"
- "faz como em /api/v1/leads" / "do what /api/v1/leads does"
- "consistência > inventar" / "match existing convention"
- "segue a abordagem da rota irmã" / "follow the sibling route's approach"
- "aplica o mesmo scoping/auth/pattern"

**Lição estrutural:** DIV-GUARD não é só "honrar o guard que o user deu" — é também "reconhecer que certas instruções são guards implícitos em si mesmas." Match-the-pattern é uma delas. Adicionar a §3 uma linha sobre a forma passiva do guard.

**Cross-ref:** esta sub-secção NÃO duplica §1-§8. O §1-§8 cobrem o caso "user deu guard explícito". §10 cobre "user deu instrução de match que é em si mesma um guard implícito" — situação diferente, mesmo protocolo.

**Caso de estudo v1.1 (Task B):**

> User: *"para a Task B (ingest activities-first) que FICA — para essa usa a opcao 3 (extrair projectActivitiesToRows para util partilhado em packages/db/src/utils/, chamado por backfill + ingest)."*

A instrução tem o trigger "segue a abordagem" implícita (o user diz "util partilhado" = replicar a estrutura de pastas do repo). Mas **não tem guard explícito sobre o backfill em si**. Resposta correcta: aplicar o protocolo, inspecionar `backfill-vendor-activities.ts` e o local onde o util vai viver, confirmar com o user antes de commitar. Foi feito (na verdade, o Task B era o caso que tinha **guard explícito** do Task A servido de precedente — foi o que activou o protocol). Resultado: 0 linhas de código tocadas, ISA com ISCs prontos, branch criado, subagente a correr, working tree dirty (esperado), push bloqueado. **Custo de ter perguntado vs. custo de ter assumido:** aqui foi 0 (a opção do user coincidiu com a default), mas o precedente do Task A justificou o custo preventivo.

**Versão completa do detector (§6 actualizado mentalmente):**

```
Procurar nas últimas 1-2 mensagens do user:
 1. "se X, PARA" / "se X, avisa" / "se X, pergunta"     → guard explícito (§1-§8)
 2. "replica o padrão" / "consistência > inventar"        → guard implícito (§10)
 3. "segue a abordagem" / "match the existing"            → guard implícito (§10)
 4. "decide tu" / "escolhe" / "à tua escolha"             → sem guard (vai; documenta a escolha)
 5. Nenhum dos acima                                    → sem guard (vai; documenta a escolha)
```

Linhas 1 + 2 + 3: **gate de inspecção prévia obrigatório.** Linhas 4 + 5: prossegue mas regista a decisão no ISA.
