# Visual Noise Ban

This file is mandatory. Inject these rules into every art-generating prompt.

## Critical visual style rule

Use clean cartoon fantasy illustration with bold readable outlines, smooth cel-shaded forms, broad color shapes, controlled gradients, expressive characters, and clear silhouettes.

## Hard negative list

Do not use:
- gritty realism
- painterly scratch texture
- stippling
- speckling
- dimpled texture
- grain
- crosshatching
- random dots
- random flecks
- dust-like visual noise
- excessive particles
- micro-highlights
- noisy stone texture
- noisy skin texture
- noisy snow texture
- noisy cloth texture
- noisy metal texture
- noisy fur texture
- over-detailed pores, pits, cracks, or stippled marks
- floating dot fields
- scattered spark/noise overlays

## Particle exception

Snow, rain, sparks, ash, debris, or magical motes may appear only when story-critical.

When used:
- keep particles sparse
- make them larger and readable
- avoid hundreds of tiny dots
- do not cover the image with texture

## QA hard fail

Regenerate any image where:
- the art style looks gritty instead of cartoon fantasy
- the image contains widespread speckles/stipple/grain
- characters or monsters have dimpled/noisy surfaces
- snow, stone, smoke, or magic becomes random-dot texture

