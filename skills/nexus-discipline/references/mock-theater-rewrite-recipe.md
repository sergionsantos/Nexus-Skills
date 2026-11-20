---
title: Mock-Theater Test Rewrite — Class-Level Recipe
source: code review of a PWA test-suite (mock-heavy tests)
applies_to: any stack where tests import mocks instead of handlers (Next.js API routes, Express routes, Fastify routes, etc.)
---

# Mock-Theater Test Rewrite Recipe

> **Class-level pattern, not M9-specific.** Whenever you find tests that
> define their own `mockGetXxx()` / `mockPostXxx()` that *reimplements* the
> handler logic instead of importing it, this recipe applies. Generic
> name: "mock-theater" (the test passes but tests nothing real).

## 1. Detect

```bash
# Files under tests/api/ (or src/__tests__/api/) that don't import a route
grep -L "from '@/app/api/" src/__tests__/api/*.test.ts tests/integration/api/*.test.ts
# or equivalent for your stack: grep -L "from '../<route-module>'"

# Files that have a mockXxx or fakeXxx helper at the top
grep -lE "(const|function) (mock|fake|stub)(Get|Post|Patch|Delete)\w+" \
  src/__tests__/api/*.test.ts
```

Either signal flags a candidate for rewrite.

## 2. Confirm the canonic pattern exists

Before rewriting, find an existing test that already imports the real route.
This is your template. Common locations:

- `tests/integration/api/chat.test.ts`
- `src/__tests__/api/chat/memory-read.test.ts`
- Any test file that has `/** @jest-environment node */` at the top AND
  `import { GET/POST } from '@/app/api/...'`.

Read it. Note the pattern:
- The 4-5 `@jest.mock(...)` calls and why each exists
- The `mockCreateClient` setup with chainable builder
- The `makeRequest` / `makeGet` / `makePost` helper
- The per-test `beforeEach` that resets mocks

## 3. The recipe (5 lines, every time)

```ts
/**
 * @jest-environment node
 */
import { NextRequest } from 'next/server'                       // 1
import { GET, POST } from '@/app/api/<resource>/route'           // 2
import { createClient } from '@/lib/supabase/server'             // 3

jest.unmock('next/server')  // only if NextResponse.redirect is in scope
jest.mock('@/lib/supabase/server')                              // 4
const mockCreateClient = createClient as jest.MockedFunction<typeof createClient>

// 5. build mockClient with from.mockImplementation((table) => {...})
```

The **5 must-haves** are:
1. `/** @jest-environment node */` — bypasses the global `jest.setup.js` `jsdom` env that pollutes the test with DOM APIs the route doesn't need.
2. `import` the real route — this is the whole point.
3. `import createClient` only — to get a `jest.MockedFunction<typeof createClient>` reference for setup.
4. `jest.mock('@/lib/supabase/server')` — Supabase is the only IO boundary worth mocking. Mocks of middleware/security layers are usually unnecessary because the route calls them directly and you'd be re-mocking the same logic.
5. `from.mockImplementation((table) => { /* branch */ })` — returns a different chain per table; each chain's terminal `.single()` / `.order()` / `.not()` / `.is()` resolves to the test's expected `{ data, error }`.

## 4. Pitfalls (4 specific to this recipe)

### 4.1 Same `from(table)` called 2x for one table

The classic case: `requireAdmin` does
```ts
.from('user_roles').select('role').eq('user_id', user.id).single()
```
and then a count query also does
```ts
.from('user_roles').select('user_id', { count: 'exact', head: true })
```

`mockImplementation` is called once per `from()` call. To distinguish:

```ts
// WRONG: dispatch on .select() arg length (supabase-js normalises)
select: jest.fn((...args) => args.length === 1 ? chainA : chainB)

// RIGHT: counter per table
const fromCalls = {}
mockClient.from.mockImplementation((table) => {
  fromCalls[table] = (fromCalls[table] ?? 0) + 1
  const callN = fromCalls[table]
  if (callN === 1) return /* role check chain */
  return /* count chain */
})
```

**Why**: `supabase-js` may not pass the second arg to `.select()` in all paths (options get unwrapped). Argument-shape dispatch is fragile; call-order is the structural signal.

### 4.2 `NextResponse.redirect()` returns 307, not 302

**Detector**:
```bash
node -e "const r=require('next/server').NextResponse.redirect('http://x'); console.log(r.status)"
# → 307
```

Tests against `NextResponse.redirect()` must expect `status === 307`, not `302`. The old mock-theater tests assumed 302 because they returned `new Response(null, { status: 302, ... })` themselves — the real framework uses 307.

**Fix**: change `expect(response.status).toBe(302)` to `expect(response.status).toBe(307)`. Also verify the `Location` header is set (the global `jest.setup.js` mock of `next/server` returns a custom `NextResponse` that does NOT set `Location` — fix with `jest.unmock('next/server')` at the top of the file).

