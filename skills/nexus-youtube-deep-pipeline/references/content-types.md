# Content Types

Matching deep templates to the kind of content being processed.

## Taxonomy ("surface" = a lighter, standard summary workflow, not bundled here)

| Content Type | Use When | Deep Template |
|---|---|---|
| `personal-development` | Life advice, mindset, relationships, mental health, personal growth | `deep_personal_development.md` |
| `trader-biography` | Interview centred on a trader's life/journey | `deep_biography.md` |
| `trading-psychology` | Fear, discipline, emotions in trading | (use surface — psychological insights don't need deep) |
| `trading-strategy` | Setup, entry, exit mechanics | (use surface — strategy details fit in 20KB) |
| `ai-tech` | Agents, LLM, frameworks, MCP, RAG | `deep_business.md` |
| `business` | Operations, sales, hiring, growth, pricing | `deep_business.md` |
| `health` | Nutrition, sleep, longevity, medical | `deep_business.md` (use bio/timeline sections if guest has story) |
| `pkm-obsidian` | Obsidian, PKM, second brain | (use surface — niche technical) |
| `tools-productivity` | Workflow, automation, apps | (use surface — usually short) |
| `protocols` | MCP, A2A, AG-UI specs | (use surface — technical specs) |
| `off-topic` | Fitness, lifestyle, celebrities | **Skip** — no knowledge value |
| `real-estate` | Property market, mortgages, rental | `deep_business.md` |

## Decision rules

These rules only pick a default when the user did not say how deep to go. An explicit request for deep (or surface) always wins, at any duration: a 10-minute video can be processed deep, and the output size follows the transcript (see `size_profile` in `scripts/generate_deep_doc.py`).
1. **Is biographical material >30% of transcript?** Use deep biography template.
2. **Is framework density >1 framework per 10min?** Use deep template.
3. **Is duration >90min?** Use deep template.
4. **Is duration <30min?** Default to surface, unless the user asked for deep.
5. **Is guest the central figure (interview, monologue, keynote)?** Use deep.
6. **Is content a tutorial, news, or opinion piece?** Default to surface, unless the user asked for deep.

## Tie-breaker

If genuinely 50/50 between surface and deep, default to **deep** for any of:
- Person with public track record (author, founder, athlete, executive)
- Quotes that might be cited later
- Personal story (family, death, founding, near-death)

Default to **surface** for:
- Round-table / multi-guest (>2 voices)
- Pure technical walkthrough
- News/announcement episodes
