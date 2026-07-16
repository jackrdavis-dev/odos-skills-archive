# End-to-end ODOS runbook

This guide explains the full system. The skill files remain the authoritative operational instructions.

## 1. Create the text handoff

Use `odos-text-studio` for a new adventure or to resume an incomplete packet. It initializes a working folder, generates a 20-row monthly option table, and pauses for the only concept decision: one independently chosen Style, Quest, and Antagonist.

After selection it generates and checkpoints, in order:

1. Adventure Skeleton
2. DM Packet
3. NPC Suite
4. Clue Web
5. Formal Stat Blocks
6. Three player-facing handout specifications
7. A style-neutral Visual Asset Brief

Finalization creates a versioned text-only export and leaves the working folder intact.

## 2. Compile the visual product

Point `odosv5-1` at the exported folder. It validates its immutable visual references, scaffolds state files, builds a validated page-copy pack, and creates exactly four calibration proofs:

- one recurring character;
- one multi-character action scene;
- one complete Scene page;
- one playable, top-down battle map.

Production waits for one explicit approval of those proofs. It then records cast identity, scene geography, and text-free art plates; compiles immutable per-asset prompts; generates one candidate at a time; runs OCR and visual QA; and promotes only passing assets.

When all mapped assets are current and approved, the packager creates Basic, Deluxe, and Premium folders, PDFs, manifests, and ZIP files. Only approved PNG masters may become PDF pages.

## 3A. Release the product

`odos-release` scans the real Desktop `New Adventures` folder, selects the oldest unpublished valid packet, validates all three ZIPs, and respects a one-release-per-Pacific-week limit.

The recoverable publication order is:

1. Create the single three-edition shop product.
2. Refine the listing and artwork.
3. Assign each edition its matching ZIP.
4. Verify the storefront and admin configuration.
5. Publish Premium, Deluxe, and Basic Patreon fulfillment posts with member notifications disabled.
6. Publish the public announcement last as the release's only notified post, with verified links to all fulfillment posts and the shop.
7. Verify every remote URL, audience, attachment, price, and file assignment.

## 3B. Build the media campaign

`odos-media-v1` selects the newest valid completed packet, matches its completed Text Studio sources when possible, and locks both into a source fingerprint.

The fixed campaign is:

- 12 Instagram posts across four weeks: exactly 3 videos and 9 images/carousels;
- 3 distinct weekly Patreon design/development articles;
- 1 spoiler-light DiceStory blog article.

Every deliverable retains sources, copy, CTA, accessibility data, rights basis, output files, publication state, and QA. Campaign creation does not imply live publishing.

## 4. Audit the result

At each boundary, ask a different question:

- **Text:** Are the facts and mechanics internally consistent and checkpointed?
- **Visual packet:** Does every approved file match references, state, hashes, OCR, style, and table use?
- **Release:** Did the correct buyer receive the correct edition, and is every remote object verified?
- **Media:** Is every public claim source-grounded, accessible, spoiler-safe, and explicitly approved?
