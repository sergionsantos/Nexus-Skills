---
name: nexus-learner
description: "Disciplined extraction of reusable learned skills from the current conversation, with an evidence gate (every claim points to verbatim evidence from the session), a dedup pre-flight against existing skills (update-over-create), naming rules, and a mechanical post-extraction validator. Use when the user says '/nexus-learner', 'extract a skill from this', 'learn this', 'capture this lesson', or at the end of a non-obvious debug/discovery that cost real effort. Do NOT use for quick notes (use a notes file) or for googleable knowledge."
version: 0.4.0
status: active
category: meta
tags: [learning, skill-extraction, meta]
linked_files:
  scripts:
    - "scripts/validate-learned-skill.py"
    - "scripts/sweep-draft-skills.py"
---

# nexus-learner — extrair lições com evidência, não com memória

> **Contrato:** um learned skill só vale o que as suas claims valem. Claim sem evidência da sessão = fabricação potencial (o modelo «lembra-se» de forma plausível mas errada). Este skill extrai MENOS do que um learner ingénuo, mas o que extrai é verificável, não-duplicado e mecanicamente válido.

Pastas de skills: nos exemplos usa-se `~/.claude/skills/`; se usas Codex, troca por `~/.codex/skills/` (ou define `SKILLS_DIR` para os scripts).

## Workflow (6 passos, ordem fixa)

### 1. GATE — extrair ou não (30 segundos)

Todas TÊM de ser sim:
- [ ] Custou esforço real de investigação/debug nesta sessão? (não: conhecimento que já tinhas)
- [ ] Um modelo competente NÃO chegaria lá em 5 min de pesquisa? (googleable → não extrair)
- [ ] Vai recorrer? (situação repetível, não one-off histórico)

Sinais NÃO-extraíveis: padrões genéricos de programação, uso de libraries, refactoring universal, boilerplate. **Na dúvida entre nota e skill → nota**; skill é para lições com detector+correcção reutilizáveis.

**Critérios de promoção (todos os 3, senão é nota, não skill):** (a) um *passing check* registável — o teste/comando que provou o caminho (exit 0, repro reproduzido, build verde); «pareceu funcionar» não conta; (b) um *padrão de falha nomeado* — consegues dizer que falha este caminho evita/diagnostica, não um vago «às vezes parte»; (c) **≥1 beco sem saída descartado** — uma abordagem concreta tentada e eliminada, com a razão. Os 3 vão escritos NO skill (o check no bloco Evidência, o padrão de falha no Detector, o beco em «O que não funcionou»). Falta algum → nota UNVERIFIED, não extraias.

### 2. DEDUP pre-flight — update-over-create (obrigatório)

```bash
grep -rli "<2-3 termos do tópico>" ~/.claude/skills/ --include="*.md" | head -5
```

Grep apanha termos literais, não sinónimos — com muitas skills falha overlap semântico. **Complementa** com pesquisa semântica se tiveres uma (um índice de skills, uma memória persistente pesquisável) usando a frase do Detector. Zero overlap em todos os caminhos disponíveis → criar.

- **Overlap real encontrado** → NÃO criar novo: actualizar o existente (nova war-story em `references/` ou linha na tabela + changelog bump). Consolidar > proliferar.
- Overlap parcial → decidir explicitamente e registar porquê («distinto de X porque Y»).
- Zero overlap → criar.

### 3. EVIDENCE harvest — o coração

Recolhe DA SESSÃO os artefactos verbatim que suportam a lição:
- Mensagens de erro exactas (copy-paste, nunca parafraseadas)
- Comandos corridos + outputs relevantes (dumps reais)
- `ficheiro:linha` dos pontos tocados
- O fix exacto aplicado + o verify que o provou

**Regra:** cada claim central do skill ganha ≥1 ponteiro de evidência. Claim sem evidência disponível → reescreve como hipótese marcada `UNVERIFIED` ou corta. Se a maioria das claims fica UNVERIFIED → a lição não está madura, não extraias.

### 4. WRITE — template e naming

**Naming (regras mecânicas):** slug kebab-case, sem acentos, SEM sufixo redundante (`-expertise` só se o nome precisar; nunca `-expertise-expertise`), ≤6 palavras, começa pelo domínio (`pnpm-...`, `postgres-...`, `kb-...`).

**Localização (project-first):** lição específica de UM repo (env vars dele, schema dele, comandos dele) → pasta de skills do projecto (ex.: `.claude/skills/` dentro do repo). Só se for cross-project (hábito pessoal, tool da máquina) → `~/.claude/skills/learned/<slug>/SKILL.md` (formato que o Claude Code descobre; o validador aceita também `<slug>.md` solto). Na dúvida → projecto: um skill global over-shared dispara onde os comandos não se aplicam.

