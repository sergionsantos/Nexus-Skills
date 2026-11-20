---
title: "When user says 'para de inventar desculpas' — HARDENED pivot-to-auth-free protocol"
description: "How to recognize the burnout signal mid-conversation and pivot immediately. Concrete rules for when to stop offering auth alternatives, when to admit the block and PARE, and when to deliver PLAN+DRY-RUN offline. Includes 2026-07-05 sessão anterior evidence + 2026-07-02 CRM repetition (this session)."
keywords: [user-burnout, pivot, auth-blocked, stop-inventing, plan-dry-run-offline, gate-vs-trigger, frustration-protocol]
source: "CRM session 2026-07-02 + 2026-07-05 sessão anterior + current session (post-auth-blocked). The hardening clause in v0.31 changelog was right in theory; in practice the agent repeats the pattern when session context doesn't carry the rule."
---

# Pivot-to-Auth-Free Protocol (HARDENED)

**This is a HARDENED version of the v0.31 changelog clause.** The original text was:

> *"Hardening 2026-07-05 (sessão sessão anterior): quando o user diz 'para de inventar desculpas', PÁRA de oferecer alternativas de auth (keychain unlock, pbpaste, password manager, 1Password, etc.). Oferecer mais 5 opções de auth quando 0 funcionam é exactamente o anti-pattern."*

**That rule is correct. This reference operationalises it with concrete decision trees and evidence from multiple sessions.**

## When this fires

Any ONE of these triggers the pivot:

1. **Direct user signal (HIGHEST PRIORITY):** "para de inventar", "remata isto", "já não há paciência", "que desatino", "trata de tu de uma vez por todas", "Epá", or any PT/EN equivalent of "stop making excuses, just do it"
2. **Two failed auth attempts in the same session** for the same operation (each offering a new variant = anti-pattern)
3. **User explicitly says "não preciso da auth"** or "faz o que puderes sem auth"
4. **More than 3 "tenta X" / "tenta Y" cycles** on the same auth dependency without progress
5. **You find yourself listing 5+ alternative auth sources** in a single message

**If you detect (1), pivot IMMEDIATELY in the same response — do not start a new "let me try" cycle.**

## Decision tree (5 nodes)

```
Q1: Is the user-visible deliverable auth-Dependent or auth-Independent?
    A1: if AUTH-DEPENDENT: admit the block, deliver PLAN + DRY-RUN offline,
        list 3 next-steps for user to unblock. PARE.
    A2: if AUTH-INDEPENDENT: continue with that, do not touch auth again.

Q2 (only if A2): Is there a sub-task the user is asking for that I CAN do
    without auth?  (e.g., commit code already written; download from
    public CDN; lint; typecheck; frontend display; document the
    block)
    → YES: pivot to that sub-task, report auth-blocked as pending.
    → NO: admit the block, PARE.

Q3 (only if I am about to offer yet another auth source):
    Has the user already declined the previous offer in this session?
    → YES: I'm in a loop. PARE immediately, do not offer alternative N+1.
    → NO: ok to offer ONE more (the LAST one), but cap at N=2 alternatives
        total in a single message.

Q4 (only if I am about to say "wait, maybe it's X"):
    Am I describing a third theory without testing the first one?
    → YES: stop theorizing. Test the first theory, or PARE.
    → NO: continue debugging.

Q5 (when the user signal is "para de inventar"):
    Should I even be doing the auth-dependent work right now?
    → if auth is the bottleneck, NO. Pivot to auth-free work.
    → if I have auth-free work to do, YES, and announce the pivot.
    → if neither, just PARE and say "I need X from you to continue".
```

## Concrete anti-patterns (do NOT do these)

1. **Listing 5+ auth sources in one message** ("use pbpaste, or keychain, or 1Password, or Bitwarden, or —"). One alternative at a time, capped at 2.
2. **"The password must be wrong, let me try"** after the user has already corrected you once. The password is probably right; YOUR flow is wrong.
3. **Pretending the script "ran successfully"** when the count went from N to 0 (typical auth-fail signature). Report "ran, got 0 results — auth likely blocked" instead.
4. **Continuing to "experiment" with auth workarounds** when the user has explicitly said "stop". Pivot to auth-free work or PARE.
5. **Inventing new "maybe it's the email not the password" theories** when the user just told you the password is correct. Stop theorising, pivot to verifiable work.

## Evidence from this session (2026-07-02 CRM)

The user sent these explicit signals:

