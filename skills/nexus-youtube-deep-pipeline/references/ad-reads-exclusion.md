# Ad Reads Exclusion

Long-form interviews (90min+) typically have 2-4 sponsor reads. They occupy 5-10% of runtime but add zero knowledge value. **Always exclude.**

## Heuristic for unknown channels

A paragraph is an ad read if it contains **2+ of these keywords**:

- "this episode is brought to you by"
- "today's sponsor"
- "head to [domain]"
- "go to [domain]"
- "code [WORD]" (with discount code)
- "link in the show notes"
- "today's episode is sponsored"
- "thanks to [brand] for sponsoring"

AND it lacks first-person guest content ("I", "we did", "my experience", "for me").

**Confidence threshold:** if 2+ keywords AND no first-person content → 95% ad read, exclude entire paragraph.

## Known sponsor reads by channel

### The Diary of a CEO (DOAC) — UK
- **LinkedIn Ads** — mid-roll, mentions "linkedin.com/diary" + "$250 credit"
- **Flightcast** — mid-roll, podcast hosting platform, "flightcast.com/doac"
- **Fiverr Pro** — mid-roll, "pro.fr.com" (note the ".fr" not ".com" — easy to miss)

### Tim Ferriss Show
- **Athletic Greens / AG1** — recurring
- **Helix Sleep** — recurring
- **4 Hour Body / Tools of Titans book plugs** — not paid, but skip in favor of content

### Huberman Lab
- **Thesis** (nootropics) — recurring
- **AG1** (supplements) — recurring
- **Momentous** (supplements) — recurring
- **Eight Sleep** (mattress) — recurring

### The Knowledge Project (Shane Parrish)
- Less sponsor-heavy; usually 0-1 reads per episode
- Helm.ai / Eight Sleep occasionally

### Lex Fridman Podcast
- Long-form (3h+), minimal sponsor reads
- When present: Magic Mind, AG1, Athletic Greens

### Acquired (podcast about companies)
- Long episodes, minimal ads
- Occasionally: Notion, Vanta

## After exclusion

The cleaned transcript should be ~5-10% shorter. If your "cleaned" version is the same length as the raw, the ad reads were not excluded.

## Verification

Spot-check: search the cleaned transcript for "linkedin.com", "flightcast.com", "AG1", "Athletic Greens". If any are present, exclusion failed.
