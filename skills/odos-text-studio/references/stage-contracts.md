# ODOS Text Stage Contracts

Use these contracts to generate original, practical D&D 5e-compatible content for a compact 3-4 hour one-shot. Write concise, table-ready prose. Avoid copyrighted settings, proprietary named characters or monsters, and copied official text.

Do not include process notes, approvals, audits, QA sections, image prompts, or commentary about generation.

## Shared Source Priority

Resolve conflicts in this order:

1. `project.json` constraints and banned concepts
2. `selected_concept.md`
3. Earlier completed stage files in generation order
4. Creative invention needed to connect the material

Never silently change established names, motives, clue truths, encounter locations, rewards, or mechanics. When a genuine contradiction exists, preserve the latest completed upstream stage and make downstream content conform to it.

## Monthly Options

File: `monthly_options.md`

Create exactly 20 entries in each of three independent columns. Each cell should be distinct, specific, and usable with any selection from the other columns. Favor one-shot-sized concepts with a strong table activity, clear stakes, and a fantasy problem that can resolve in 3-4 hours.

Return only this Markdown table, with exactly 20 data rows:

```markdown
| # | Adventure Style / Structure | Main Quest Premise | Antagonist |
|---:|---|---|---|
| 1 | ... | ... | ... |
```

Rules:

- Number rows 1 through 20.
- Treat cells as independent options, not matched row concepts.
- Keep each cell to roughly 8-30 words.
- Make Style describe play structure, not plot dressing.
- Make Quest state an actionable objective and stakes.
- Make Antagonist describe a usable opposing force, motive, and pressure.
- Avoid final NPC proper names here; establish names after selection so history can be checked.
- Do not add text before or after the table.

## Adventure Skeleton

File: `adventure_skeleton.md`

Read: `project.json`, `selected_concept.md`, and the prior-name avoidance list.

Target: 1,200-1,800 words.

Use exactly these headings:

```markdown
# Adventure Skeleton
## Title Candidates
## One-Sentence Pitch
## Adventure Promise
## Page-by-Page Packet Plan
## Three Core NPCs
## Scene Flow
## Key Locations
## Encounter Skeleton
## Clue and Fail-Forward Structure
## Rewards and Treasure
## Asset Checklist
```

Requirements:

- Supply 5 title candidates and identify one working title.
- Define a beginning, escalating middle, finale, and likely epilogue within 3-4 hours.
- Build 3 core NPCs with distinct names, roles, motives, visible tells, and table utility.
- Plan at least 3 major scenes plus a finale.
- Include two locations suitable for useful top-down battlemaps.
- Make failure change circumstances without ending play.
- Establish the truths that later clues will reveal.
- Keep the asset checklist factual and style-neutral.

## DM Packet Draft

File: `dm_packet.md`

Read: `project.json`, `selected_concept.md`, `adventure_skeleton.md`.

Target: 3,000-4,500 words.

Use exactly these headings:

```markdown
# DM Packet Draft
## Adventure Overview
## Read-Aloud Opening
## Starting Hook
## Important NPCs
## Adventure Flow
## Locations
## Clues and Secrets
## Encounters
## Treasure and Rewards
## Finale
## DM Quick Reference
```

Requirements:

- Give the DM the truth, stakes, antagonist plan, timeline, and player objective early.
- Keep read-aloud passages short and sensory, normally 40-100 words.
- For each scene provide purpose, immediate situation, likely approaches, checks only where failure matters, consequences, and exits.
- Use DCs appropriate to the selected level range and difficulty.
- Do not gate essential progress behind one roll.
- Keep locations spatially understandable and actionable.
- State encounter goals beyond reducing enemies to zero hit points where appropriate.
- Do not write final formal stat blocks or image prompts.
- End with a dense quick-reference section usable during play.

## NPC Suite

File: `npc_suite.md`

Read: `project.json`, `selected_concept.md`, `adventure_skeleton.md`, `dm_packet.md`.

Target: 1,800-2,800 words.

Use exactly these headings:

```markdown
# NPC Suite
## NPC Roster Table
## Core NPC Profiles
## NPC Stat Blocks
## Antagonist Deepening
## Improvisation Support
## Art/Token Needs
```

Requirements:

- Preserve all established names and roles.
- Include role, objective, fear, leverage, voice, visible tell, starting attitude, knowledge, lie or omission, and change trigger for each core NPC.
- Make the antagonist's plan playable rather than purely historical.
- Include compact table-use statistics for NPCs likely to enter danger: AC, HP, speed, key saves or skills, attacks/actions, and one signature feature.
- Keep these light NPC blocks distinct from the formal blocks in `stat_blocks.md`.
- Add improvisation lines or reactions for likely player surprises.
- Keep Art/Token Needs to subject identity and required coverage only. Do not use style language.

## Clue Web

File: `clue_web.md`

Read: `selected_concept.md`, `dm_packet.md`, `npc_suite.md`.

Target: 1,600-2,400 words.

Use exactly these headings:

