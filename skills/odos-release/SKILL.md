---
name: odos-release
description: Publish approved ODOSv5.1 One Dollar One Shot packets from Desktop/New Adventures to Patreon and the DiceStory Shop. Use when Codex must find the oldest Ready.txt adventure, validate Basic/Deluxe/Premium ZIPs, prepare marketing copy and artwork, create tier-gated Patreon release posts, create or resume one three-edition shop product, audit or recover a partial release, enforce one release per Pacific-time week, or report release failures.
---

# ODOS Release

## Read first

Read `references/release-config.json` and `references/publishing-contract.md` before every run. Read `references/content-contract.md` before writing release copy. Read `references/release-timing-plan.md` before measuring performance or proposing a schedule change.

Never store usernames, passwords, cookies, one-time codes, or session material in this skill, a repository, a staging folder, or command output. Use the user's existing authenticated Chrome sessions. Stop and report an authentication failure when a required session is unavailable.

If a setup gate in `release-config.json` is unresolved, run validation and staging only. Do not create external drafts or mutate Patreon, the shop, or the website.

## Choose the mode

- Use `audit` for read-only discovery, validation, account checks, and ledger inspection.
- Use `manual` for a user-invoked release. Validate and stage first, then require explicit approval immediately before the first external mutation unless the user's current request already authorizes live publishing.
- Use `scheduled` only when the automation prompt explicitly authorizes one live release. Publish at most one adventure and enforce the Pacific-time weekly limit.
- Use `resume` when the ledger contains an incomplete release. Verify recorded remote objects before continuing at the first incomplete phase.

## Discover and validate

Treat `Ready.txt` only as an eligibility signal. Its appearance never triggers immediate publication. In normal operation, publish only during the configured weekly scheduled run; an off-schedule manual release requires explicit authorization in the user's current request.

Resolve this skill's installation directory and an available Python runtime, then run:

```powershell
python "<skill-dir>/scripts/preflight_release.py" --prepare
```

The script must:

- Resolve the real Windows Desktop, including OneDrive redirection.
- Scan `Desktop/New Adventures` for folders containing `Ready.txt`.
- Skip releases marked complete in the ledger.
- Select the oldest unpublished release.
- Enforce one completed release per ISO week in `America/Los_Angeles`.
- Require exactly `Ready.txt` and the three title-matched tier ZIPs.
- Verify ZIP CRCs, safe paths, embedded ODOSv5.1 manifests, matching title/run ID, tier hierarchy, PDFs, covers, and SHA-256 hashes.
- Stop on the oldest release when it is invalid; never skip it to publish a newer packet.

Treat `no_ready` and `weekly_limit_reached` as successful no-ops. Treat `invalid` as a release failure. Do not publish when files change after preflight.

The prepared staging directory contains `release-context.json`, `cover.png`, and `overview.png`. Inspect the two images directly and use the embedded manifest inventories to describe edition differences.

## Start or resume state

Initialize the release before any external mutation:

```powershell
python "<skill-dir>/scripts/release_state.py" start --context <release-context.json>
```

Use `release_state.py show` before every retry. After each verified phase, advance the ledger and record its remote URL or ID. Record a failure without discarding the last successful phase.

Never infer success from a click. Require a resulting URL, visible published state, selected audience, attached filename, product edition, or other authoritative signal.

## Prepare release content

Create the artifacts required by `references/content-contract.md` in the release staging directory. Base claims on the cover, overview, and embedded manifests. Keep copy spoiler-light. Do not invent levels, runtime, contents, or benefits that are not visible in the packet.

Use the approved packet cover as the default hero image. Add concise alt text. Explain exact Basic, Deluxe, and Premium differences with inventory counts.

## Run live preflight

Use Chrome control because publishing depends on existing signed-in sessions. Read its file-upload guidance before attaching any ZIP or image. Use current DOM snapshots and visible labels; do not hardcode fragile selectors.

Before mutations, verify:

1. The Patreon creator identity and URL match the config.
2. All required Patreon tiers exist at the expected prices and have an unambiguous edition mapping.
3. The shop supports one product with three independently priced, independently delivered editions.
4. The source ZIP hashes still match `release-context.json`.
5. No matching Patreon post or shop product already exists outside the ledger.

Stop on any mismatch. Never degrade to three unrelated shop products, one shared attachment, or broader Patreon access.

## Publish in recoverable order

Follow `references/publishing-contract.md` exactly.

1. Create the initial single shop product.
2. Return through Admin, open the product's Edit action, refine the listing, upload its cover/product imagery, set image display/crops, and save.
3. Open Manage Files or the edition-file editor, assign the three tier ZIPs, and verify all three editions.
4. Publish and verify the Premium download post with email and push notifications disabled.
5. Publish and verify the Deluxe download post with email and push notifications disabled.
6. Publish and verify the Basic download post with email and push notifications disabled.
7. Publish the public announcement last, with notifications enabled as the release's only notified post, and link it to all three correctly gated download posts.
8. Skip homepage mutation while it is disabled in config and remind the user that homepage integration remains pending.
9. Run live verification and mark the release complete only when every required surface passes.

Search for an exact existing object before creating one. On retry, reuse verified remote objects and resume from the next ledger phase.

## Report failures

Record failures with `release_state.py fail`. Report the adventure, failed phase, safe error summary, and next action in the Codex task. Use the configured email only as a fallback when task reporting is unavailable and an authenticated mail session exists. Never include secrets, cookies, or full browser diagnostics.

Do not attempt email reporting while `failure_reporting.email_enabled` is false. After the first fully verified end-to-end release, remind the user to design and enable a different email alert method; keep that work deferred until the core release system succeeds.

Keep `Ready.txt` and the source ZIPs unchanged after release. The ledger, staging files, and reports belong under the configured local state directory.