### 4.3 `from.mockImplementation` returns the wrong shape

`supabase-js` chains terminate with a Promise. Each chain method (`select`, `eq`, `order`, `is`, `not`, `single`) can be either:
- **terminal** (returns a Promise): `.single()`, `.then(...)` patterns
- **non-terminal** (returns a new chainable): `.select()`, `.eq()`, `.order()`

For terminal calls like `.not('archived_at', 'is', null)`, the returned object IS a Promise. The route does `await query` — so the chain must resolve correctly.

**Pattern**:
```ts
chain.not = jest.fn(() => Promise.resolve({ data: ..., error: ... }))   // right
chain.is  = jest.fn(() => chain)                                          // wrong — breaks await
```

A common bug: making `.is()` return a chain when the route expects it to be terminal. Verify by reading the route's actual call sequence.

### 4.4 `mockClient` is re-instantiated per test via `setupClient()`

In `beforeEach`, **return the mock client** so per-test overrides can mutate it:
```ts
function setupClient(opts = {}) {
  const mockClient = { auth: { ... }, from: jest.fn(...) }
  mockCreateClient.mockResolvedValue(mockClient)
  return mockClient  // return it
}

it('override case', async () => {
  const mc = setupClient()  // capture
  mc.from.mockImplementation(...)  // per-test override
})
```

If you instead do `setupClient(); (mockCreateClient as any).mock.results[0].value`, you depend on call order — fragile when the route calls `createClient()` multiple times (e.g., GET then GET inside an enrichment helper).

## 5. Proof of fixity (ISC for the rewrite)

A rewrite is **proven** when:
- **All test cases green** (`npx jest <file>` exit 0)
- **At least one bug real** discovered (the reescrita surfaces a discrepancy between what the mock assumed and what the route does). If zero bugs found, the rewrite is suspect — likely the mock is still reimplementing too much.
- **Type check clean** (`npx tsc --noEmit` exit 0 on the file)

Example bugs that the rewrite surfaced :
1. `requireAdmin` returns 403 for unauthenticated (expected 401) — review BE-20.
2. `GET /api/agents` returns `undefined` for missing `avatar_url` (expected `null`) — route:18.
3. `NextResponse.redirect` returns 307, not 302 — old test assumed wrong.
4. `jest.setup.js` globally mocks `next/server` without Location header — forces `jest.unmock('next/server')` per file.

## 6. Common anti-patterns during the rewrite

| Anti-pattern | Fix |
|---|---|
| `mockClient.from = jest.fn()` (replaces, doesn't chain) | Use `mockClient.from.mockImplementation((table) => ...)` to keep the original `jest.fn()` and add behaviour. |
| One big `from.mockImplementation` with 200 lines of branching | Extract per-table factory: `const userRolesChain = makeChain(...)`, `const conversationsChain = makeChain(...)`. |
| Forgetting `jest.clearAllMocks()` in `beforeEach` | The mock state leaks between tests; the second test sees the first test's `.mockResolvedValueOnce` etc. |
| Mocking `loadAllAgents` from `@/lib/agents/loader` separately | It's used by some routes; mock only if the route imports it. |
| Using `as any` everywhere to silence TS | Tolerable for chain returns (TS can't follow dynamic chains), but document the intent. Pattern: `const chain: any = {}; chain.select = jest.fn(() => chain)`. |

## 7. Workflow checklist

```markdown
- [ ] Detected candidates via grep
- [ ] Found canonic pattern (chat.test.ts or similar) to copy structure from
- [ ] Read the REAL route to understand what it imports and calls
- [ ] Created the new test file with 5-line recipe at top
- [ ] Built per-table factories (or single dispatch on table name)
- [ ] Implemented each test case as: setupClient() -> call route handler -> assert response
- [ ] Ran `npx jest <file>` until all green
- [ ] Confirmed at least 1 bug real was discovered (else rewrite is suspect)
- [ ] Ran `npx tsc --noEmit` (clean on this file)
- [ ] Committed as 1 atomic commit per file (revert-safe)
- [ ] Updated relevant ISA (ISC ticked with concrete evidence)
```

## 8. When NOT to apply this recipe

- The "test" is actually a contract test for an external library (mock the lib, exercise your wrapper).
- The route is a trivial passthrough with no logic to test (e.g., `app.get('/health', () => 'ok')`) — a "mock the handler" test is fine.
- The route calls `await` external services (S3, Stripe) where the mock boundary is the service, not the DB.

## 9. Real-world impact (PWA code review)

- **6 test files reescritas**, 49/49 tests green.
- **6 stub files apagados** (5 simples + 1 duplicado antigo).
- **4 bugs reais descobertos** que estavam escondidos pelos mocks (ver §5).
- **7 commits atómicos**, cada um revert-safe.
- Working tree: limpo após cada commit (paralelismo com outra thread M5/M6 validado sem conflito).