```markdown
# Clue Web
## Investigation / Discovery Goal
## Truth Map
## Clue Roster Table
## Three-Clue Rule Coverage
## Scene-by-Scene Clue Placement
## NPC Knowledge Matrix
## Red Herrings / False Leads
## Fail-Forward Toolkit
## Player-Facing Handout Seeds
## Clue Web Quick Reference
```

Requirements:

- Define each conclusion players need, then support it with at least 3 independently discoverable clues.
- Distinguish observable clue, interpretation, source, access method, and consequence.
- Never require a successful check to notice an essential clue; checks may add speed, precision, safety, or context.
- Make NPC knowledge consistent with motives and scene access.
- Use at most 2 fair false leads and give each a concrete disconfirming detail.
- Include fail-forward consequences for missed, destroyed, ignored, or misunderstood evidence.
- Handout seeds must identify plausible in-world artifacts without explaining solutions to players.

## Stat Blocks

File: `stat_blocks.md`

Read: `project.json`, `dm_packet.md`, `npc_suite.md`, `clue_web.md`.

Target: 2,200-3,600 words.

Use exactly these headings:

```markdown
# Stat Blocks
## Stat Block Roster
## Design Notes
## Formal Stat Blocks
## Encounter Packages
## Boss / Finale Tuning
## Quick Reference
```

Requirements:

- Create original 5e-compatible stat blocks; do not copy official prose or proprietary creatures.
- Tune expected threat to level range, party size, and requested difficulty.
- Every formal creature block needs name, size/type/alignment, AC, HP with dice expression, speed, six abilities, saves, skills, resistances/immunities/senses/languages where relevant, challenge estimate, proficiency bonus, traits, actions, reactions or bonus actions where useful, and tactics.
- Make mechanics express story identity and remain easy to run.
- Encounter Packages must state composition, starting positions, terrain, enemy objective, morale, escalation, and noncombat resolution.
- Provide explicit boss tuning levers for weaker and stronger parties.
- Avoid long spell lists. Put needed effects directly in the block when possible.

## Player Handouts

File: `player_handouts.md`

Read: `adventure_skeleton.md`, `dm_packet.md`, `npc_suite.md`, `clue_web.md`, `stat_blocks.md`.

Target: 1,200-1,800 words total.

This stage is a text-only production brief. Describe exactly 3 full-page, player-facing, image-heavy artifacts. Each must be a different artifact type and useful for inspection, comparison, inference, or encounter interaction. Do not create handout images or deterministic page layouts.

Use exactly these headings:

```markdown
# Player Handouts
## Handout 1
### Handout Type
### Player-Facing Artifact
### Image-Heavy Description
### Readable Text On The Handout
### Physical / Digital Use
## Handout 2
### Handout Type
### Player-Facing Artifact
### Image-Heavy Description
### Readable Text On The Handout
### Physical / Digital Use
## Handout 3
### Handout Type
### Player-Facing Artifact
### Image-Heavy Description
### Readable Text On The Handout
### Physical / Digital Use
```

Rules:

- Include only what players may safely see.
- Do not include DM notes, solution keys, hidden truths, clue labels, correct interpretations, secret identities, motives, spoiler warnings, or encounter answers.
- Let visible symbols, routes, marks, fragments, labels, diagrams, lists, sketches, and contradictions carry the usable information.
- Keep in-world written text short enough to render legibly.
- Do not include art style, rendering, palette, camera, lighting, medium, or page-layout directions.
- Good types include an annotated map, torn letter, public notice, journal page, riddle sheet, folk verse, manifest, field note, official document, or mechanism diagram.

## Visual Asset Brief

File: `visual_asset_brief.md`

Read every completed packet stage.

Target: 1,000-1,600 words.

Use exactly these headings:

```markdown
# Visual Asset Brief
## Use Boundary
## Cover Subject Inventory
## Location Inventory
## NPC Inventory
## Monster / Hazard / Boss Inventory
## Handout / Prop Inventory
## Battlemap Inventory
## VTT Token Inventory
## Asset Checklist
```

Under `## Use Boundary`, write exactly:

`This file is subject inventory only. ODOSv4 owns image references, page samples, final art style, visual-noise controls, and image prompt construction.`

Requirements:

- Describe only concrete subject facts that ODOSv4 needs to identify assets.
- For important people, creatures, locations, props, maps, and tokens, include 3-6 stable identity anchors when known: role/species, age impression, build/silhouette, face/expression, clothing/gear, carried prop, visible mark, scale, terrain, or story-critical spatial relationship.
- Use color only when it is a literal in-world identity fact such as a red sash or blue wax seal.
- List weather, smoke, dust, magic, debris, or particles only when they are story facts.
- Do not use style vocabulary, including cartoon, storybook, painterly, realistic, gritty, cinematic, ornate, cel shaded, parchment, bold outlines, smooth shading, dramatic lighting, atmospheric, or high detail.
- Do not provide image-model phrases, camera angles, compositions, palettes, textures, page layouts, or generation prompts.
- Include exactly 2 battlemap subjects and all important NPC, monster, boss, and hazard VTT token subjects.
