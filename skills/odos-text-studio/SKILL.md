---
name: odos-text-studio
description: Generate or resume complete ODOS adventure text packets directly in Codex without calling an external AI API. Use when the user asks for ODOS Studio text generation, three columns of 20 monthly options, an Adventure Skeleton, DM Packet, NPC Suite, Clue Web, original 5e-compatible stat blocks, three player-facing handouts, a style-neutral Visual Asset Brief, or a text-only handoff for odosv4. Checkpoint every stage to disk and resume interrupted packet builds without regenerating completed work.
---

# ODOS Text Studio

Create the adventure text with the active Codex model. Persist every completed stage as a separate Markdown file so an interruption cannot erase earlier work.

## Non-Negotiable Rules

- Do not call the OpenAI API, the hosted Text Studio, or another paid model endpoint.
- Do not ask for or use an API key.
- Do not generate images, page layouts, PDFs, tokens, or battlemaps in this skill.
- For player handouts, generate only text specifications: the artifact type, observable visual contents, exact readable in-world text, and player-safe usage notes. Do not create the handout image or deterministic page layout.
- Do not copy image assets, page samples, or style references into the handoff.
- Treat `visual_asset_brief.md` as subject inventory only. Never put art style, medium, rendering, palette, lighting, camera, composition, texture, or page-layout directions in it.
- Let `odosv4` own all image references, page samples, visual style, visual-noise controls, and image prompt construction.
- Do not add approval gates, lock stages, QA reports, audits, or process commentary to packet content.
- Pause only after monthly options so the user can choose one item from each column. After selection, generate all remaining stages sequentially unless the user pauses.
- Save each stage before drafting the next one. Never keep multiple completed stages only in chat context.
- Never overwrite a completed stage without preserving its previous revision.
- Never regenerate completed stages on resume unless the user explicitly asks.

## Default Storage

Use this root unless the user specifies another location:

`%USERPROFILE%\OneDrive\Desktop\New Text Packet`

- In-progress packets: `Saved\<Adventure Name> [working]`
- Finished handoffs: `Exported\<Adventure Name> v# dd-mm-yy`

Use `scripts/manage_packet.py` for initialization, checkpointing, selection, status, and final export. The script writes files atomically and keeps replaced files under `.history`.

If filesystem permissions block the exact packet root, request approval for that root. Do not silently save elsewhere.

## Start Or Resume

### Resume

When the user names a packet folder or asks to resume:

1. Run `manage_packet.py status --packet <folder>`.
2. Read `progress.json`, `project.json`, and only the source files needed for the next incomplete stage.
3. Continue at the stage returned by `manage_packet.py next --packet <folder>`.
4. If the status is `awaiting_selection`, show `monthly_options.md` and ask for three numbers: Style, Quest, and Antagonist.

When no packet is named, run `manage_packet.py list` and use the single incomplete packet if exactly one exists. If several exist, ask which packet to resume.

### New Packet

Collect these project constraints from the user's prompt:

- Working title
- Release month
- Level range
- Party size
- Tone
- Difficulty
- Theme notes
- Banned concepts

Preload these defaults whenever the user does not provide an override:

- Level range: `3-8`
- Party size: `2-6`
- Difficulty: `Moderate`

Do not ask the user for a field already covered by these defaults. If other constraints are absent, ask one concise question containing only the remaining missing fields. Accept `unspecified` or `none`; do not force invention.

Initialize the checkpoint folder:

```powershell
python scripts/manage_packet.py init --title "<title>" --release-month "<month>" --level-range "<levels>" --party-size "<size>" --tone "<tone>" --difficulty "<difficulty>" --theme-notes "<notes>" --banned-concepts "<bans>"
```

Use the returned packet folder for every later command.

## Generation Workflow

Read [references/stage-contracts.md](references/stage-contracts.md) before drafting. Follow its exact heading contracts and content boundaries.

### 1. Monthly Options

Generate `monthly_options.md` as exactly 20 rows with three independently selectable columns:

1. Adventure Style / Structure
2. Main Quest Premise
3. Antagonist

The entries in a row do not form a locked concept. The user may choose any Style, any Quest, and any Antagonist from different rows.

Write the draft to a temporary Markdown file, then checkpoint it:

```powershell
python scripts/manage_packet.py save-stage --packet "<packet-folder>" --stage monthly_options --input "<draft-file>"
```

Show the numbered table in chat and ask the user to answer in this compact form:

`Style 4, Quest 12, Antagonist 7`

Record the selection:

```powershell
python scripts/manage_packet.py select --packet "<packet-folder>" --style 4 --quest 12 --antagonist 7
```

Do not create a separate lock or approval stage.

### 2. Sequential Text Stages

Generate these in order:

1. `adventure_skeleton`
2. `dm_packet`
3. `npc_suite`
4. `clue_web`
5. `stat_blocks`
6. `handouts`
7. `visual_asset_brief`

For every stage:

1. Run `manage_packet.py next --packet <folder>` and confirm the expected stage.
2. Read `project.json`, `selected_concept.md`, and the upstream files named in the stage contract.
3. Draft only that stage. Keep it within the contract's target length.
4. Write the draft to a temporary file with `apply_patch`.
5. Run `manage_packet.py save-stage --packet <folder> --stage <stage> --input <draft-file>`.
6. Confirm the checkpoint succeeded before starting the next stage.
7. Continue automatically.

Do not paste long completed stages into chat. Give short checkpoint updates and keep the authoritative copy on disk.

If interrupted, the next invocation must resume from `progress.json`. A partially drafted temporary file is not complete and must not advance the manifest.

## Name Continuity

Before creating final character names, run:

```powershell
python scripts/manage_packet.py history-names
```

Treat the returned names as an avoidance list. Do not reuse exact full names, near-spellings, or a prior character's distinctive first-name/surname pairing. Keep names consistent across all files in the current packet.

## Revisions

When the user edits or requests regeneration of a stage:

1. Read downstream stages and identify which ones depend on the changed facts.
2. Save the revised stage with `save-stage`; the script archives the old file.
3. Mark affected downstream stages stale with:

```powershell
python scripts/manage_packet.py invalidate --packet "<packet-folder>" --from-stage "<stage>"
```

4. Regenerate only the invalidated downstream stages.

For typo-only edits that do not alter names, mechanics, clues, scenes, or asset subjects, save the edit without invalidating downstream stages.

## Finalize

After all eight stage files are complete, run:

```powershell
python scripts/manage_packet.py finalize --packet "<packet-folder>"
```

The command validates the file set, writes `codex_handoff.md`, and creates a versioned text-only folder under `%USERPROFILE%\OneDrive\Desktop\New Text Packet\Exported`. It does not delete the working packet.

Report the absolute exported folder. Nothing is copied into any packet-building skill. The user may later point a separate packet-building task at this folder, but do not invoke one unless asked.

## Failure Handling

- On any tool or context failure, stop after the last confirmed checkpoint.
- Report the packet folder and the next incomplete stage.
- Do not restart the packet.
- Do not regenerate a stage merely because chat output was interrupted; inspect the saved file and manifest first.
- Do not make automatic retries that can duplicate work or cost.
