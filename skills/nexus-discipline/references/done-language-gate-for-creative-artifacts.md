---
name: done-language-gate-for-creative-artifacts
description: |
  Bash specifics para a Rule 1 (live-probe, SKILL.md §1) — verificação honesta de
  artefactos criativos/documentais (advocate, spec, plan, KB doc, research report)
  onde não há test suite para forçar o probe. Inclui os 3 falsos negativos
  apanhados na sessão advocate-c15 de 2026-07-11.
tags: [verification, creative-artifact, grep-pitfalls, done-language]
source-session: advocate-c15 / Modo-A NewVenture run-1 research, 2026-07-11
---

# DONE-LANGUAGE gate — bash specifics

> Companhão da Rule 1 (live-probe, SKILL.md §1). A regra conceptual vive lá; este
> ficheiro é o "como faço o probe correctamente em bash para que o gate não me
> deixe passar num falso verde".

## O padrão de 3 nós (relembrado, ordem obrigatória)

1. `ls -la <path> && wc -l <path>` — prova existência + dimensões.
2. **Probe estrutural** com `grep` para cada marca obrigatória — counts visíveis.
3. Reportar na taxonomia de 4 estados (SKILL.md §2) — **nunca "done" como monolítico**.

O erro da sessão 2026-07-11 foi saltar o nó 2 e dizer "Ficheiro criado" só com
o nó 1 (e um `write_file` tool call anterior). O utilizador invocou o gate
explicitamente. A correcção correu o nó 2 e o nó 3 juntos.

## Três armadilhas bash apanhadas nesta sessão (2026-07-11)

### Armadilha 1 — `grep -c` conta LINHAS, não OCORRÊNCIAS

```bash
# ERRADO para contagem de ocorrências — conta linhas com ≥1 match:
grep -cE "https?://" file.md       # → pode dar 1 mesmo com 4 URLs no ficheiro

# CORRECTO para contagem de ocorrências únicas (sort + wc -l):
grep -oE "https?://[^[:space:])]+" file.md | sort -u | wc -l
```

**Quando usar cada:** `grep -c` para "tem pelo menos 1?"; `sort -u | wc -l` para
"quantos únicos?". Na sessão 2026-07-11 reportei `1 URL` quando havia 3 — falso
negativo silencioso.

### Armadilha 2 — `sed`/`awk` em PT-PT com chars não-ASCII devolve 0

A combinação `awk '/START/,/END/' | sed '1d;$d' | wc -w` na sessão
2026-07-11 (tentativa de contar palavras na "Objecção a responder" que tinha
`ç` / `ão` / `ão`) devolveu `0 0` — **silencioso**, sem erro. O `sed` em
macOS, em combinação com pipes UTF-8, partiu.

**Workaround que funcionou:** usar `sed -n 'N,Mp' file | wc -w` directamente
(extrair linhas por número, sem range por pattern), evitando o `awk` range
regex que falha em UTF-8.

```bash
# NÃO FÁ (silencioso 0 em macOS com UTF-8):
awk '/^## 3\. /,/^## 4\./' file | sed '1d;$d' | wc -w

# FÁ (pipes simples, sed por linha):
sed -n '27,40p' file | wc -w
```

**Generalize:** sempre que vires `awk '/pattern/,/pattern/'` em verificação de
texto com potencial UTF-8, re-escreve para `grep -n` + `sed -n 'N1,N2p'`.

### Armadilha 3 — Mau padrão de `grep -cE "^## [1-4]\."` (respondeu `4` mas faltava conteúdo)

Na sessão 2026-07-11, o `grep -cE "^## [1-4]\." file.md` devolveu `4` — parecia
"todas as 4 secções obrigatórias presentes" — mas a secção "Objecção a
responder" tinha um parágrafo escrito depois de uma blockquote `>` e o heading
era `### > **"Este segmento…"` que não matchava `^##` algum. A contagem estava
correcta (4) mas a interpretação era enganadora.

**Forma mais robusta:** combinar **heading match + content presence check**:

```bash
# Heading OK?
grep -qE "^## 3\. Objecção a responder" file.md && echo "heading OK"

# Conteúdo da secção tem tamanho razoável?
sed -n '/^## 3\./,/^## 4\./p' file.md | wc -c    # bytes da secção
# Esperado: > 500 bytes para objecção substantiva
```

**Lição:** o `grep -c` dum pattern pode devolver "OK" mas a secção pode ter
apenas o heading e zero conteúdo. Sempre combinar count de heading com
contagem de chars/words da secção.

## Template reutilizável de verify gate (creative artifact)

```bash
F=/path/to/artefacto.md

echo "=== NODE 1: existence + dimensions ==="
ls -la "$F"
wc -l "$F"

echo ""
echo "=== NODE 2: structural probe ==="
echo "Headings (esperados: ## 1. ## 2. ## 3. ## 4.):"
grep -cE "^## [1-4]\." "$F"

echo "Required URLs (esperado: N):"
grep -oE "https?://[^[:space:])]+" "$F" | sort -u | wc -l

echo "Required numbered list (esperado: 5 bullets no resumo):"
awk '/^## Resumo de 5 linhas/,/^---$/' "$F" | grep -cE "^[1-5]\. "

echo ""
echo "=== NODE 3: state report (4-state taxonomy) ==="
# Relatar na prosa o que cada nó mostrou acima — nunca como monolítico "done".
```

## Quando este padrão NÃO se aplica

- **Código com test suite** — Rule 1 (live probe via tests/build) sobrepõe-se.
- **Edits num só ficheiro com verify imediato a jusante** — a próxima tool call
  já é a prova (ex.: editas `config.yaml`, o próximo `restart service` falha se
  o YAML estiver partido).
- **Pesquisa/resposta conversacional** — não produz artefacto escrito,
  não há ficheiro a verificar.

## Ligações

- Regra conceptual: `nexus-discipline` §1 (Rule 1, live-probe) e §2 (taxonomia de 4 estados).
- Esta reference trata de correcção/verificação honesta; avaliação de qualidade criativa é outro assunto.