1. "Epá, que desatino! Andas há horas e horas e horas à volta desta merda e não consegues dar a volta a isto."
2. "A password que eu te estou a dar é a password real, é a password que está no keychain, é a password com que eu entro, é a password que funciona."
3. "Epá, para de inventar e remata isto uma vez por todas, pá! Por amor de Deus, já não há paciência!"
4. "a pergunta é simples, o que estas a fazer?"

**What the agent did wrong:** continued trying auth workarounds (pbpaste via clipboard, keychain unlock, etc.) for several more turns AFTER signal (3). The correct action would have been: "OK, I can't get auth. Here's what I CAN do without auth: A, B, C. Which do you want?"

**What the agent should have done:**

- After (1): "OK, I give up on the login. Here's a different path — let me work on task C (which doesn't need auth) while you figure out the auth."
- After (3): "OK, stopping all auth attempts. The DB write that needs auth is blocked. Let me commit the B and C frontend patches instead."

## When to commit / when to PARE

- If the user-visible work has 2+ sub-tasks and at least one is auth-free, **commit the auth-free one in this turn**, mention the blocked one in the report. Don't wait for the user to say "ok, do B".
- If the user-visible work is entirely auth-dependent, **PARE in the same turn** with: "I need X to continue. Here's exactly what to do." Don't offer 3 alternatives. Just PARE.

## The "pivot, not stop" rule

When you pivot, **say what you're pivoting TO**, not just "I'm stopping auth". The user wants progress, not stalling:

GOOD: "OK, pivoting to commit the C patches (don't need auth) — let me know if you want me to do A again later."

BAD: "I can't get auth. Let me know how to proceed." (forces user to direct)

GOOD: "Auth is blocked, can't re-scrape A. Doing A's schema migration and B's frontend in the meantime. Re-attempt A in next session."

BAD: "Maybe try unlocking keychain first, or 1Password, or Bitwarden..." (lists 5 options, the user already declined 3)

## Why the v0.31 rule wasn't enough

The v0.31 rule was added based on a SINGLE session (sessão anterior). Single-session rules are easy to forget when context shifts. The HARDENED version of this rule:

1. **Pre-emptive check before offering any auth source**: have I offered 2+ already in this session? If yes, do not offer a 3rd.
2. **Watch for the user signal in their first message of a turn**: PT/EN frustration markers, "Epá", "stop", "para de", "trata de tu", "que desatino", "remata".
3. **Track auth-failure cycle count in the current session**: a simple counter incremented each time a different auth source fails. At 2, pivot. At 3, PARE and ask the user.

## Cycle counter implementation (informal, in your head)

```
[0] First auth attempt — try normally
[1] First auth failed, try 1 alternative
[2] Alternative 1 failed, do NOT offer another — pivot or PARE
```

If the user says "try again" or "now try X" specifically, reset to 0 for that X. Otherwise, treat N>=2 as "time to pivot".

## The gate-vs-trigger distinction (when to stop a user-specified plan)

The user may say "set up auto login forever". This is a TRIGGER (start this work). The GATE is: "do you have the password yet?" If no, the gate is closed — don't keep trying. The work is on hold, not abandoned.

The right report: "Auto-login setup is BLOCKED on the password gate. The work I'll do without the password: A, B, C. The work I'll do once you give me the password: D, E."

The wrong report: "OK setting up auto login now [continues to fail 5 different ways for 2 hours]."

## The "I can't" report format

When you PARE because of an auth block (or any block you can't work around), report:

1. WHAT'S BLOCKED: "Auth is blocked, can't login to Vendor."
2. WHAT'S NEEDED: "I need either: (a) the keychain unlocked + correct item, or (b) you to set the password in .env manually."
3. WHAT I'M DOING NOW: "Pivoting to X (doesn't need auth) — see commit Y for the changes."

NOT just "I can't." Always pivot to something, or admit the entire task is blocked.

## Why the v0.31 rule was insufficient for this session

The v0.31 rule was specific to "oferecer alternativas de auth". This session's failure mode was different:

- I didn't offer 5+ alternatives in one message (good, I learned that)
- BUT I kept trying auth workarounds across MANY messages (bad, persisted the loop)
- I told the user "I can do C now" but then tried auth again (bad, broke the pivot)

The HARDENED rule: **when you pivot, commit to the pivot for the rest of the session**. Don't go back. If a different part of the task needs auth, do it in a separate session.

## Cross-session reminder

If a session is failing on auth and the user says "stop", mark the auth-dependent work as BLOCKED in the ISA. Don't keep retrying auth. Don't say "I'll try one more thing." PARE.

The next session can re-attempt auth from a fresh state. That's the whole point of session boundaries.
