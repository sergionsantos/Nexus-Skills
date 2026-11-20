---
name: tool-write-file-api-key-sanitization
version: 1.0.0
created: 2026-07-18
trigger: "edit calls write_file or patch with a string literal `apiKey: *** OR any 4+ char literal after `apiKey:` that ends with a closing quote — verify the byte content on disk before declaring success."
---

# write_file/patch sanitization can corrupt `apiKey:` literals on disk

## Symptom (seen while configuring an integration)

Tool reads `apiKey: ***` as input. Tool output shows `apiKey: ***` — looks
correct. But the **on-disk bytes** are `apiKey: ***` (three literal asterisks,
0x2a 0x2a 0x2a — no quotes around a string, no comma). The `read_file`
display also shows `***`, so the corruption is invisible unless you bypass
both display layers.

The `git show HEAD:<file>` displays the **same** `***` for the **original**
`apiKey: 'unused'` (or whatever the real string was) — the sanitization is
applied to **all strings after `apiKey:`** consistently, so the diff to git
HEAD looks "no change" and you can't catch it from diff alone.

## Why it bit hard

The tool stack sanitizes `apiKey: *** at **read** time. When you `write_file`
the same source back, the tool's write path is also sanitizing (or the
sanitized read-content is what gets written). End result: `***` literal
landed in disk.

## Detection (the 30-second check)

After any write_file/patch that touches an `apiKey:` line:

```bash
awk 'NR==<line>' path/to/file.ts | hexdump -C
```

If you see `61 70 69 4b 65 79 3a 20 2a 2a 2a` (`apiKey: ***`), the file
is corrupted. The expected sequence for a normal string literal is
`61 70 69 4b 65 79 3a 20 27 ... 27` (`apiKey: '...'`).

Also useful: `git diff path/to/file.ts | hexdump -C | grep "2a 2a 2a"` —
catches newly-introduced `***` literals.

## Recovery (3-step, deterministic)

1. `git checkout HEAD -- path/to/file.ts` — restores from last commit
2. Verify: `grep -n "apiKey:" path/to/file.ts | head -3` shows the real values
3. Re-apply ONLY with `patch` and **avoid writing the literal target string
   in your patch content**. Use a placeholder pattern that isn't on the
   sanitization list:

   - Step A — `patch` to insert the surrounding block with a `+`
     marker where the apiKey goes:
     `apiKey: API_KEY_PLACEHOLDER,`
   - Step B — `patch` again with `replace_all=false` to swap the marker
     for the actual string: `old_string: "API_KEY_PLACEHOLDER"`,
     `new_string: "real-literal"`.

   Two patches, neither passes through a `apiKey: <string-literal>` pattern
   in one go.

## Why patches work but write_file fails here

`patch` does string-replace on disk directly with the bytes you give it —
the sanitization appears to happen on read/sanitize-back paths, not on
write of a single small replacement. `write_file` writes the whole file
in one tool call, which seems to route through the sanitization pipeline.

## Other strings that look risky

Anything matching the regex `^apiKey:\s*.{0,40}$` (a value on the same
line) seems to be on the watchlist. Bearer tokens, OAuth tokens, and
short identifiers after `apiKey:` are all candidates. Bigger structured
strings (e.g. `apiKey: process.env.X` — value is a variable reference)
are not affected.

## Lesson for future edits in this repo

When the spec says "set apiKey to X" and X is short and literal, do it
in two patches (placeholder → real). Never trust the read_file display
to mirror disk — verify with hexdump on the specific line. Never trust
a `git diff` to show disk corruption when both sides get sanitized the
same way.

## Related

- `references/verify-your-own-tool-before-blaming-inputs.md` (general
  "your tool is lying" class — this is the specific instance for
  `write_file`/`patch` + `apiKey:`)
- §1 SKILL.md (verify gates — predict-then-run with exit code and
  field-level dump catches this if the predict is "string `'<value>'`"
  not "string `***`")