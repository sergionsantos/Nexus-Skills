# VERIFY-YOUR-OWN-TOOL-BEFORE-BLAMING-INPUTS (2026-07-05, CRM)

## When this rule applies

You have a tool that processes an external input (login form, parser,
API client, etc.) and the tool reports failure: "rejected", "invalid
credentials", "format error", "not found", "HTTP 4xx", etc.

## The reflex (in one line)

**Before you conclude the input is bad, prove your tool is correct.**

## The 3-node structural check (run BEFORE blaming the input)

### 1. Is the URL/endpoint real and current?

```bash
curl -sI https://app.vendor.example/listing/details/7165227
# Look at:
#   - HTTP status (not 404, not redirect to login)
#   - Location header (where would you land?)
#   - Set-Cookie header (does the auth even need to be there?)
```

If you wrote `login.vendor.example/account/login` but the real entry is
via Microsoft SSO redirect from `app.vendor.example`, your 404 is not the
user's problem.

### 2. Does the selector exist in the current DOM?

```javascript
const count = await page.locator('input[name="loginfmt"]').count();
console.log(`loginfmt inputs found: ${count}`);
// If 0, your selector is wrong, not the password.
```

Run this BEFORE `fill()`. Playwright's `fill` will time out silently
if the selector doesn't exist; your script then claims "submitted
but failed" — but you never submitted anything.

### 3. Is the value you're processing actually what you think it is?

```typescript
const scrapeText = await page.evaluate(() => document.body.innerText);
console.log(`first 200 chars: ${scrapeText.slice(0, 200)}`);
// If empty, you have a hydration problem, not a data problem.
```

For form values, regex captures, API response parsing: **log the raw
input before parsing it.** A regex like `/Preço do Imóvel: (\d+)/` on
an empty body returns null — and then you say "no price found" when
the truth is "no body found."

## Case study (2026-07-05, CRM)

I wrote `vendor-login.ts` and ran it twice. Both times it reported
"FATAL: This username may be incorrect." Both times I concluded
"the password must be wrong" and asked the user to provide it again.

The password was correct. The bug was:

```typescript
const LOGIN_URL = "https://login.vendor.example/account/login";
// ❌ This returns 404. The page says "To create a new account,
//    contact the vendor's support" — clearly a maintenance page.
```

The real entry point is:
```typescript
const START_URL = "https://app.vendor.example";
// ✅ Server-side redirects to https://login.microsoftonline.com/.../oauth2/authorize
// ✅ Then the MSO interstitial shows: input[name="loginfmt"] for email
// ✅ Then input[name="passwd"] for password
// ✅ Then idSIButton9 to submit
```

One `curl -sI https://login.vendor.example/account/login` would have shown
me the 404 in 1 second. I never ran it because I was inside a
"the password must be wrong" loop.

## Cost of skipping the structural check (real numbers from session)

| Iteration | What I did | Time | Outcome |
|---|---|---|---|
| 1 | Login script run, "username incorrect" | 2 min | Failure |
| 2 | Asked user for password | 5 min | User pastes password |
| 3 | Run again, "username incorrect" | 2 min | Failure |
| 4 | Concluded "must be clipboard issue" | 10 min | Still no success |
| 5 | Investigated pbpaste parsing | 5 min | Discovered clipboard had wrong content |
| 6 | Concluded "must be keychain item" | 15 min | New keychain item, still no success |
| 7 | Re-ran with clipboard | 5 min | Still 404 |
| 8 | **finally** dumped DOM via `_debug_login.mjs` | 1 min | Found `/account/login` returns 404 |
| 9 | Fixed URL to MSO redirect | 5 min | NEW error: "username incorrect" — this time real |

**Total: 50 minutes to discover what a 1-second `curl -sI` would have
shown at iteration 1.**

The session then had a separate 7-hour rabbit hole (login attempts
with keychain locked) — but the lesson applies: **before spending
a 4th re-try on any tool failure, run a 1-second structural check.**

## When to apply (decision tree)

```
Tool returns failure
  │
  ├─ Did I see the raw input/response? ── no ──→ INSPECT (curl/locator/dump)
  │                                              │ 1-5 min, often finds the bug
  │                                              ↓
  │                                          Was the URL/selector/value wrong?
  │                                          │
  │                                          YES → fix the tool
  │                                          NO  → input is the problem
  │
  └─ Yes → I saw the raw input/response
            │
            └─ Is the input structurally correct (length, format, range)?
                │
                └─ No → ask user to provide valid input
                └─ Yes → input is valid but tool rejects → fix the tool
```

## Anti-patterns (don't do these)

| Anti-pattern | Cost in 2026-07-05 | Correct reflex |
|---|---|---|
| "The password must be wrong, let me ask again" | 2 hours of asking | "Let me `curl -sI` the auth endpoint to see what's there" |
| "The CSV is malformed, let me try a different parser" | (no session case, but common) | "Let me `head -1` the CSV to see the actual column order" |
| "The API changed, let me read the docs" | (no session case) | "Let me `curl -sI` the API to see if it's still 200, then dump one response" |
| "The selector is broken, let me try a different CSS" | (common) | "Let me `page.locator(...).count()` to see if it exists at all" |
| "The regex is wrong, let me try a different pattern" | 1 hour debugging | "Let me `console.log(text.slice(0, 200))` to see what I'm matching" |

## How to add this reflex to your turn (tactical)

After any tool failure that has a "user input was bad" interpretation:

1. **Pause.** Don't re-run yet.
2. **Add ONE line** that dumps the raw state: `console.log(rawInput)`,
   `console.log(response.headers)`, `page.screenshot()`, etc.
3. **Re-run.** Read the dump.
4. **Decide** based on what the dump actually shows, not on what the
   error message implies.

The ONE line is the difference between 7 hours and 7 seconds.

## Self-test before blaming input

Ask in order:
1. Did I `curl -I` or `page.screenshot()` the input source?
2. Did I `page.locator(...).count()` to verify the selector exists?
3. Did I `console.log` the raw value before parsing it?
4. Did I `node -e` the regex on a known-good string to verify it matches?

If 2+ are "no" — run them. The dump will tell you where the bug is.
If all 4 are "yes" and the input still fails — then the input is
the problem, and you can ask the user with confidence (not hedging).
