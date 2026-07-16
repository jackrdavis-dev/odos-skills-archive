# ODOSv5 Image Call Protocol

ODOSv5 must make actual image-generation calls.

## Hard stop

If image generation is unavailable, stop.

Do not use HTML rendering, CSS rendering, Pillow rendering, SVG rendering, browser screenshots, canvas rendering, PDF export, DOCX export, or markdown-to-image exports.

## Required process

For each output image:

1. Build the final prompt using ODOSv5 prompt templates.
2. Include or reference relevant page samples and art-style samples.
3. Invoke the image-generation skill/tool.
4. Save the generated raster PNG using the required filename.
5. Inspect the image for QA.
6. If it fails, regenerate with a targeted repair prompt.
7. Record result in `qa-report.md`.

## Required generation order

1. Generate one character, one multi-character scene, one complete Scene page, and one battle map; wait for one explicit approval.
2. Record the cast and isolated character crops using autonomous QA.
3. Record the scene storyboard using autonomous QA.
4. Generate and record text-free character, monster, clue/object, and scene art plates.
5. Generate remaining core pages using routed original page samples.
6. Generate appendix pages, handouts, tokens, and maps.
7. Review cross-page contact sheets after every logical batch.
8. Approve the run and build locked packaging.

## Five-reference budget

Never pass more than five images to one image-generation call. For packet pages prefer one routed original page sample, one original art-style sample, one relevant identity or art plate, the exact logo, and one scene reference. Generated intermediates never replace the original art-style sample.

## Candidate discipline

Generate every output into `working/candidates/<run-id>/`. Compile an immutable prompt, register the candidate, record OCR and visual QA, then promote it with `odosv5_state.py`. Never write a tool output directly over a final asset.

## Maximum repairs

Default:
- up to 2 repair attempts per failed core page
- up to 1 repair attempt per appendix art page
- up to 2 repair attempts for stat-heavy appendix pages
- up to 1 repair attempt per token or map

If a page still fails, stop and report the failure clearly.

## Locked-in Protocol Addendum

These rules are mandatory and override any looser wording above.

### One asset at a time

Never generate several images and then assign filenames only by newest timestamp order. If multiple generated images exist, inspect and bind each one to its filename deliberately.

Required loop:

1. Compile one immutable prompt.
2. Generate one candidate.
3. Register its prompt, references, dependency revisions, and hash.
4. Inspect the saved candidate.
5. Run OCR and page-specific visual QA.
6. Record pass/fail in `asset-status.json` and summarize it in `qa-report.md`.
7. Promote only a passing current candidate.
8. Only then generate the next asset.

### Style drift controls

After every generated page or asset, compare against the approved calibration proofs in `style-lock.json`, relevant cast crops, storyboard, and art plates. Hard fail and repair if the image drifts toward:

- gritty/dark fantasy splash art
- realistic rendering instead of bright cartoon fantasy
- increasing snow/stone/skin/fur/metal texture noise
- missing or substituted ODOS logo treatment
- flat, quiet, low-energy banners when the reference uses bold dimensional ODOS banners
- D&D ampersand, D&D compatibility badge, or any unauthorized brand mark

For repair prompts, use positive corrections such as broad smooth snow shapes, clean cel-shaded stone planes, solid smooth skin, simple fur tufts, bold graphic lightning, and animated-cartoon background simplicity.

### Stat-page controls

For Page 2, Page 3, and all appendix stat pages, include only validated stat-safe copy that has passed `statblock-contracts.md`. If the stat-safe copy fails validation, do not generate the image. Fix the copy first.

### Battle map controls

Battle maps must be generated as playable VTT maps, not scenic illustrations. Hard fail if they include labels, callouts, red circles, arrows, creatures, ornate packet frames, isometric/perspective camera, scenic horizons, or clutter that obscures the grid. Use top-down/overhead orthographic language and broad readable terrain shapes.

