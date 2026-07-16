# ODOSv5 Stat Block Contracts

ODOSv5 must produce D&D 5e / 5.5e usable stat information.

## Core packet vs appendix

Core packet pages use compact stat blocks.
Appendix pages use full stat blocks.

Do not put full appendix stat blocks on crowded core pages unless the page has space.

## Compact NPC stat block

Every NPC card on Page 2 must include at minimum:

```text
AC [number] | HP [number] | Speed [number] ft.
STR [n] DEX [n] CON [n] INT [n] WIS [n] CHA [n]
Skills: [skill +bonus], [skill +bonus]
Senses: passive Perception [number]
Action: [Name]. +[bonus] to hit, [damage/effect].
Trait: [Name]. [short mechanical support effect].
```

Optional if space:
- Languages
- Reaction
- Save bonus

Do not use icon-only stats.

## Compact monster stat card

Every monster/minion card on Page 3 must include at minimum:

```text
[name]
[type], [role], CR [rating]
AC [number] | HP [number] | Speed [number] ft.
STR [n] DEX [n] CON [n] INT [n] WIS [n] CHA [n]
Senses: [senses], passive Perception [number]
Trait: [Name]. [short effect].
Action: [Name]. +[bonus] to hit or DC [n] save, [damage/effect].
Tactics: [short combat behavior].
```

For intelligent villains, include:
- Languages
- 2+ actions if possible
- a roleplay/tactics section

## Full NPC appendix stat block

Appendix NPC pages must include:

```text
NAME
Medium humanoid, alignment

Armor Class [number]
Hit Points [number]
Speed [number] ft.

STR DEX CON INT WIS CHA
[n] [n] [n] [n] [n] [n]

Saving Throws [if any]
Skills [list]
Damage Resistances [if any]
Damage Immunities [if any]
Condition Immunities [if any]
Senses [list], passive Perception [number]
Languages [list]
Challenge [rating] (PB +[n])

Traits
[trait name]. [mechanical text]

Actions
[action name]. [attack/save/effect text]

Bonus Actions
[if any]

Reactions
[if any]

Tactics
[how to run them at the table]
```

## Full monster / villain appendix stat block

Appendix monster/villain pages must include:

```text
NAME
Size type, alignment or temperament

Armor Class
Hit Points
Speed

STR DEX CON INT WIS CHA

Saving Throws
Skills
Damage Vulnerabilities
Damage Resistances
Damage Immunities
Condition Immunities
Senses
Languages
Challenge / PB

Traits
Actions
Bonus Actions
Reactions
Legendary Actions or Lair Effects if appropriate
Tactics
Scaling Notes
Dialogue / Roleplay if intelligent
```

## Stat block QA hard fails

Hard fail if:
- AC is missing
- HP is missing
- Speed is missing
- ability scores are missing
- actions are missing
- attack bonus or save DC is missing for attacks/effects
- monster/villain tactics are missing
- appendix pages do not include full stat block categories
- stats are replaced by icons only

## Locked-in Stat Fidelity Addendum

These rules are mandatory and override any looser wording above.

Compact does not mean decorative, impressionistic, or incomplete. Full does not mean rewritten from memory. Source mechanics must be preserved unless the source is absent or internally contradictory.

### Stat-safe copy workflow

Before generating Page 2, Page 3, or any appendix stat page, create stat-safe copy from source files and validate it against this file.

Validation questions:

1. Can a DM run this NPC/monster from the generated page without opening another file?
2. Are all source attack bonuses, save DCs, damage/effects, traits, reactions, bonus actions, tactics, and scaling notes preserved or explicitly marked as absent?
3. Are compact stat blocks compact only in wording, not in required mechanical categories?
4. Are appendix stat blocks full D&D-style blocks, not enlarged compact blocks?
5. Did any aesthetic/layout choice remove mechanics? If yes, regenerate with less art or split content.

### Compact stat blocks

Compact stat blocks must still include every required field already listed above. If required compact fields do not fit, reduce art/decorative copy or move nonessential flavor to appendix pages; never omit required mechanics.

If the source NPC has helper actions, reactions, support traits, tool proficiencies, noncombat mechanics, attack rider effects, recharge notes, or special tactical rules, preserve the most table-relevant ones. Do not replace them with generic attacks unless no source mechanics exist.

Compact monster cards must preserve real attack bonuses or save DCs and real damage/effects. Do not turn source actions into generic names like `Attack` or omit rider effects such as push, grapple, prone, frightened, healing suppression, recharge, or reaction restrictions.

### Full appendix stat blocks

Appendix NPC, monster, and villain pages must use the exact source stat block when available, preserving category names and mechanics. If a category truly does not exist in source, write `None` or `Not listed` rather than deleting the category.

Full appendix stat blocks must include the full D&D-style category set from this file, including tactics and scaling notes for monsters/villains and roleplay/dialogue for intelligent creatures.

### Additional stat QA hard fails

Hard fail if:

- compact stats omit required fields from this contract
- full appendix stats omit required categories instead of marking absent fields as `None` or `Not listed`
- source mechanics were rewritten into weaker or generic substitutes
- attack rider effects, save DCs, recharge notes, bonus actions, reactions, tactics, or scaling notes were silently dropped
- the generated page cannot run the creature/NPC at the table without opening another file

