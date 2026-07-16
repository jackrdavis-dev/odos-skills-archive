# ODOS Production Skills Archive

A preservation-first, educational snapshot of the four skills that make up the current One Dollar One Shots production system:

1. **ODOS Text Studio** creates a checkpointed, text-only adventure handoff.
2. **ODOS v5.1** turns that handoff into image-generated packet pages, VTT assets, PDFs, and locked tier archives.
3. **ODOS Release** validates and publishes one approved three-edition product to Patreon and the DiceStory Shop.
4. **ODOS Media v1** turns the newest completed adventure into a source-locked 16-deliverable marketing campaign.

The repository includes a dependency-free documentation website, readable architecture guides, and source snapshots of every skill's instructions, scripts, references, configuration, and supplied visual assets.

## Open the documentation

Open `index.html` directly, or serve the folder with any static web server. The published GitHub Pages URL is intended to be the canonical reading experience once Pages is enabled.

## Repository map

```text
.
├── index.html                 # Educational website
├── styles.css                 # Site presentation
├── app.js                     # Progressive enhancement only
├── archive-manifest.json      # File sizes and SHA-256 integrity ledger
├── docs/
│   ├── ARCHITECTURE.md        # System boundaries and handoffs
│   ├── PRESERVATION.md        # Snapshot and restoration policy
│   ├── RUNBOOK.md             # End-to-end operator guide
│   └── SECURITY.md            # Public-repository safety notes
├── skills/
│   ├── odos-text-studio/
│   ├── odosv5-1/
│   ├── odos-release/
│   └── odos-media-v1/
└── scripts/
    ├── build-manifest.ps1     # Rebuilds the source hash ledger
    └── verify-archive.ps1     # Structural and sensitive-data checks
```

## Canonical pipeline

```text
idea + constraints
  → ODOS Text Studio
  → versioned text handoff
  → ODOS v5.1
  → Basic / Deluxe / Premium ZIPs + Ready.txt
  ├─→ ODOS Release → Patreon + DiceStory Shop
  └─→ ODOS Media v1 → Instagram + Patreon editorial + DiceStory blog package
```

Release and Media are sibling consumers of the same approved product output. Media is not a prerequisite for Release, and Release is not a prerequisite for Media.

## Important safety model

- Text Studio pauses once for concept selection, then checkpoints each stage.
- v5.1 requires one explicit four-proof visual approval before autonomous production.
- Release treats `Ready.txt` as eligibility, never as automatic permission to publish.
- Media requires complete campaign review and explicit approval before scheduling or posting.
- Credentials, browser sessions, cookies, and one-time codes never belong in the repository.

## Preservation notes

The public snapshot intentionally normalizes machine-specific paths and replaces one inactive fallback email value with a non-routable placeholder. These changes are listed in [docs/PRESERVATION.md](docs/PRESERVATION.md). Runtime state, generated adventure packets, customer ZIPs, credentials, cookies, and caches are not archived.

## Verification

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-archive.ps1
```

The verifier confirms the four source snapshots, required entrypoints, Python syntax, links used by the documentation site, and absence of common secret patterns.

Rebuild the source integrity ledger after an intentional snapshot update:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-manifest.ps1
```
