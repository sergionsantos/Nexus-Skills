# Pattern: Sibling-edits clobber em multi-agent

> **Pitfall (2026-07-04, M15/M17/M18 projecto X):** quando multi-agent, sibling subagents editam o mesmo ficheiro **enquanto** o autor principal está a editar. Sem `read_file` antes de `patch`, o autor pode overwrite trabalho do sibling.

## Sintoma

Warning `read_file` antes de cada `patch`:
```
"_warning": "/path/to/file.ts was modified by sibling subagent '20260702_173811_3f725d' but this agent never read it."
```

Quando o autor ignora este warning:
- Build quebra com "function X defined twice" (sibling wrote a copy of X)
- Build quebra com "missing import" (sibling removed it)
- Source fica com **partial merge** — work from both agents lost

## Caso real (M15 → M17 projecto X)

Durante M17 polish:
1. **M17 author** edita `lib/api/issues.ts` (adds `useLabels(teamId?)` parameter).
2. **Sibling subagent** (em paralelo) também edita o mesmo ficheiro (M15 side-effect).
3. M17 author `patch` overwrite parte do trabalho do sibling.
4. Build falha com "useSubIssues import not found" (que sibling tinha adicionado).

**Fix**: depois do warning, **re-read the file** antes do próximo `patch`.

## Fix canónico

```ts
// 1. Após warning, read_file do ficheiro completo
const current = await read_file(path=targetFile);

// 2. Identificar divergências vs o que pretendias escrever
// (pode haver mudanças do sibling que deves preservar)

// 3. Re-aplicar o patch sobre a versão actual do disco
patch(path=targetFile, old_string=new_old_string_based_on_actual, new_string=...);

// 4. Run verify imediatamente após
```

## Sequência segura para ficheiros partilhados

```
read_file (lê versão actual)
  ↓
patch (escreve baseado no que leste)
  ↓
build (verifica que não quebrou)
  ↓
verify (probe regression)
```

**Race window**: entre `read_file` e `patch`, sibling pode ter escrito. Aceitar **read → patch → build → if sibling warning, read again → patch again**.

## Detector

A própria tool emite o warning:
```
"_warning": "X was modified by sibling subagent 'xxx' but this agent never read it."
```

**Nunca ignorar este warning.** Tratá-lo como **gate** antes do patch.

## Lição lateral: sequenciar edits

Em multi-agent, **edits paralelos ao mesmo ficheiro são races**. Para evitar:

1. **Sequenciar**: autor principal completa + builds, antes de sibling começar.
2. **Lock-files**: ficheiro `.lock` no repo a sinalizar "agent X está a editar".
3. **Different files**: dividir trabalho por file ownership (autor A → file X, autor B → file Y).

Em multi-agent com **delegate_task**, o orquestrador é quem decide o sequencing. Subagents devem **reportar file touched** ao iniciar e **só outro subagent pode tocar** após o build verde do primeiro.

## Caso de estudo (M17 projecto X)

```
M17.1.1 useLabels hook author → edit hooks/use-labels.ts
M17 sibling (M15 retroactive) → edit lib/api/issues.ts (diferente)

(Estes não colidiram — ficheiros diferentes)

M17.3.3 author → edit issue-detail.tsx + lib/api/issues.ts (useSubIssues export)
M17 sibling (M15 retroactive) → edit lib/api/issues.ts (refreshIssueFromArchive)

(Colidiu! Sibling tinha acabado de adicionar fetchArchivedIssues, mas author não leu.)

FIX: read_file lib/api/issues.ts → patch com base na versão lida.
```

## Anti-pattern

```ts
// ❌ Ignorar warning
patch(path=file.ts, old_string="v1", new_string="v2")  // overwrite sibling
// Build fails later

// ✅ Re-read after warning
read_file(path=file.ts)  // version 2.1 (with sibling changes)
patch(path=file.ts, old_string="v2", new_string="v2.2")  // safe merge
```

## Resumo (1-liner)

**Multi-agent: warning "modified by sibling" é gate, não info. Re-read file → patch → build → verify. Sequential edits > parallel para shared files.**