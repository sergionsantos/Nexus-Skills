# AUTH-BLOCKED-REDIRECT-FIRST (2026-07-05, CRM session)

## When this rule applies

You are blocked on external auth/credentials (login expired, keychain
locked, password rejected, OAuth redirect loops, captcha required, etc.)
**AND** the task you were given has sub-components that don't require that
auth (DB reads, file ops, infra setup, UI patches, scripts that run
against public endpoints, documentation, skill writing, etc.).

## The reflex (in one line)

**Stop grinding on the auth. Pivot to the auth-free subtask. Report
the auth-blocked state explicitly as pending, then ship the rest.**

## Why

The 2026-07-05 CRM session ran 7 hours attempting Vendor
re-authentication (cookie import from Chrome Profile 1, keychain
unlock, Playwright headless login, pbpaste from clipboard) before
the user exploded:

> *"Epá, para de inventar e remata isto uma vez por todas, pá! Por
> amor de Deus, já não há paciência! Há horas de volta, de volta, de
> volta."*

The actual unlock was 30 seconds away: **the photo-download task
that was the goal** was a public-CDN operation
(`https://img.vendor.example/mxw-650/.../uuid.jpg` returns 200 with
`access-control-allow-origin: *` and requires no auth). Seven hours
of login attempts produced zero working output. The first 79 photos
took 7 seconds to download after the pivot.

## Anti-pattern (what I actually did)

1. Auth failure → blame the password → ask for password again via
   insecure channel
2. Re-try same script with new password in different keychain item
3. Re-try same script with password from clipboard
4. Re-try same script with the user's plaintext-password-that-was-pasted-to-chat
5. Each re-try: write a new exception-handler block, log the same
   error, and declare "the password must be wrong"
6. ... 7 hours later, give up on auth, **finally** check if the photo
   URL is public → 200 OK in 1 second

The diagnostic was always 5 minutes away: `curl -I https://img.vendor.example/...jpg`
would have shown the `access-control-allow-origin: *` header. But I
never ran it because I was inside a "try to authenticate" loop.

## How to apply the reflex (5-second check)

Before the 3rd re-try of any auth-dependent step, ask:

1. **What part of this task doesn't need the auth?** (Read DB? Patch UI?
   Download a public file? Update a script?)
2. **Can I do that part NOW and ship it?** (Often yes.)
3. **Will the user gain more from the partial ship or from one more
   auth attempt?** (Partial ship. Always partial ship.)

If partial ship wins: do it. Report the auth-blocked state as a
single line: *"X is auth-blocked; pending <key> from user. Shipped
Y in the meantime."*

## Pitfall correlato: don't blame the input before checking your tool

The reflex *Verify-your-own-tool-before-blaming-inputs* (see `verify-your-own-tool-before-blaming-inputs.md`; in the
SKILL.md) is the upstream cousin. In the same session, I assumed
the password was wrong when actually my login script was hitting
`/account/login` (which returns **404**) when the real entry point
is the Microsoft SSO redirect chain from
`https://app.vendor.example`. Two failures before I ran
`curl -sI` to see what was actually there.

The 3-node check (see related reflex in `verify-your-own-tool-before-blaming-inputs.md`):
1. `curl -I` or `fetch --head` on the base URL — see redirects
2. `page.locator(selector).count()` — does the selector actually exist?
3. If your tool uses a hardcoded URL, verify it **currently** returns 200

If 1 of these is wrong, the password isn't the problem. **Always
run the structural check before assuming the user is the problem.**

## Cases this rule applies to (from session 2026-07-05)

- **CDN download of public images** (auth is irrelevant)
- **DB reads via `getDb("worker")`** (BYPASSRLS role, no user auth)
- **Frontend patches** (TypeScript + git commit + push, no API call)
- **Backend infra setup** (`@fastify/static`, gitignore, .gitkeep, route
  deletion)
- **Skill-library curation** (writing references/, no execution)
- **ISA document writing** (markdown only, no auth needed)
- **Shell script execution that reads from filesystem** (no auth)

The common shape: "I need to write/read X" — write/read can be done
locally. The auth is for the "I need to interact with the system to
GET X" branch. If the system **already gave you X** (cookie in
Chrome, public file on CDN, Git history) — skip the auth dance.

## Cost analysis (rule of thumb)

| Action | Time | Outcome |
|---|---|---|
| 1st re-try of auth | 5-15 min | Often fails same way |
| 2nd re-try of auth | 5-15 min | Failure pattern unchanged |
| 3rd re-try of auth | 5-15 min | Pattern crystallizes; you're now in rabbit hole |
| Pivot to auth-free subtask | 30-60s | Ships value, decomposes the problem |
| Inspect your own tool (curl/locator/etc.) | 30-60s | Often reveals the bug |

The math: 3 re-tries = 30-45 min burned. Pivot = 60s. Inspection = 60s.
The pivot path **always** wins if the auth-free subtask is non-trivial
(>5 min of work).

## Self-test before declaring auth-blocked

Ask in order:

1. Did I `curl -I` the base URL? (`curl -sI https://app.vendor.example/.../file.jpg`?)
2. Did I dump the DOM via Playwright before assuming selector structure?
3. Did I check whether the **target** (not the auth) is publicly accessible?
4. Is there a `--dry-run` mode that exercises the rest of the pipeline?

If 3+ of those are "no" — pivot to those diagnostics first, then
declare the auth-blocked.

## When this rule does NOT apply

- The whole task is auth (e.g. "set up SSO" — the SSO IS the deliverable)
- The auth-blocked subtask is the *only* task in scope (no auth-free
  alternatives exist)
- The user has explicitly said "wait, fix the auth first" (rare but
  possible — the user knows they have a credential in their pocket)

In all other cases: pivot.

## What to report to the user

Format: 1-line per item, max 3-4 lines. No excuses, no hedging.

```
B: shipped (commit c1582ed). C: 79/79 photos downloaded (commit 23e7ff1).
A: auth-blocked. Needs <what> from user.
```

Compare to the anti-pattern (the one I did 7 times):
```
A: tried login with keychain password, got rc=36, keychain locked.
Tried with pbpaste, password seems wrong. Tried pbcopy </dev/null, 
still wrong. Maybe the user meant a different password? Let me ask...
```

The user pattern-matches the first format to "agent is working
autonomously, ship is real" and the second to "agent is stuck in a
loop, will burn more rounds if I don't intervene." Trust is a function
of report quality, not of effort.
