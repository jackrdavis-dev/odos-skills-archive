---
name: odosv5-1
description: Convert an ODOS Studio or Packet Foundry adventure export into a stateful One Dollar One Shot v5.1 raster PNG packet and locked Patreon distribution. Use for complete ODOS packet pages, character and scene art, appendix/stat pages, player handouts, VTT tokens, battle maps, PDFs, and Basic/Deluxe/Premium archives. Require one explicit four-proof visual checkpoint, preserve the original ODOSv5 page and art references throughout generation, and create final production PNGs only through image-generation calls.
---

# ODOSv5.1 Stateful Packet Compiler

## Non-negotiable production mode

Generate every final page, appendix page, token, handout, and map through an actual image-generation call. Never substitute HTML, CSS, Pillow, SVG, browser rendering, canvas, DOCX, or deterministic page compositing for production PNGs.

Use deterministic scripts only for state, prompt compilation, crops, OCR, QA contact sheets, hashes, PDF embedding, tier copying, and ZIP packaging. Stop if image generation is unavailable.

## Start and validate

Run:

```powershell
python scripts/validate_reference_assets.py
python scripts/scaffold_odosv5_project.py <packet-dir> --title "Adventure Title" --slug "adventure-title"
```

State remains authoritative in:

- `run-state.json`
- `approval-policy.json`
- `style-lock.json`
- `cast-lock.json`
- `scene-lock.json`
- `art-plates.json`
- `asset-status.json`
- `distribution-map.json`

Manifest status moves only through `scaffolded -> calibrating -> generating -> qa_failed | approved -> packaged`. Dependency changes invalidate affected assets.

## Immutable reference authority

Use these roles exactly.

### Page composition

The original ODOSv5 files in `assets/page-samples/` control packet composition, density, title placement, panel geometry, art-to-text ratio, footer treatment, and visual hierarchy. They may contain unrelated adventure art; never copy that story content or those characters.

Route them according to `references/page-reference-routing.json`:

- Cover: `Rumble TM Cover.png`
- Scene-flow page: `ig_08e5f85f801b3b79016a4b8342672481968fd37f4b8bd2fee6.png`
- Other core and appendix pages: `ig_0037031b75f5be41016a4b799ff8388194b04ded71a7e313f8.png`
- Player handouts: no packet-page sample; preserve their successful in-world artifact treatment

The compiler refuses a packet page that lacks its routed page sample.

### Illustration style

The original images in `assets/art-style-samples/` are the permanent rendering authority for characters, monsters, scenes, appendix art, tokens, and maps:

- `generated-hero-pantheria-cartoon-v6.png`
- `Saedaxi Midnight Escape.png`
- `Tavern People.png`

Every visual image call except in-world handouts must directly include at least one original art-style image. Generated calibrations, cast sheets, crops, storyboards, art plates, earlier pages, and earlier maps never replace the original style authority. The compiler enforces this rule.

Target bold cartoon contour work, simplified expressive anatomy, saturated clean colors, firm two-to-three-step cel shading, clear silhouettes, and low surface noise. Reject painterly blending, semi-realistic rendering, soft anime polish, gritty textures, speckling, grain, and recursive style drift.

### Identity, composition, and branding

- Approved cast crops control recurring identity only.
- One approved scene panel or art plate controls composition only.
- `assets/logos/Logo 4.png` controls branding only and is mandatory on packet pages.
- Page samples never control illustration rendering.

Use at most five references per call. A normal packet-page budget is page sample, original art style, relevant art plate, exact logo, and one identity or scene reference.

## One visual checkpoint

The default policy is `single_visual_checkpoint`. Do not auto-approve style.

Before the production run, generate exactly four proofs:

1. one recurring character
2. one multi-character action scene
3. one complete Scene page using the restored ODOSv5 Scene page sample
4. one complete playable battle map

Every proof must directly include the appropriate original references. Display the four proofs together and wait for one explicit user approval. Repair only the failing proof when requested.

Record the accepted checkpoint:

```powershell
python scripts/odosv5_state.py --packet-dir <packet-dir> approve-style \
  --character-proof <character.png> \
  --scene-proof <scene.png> \
  --page-proof <scene-page.png> \
  --map-proof <battle-map.png> \
  --reference art-1=<generated-hero-pantheria-cartoon-v6.png> \
  --reference art-2=<Saedaxi Midnight Escape.png> \
  --reference art-3=<Tavern People.png> \
  --reference page-cover=<Rumble TM Cover.png> \
  --reference page-scene=<ig_0037031b75f5be41016a4b799ff8388194b04ded71a7e313f8.png> \
  --reference page-flow=<ig_08e5f85f801b3b79016a4b8342672481968fd37f4b8bd2fee6.png> \
  --reference logo=<Logo 4.png> \
  --approved-by <user-name> \
  --qa-report <visual-checkpoint-qa.json>
```

After this single checkpoint, use `codex-autonomous-qa` for cast recording, scene recording, art plates, candidate promotion, run approval, and packaging. Stop only for a requested creative change, source ambiguity affecting story meaning, three failed candidates for one asset, stale hashes, unavailable image generation, or packaging failure.