**Template do corpo:**

```markdown
# <título>

## Detector
Como reconhecer que esta situação está a acontecer — sinais concretos (erro X, sintoma Y, contexto Z).

## Anti-pattern
O que o instinto faz de errado, e porquê parece razoável no momento.

## Forma correcta
A heurística de decisão (decision tree / passos) — como PENSAR, não só o que digitar.

## Evidência (sessão <data>)
- `<erro/output verbatim>` — <contexto>
- <ficheiro:linha> — <o que mostra>

## O que não funcionou
Abordagens tentadas e eliminadas nesta sessão, com a razão — a próxima sessão salta os becos, não só segue o caminho bom.

## Scope
Onde aplica e onde NÃO aplica (limites explícitos).
```

Frontmatter: `description` com o QUE + QUANDO usar (padrão use-when, «pushy» mas preciso) + `triggers:` lista de frases/termos que apareceriam ao re-encontrar o problema (fragmentos de erro > palavras genéricas).

### 5. VERIFY mecânico — nunca saltar

```bash
python3 ~/.claude/skills/nexus-learner/scripts/validate-learned-skill.py <path-do-skill-novo>
```

Valida: frontmatter parseia · naming rules · triggers não colidem com skills existentes (grep) · secções obrigatórias presentes · claims de evidência têm conteúdo. Exit ≠0 → corrige antes de reportar. (No Windows: `PYTHONUTF8=1 python ...`.)

### 6. REPORT — linguagem de estado honesta

- Reporta: path criado/actualizado · claims com evidência N/M · UNVERIFIED restantes · resultado do validador.
- Skill nasce `status: draft` — **só passa a considerar-se provado quando disparar e ajudar 1× real**. Regista esse 1º uso no changelog do skill **e muda o status nesse momento** (não fica para depois: um draft com uso real esquecido é uma folha desactualizada).
- **Antes de promover a active, revisão independente da CORRECÇÃO** (outro revisor/agente, lente ≠ autor): o validador só vê forma; uma generalização errada que «pareceu ajudar» auto-injecta-se via triggers para sempre. 1 passagem, findings corrigidos, depois promove.
- Sweep de drafts estagnados: `python3 ~/.claude/skills/nexus-learner/scripts/sweep-draft-skills.py` — **cadência sugerida: semanal (numa revisão semanal tua); dono da decisão: tu** — por skill: promover (uso real houve) ou fundir/apagar. ⚠️ o sweep usa mtime como proxy (edição não-relacionada reseta o contador; uso real regista-se no changelog do skill — confirma lá antes de decidir). Skills ACTIVE obsoletos não aparecem no sweep — caça-os na revisão de changelog.

## Anti-padrões (deste skill)

| Anti-padrão | Correcção |
|---|---|
| Extrair de memória («lembro-me que o erro era...») | Passo 3 — evidência verbatim ou UNVERIFIED |
| Criar um skill duplicado | Passo 2 — dedup, update-over-create |
| Slug `<x>-expertise-expertise` / acentos | Passo 4 naming rules |
| Extrair a meio do debug (lição imatura) | Passo 1 — só pós-verify do fix |
| Auto-actualizar skills sem revisão | Updates a skills existentes passam por revisão (ver `nexus-discipline`, se instalada) |
| Triggers genéricos («error», «fix») | Fragmentos de erro específicos + termos de domínio |

## Relação com o ecossistema

- Learners genéricos de outras suites (ex.: `learner` do oh-my-claudecode): podem coexistir; este é para uso deliberado — não competir por auto-trigger.
- Skills relacionadas deste repo (opcionais): `nexus-discipline` (disposição de trabalho) · `nexus-plan-spec` (specs) · `nexus-skill-creator` (skills novas de raiz — quando a coisa a criar não vem de uma lição de sessão, vai lá).

## Changelog
- v0.4.0: o validador exige CONTEÚDO, não só headers — Detector obrigatório por si, «O que não funcionou» com ≥1 bullet não-vazio, Evidência com marca de passing-check (exit 0/PASS/comando verbatim); triggers em block-list YAML são parseados. Revisão independente da correcção antes de draft→active. Sweep com dono+cadência + aviso mtime-proxy.
- v0.3.0: validador exige «O que não funcionou» (`--legacy` degrada para aviso ao re-validar skills antigos). Dedup ganha caminho semântico. Novo `sweep-draft-skills.py` + regra «status muda no momento do 1º uso».
- v0.2.0: critérios de promoção 3-gates (passing check + failure pattern + ≥1 dead-end) e secção «O que não funcionou», ideias colhidas de github.com/Kulaxyz/self-learning-skills; heurística de scope project-first.
- v0.1.0: criação — evidence gate, dedup, naming, verify mecânico.
