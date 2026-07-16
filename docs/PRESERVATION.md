# Preservation policy

## What is preserved

Each directory under `skills/` is a runnable source snapshot containing the skill entrypoint, referenced documentation, scripts, configuration, agent metadata, and supplied visual reference assets. Python bytecode caches are excluded because they are generated, platform-specific artifacts.

## Public-snapshot normalizations

The operational source was copied on 2026-07-16 and then sanitized for a public repository:

1. The machine-specific Text Studio root `C:\Users\<user>\OneDrive\Desktop\New Text Packet` is represented as `%USERPROFILE%\OneDrive\Desktop\New Text Packet`.
2. The inactive release fallback email is represented as `alerts@example.invalid`.

Neither change alters production logic. The first makes the path portable; the second prevents a personal address from becoming repository data. The original local skill installations remain untouched.

## What is deliberately excluded

- Generated adventures and media campaigns
- Basic, Deluxe, and Premium customer archives
- `Ready.txt` release folders
- Release ledgers and staging directories
- Authenticated browser state, cookies, passwords, API keys, one-time codes, and credentials
- Python `__pycache__` directories and other rebuildable caches

## Recommended snapshot procedure

1. Copy each selected skill directory into `skills/<skill-name>/`.
2. Remove generated caches.
3. Reapply documented public normalizations.
4. Run `scripts/verify-archive.ps1`.
5. Review the diff, especially configuration and newly added binary assets.
6. Commit with the source date and a short change summary.
7. Tag meaningful releases, for example `archive-2026-07-16`.

## Restoration procedure

Restoration should be intentional because local paths and account configuration differ by machine:

1. Review `SKILL.md` and all referenced contracts.
2. Copy the desired snapshot to the Codex skills directory under the same folder name.
3. Replace portable placeholders with local, non-secret configuration.
4. Validate required runtimes and referenced assets.
5. Run only read-only validation commands first.
6. Never restore browser sessions, credentials, or remote publication state from source control.

## Integrity model

Git history is the primary preservation ledger. A tag records a complete point-in-time snapshot, while file-level review exposes every later change. The verification script checks structure and obvious safety issues; it is not a substitute for reviewing a public diff before publishing.
