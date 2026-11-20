# Deep Processing Checklist

What to look for when reading a transcript in chunks to maximize extraction. Run through this list **for every chunk** before moving to the next.

## Per-chunk checks

### 1. Sponsor / ad reads (EXCLUDE)
- Phrases like "this episode is brought to you by", "today's sponsor is", "go to [domain]", "code [WORD]"
- "head to [URL]", "link in the show notes", "discount code"
- Channel-specific: DOAC = LinkedIn Ads / Flightcast / Fiverr Pro; Tim Ferriss = Athletic Greens / Helix Sleep / 4 Hour Body; Huberman = Thesis / AG1 / Momentous
- **Rule:** if a paragraph contains 2+ sponsor keywords AND no first-person guest content, EXCLUDE entire paragraph.

### 2. Frameworks / concepts
- Numbered lists ("there are 4 vectors...", "the value equation has 4 components...")
- Mental models ("think of it like a tower of blocks", "imagine you're a plant...")
- Heuristics with catchy names ("the 80-year-old mindset", "doors metaphor", "fog starts to clear")
- **Action:** if a concept has a name + a structure, add to **Conceitos Centrais** with the structure.

### 3. Verbatim quotes
- Lines that start with `>>` (transcript speaker tag) followed by impactful phrasing
- Phrases with emphasis, alliteration, or rhythm
- Direct advice ("here's what I'd tell my 20-year-old self", "the only way to...")
- **Action:** preserve verbatim quotes (up to the count in the SIZING block; 40 for a 90+ minute source), grouped by theme, in **Citações Relevantes**.

### 4. Biographical fragments
- Family references: "my dad", "my mom", "my wife", "my kids"
- Age markers: "when I was 26", "at 24 years old", "before the age of 25"
- Career milestones: "when I exited", "the $46M deal", "we launched..."
- Emotional events: "when my mom died", "the lawsuit", "I tore my colon"
- **Action:** collect ALL biographical fragments across chunks, then reconstruct chronologically in **A Linha Pessoal**.

### 5. Numeric / specific claims
- Dollar amounts: "$106 million", "$46M", "$240,000 opportunity cost"
- Time periods: "4 weeks later", "30 to 40 years", "in 18 months"
- Specific people: "Bill Ackman", "Steve Wynn", "Tony Robbins", "Arthur Brooks"
- Books, movies, references: "Berkshire Hathaway", "the Innovator's Dilemma"
- **Action:** these are the EASIEST to fabricate and EASIEST to verify. Add to fact-check candidate list.

### 6. Stance / opinion vs fact
- "I think", "in my opinion", "I'd say", "for me" → opinion
- "There's research", "studies show", "the data says" → fact-claim
- "I tried", "I did", "we did" → first-person experience
- **Action:** opinions can be paraphrased. First-person experience and research claims should be quoted verbatim.

### 7. Comparisons / contrasts
- "A vs B" patterns
- "The fastest way to $10M is NOT the fastest way to $100M"
- "Most people think X; I think Y"
- **Action:** comparisons often make great insights. Capture as Mudanças de Mindset entries.

## Cross-chunk checks (after all chunks read)

### 8. Contradictions / evolutions
- Did the guest say X in chunk 1 and revise in chunk 4?
- Did the framing shift (e.g., "this is what I thought" → "now I think")?
- **Action:** flag in Metadados Internos with `evolução: true` tag.

### 9. Forgotten / dropped threads
- Did a story start in chunk 2 and never resolve?
- Did a person's name appear and not get explained?
- **Action:** search the cleaned transcript for resolution. If not found, note in `gaps` for fact-check.

### 10. Quotes that don't have context
- A quote like "I tried to change as little about my life as possible" — what's the context?
- **Action:** locate the surrounding paragraph, include both in Citações Relevantes.

## Time tracking

- Each chunk should take ~2-3 minutes to read with this checklist
- Total reading time: 8-12 minutes
- LLM generation: 5-8 minutes (4 chunks + 1 fact-check)
- Patches: 2-5 minutes (if any)
- **Total: ~15-25 minutes** for a 2h video

If you're going faster than this, you're probably missing ad reads or bios.
