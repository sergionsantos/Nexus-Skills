# Digest frontmatter schema

Produced by `scripts/finalize_doc.py`. Order is fixed. The `[[...]]` wikilink syntax is Obsidian-style; in a plain-markdown setup it is just text.

| Key | Format | Source |
|---|---|---|
| `title` | double-quoted string | video metadata (never the model's) |
| `channel` | `"[[People/<Canal-Slug>]]"` | metadata; page must exist (`--people-dir` creates a stub) |
| `source` | quoted channel name | metadata |
| `date` | `"YYYY-MM-DD"` | metadata (upload date) |
| `url` | quoted watch URL | metadata |
| `video_id` | quoted 11-char YouTube id | derived from `url`; the dedup key |
| `language` | `"EN"` etc. | `--language` |
| `duration` | `"mm:ss"` or `"h:mm:ss"` | normalised (`00:16:27` -> `16:27`) |
| `content_type` | `"ai-tech"` etc. | `--content-type` |
| `tema_principal` | ONE double-quoted line | model; fallback = first sentence of Sumário |
| `tags` | block list, 5-10 | model; fallback `[content_type, channel, youtube]` |
| `topics` | block list, 6-10 | model (omitted if absent) |
| `has_quotes` | `true`/`false` | true if a `Citações` section exists |
| `pipeline` | `nexus-youtube-deep-pipeline` | script |
| `pipeline_run` | `"YYYY-MM-DD"` | script |
| `pipeline_generator` | e.g. `"claude-sonnet"` | `--generator` |
| `fact_check` | `"pass"` or `"exceptions:N"` | `--fact-check` |

Rules: one digest per `video_id`. No trading fields (`trader`, `instrument`) outside trading folders. Body starts with an H1 and has a `Sumário` section; no wrapper fences, no text about files or tools.

## Duplicates and status
One digest per `video_id`. When an older digest of the same video is kept, it may carry `status: superseded` and `superseded_by: "[[<canonical file stem>]]"` (never delete). No `status` key means current. Indexers and agents should skip `status: superseded`. A `video_id` shared by files with unrelated titles is a metadata error (not a duplicate): fix the id, do not supersede.
