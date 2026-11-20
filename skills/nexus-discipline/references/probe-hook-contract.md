# Pattern: Hook contract probing — don't search for `data: T[]` literal

> **Pitfall (2026-07-04, M17.4 v0110 projecto X):** hooks via `useQuery({ queryFn, ... })` não têm `data: T[]` literal no source — o tipo é inferido de `queryFn`. Probes que procuram annotation literal são false-fails.

## Sintoma

Hook assim:
```ts
export function useSubIssues(parentId: string | undefined) {
  return useQuery({
    queryKey: parentId ? qk.subIssues(parentId) : ["sub_issues", "_disabled"],
    queryFn: () => fetchSubIssues(parentId!),
    enabled: !!parentId,
  });
}
```

**Probe**:
```bash
grep -qE 'data: Issue\[\]' hooks/use-sub-issues.ts
# → FAIL (no match)
```

**Real**: hook retorna `Issue[]` (via inference de `fetchSubIssues`). Probe está errado, não o hook.

## Causa

Hooks `useQuery({ queryFn, ... })` retornam **diretamente o output de useQuery** (sem destructure explícito). O tipo é `UseQueryResult<TQueryFnData, TError>` onde `TQueryFnData` é inferido de `queryFn`.

**Annotation literal `data: Issue[]`** só aparece se houver **destructure explícito**:
```ts
const { data } = useQuery<Issue[]>({ ... })  // raro
```

ou
```ts
return useQuery<Issue[]>({ ... })  // raro
```

## Fix canónico

Probes para hooks via `useQuery` devem procurar:

| Pattern | Why |
|---|---|
| `queryFn` signature | Define o tipo de retorno |
| `queryKey` discriminant | Distingue cache hits/misses |
| `enabled: !!X` | Disable flag — runtime critical |
| import de `useQuery` | Confirma hook usa TanStack Query |

**Exemplo fix**:
```bash
# ❌ Probe original (failed):
grep -qE 'data: Issue\[\]' hooks/use-sub-issues.ts  # no match

# ✅ Probe fixed (passed):
grep -qF 'fetchSubIssues(parentId' hooks/use-sub-issues.ts  # match
```

## Tabela de tradução

| O que procuras | Probe queryFn | Probe queryKey | Probe enabled | Probe import |
|---|---|---|---|---|
| Hook tem query X | `grep -F 'fetchX'` | `grep -F 'qk.x('` | `grep -F 'enabled:'` | `grep -F 'useQuery'` |
| Hook disable quando X falsy | `grep -F 'queryFn'` | `grep -F '_disabled'` | `grep -F 'enabled: !!X'` | (n/a) |
| Hook retorna Y[] | `grep -F 'fetchY(` (assume return Y[]) | (n/a) | (n/a) | (n/a) |

## Aplicação a outros hooks

| Hook | Probe via |
|---|---|
| `useQuery` | `queryFn`, `queryKey`, `enabled` |
| `useMutation` | `mutationFn` |
| `useInfiniteQuery` | `queryFn`, `getNextPageParam` |
| `useQueryClient` | métodos usados (`setQueryData`, `invalidateQueries`) |

## Caso real (M17.4 v0110)

```bash
# Probe original:
grep -qE 'data: Issue\[\]' "$APP/hooks/use-sub-issues.ts"  # FAIL

# Probe fixed (3 sub-assertions):
grep -qF 'fetchSubIssues(parentId' "$APP/hooks/use-sub-issues.ts"  # PASS — queryFn signature
grep -qF 'qk.subIssues(parentId)' "$APP/hooks/use-sub-issues.ts"     # PASS — queryKey
grep -qF 'enabled: !!parentId' "$APP/hooks/use-sub-issues.ts"          # PASS — enabled flag
```

## Lição geral (type probes)

Para qualquer **type inference** site em TypeScript/React:
- **`function f(): Promise<T[]>`** → return type tem **annotation literal** no source. Probe `f(): Promise<T[]>`.
- **`useQuery({ queryFn: () => X() })`** → return type é **inferred** via `X()`. Probe `X()` (signature), não o tipo de retorno.
- **`const x = useQuery(...)` followed by `x.data`** → tipo é inferred. Probe o ponto de uso (`x.data`) ou queryFn.

## Detector

Se probe procura tipo de retorno de hook e falha:
1. Procure pelo **input** do hook (queryFn/mutationFn) em vez.
2. Se input está OK mas tipo continua errado → type assertion explícita pode estar em `.d.ts` files, não `.tsx` — verificar `*.d.ts` no repo.

## Resumo (1-liner)

**Probes para hooks `useQuery`/`useMutation`: procurar `queryFn`/`mutationFn` signature, NÃO o tipo de retorno (que é inferido e não está no source).**