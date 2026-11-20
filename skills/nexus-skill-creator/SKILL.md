---
name: nexus-skill-creator
description: "Criação disciplinada de skills novas de raiz, thin e doctrine-first: skills nascem com triggers+anti-triggers, secção de verificação user-facing, regra anti-acreção, changelog, e estado draft até 1º uso real. Usar quando o utilizador diz '/nexus-skill-creator', 'cria um skill para X', 'transforma este workflow num skill', 'nova skill'. Para EVAL PESADO (benchmark, viewer, iterações com baselines) usar o skill-creator oficial do plugin, se instalado. Para extrair uma lição da sessão actual usar nexus-learner."
version: 0.2.1
status: active
category: nexus
tags: [nexus, skill-authoring, meta]
linked_files:
  scripts:
    - "scripts/bridge-skill.sh"
---

# nexus-skill-creator — skills que nascem verificáveis e não incham

> **Contrato:** um skill é um sistema com modos de falha conhecidos: dispara quando não devia (trigger fraco), não dispara quando devia (description vaga), incha por acreção até ninguém o ler (600+ linhas), e declara valor que nunca ninguém verificou. Este skill desenha contra os 4.

## Workflow (6 passos)

### 1. INTENT — 4 perguntas antes de escrever

1. O que deve o skill permitir fazer? (1 frase)
2. **Quando dispara?** — frases reais do utilizador, contextos
3. **Quando NÃO dispara?** — os near-misses (partilham keywords mas pedem outra coisa) — tão importante como o 2
4. Como é que o UTILIZADOR verifica que funcionou? (se não há resposta, o skill vai declarar valor não-verificável)

Se a origem é "captura o workflow desta conversa": extrai passos/tools/correcções do histórico primeiro, confirma com o utilizador.

### 2. DEDUP pre-flight

```bash
ls ~/.claude/skills/ | grep -i "<termo>"; grep -rli "<tópico>" ~/.claude/skills/*/SKILL.md | head -5
```
Grep apanha literais, não sinónimos — **complementa com uma pesquisa semântica** se tiveres uma (pesquisa na memória persistente ou no histórico com a frase de intent do passo 1), como o nexus-learner exige. Skill parecido existe → **estender** (nova secção/reference + changelog) em vez de criar. Regista a decisão.

### 2b. LOCALIZAÇÃO — onde o skill nasce (decide ANTES de escrever)

- Lição/tooling de UM repo → pasta de skills do projecto (ex.: `.claude/skills/` dentro do repo).
- Cross-project, só Claude Code → `~/.claude/skills/<slug>/`.
- **Skill que mais do que um agente tem de descobrir** (ex.: Claude Code E Codex, que lê `~/.codex/skills/`): um skill só numa das pastas é invisível ao outro agente; "criei o skill" sem a segunda localização é falso para metade das ferramentas.
- **Não é default — é on-demand e fácil:** quando o pedido incluir "disponibiliza também no Codex" (ou equivalente), corre `bash <pasta-deste-skill>/scripts/bridge-skill.sh <nome>` — idempotente, mantém a pasta real onde já está e cria o symlink (ou `--copy`) no outro lado, verificando que `SKILL.md` resolve nos dois paths. Usa `--dry-run` para ver o que faria; ver `README.md`.

### 3. DESIGN — estrutura por tamanho (progressive disclosure)

| Conteúdo | Onde |
|---|---|
| Contrato + workflow + tabelas de decisão | SKILL.md (**200 linhas = alvo soft; 250 = tecto duro que dispara cirurgia** — os dois números do passo 6 e da Verificação são ESTE par, não contradição) |
| Docs de apoio, war stories, casos datados | `references/*.md` |
| Templates de output | `templates/*.md` |
| Passos determinísticos/repetitivos | `scripts/*` (se 2+ usos vão reescrever o mesmo helper → bundle) |

**Frontmatter:** `name` (kebab, sem acentos) · `description` = QUE + QUANDO usar + quando NÃO ("pushy" mas preciso — é o mecanismo de triggering; o modelo sub-dispara skills, a description compensa) · `version` · `status: draft`.

### 4. WRITE — secções obrigatórias do corpo

1. **Contrato** (1 parágrafo: o que garante e a que custo)
2. **Workflow** (passos numerados, imperativo, explica PORQUÊ em vez de MUSTs gritados)
3. **Quando NÃO usar** (anti-triggers por extenso)
4. **Verificação** (como o utilizador confirma que o skill fez o que devia — check falível, não "parece bem")
5. **Anti-padrões** (tabela: erro → correcção)
6. **Changelog** (1 linha por versão)

