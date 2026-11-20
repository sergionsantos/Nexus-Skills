---
name: read-file-display-vs-disk-sanitization
version: 1.0.0
created: 2026-07-19
trigger: "You read_file a line that contains a secret-like literal (apiKey / Authorization / Bearer / key / token / password / secret) and the displayed output shows ***. Before trusting the display as the on-disk state, run a hexdump on the line and compare against git HEAD."
---

# read_file display sanitization vs on-disk reality

## Symptom (seen in a multi-agent integration plan)

`read_file` displays certain secret-shaped strings as `***` in its output, even when the file on disk has the real value. The display sanitization is applied to **all reads**, including reads of files you just wrote, reads of files from `git show HEAD:<file>`, and reads of files from a running process. So:

| Source read | On disk | Display shows |
|---|---|---|
| File you wrote 5 min ago | real value | `***` |
| `git show HEAD:src/lib/ai/providers.ts` | real legacy value | `***` |
| `git diff HEAD -- providers.ts` | unchanged line | `***` (both sides) |
| File after your buggy `write_file` | `***` literal (3 asterisks, no quotes) | `***` |

The display sanitization is symmetric and consistent. Diff-based detection is **impossible** for these strings (diff is on disk but you can only see `***` on both sides).

## The two-corrupt-state confusable

When the disk has a corrupted `***` (3 literal asterisks) and you `read_file` it, you see `***`. Same display as the file you want it to look like. So you cannot tell:

- (a) "Disk has the real value, display is sanitized" — happy case
- (b) "Disk has been corrupted to `***` by a previous write_file" — bug

The only way out: **bypass the display layer with `hexdump -C` on the exact line.**

## Detection recipe (10 seconds)

After any edit that touches a secret-shaped line, run:

```bash
awk 'NR==<line>' path/to/file.ts | hexdump -C
```

| Hex pattern | Meaning |
|---|---|
| `61 70 69 4b 65 79 3a 20 2a 2a 2a` | `apiKey: ***` literal — disk corrupted (3 literal `0x2a`, no quotes) |
| `61 70 69 4b 65 79 3a 20 27 ... 27` | `apiKey: '<real-value>'` — disk correct, display was sanitized |
| `61 70 69 4b 65 79 3a 20 XX XX XX XX` (5+ chars, not all `2a`) | `apiKey: '<random-string>'` — disk correct |

For `Bearer ...`, `Authorization: ...`, `password:`, `secret:`, `token:`, `key:` — same pattern.

## Why this is the right escape hatch

`write_file` writes whole files; if your source had `***` from a previous read, that's what lands on disk. `patch` with `old_string` / `new_string` writes byte-for-byte — but if **you** typed `***` as the new string (because your prior `read_file` showed `***` and you "fixed" it"), you've corrupted the file.

The escape hatch: when the displayed line shows `***`, **never copy-paste `***` into a `write_file` / `patch` payload**. Either:

1. Use `hexdump` first to see what's actually on disk, OR
2. Use a placeholder pattern (`API_KEY_PLACEHOLDER`) in two patches (insert-with-placeholder, then swap-placeholder-for-real-string). The reference `write-file-api-key-sanitization-corrupts-disk.md` already documents the two-patch recipe.

## A second variant: git show sanitizes too

`git show HEAD:<file>` displays `***` for the same reason as `read_file`. Diff to HEAD is sanitized on both sides. Use `hexdump` instead.

## A third variant: patch tool can garble long replacements

Observed in the same session: when `patch` was told to replace a 2-character marker with a longer multi-line string, the diff display showed the right text but `hexdump` showed the file was missing chunks. The patch tool seems to silently truncate long replacements.

The fix is the same: **always `hexdump` the line after a `patch`** for any non-trivial replacement.

## Recovery recipe (when you've corrupted a file)

1. `git checkout HEAD -- path/to/file.ts` (restore from last commit)
2. `awk 'NR==<line>' path/to/file.ts | hexdump -C` (verify disk now has real values)
3. Re-apply your edit **without** passing through any `***` from a display. Either:
   - `git show HEAD:path/to/file.ts > /tmp/orig.ts` then `awk 'NR==<line>' /tmp/orig.ts | hexdump -C`
   - If `/tmp/orig.ts` also shows `***`, restore from your editor's local history (the IDE keeps git objects locally) or ask the user.

## Lesson for future edits in this repo

- **Trust disk, distrust display.** For secret-shaped strings, the displayed `***` is a hint, not the truth.
- **Hexdump the line after any write_file or patch that touches a secret-shaped line.** 1-second check, catches both corruption variants.
- **Never copy `***` from a display into a write tool.** If you see `***` and need to know what's actually there, hexdump.
- **Patch tool can garble long replacements.** Hexdump after patch for non-trivial edits.
- **The two sanitizations are different.** `write_file` corrupts; `read_file` hides. Both manifest as `***`. Different fixes.

## Related

- `references/write-file-api-key-sanitization-corrupts-disk.md` — write-side corruption (canonical case this skill extends)
- `references/verify-your-own-tool-before-blaming-inputs.md` — general "tool is lying" reflex; this is the specific read_file-vs-disk instance
- `nexus-discipline` SKILL.md §1 (verify gates — predict-then-run with byte-level dump catches both corruption directions)