# ODOSv5 Asset Contracts

## Reference folders

Project-local:
- approved proofs recorded in `style-lock.json`
- approved cast sheet/crops recorded in `cast-lock.json`
- approved storyboard recorded in `scene-lock.json`
- approved art plates recorded in `art-plates.json`
- `logos/`

Skill-local:
- `assets/page-samples/`
- `assets/art-style-samples/`
- `assets/style-character/`
- `assets/style-environment/`
- `assets/style-token/`
- `assets/style-battle-map/`
- `assets/logos/`

Use the routed illustrated page sample for production page composition. Its embedded characters and story content must not be copied and never override `art-style-samples/`.

## Art style samples

Primary authority for character, monster, scene, appendix, token, and battle map illustration style.

## Page samples

Primary authority for ODOS packet layout, ornate border, page plaques, footer ribbons, text panel density, page medallions, sidebars, and hierarchy.

They do not control the content illustration style if they conflict with art-style-samples.

## VTT token outputs

Recommended output:
- 512x512 or 1024x1024 PNG
- circular crop or circular border
- subject centered
- no text
- strong silhouette
- clean background or transparent background
- simple sticker-like cartoon fantasy rendering
- broad shape language readable at thumbnail size
- no portrait-painting detail, gritty texture, noisy rim effects, tiny particles, or realistic lighting

## Battle map outputs

Recommended output:
- square PNG
- top-down
- grid preferred
- no ornate packet frame
- no isometric view
- no long text labels
- clean readable terrain
- simplified cartoon VTT terrain matching the art-style samples
- broad smooth land/water/stone/wood shapes
- sparse props only where they improve play
- bright palette even for night, horror, cave, river, or finale scenes
- at least three tactically distinct zones
- at least two usable entrances or exits
- connected routes, meaningful cover or hazards, and no large dead zones

Hard fail battle maps that look like detailed commercial realism maps, painterly scenic illustrations, dark gritty maps, dense texture fields, decorative diagrams, empty fields, or disconnected set dressing. Playable but visually off-style maps still fail. Record every passing map against `battle-map-qa-schema.json`.

