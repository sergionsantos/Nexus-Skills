# Independent Code-Review CALL — orquestrador ↔ revisor playbook

> Trigger: o prompt do orquestrador começa com "CALL N (revisor, code-review INDEPENDENTE)" ou equivalente. Lens ≠ autor (o prompt de implementação foi outro). Lens reporta, NÃO corrige. Aprovação de fix é do owner.

## 1. Inputs canónicos (ler integralmente)

1. **Brief do orquestrador** — lista explícita de ficheiros no diff staged (path + tipo NEW/M + hunk count esperado). Tomar como scope: se um finding quiser tocar em ficheiro fora da lista, é scope-creep.
2. **ISA-B** — path canónico `.isa/ISA-<slug>.md` na root do project. NÃO reler se o briefing diz "tu conheces". Reler só se for ambíguo.
3. **`git diff --cached --stat`** — confirmar números do brief contra o real (findings sobre staging sujo são válidos).
4. **`git status -sb`** — detectar ficheiros unstaged (não fazem parte do staged diff — nota-los como INFO, não culpar).
5. **ISA-CALLx (audit trail)** — ler SE existir e referenciar decisões já tomadas. Se headline diz "STOP — trabalho já feito", respeitar (CALL 3 lesson).

## 2. Verificações obrigatórias ANTES de categorizar findings

Correr estas 4 verificações em paralelo **antes** de escrever qualquer finding. Falha nelas = findings inválidos.

```bash
# (a) typecheck verde — pré-requisito para confiar em findings
cd <repo> && pnpm --filter <affected-pkg> typecheck 2>&1 | tail -20

# (b) schema real vs tipo do código consumidor (drizzle Date/string)
grep -A 5 "pgTable.*<table>" packages/db/src/drizzle/schema/schema.ts

# (c) duplicação de helpers que pareciam ser extraídos para util partilhado
rg -l "<helperName>" --type ts

# (d) callers reais e schema-alignment dos tipos exportados
rg "<exported-symbol>" --type ts
```

Output esperado:
- (a) `0 erros` — se ≥1, parar e reportar "typecheck broken, fix primeiro".
- (b) confirmar `mode:'string'` em colunas que código trata como `Date`.
- (c) helper extraído deve ter ≤1 ocorrência (a nova, no util). >1 = refactor incompleto.
- (d) lista de consumidores — coerência de tipo neles é o ISC real.

## 3. Taxonomia de findings (frozen)

| Tier | Significado | Bloqueia merge? | Obriga patch no PR? |
|---|---|---|---|
| **BLOCKER** | Correcção silenciosamente partida (type mismatch, contract breach, will-break-at-runtime) | Sim | Sim |
| **MAJOR** | Smell substancial, latent bug, ou fragility arquitectural (DDL-in-tx, write-only API pública, shadow vars) | Sim (recomendado) | Sim |
| **MINOR** | Code smell local, naming, comments órfãos, contrato opcional | Não | Patch no follow-up |
| **NIT** | Cosmético (typos, dotfiles outliers, scripts redundantes em package.json) | Não | Pode batch no follow-up |

**Regra de escalação**: um finding é BLOCKER se, ao rodar o fluxo em runtime em vez de compile-time, falharia. Se falha em compile-time já é conhecido e skipável = MINOR.

## 4. Formato de output (imutável pelo owner)

```
**FINDINGS**

[BLOCKER] B-N
file: <path>, line <N>
explain: <1 linha — o schema diz X, o código diz Y, porquê conflita>
fix: <1 linha — a correcção concreta>

[MAJOR] M-N
…

**VEREDICTO: <APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION>**

Justificação: <2-3 linhas>.
```

Max 2000 tokens totais. Se exceder, cortar NITs (não bloqueantes) ou mover para `references/<call>-findings.md`.

## 5. Regras comportamentais (não negociáveis)

1. **Não corrigir nada.** Patches são propriedade do implementador (ou dono do branch). Aplicar fix durante review = contamination do lens.
2. **Não fazer perguntas especulativas.** Findings devem ser binários: "schema diz A, código diz B". Se não tens dados, NÃO categoriza.
3. **Não expandir scope.** Se a review descobre um problema num ficheiro fora da lista do brief, é **INFO** no fim do report, não finding principal. O owner decide se quer abrir nova CALL.
4. **Não negociar o veredicto.** REQUEST_CHANGES é o veredicto natural quando há ≥1 BLOCKER ou ≥2 MAJOR. NEEDS_DISCUSSION é para ambiguidade que o owner pode esclarecer (ex: ISA referenciada que não foi confirmada como existente).
5. **Lente independente ≠ melhor lente.** O implementador pode ter razão e tu podes estar errado. Findings são hipotéticos até o owner os validar. Tom = "these are potential issues, decide".
6. **Tudo verificado ou explicitamente UNVERIFIED.** Se não correste uma verificação, di-lo: "verify: NOT RUN" é mais útil do que silêncio.

## 6. Trigger de patch tool

Único caso em que deves aplicar patch durante review: quando o typecheck falha E a falha é 1-liner que resolves o tipo (ex: `as any` → `as unknown as X`). Aplica + re-verifica typecheck + reporta como "applied-on-the-fly fix for N, others unchanged". Tudo o resto fica para o owner.

## 7. Relação com ISA-CALLx (audit trail do implementador)

O implementador muitas vezes escreve `.isa/ISA-CALLx-<topic>.md` durante a CALL de implementação, com matriz spec-vs-realidade (ex: CALL 3 mostrou que o util já existia com API divergente). **Lê esta ISA antes de duplicar análise** — pode já ter documentado divergências que aparecem como findings no teu lens. Se a sua análise bate com a tua, cita-a em vez de re-analisar.

## 8. Checklist final antes de enviar

- [ ] Veredito presente e claro (1 linha)
- [ ] Cada finding tem file + line + 1-linha explain + 1-linha fix
- [ ] Tier alinhado com §3 (não inventar "CRITICAL" / "TRIVIAL")
- [ ] Nenhuma pergunta especulativa
- [ ] Nenhum patch aplicado (excepto §6)
- [ ] Cabe em 2000 tokens
- [ ] Não duplica análise do ISA-CALLx do implementador
- [ ] Relembro ao owner o que ele precisa decidir (se aplicável)

## 9. Caso de estudo: CALL 5 (2026-07-01, Task B)

- **Context**: review de `feat/vendor-ingest-activities-first`, 5 ficheiros staged, util novo + 3 callsites refactor + 2 TODOs documentando gap sistémico multi-tenancy-sprint.
- **Findings emitidos**: 1 BLOCKER (Date↔string drizzle mode mismatch — passou typecheck por overload permissivo, vai estoirar em runtime), 3 MAJOR (write-only counter na API pública do util, DDL dentro de tx com INSERTs anteriores, shadow var com nome igual em 2 escopos), 4 MINOR, 3 NIT.
- **Veredicto**: REQUEST_CHANGES (1 BLOCKER + 3 MAJOR não corrigíveis sem decisão do owner).
- **Surpresa útil**: a descoberta B-1 só foi possível porque (a) `pnpm typecheck` passou e (b) `grep "mode:'string'" schema` foi correuno 2-verificações paralelo. Se tivesse julgado só com "tipo parece OK", B-1 escapava.
- **Não-encontrado** mas esperado: race conditions de worktree (C-3) — branch nova em worktree não partilhado, então não aplicável. Notei como ausente, não como problema.
