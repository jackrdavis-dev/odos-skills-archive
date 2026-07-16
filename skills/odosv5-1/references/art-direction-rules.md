# ODOSv5 Art Direction Rules

## Two-style system

ODOSv5 uses two separate style authorities.

### Page composition style

Use the original files in `page-samples/` for page frame, parchment color, gold border, title plaques, footer ribbons, section boxes, icon medallions, packet density, art-to-text ratio, and overall ODOS page identity. Their embedded characters and scenery are unrelated examples; never copy that story content.

### Content illustration style

Use `art-style-samples/` for characters, NPC portraits, monsters, scene setting images, appendix art, cover art, battle maps, and VTT tokens.

Inspect every current art-style sample before calibration and record its SHA-256 in `style-lock.json`. Project proofs must be visibly derived from the shared rendering behavior of those current references. Provisional asset-class seeds may focus the proof but may not redefine the style.

If these conflict, content illustration style wins for all artwork.

## Required content art style

Clean cartoon fantasy:
- bold readable outlines
- expressive character faces
- strong silhouettes
- smooth cel shading
- broad clean color shapes
- saturated but controlled color palette
- simple cartoon staging
- readable action
- controlled gradients
- clean surfaces
- minimal noise
- no gritty realism

## Reference-match standard

ODOSv5 must preserve the same visual behavior as ODOSv4. V5 packaging changes do not permit a style change.

The art-style samples are not mood boards. They are the pass/fail target. A generated image must read at a glance as belonging to the same bright arcade/cartoon fantasy family as the provided samples. If it merely looks like a nice fantasy illustration, detailed digital painting, dark adventure splash page, or realistic VTT asset, it fails.

Do not accept borderline style drift because the page is complete, readable, mechanically useful, or table-playable. Functional but off-style images are failed images.

## Subject-matter override ban

Adventure tone must never override the reference art style. Horror, night, poison, undead, betrayal, storms, rivers, caves, ruins, and finales must still be bright, clean, chunky, saturated, and cartoon-first. Use color-coding, expressive poses, clear silhouettes, and simple graphic effects to carry danger instead of darkness, realism, dense texture, or visual noise.

## What to avoid

Avoid gritty realism, hyper-detailed grimdark rendering, cinematic realism, dark fantasy splash art, realistic VTT map rendering, dimpled textures, speckled highlights, stippled snow/stone/skin, grainy painterly brushwork, muddy contrast, random particles, unreadable clutter, over-textured armor, stone, snow, water, smoke, fire, magic, or fur, excessive micro-detail, and ornate detail that is not visible in the references.

## Required prompt injection

Every page prompt with artwork must include:

"The packet frame is ornate ODOS fantasy UI, but all content illustrations use the art-style-samples as the primary authority: clean cartoon fantasy, bold outlines, smooth cel shading, controlled gradients, clear silhouettes, expressive characters, and no gritty/speckled visual noise."
## ODOS logo lock

Use the actual logo file from `assets/logos/` or the user-provided logo folder. Do not prompt for a generic ODOS-like logo.

Every core page and packet-style appendix page must include the selected logo file path in the prompt and must visually match the provided ODOS / One Dollar One Shots logo treatment. Missing, invented, misspelled, or substituted logo marks are hard failures.

Never include D&D ampersand logos, compatibility badges, fake publisher marks, or legal boilerplate unless the user explicitly provides approved art and text for them.

## Approved style lock

Approve one recurring character, one multi-character scene, one complete Scene page, and one battle map before packet production. Record their paths and hashes in `style-lock.json`.

Keep at least one original `art-style-samples/` image directly present in every later visual call. Approved proofs focus identity, composition, page behavior, and map behavior; they never replace the original style authority.

```text
Match the approved style calibration proofs: thick readable outlines, smooth limited cel shading, saturated clean colors, broad simple effects, and low visual noise. Do not drift darker, painterly, realistic, over-detailed, texture-heavy, or noisy.
```

Generated packet pages are never the primary style authority. When a page drifts, compare it to the approved calibration proofs and invalidate the affected dependency rather than strengthening cumulative prose.

## No borderline acceptance

The following phrases are banned as QA acceptance logic: "slightly detailed but accepted", "a bit dark but usable", "moderate texture but readable", "not ideal but playable", "borderline pass", "close enough", and any equivalent.

If the image has to be defended with one of those phrases, regenerate it.

