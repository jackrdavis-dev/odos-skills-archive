# ODOSv5 Packet Structure

## Core Packet

The core packet is a table-running document. It should be compact, visually rich, and practical at the table.

Required pages:

1. `page-00-cover.png`
2. `page-01-adventure-overview.png`
3. `page-02-npcs.png`
4. `page-03-monsters-main-villain.png`
5. `page-04-scene-flow-overview.png`
6. `page-05-scene-01.png`
7. `page-06-scenes-02-03.png`
8. `page-07-finale-scene.png`
9. `page-08-clues-secrets-dm-tools.png`
10. `page-09-rewards-carry-forward.png`

## Appendix

The appendix is for expanded art, expanded roleplay, and full stat blocks. It may use lower text density than the core packet except on stat pages.

Required appendix families:
- one full-page scene / setting artwork page per major scene
- one full-page NPC appendix page per important NPC
- one full-page monster / villain appendix page per monster or villain

## Additional Assets

Generate:
- VTT-ready circular tokens for every important NPC
- VTT-ready circular tokens for every monster and villain
- battle maps for each major scene
- battle map for the finale

## Reports and working files

Also produce:
- `manifest.json`
- `page-copy-pack.json`
- `run-state.json`
- `style-lock.json`
- `cast-lock.json`
- `scene-lock.json`
- `art-plates.json`
- `asset-status.json`
- immutable prompts under `working/prompts/<run-id>/`
- `qa-report.md`
- `distribution-map.json`
- `distribution/Basic/`
- `distribution/Deluxe/`
- `distribution/Premium/`
- Basic, Deluxe, and Premium tier zip archives

## Philosophy

Core packet = compact table-use pages.
Appendix = full art and full stat pages.
Additional assets = VTT play tools.
Distribution = customer-ready Patreon products.

Do not attempt to cram full appendix content into core pages.

Do not manually sort or rename tier deliverables. Use `distribution-map.json` and the ODOSv5 distribution packager.