Estilo: explica o porquê — modelos têm theory of mind; instruções com razão generalizam, ALL-CAPS-MUSTs overfittam. Exemplos ilustram princípios, não são material de copy-paste.

### 5. SMOKE — verificação leve (não é o eval pesado)

- Escreve 1-2 test prompts realistas + **prediz o comportamento esperado** antes de correr (predict-then-run).
- Corre 1× (tu próprio ou subagente com o skill).
- Negative control **obrigatório sempre que existam keywords partilhadas com outros skills/pedidos** (é onde o trigger-design falha): prompt near-miss que NÃO devia disparar → confirma que não dispara. Só dispensável quando o trigger é inequivocamente único.
- Frontmatter parseia: `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]).read().split('---')[1])" <SKILL.md>`
- **Eval a sério** (benchmark, viewer, baselines, iterações, description optimization): usa o `skill-creator` oficial do plugin — a maquinaria existe lá, não se duplica.

### 6. STATUS + manutenção

- Nasce `status: draft`. **Activa** após 1º uso real com sucesso (regista no changelog) **E revisão independente da correcção** (critic/code-reviewer, lente ≠ autor — INCONDICIONAL, não só para trabalho sem supervisão: um skill de doutrina auto-injecta via triggers, é unattended por definição; o smoke do passo 5 é a lente do autor e não chega — paridade com nexus-learner).
- **Regra anti-acreção (a mais violada no ecossistema):** pitfall/war-story novo = **1 linha na tabela de anti-padrões + corpo em `references/<slug>.md`** — NUNCA secção inline nova. SKILL.md que passa das ~250 linhas = cirurgia de emagrecimento antes de qualquer conteúdo novo. (Caso real: um skill de disciplina chegou a 606 linhas por acreção inline em 4 dias, contra a sua própria decisão de arquitectura.)
- Updates passam por review independente quando o skill guia trabalho unattended.
- Version bump + changelog em toda a alteração de comportamento.

## Quando NÃO usar

- Lição/gotcha descoberto NESTA sessão → `nexus-learner` (tem evidence gate próprio).
- Eval quantitativo pesado, benchmark com baselines, description optimization loop → `skill-creator` oficial.
- Nota rápida/preferência → notas do utilizador ou ficheiro de instruções do projecto (CLAUDE.md/AGENTS.md), não skill.
- Automação que o harness deve FORÇAR (correr sempre) → hook em settings.json, não skill (skills são best-effort; hooks são garantia).

## Verificação (deste próprio skill)

Skill novo criado por este workflow passa: frontmatter parseia · secções obrigatórias presentes (≥5 headers `##`) · ≤200 ln (soft) · smoke com predição + negative control corridos · status draft. Check rápido: `grep -c "^## " <SKILL.md>` ≥5 — **isto valida FORMA, não valor** (5 headers vazios passam); o gate de VALOR é a revisão independente do passo 6, sem a qual o skill não sai de draft.

## Anti-padrões

| Anti-padrão | Correcção |
|---|---|
| Description só diz O QUE (não QUANDO) | Passo 3 — use-when + anti-triggers na description |
| Skill de 500 linhas à nascença | Passo 3 — corpo mínimo + references/ |
| "Funciona" sem ninguém testar | Passo 5 — smoke com predição; draft até uso real |
| Duplicar skill existente | Passo 2 — dedup, estender |
| War story inline no corpo | Passo 6 — anti-acreção |
| Skill para o que devia ser hook | Quando NÃO usar — enforcement é hardware |

## Changelog
- v0.2.1: `scripts/bridge-skill.sh` — disponibilização em dois agentes (Claude Code + Codex) on-demand, não por omissão. Idempotente, 3 casos (symlink/cópia numa direcção ou outra, no-op), conflito e inexistente falham explícito, `--dry-run`. Passo 2b aponta para ele.
- v0.2.0: fixes pós-red-team: passo 2b LOCALIZAÇÃO; dedup com caminho semântico; review independente INCONDICIONAL antes de draft→active; negative-control obrigatório com keywords partilhadas; Verificação declara grep=forma/review=valor; 200-soft/250-ceiling reconciliado; version field sincronizado.
- v0.1.1: draft→active após 1º uso real (workflow de 6 passos seguido integral; smoke apanhou divergência real).
- v0.1.0: criação — progressive disclosure, trigger design, explain-why + anti-acreção, verify user-facing, draft-gate, smoke predict-then-run.
