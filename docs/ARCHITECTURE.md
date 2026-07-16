# ODOS architecture

## The system in one sentence

ODOS is a staged publishing pipeline in which immutable, hashable artifacts move from text creation to visual production and packaging, then branch into product release and editorial marketing.

## Component responsibilities

| Skill | Owns | Does not own | Primary durable state |
|---|---|---|---|
| ODOS Text Studio | Adventure concept, DM-facing prose, NPCs, clues, original 5e-compatible mechanics, handout specifications, visual subject inventory | Images, page design, PDFs, tokens, maps, publishing | `progress.json`, `project.json`, one Markdown file per stage, `.history/` |
| ODOS v5.1 | Visual calibration, cast and scene locks, image-generated packet pages, handout art, tokens, maps, PDFs, tier packaging | Adventure ideation, live publishing, campaign scheduling | `run-state.json`, lock files, `asset-status.json`, `distribution-map.json` |
| ODOS Release | Eligibility checks, tier validation, shop product, Patreon fulfillment posts, publication ledger | Packet generation, marketing campaign production | release context, source hashes, local release ledger, verified remote IDs/URLs |
| ODOS Media v1 | Source-grounded creative brief, 12 Instagram posts, 3 Patreon articles, 1 blog article, campaign QA and optional publishing | Product fulfillment, edition pricing, packet generation | `campaign-manifest.json`, `run-state.json`, source fingerprint, deliverable QA |

## Handoff graph

```text
ODOS Text Studio
  exported folder:
  project.json + selected_concept.md + stage Markdown + codex_handoff.md
           │
           ▼
ODOS v5.1 Stateful Packet Compiler
  approved PNG masters + manifests + PDFs
  Basic.zip + Deluxe.zip + Premium.zip + Ready.txt
           │
           ├────────────────────────────┐
           ▼                            ▼
ODOS Release                       ODOS Media v1
  oldest eligible packet              newest valid packet
  one release / Pacific week          16-deliverable campaign
  verified product URLs               approval-locked snapshot
```

## Why the branch matters

Release and Media select source packets differently. Release chooses the **oldest unpublished valid** packet and enforces a weekly limit. Media chooses the **newest completed valid** packet and locks a campaign to its source fingerprint. That difference is intentional: fulfillment drains a queue fairly, while marketing follows the most recent product.

## Cross-skill contracts

### Text Studio → v5.1

- Stable facts live in the completed Markdown stages.
- `visual_asset_brief.md` is subject inventory only; it must not dictate rendering style or layout.
- Player handouts are text specifications until v5.1 generates the images.
- Revisions invalidate only dependent downstream text stages.

### v5.1 → Release

- Exactly three title-matched tier ZIPs and `Ready.txt` form the delivery folder.
- Embedded manifests must agree on title, run ID, hashes, skill version, tier hierarchy, PDFs, and contents.
- `Ready.txt` means eligible for a scheduled/manual release check; it is not a publish command.
- The three gated fulfillment posts do not notify members; the final public announcement is the release's single notification and links to all fulfillment posts plus the shop.

### v5.1 → Media

- The Premium manifest and extracted media are visual authority.
- Matching Text Studio Markdown is factual and design-analysis authority.
- Source hashes are frozen into a campaign fingerprint; changed sources require a new review.

## State-machine pattern

Every skill avoids inferring truth from loose filenames alone:

- Text Studio advances only when `manage_packet.py save-stage` checkpoints a valid stage.
- v5.1 promotes one candidate only after references, prompt, dependency revisions, hash, OCR, and visual QA are recorded.
- Release advances only after a remote object is reopened and verified.
- Media advances only through manager validation and atomic deliverable updates.

This shared pattern—explicit state, immutable evidence, and resumability—is the architectural spine of ODOS.

## Human approval boundaries

| Moment | Required human action |
|---|---|
| Text concept | Choose one Style, one Quest, and one Antagonist from the monthly table |
| Visual language | Approve four proofs together: character, action scene, complete Scene page, and playable map |
| Product publication | Explicitly authorize external publishing unless an approved scheduled run already grants it |
| Campaign publication | Review and approve the exact campaign snapshot before scheduling or posting |

## Failure containment

- A failed or interrupted Text Studio run resumes from the last saved stage.
- A failed v5.1 asset never overwrites the approved final; it stays in the candidate area.
- A partial release resumes from the first incomplete ledger phase without duplicating verified remote objects.
- A media campaign records `blocked` for missing access/tooling and `failed` for attempted operations that error.