## Production workflow

### Source and copy

Read `references/source-file-map.md`. Build `page-copy-pack.json`, validate it with `scripts/validate_page_copy_pack.py`, and validate stat mechanics against `references/statblock-contracts.md`.

### Cast and scenes

Build a composite cast sheet and isolated crop for every recurring character. Every cast generation call must directly include an original art-style sample. Record source attributes, equipment, ancestry, proportions, costume, and forbidden drift.

Build one differentiated storyboard containing every major scene. Every storyboard generation call must directly include an original art-style sample. Record camera, geography, palette, action, and visible clues. Crop the approved storyboard into isolated scene references.

Record cast and scenes after the four-proof checkpoint using persisted QA evidence. These are state locks, not additional user approval stops.

### Art plates

Generate text-free character, creature, scene, and repeated-prop plates before packet pages. Each plate call must include an original art-style reference plus only the relevant identity or scene references. Never use an all-cast sheet for a single-character plate.

Generated art plates preserve identity and composition; they do not become style masters.

### Packet pages

Build one compact asset-spec JSON per page. Include its routed original page sample, an original art-style sample, exact logo, and relevant approved plate. Compile with `scripts/compile_odosv5_prompt.py`; never edit compiled prompts.

Generate one candidate, register it, inspect the saved PNG, run OCR where applicable, record QA, and promote only a passing candidate. Use targeted repair for text, identity, logo, layout, or art-style failures.

The complete Scene page from the checkpoint is the first packet proof. Compare all later page contact sheets against both that approved page and the original routed page samples. Reject pages that collapse into generic six-box templates or lose the reference page’s art-to-text balance.

### Player handouts

Keep handouts image-heavy, player-facing, spoiler-safe, and formatted as in-world artifacts. Do not add ODOS packet chrome, logo, or stat-page framing. Preserve the direct handout workflow that does not depend on recurring cast or scene-style intermediates.

### Tokens

Use an approved identity crop plus an original art-style sample. Require one subject, a clean circular frame, simple background, no text, and a readable silhouette at 128 px.

## Battle maps

The fourth visual-checkpoint proof is the approved map authority for the run, but it never replaces the original art-style sample. Every production map call must include both.

Require:

- strict 90-degree orthographic top-down view
- a subtle aligned square grid
- at least three tactically distinct zones
- at least two usable entrances or exits
- connected movement routes
- meaningful cover, hazards, elevation cues, or interactable terrain
- clear encounter space without large dead zones
- restrained prop density
- no text, labels, creatures, decorative packet frame, perspective, or horizon

Record a passing map with:

```powershell
python scripts/odosv5_state.py --packet-dir <packet-dir> record-qa \
  --asset <battle-map-path> --result pass \
  --checked-by codex-autonomous-qa \
  --visual-report <battle-map-qa.json>
```

The report must satisfy every field in `references/battle-map-qa-schema.json`. A merely overhead or attractive map is not enough; it must be tactically useful and match both the original art style and approved map proof.

## Immutable candidate loop

For every production asset:

1. Write a compact asset spec with content, references, required text, invariants, characters, scene, art plates, and copy keys.
2. Compile with `scripts/compile_odosv5_prompt.py`.
3. Generate exactly one candidate into `working/candidates/<run-id>/`.
4. Register with `odosv5_state.py register-candidate`.
5. Inspect the saved candidate and batch contact sheet.
6. Run OCR for packet and stat pages.
7. Record QA; maps additionally require `--visual-report`.
8. Promote only a passing candidate.

Never overwrite final assets directly from the image-generation output folder.

## Packaging

When every mapped asset is approved, current, and hash-matched:

```powershell
python scripts/odosv5_state.py --packet-dir <packet-dir> approve-run \
  --approved-by codex-autonomous-qa --qa-report <final-run-qa.json>
python scripts/build_odosv5_distribution.py --packet-dir <packet-dir>
```

Build and test Basic, Deluxe, and Premium PDFs and ZIPs according to `references/distribution-packaging.md`. PDFs may only embed approved PNGs.

Copy exactly the three finished tier ZIPs and `Ready.txt` to the machine’s actual Desktop location. Detect OneDrive Desktop redirection instead of assuming `%USERPROFILE%\Desktop` exists.

## Required final audit

- Validate all JSON and reference assets.
- Verify every mapped asset is approved/current and hash-matched.
- Confirm every non-handout visual prompt contains an original art-style reference.
- Confirm every packet page prompt contains its routed original page sample and exact logo.
- Inspect contact sheets against the four approved proofs and original references.
- Verify map QA reports and tactical usability.
- Verify OCR, PDF page counts, tier inventories, ZIP integrity, and manifest source hashes.
- Render representative first, middle, appendix, handout, and final PDF pages.
- Confirm the Desktop delivery folder contains exactly three ZIPs and `Ready.txt`.
- Report the run ID and packaged status.
