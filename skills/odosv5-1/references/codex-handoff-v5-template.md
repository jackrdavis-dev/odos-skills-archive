# ODOSv5 Codex Handoff Template

Use this template in future Generator exports.

```text
Use the odosv5 skill with $imagegen to generate the complete ODOS v5 packet from this export:

[EXPORT ZIP OR FOLDER PATH]

This is a full-image-generation workflow, not a deterministic renderer.

STRICT RULES:
- Do not render packet pages with HTML, CSS, Pillow, SVG, canvas, browser screenshots, or any code-based compositor.
- Do not create placeholder pages.
- Do not output plain box layouts or simple worksheet-style pages.
- Use actual image-generation calls for all core packet pages, appendix pages, VTT tokens, and battle maps.
- If image generation is unavailable, stop immediately and say so.

REFERENCE FOLDERS:
- Primary content art style: [PATH TO art-style-samples]
- Original ODOSv5 page composition: [PATH TO page-samples]
- ODOS logo/reference: [PATH TO logos OR art-style-samples]

CRITICAL STYLE:
Page samples control only the ornate packet layout.
Art-style samples control all illustrations.
Use clean cartoon fantasy art: bold readable outlines, smooth cel shading, controlled gradients, expressive faces, strong silhouettes, clean surfaces.
No speckles, no stippling, no grain, no dimpling, no random dots, no gritty surface texture.

WORKFLOW:
1. Extract and read the export zip.
2. Analyze the exported files and build `page-copy-pack.json`.
3. Build page-specific prompts using ODOSv5 page contracts.
4. Generate one recurring character, one multi-character scene, one complete Scene page, and one battle map; wait for one explicit approval.
5. Record cast, scenes, and art plates with autonomous QA.
6. Generate remaining core and appendix pages with routed original page samples.
7. Generate player handouts, VTT tokens, and battle maps.
8. QA every image and regenerate failed pages. Maps require the structured battle-map QA report.
9. Return the final PNG packet files, `manifest.json`, `run-state.json`, all lock/state JSON files, `page-copy-pack.json`, and `qa-report.md`. Immutable per-asset prompts remain under `working/prompts/<run-id>/`.

QUALITY GATES:
- Stop if the cover is not a high-quality ODOS-style fantasy packet page.
- Stop if Page 2 has icon-only stats instead of compact D&D-style stats.
- Stop if Page 3 lacks usable monster/villain actions, tactics, and stat details.
- Stop if Page 5 cannot be used to run the scene at the table.
- Stop if the content art drifts into gritty, speckled, stippled, noisy, or dimpled style.
```

