# ODOSv5 Patreon Distribution Packaging

## Goal

Build three customer-ready Patreon tier folders from the same approved, hash-locked ODOSv5 PNG packet without manual sorting or renaming.

The approved PNG packet remains the master source. Distribution packaging copies from that source, applies customer-facing filenames, assembles tier PDFs from approved PNG pages, writes provenance-rich tier manifests, and creates ZIP archives.

Do not use HTML, CSS, browser screenshots, SVG, Pillow, or page-layout rendering for this step. The PDF step may only embed already generated PNG page images as full PDF pages.

## Locked preconditions

Packaging is forbidden until:

- `manifest.json` and `run-state.json` are `approved` or unchanged `packaged`
- style, cast, storyboard, and art-plate gates are approved
- every mapped item has an approved/current record in `asset-status.json`
- every source hash matches its approved output hash
- every dependency revision matches the current run revisions

The packager builds in `working/distribution-staging/<run-id>/` and replaces the live distribution only after the staged PDFs, manifests, and ZIPs succeed. Tier manifests must include source SHA-256, prompt SHA-256, run ID, skill version, and dependency revisions.

## Required Distribution Files

After PNG generation and QA, create:

- `distribution-map.json`
- `distribution/Basic/`
- `distribution/Deluxe/`
- `distribution/Premium/`
- `Scorched Sea Survival - Basic.zip` style tier archives using the actual adventure title
- `Scorched Sea Survival - Deluxe.zip`
- `Scorched Sea Survival - Premium.zip`

## Distribution Map Schema

Create `distribution-map.json` in the packet output folder before packaging.

Use this shape:

```json
{
  "title": "Adventure Title",
  "slug": "adventure-title",
  "version": "odosv5",
  "items": [
    {
      "source": "page-00-cover.png",
      "display_name": "01 - Cover - Adventure Title.png",
      "role": "cover",
      "pdf_order": 1,
      "tiers": ["basic", "deluxe", "premium"]
    }
  ],
  "tier_rules": {
    "basic": {
      "pdf_roles": ["cover", "core_page"],
      "png_page_roles": ["cover", "core_page"],
      "battle_maps": "basic_selected",
      "tokens": "villain_token"
    },
    "deluxe": {
      "pdf_roles": ["cover", "core_page"],
      "png_page_roles": ["cover", "core_page"],
      "battle_maps": "deluxe_selected",
      "tokens": "all"
    },
    "premium": {
      "pdf_roles": ["cover", "core_page", "appendix_page"],
      "png_page_roles": ["cover", "core_page", "appendix_page"],
      "battle_maps": "all",
      "tokens": "all"
    }
  }
}
```

## Item Roles

Use only these roles:

- `cover`
- `core_page`
- `appendix_page`
- `battle_map`
- `token`
- `report`

Only `cover`, `core_page`, and `appendix_page` receive `pdf_order`.

## Required Tier Contents

### Basic

- PDF: cover + all core pages
- PNG Pages: cover + all core pages
- Battle Maps: exactly 1 selected map
- Tokens: villain token only

Prefer the most generally useful map for Basic. Usually this is the ship/deck map, starting encounter map, or map most likely to be reused in play.

### Deluxe

- PDF: cover + all core pages
- PNG Pages: cover + all core pages
- Battle Maps: exactly 3 selected maps
- Tokens: all tokens

Prefer the three maps that best cover beginning, middle, and finale play.

### Premium

- PDF: cover + all core pages + all appendix pages
- PNG Pages: cover + all core pages + all appendix pages
- Battle Maps: all battle maps
- Tokens: all tokens

## Folder Layout

Create this layout:

```text
distribution/
  Basic/
    PDF/
    PNG Pages/
    Battle Maps/
    Tokens/
    manifest-basic.json
  Deluxe/
    PDF/
    PNG Pages/
    Battle Maps/
    Tokens/
    manifest-deluxe.json
  Premium/
    PDF/
    PNG Pages/
    Appendix Pages/
    Battle Maps/
    Tokens/
    manifest-premium.json
```

For Premium, place cover and core pages in `PNG Pages/`, and appendix pages in `Appendix Pages/`.

## Customer-Facing Filenames

Do not expose raw generation filenames inside tier folders.

Use clean names:

- `01 - Cover - [Title].png`
- `02 - Adventure Overview.png`
- `03 - NPCs and Crew.png`
- `04 - Monsters and Main Villain.png`
- `05 - Scene Flow Overview.png`
- `06 - Scene 1 - [Short Name].png`
- `07 - Scenes 2-3 - [Short Name].png`
- `08 - Finale - [Short Name].png`
- `09 - Clues, Secrets, and DM Tools.png`
- `10 - Rewards and Carry-Forward Hooks.png`
- `Appendix - Scene - [Name].png`
- `Appendix - NPC - [Name].png`
- `Appendix - Monster - [Name].png`
- `Battle Map - [Name].png`
- `Token - [Name].png`

Use the actual title, NPC names, monster names, and map names from the generated asset plan.

## PDF Assembly

Build one PDF per tier:

- `[Title] - Basic.pdf`
- `[Title] - Deluxe.pdf`
- `[Title] - Premium.pdf`

PDF page order:

1. Cover
2. Core pages in core packet order
3. Premium only: appendix scene pages, appendix NPC pages, appendix monster pages

The PDF must preserve the original PNG page artwork. It may scale the whole PNG uniformly to a page, but it must not redraw text, redesign layout, add headers, add footers, or composite new page elements.

## Packager Script

Use `scripts/build_odosv5_distribution.py` when possible.

Expected usage:

```bash
python scripts/build_odosv5_distribution.py --packet-dir path/to/generated-packet
```

The script reads `distribution-map.json`, creates tier folders, copies and renames assets, writes tier manifests, assembles PDFs from mapped page PNGs, and creates tier zip archives.

If the script fails because the distribution map is incomplete, fix `distribution-map.json`; do not sort files manually.

