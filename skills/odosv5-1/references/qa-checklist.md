# ODOSv5 QA Checklist

Inspect every generated image.

## Global hard fails

Regenerate or stop if:
- page was rendered with HTML/CSS/Pillow/SVG/browser screenshot
- page looks like a worksheet, web app export, or plain document template
- page lacks ODOS fantasy packet style
- page does not visually match the inspected reference images and approved style anchor at a glance
- title or major names are misspelled
- major text is gibberish
- page has placeholder text
- content art has speckling, stippling, grain, dimpled texture, random dots, noisy water, noisy smoke, tiny clutter fields, or over-rendered surfaces
- art style is gritty realism, painterly fantasy illustration, dark splash art, realistic VTT rendering, or any style other than the provided clean cartoon fantasy references
- required page sections are missing
- candidate was written directly over a final asset instead of promoted through state
- prompt, references, dependency revisions, or output hash are not recorded
- a recurring character differs from the approved cast crop
- a scene contradicts its approved storyboard camera, geography, palette, action, or clues

## Core page QA

Page 01 hard fail:
- missing labeled At a Glance panel with at least 5 useful bullets
- read-aloud too short

Page 02 hard fail:
- icon-only stats
- missing AC/HP/Speed/ability scores
- fewer than 3 dialogue suggestions per NPC

Page 03 hard fail:
- no actions
- no AC/HP/Speed
- no combat guidance
- no villain roleplay

Page 04 hard fail:
- ascent/descent visual is reversed
- Scene 1 placed at destination/end of route
- finale not at end of path
- arrows contradict scene order

Page 05 hard fail:
- setting art consumes most of page
- missing key checks
- missing fail-forward
- missing escalation
- scene cannot be run from the page

Page 06 hard fail:
- one scene missing
- no useful DM mechanics

Page 07 hard fail:
- no combat run guidance
- no escalation
- no victory/failure outcomes

Page 08 hard fail:
- no fail-forward content
- no dialogue options

Page 09 hard fail:
- no continuation hooks

Appendix NPC hard fail:
- full D&D-style stat block missing

Appendix Monster hard fail:
- full D&D-style stat block missing
- tactics missing

Token hard fail:
- no circular token format
- text included
- noisy/gritty art
- detailed portrait-medallion rendering instead of a simple readable cartoon token

Battle map hard fail:
- not top-down
- no playable terrain
- ornate packet frame used
- isometric view
- realistic map rendering, dense terrain texture, cluttered props, or scenic illustration style instead of simplified cartoon VTT terrain

## Locked-in Final QA Addendum

These rules are mandatory and override any looser wording above.

### Tight global hard fails

Use this compact pass for every image. Do not add more QA categories unless the user asks. Regenerate or stop if any fail:

- Logo pass: required packet page lacks the real provided ODOS logo, substitutes a generic/invented logo, misspells the mark, or includes unauthorized D&D branding.
- Style pass: art must match the approved calibration proofs recorded in `style-lock.json` at a glance. Generated packet pages are not style authorities. If the result reads as a different style family, regenerate even when it is beautiful, readable, complete, or playable.
- Noise pass: image has dense texture, speckles, stippling, grain, tiny shard fields, pitted/dimpled surfaces, noisy water/steam/smoke, over-rendered props, or accumulating visual clutter.
- Use pass: saved filename does not match content, required page sections are missing, stat blocks are not mechanically runnable, token is not usable at VTT scale, or battle map is not playable.

### No completion-biased acceptance

Do not accept an image because it is finished, readable, mechanically correct, or table-usable if it fails the style or noise pass.

Forbidden acceptance language:

- "slightly detailed but accepted"
- "a bit dark but usable"
- "moderate texture but readable"
- "borderline pass"
- "not ideal but playable"
- "close enough"

Any image described that way must be regenerated or reported as unresolved.

### Stat page additional hard fails

Page 02 hard fail:

- compact NPC stat blocks omit required fields from `statblock-contracts.md`
- source NPC helper mechanics or support actions are replaced by generic filler

Page 03 hard fail:

- compact monster/villain stat blocks omit required fields from `statblock-contracts.md`
- source attacks, save DCs, rider effects, tactics, or villain pressure points are silently dropped

Appendix NPC hard fail:

- full stat block categories from `statblock-contracts.md` are omitted
- source mechanics are rewritten into weaker/generic substitutes
- missing categories are deleted instead of marked `None` or `Not listed`

Appendix Monster hard fail:

- full stat block categories from `statblock-contracts.md` are omitted
- tactics missing
- scaling notes missing
- source mechanics are rewritten into weaker/generic substitutes
- attack bonuses, save DCs, damage/effects, bonus actions, reactions, recharge notes, or rider effects are silently dropped

### Battle map additional hard fails

Battle map hard fail:

- labels, callouts, red circles, arrows, or creatures appear on the map
- terrain texture noise obscures grid/playability
- scenic/isometric illustration is substituted for overhead VTT terrain
- map looks like a realistic/detailed VTT product instead of the provided bright cartoon fantasy reference style
- subject tone makes the map dark, grim, muddy, or over-textured

### Final audit

Before reporting completion, inspect every final saved filename, not only the newest generated image. Verify:

- filename/content match
- core page order is correct
- approved style lock is still visible across pages
- stat pages are mechanically runnable
- battle maps are top-down and playable
- `manifest.json`, `page-copy-pack.json`, and `qa-report.md` reflect the actual files
- `run-state.json`, all lock files, and `asset-status.json` reflect the actual files
- no mapped asset is candidate, failed, provisional, or stale
- every mapped source SHA-256 matches its approved record
- OCR reports cover titles, names, mechanics, and required headings
- a contact sheet for each generation batch was visually reviewed
- tier manifests record matching source and prompt hashes

