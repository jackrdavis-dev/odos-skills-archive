# ODOSv5 Prompt Template

## Core page prompt template

```text
Generate {{filename}} as a finished raster PNG page for a One Dollar One Shot v5 D&D 5e adventure packet.

ADVENTURE:
Title: {{adventure_title}}
Level Range: {{level_range}}
Tone: {{tone}}
Core Fantasy: {{core_fantasy}}

PAGE:
Page Number: {{page_number}}
Page Title: {{page_title}}
Page Purpose: {{page_purpose}}

STYLE AUTHORITY:
Use the routed original ODOSv5 page sample for packet composition, density, title placement, panel geometry, illustration-to-text balance, footer treatment, and hierarchy. Do not copy its characters, scenery, title, or story content.
Directly reference an original image from `art-style-samples/` for all illustrations: clean arcade/cartoon fantasy, bold readable outlines, smooth cel shading, broad simple shapes, expressive faces, strong silhouettes, and clean surfaces. Generated proofs never replace this original style reference.
If page style conflicts with art style, the art-style-samples win for illustrations.
Use the actual ODOS logo asset from the identified `logos/` file: {{odos_logo_path}}. The logo must visibly match the provided ODOS / One Dollar One Shots reference, not an invented ODOS-like mark.
Match `style-lock.json`, `cast-lock.json`, `scene-lock.json`, and the approved art plate at their recorded revisions. Generated pages are not style authorities. Do not drift darker, painterly, realistic, over-detailed, texture-heavy, or visually noisy.

REFERENCE BUDGET:
Use at most five references: routed original page sample, original art-style sample, approved identity or art plate, exact logo, and one scene reference. Omit roles not needed by this asset.

VISUAL NOISE BAN:
No gritty realism. No cinematic realism. No dark fantasy splash art. No realistic VTT rendering. No stippling. No speckling. No dimpled texture. No grain. No random dots. No scratchy painterly texture. No excessive particles. No noisy water, stone, skin, snow, cloth, metal, fur, smoke, fire, or magic. Keep surfaces clean, broad, and reference-matched.

PAGE STRUCTURE:
{{page_structure}}

TEXT TO TYPESET:
{{page_safe_copy}}

ART DIRECTION:
{{page_art_direction}}

STRICT REQUIREMENTS:
- Make the actual final page image, not just a prompt or mockup.
- Use the real provided ODOS logo asset where packet branding is required.
- Use only the provided packet content and compressed page-safe copy.
- Do not copy sample packet text.
- Do not use placeholder text.
- Keep all major headings readable and correctly spelled.
- Keep body text readable.
- Do not place random words inside illustration panels.
- Do not replace D&D stat blocks with icons only.
- Do not omit required page sections.
- Final output must be a polished high-quality raster PNG.
```

## Appendix art prompt template

```text
Generate {{filename}} as a full-page appendix art PNG for the ODOSv5 adventure packet.

STYLE:
Clean arcade/cartoon fantasy from art-style-samples: bold outlines, smooth cel shading, broad simple shapes, expressive characters, strong silhouettes, clean surfaces.
Match the approved style lock, relevant cast crop, and approved art plate. Keep the same bright cartoon look and do not become darker, painterly, over-detailed, realistic, or noisy. Functional but off-style is failure.
Use a light ODOS ornate frame and title plaque only if appropriate.
If a packet-style frame is used, include the real ODOS logo asset from {{odos_logo_path}}.
Do not use gritty realism, speckles, stippling, grain, dimpled texture, random dots, or excessive particles.

SUBJECT:
{{subject}}

SCENE / CHARACTER / MONSTER DETAILS:
{{details}}

TEXT:
Use only a small title plaque and short caption:
Title: {{title}}
Caption: {{caption}}

Do not include dense body text.
```

## Token prompt template

```text
Generate {{filename}} as a VTT-ready circular token PNG.

Subject: {{name}}
Description: {{visual_description}}

Style:
Match the approved token calibration proof and approved character crop: bright cartoon fantasy, bold outline, smooth cel shading, strong silhouette, saturated clean colors, simple sticker-like token rendering, readable at small size, no visual noise, no speckles, no stippling, no grain, no random dots.

Requirements:
- centered bust or upper-body portrait
- circular token crop or clean circular border
- no text
- transparent or clean simple background if possible
- readable silhouette
```

## Battle map prompt template

```text
Generate {{filename}} as a top-down D&D battle map PNG.

Scene: {{scene_name}}
Adventure: {{adventure_title}}

Map Requirements:
{{map_requirements}}

Style:
Top-down only, not isometric. Match the approved battle-map calibration proof while staying map-usable: simplified bright cartoon VTT map style, broad smooth terrain shapes, saturated clean colors, clear playable terrain, sparse props, and low detail density. Grid preferred unless user says otherwise. No text, no labels, no title, no arrows, no callouts, no creatures, no packet frame.

Visual noise ban:
No speckled noise, no stippled texture, no gritty grain, no random dot fields, no noisy water, no dense props, no realistic map texture, no scenic illustration rendering. Terrain should be simple, clean, broad, and readable for play. A playable map that looks realistic, dark, painterly, or overly detailed fails.
```

