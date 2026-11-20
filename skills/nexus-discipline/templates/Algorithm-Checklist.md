# Checklist — OBSERVE → THINK → PLAN → BUILD → EXECUTE → VERIFY → LEARN

> Usar durante execução de task E3+. Marcar cada checkbox à medida que avança.
> Âncora doutrinária: `nexus-discipline/SKILL.md` §1 (verificação) + `references/effort-and-process.md` (§1 calibração, §3 processo).
> Template: `nexus-discipline/templates/Algorithm-Checklist.md`

---

## ━━━ 👁️ OBSERVE ━━━ 1/7

### Intent Echo
- [ ] 🎯 INTENT escrito (reformulação do pedido numa frase)

### Effort Calibration
- [ ] Tier classificado (E1 / E2 / E3 / E4 / E5) — ver `Tier-Guide.md`
- [ ] Justificação do tier (1 frase)
- [ ] Cerimónia proporcional ao tier (não trazer E5 a um typo)

### Reverse Engineering
- [ ] Wants explícitos identificados
- [ ] Not-wanted explícitos identificados
- [ ] Not-wanted implícitos identificados
- [ ] Speed/urgency signal avaliado

### Preflight Gates
- [ ] Gate A (Diagnóstico/reprodução) — passou / não aplicável
- [ ] Gate B (Deploy/API/produção) — passou / não aplicável
- [ ] Gate C (Serviço externo) — passou / não aplicável
- [ ] Gate D (Research/fonte) — passou / não aplicável

### Reproduce-First Blocking Gate
- [ ] Se Gate A disparou: reproduzir antes de continuar

### ISA Scaffold
- [ ] ISA criada / actualizada em `.isa/ISA-[nome].md`
- [ ] `phase: observe` no frontmatter
- [ ] Goal definido
- [ ] Critérios ISC definidos (binários, testáveis, granulares, independentes)

### ISC Quality Check
- [ ] Cada ISC é binário (sim/não)
- [ ] Cada ISC é verificável por tool (não por "parece certo")
- [ ] Contagem de ISCs proporcional ao tier (ver Tier-Guide)

---

## ━━━ 🧠 THINK ━━━ 2/7

- [ ] ISA actualizada: `phase: think`

### Risk Analysis
- [ ] 🎲 RISKIEST ASSUMPTIONS documentados (o que o trabalho assume ser verdade)
- [ ] ⚰️ PREMORTEM completo (modos de falha que o trabalho tem de aguentar)
- [ ] ☑️ PREREQUISITES CHECK feito (bloqueios reais; arquitectura verificada — não modelo mental)

### ISC Refinement
- [ ] ISCs revistos após risk analysis; refinados se necessário

---

## ━━━ 📋 PLAN ━━━ 3/7

- [ ] ISA actualizada: `phase: plan`

### Planning Output
- [ ] 📐 SCOPE definido (depth / breadth / breadth-then-depth + justificação curta)
- [ ] 📐 SESSION definido (single / fix-now+redesign-later / combined)
- [ ] 📐 ROOT-CAUSE identificado ou marcado TBD

### Deliverable Manifest
- [ ] Se 2+ sub-tasks: manifest criado (D1..DN, uma linha por sub-task)
- [ ] Cada Dn: descrição curta com quote do pedido original

### Gates de Plano
- [ ] Delegation Gate: consigo fazer sozinho ou vale delegar?
- [ ] Parallelism Opportunity Scan: operações independentes identificadas
- [ ] Critic do plano (E4+): revisor independente reviu o plano/ISA antes de BUILD

---

## ━━━ 🔨 BUILD ━━━ 4/7

- [ ] ISA actualizada: `phase: build`

### Grounding (Disposição — Reflexo #3/#4)
- [ ] Estado real estabelecido (`git status`, grep do alvo, `ls`, run-state)
- [ ] Região exacta lida antes de editar (contexto fresco, não de há 5 passos)

### Root-Cause-at-Ingestion Checkpoint
- [ ] Onde entra o bad state?
- [ ] Fix no ponto de entrada resolve bugs similares a jusante?
- [ ] A tracing vai database-up ou display-down?

### Capability Invocation
- [ ] Cada capability/tool invocada via tool call real (texto-only não conta)
- [ ] Nenhuma capability phantom

---

## ━━━ ⚡ EXECUTE ━━━ 5/7

- [ ] ISA actualizada: `phase: execute`

### Inline Verification
- [ ] Cada ISC `[ ]` → `[x]` com evidência de tool no mesmo bloco
- [ ] Progresso actualizado no ISA após cada ISC fechado

### Forbidden Language Check
- [ ] Nenhum "should work"
- [ ] Nenhum "should be" / "expected to"
- [ ] Nenhum "a mudança está lá" sem Read/Grep
- [ ] Nenhum "done" sem evidência de tool
- [ ] Nenhum "no errors" sem o log real

### Re-Evaluate Loop (Disposição — Reflexo #2)
- [ ] Após cada lote de resultados: parei, li o que voltou, actualizei o plano

---

## ━━━ ✅ VERIFY ━━━ 6/7

- [ ] ISA actualizada: `phase: verify`

### Rule 1 — Live-Probe
- [ ] Artefactos user-facing verificados com tool probe (não "parece certo")
- [ ] Nenhum "should work" / "looks fine" / "tests pass" sem evidência

### Rule 0 — Gate de Revisão Independente (código não-trivial / unattended)
- [ ] Revisor independente (subagente `code-reviewer`/`verifier`) recebeu spec + output
- [ ] Findings BLOCKER/HIGH corrigidos
- [ ] Fixes re-verificados (podem introduzir regressões)
- [ ] Uma passagem de revisão devolveu zero findings no diff

### Advisor Calls (E3+, opcional)
- [ ] Advisor call antes de commit de abordagem (se E3+)
- [ ] Advisor call se stuck ou a divergir
- [ ] Advisor call após deliverable durável

### Cross-Vendor Audit (E4/E5, opcional)
- [ ] Segunda lente cross-vendor corrida após advisor

### Rule 3 — Conflict-Surfacing
- [ ] Conflitos advisor vs empírico resolvidos (max 2 re-calls)
- [ ] Se não resolvido após 2 re-calls: escalado ao utilizador

### Re-Read Check (gate final — todos os tiers)
- [ ] Última mensagem do utilizador re-lida verbatim
- [ ] Cada ask explícito enumerado vs o que foi shipped
- [ ] Nenhum `✗` bloqueia `phase: complete`

---

## ━━━ 📚 LEARN ━━━ 7/7

- [ ] ISA actualizada: `phase: learn`

### Learning Inventory
- [ ] 🧠 O que devia ter feito diferente?
- [ ] 🧠 O que faria um algoritmo mais esperto?
- [ ] 🧠 Os preflight gates dispararam? Foram úteis ou desperdício?
- [ ] 🧠 A Doutrina de Verificação disparou? Apanhou algo?

### Propagação
- [ ] Insight reusável e não-óbvio marcado como `[skill: <slug>]` candidato (se aplicável)
- [ ] Changelog entry criado no ISA (conjecture / refuted-by / learned)

- [ ] ISA actualizada: `phase: complete`

---

## ━━━ ESTADO FINAL ━━━

**Status:** [ ] In Progress / [ ] Complete  
**Tier:** E1 / E2 / E3 / E4 / E5  
**ISA path:** `.isa/ISA-[nome].md`  
**Data:** ___

---

> **Linguagem de estado canónica:**
> - *"implementado, happy-path testado, por rever"* — intermédio
> - *"revisto independente + verificado limpo, done"* — só ISTO é done
