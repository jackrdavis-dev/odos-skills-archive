# Publishing contract

## Preconditions

Require a `ready` preflight result, unchanged ZIP hashes, no completed release in the current Pacific-time ISO week, authenticated Patreon and shop sessions, an exact Patreon edition-to-tier mapping, and shop edition-variant support. Resolve every `setup_gates` item in `release-config.json` before live publishing.

## Remote object keys

Use the release ID from `release-context.json` as the idempotency key. Before creation, search exact titles and inspect likely matches. Record every verified URL or ID in the ledger immediately.

## Shop contract

Create one product with three options:

| Edition | Price | Delivery |
| --- | ---: | --- |
| Basic | $1 | `<Title> - Basic.zip` |
| Deluxe | $3 | `<Title> - Deluxe.zip` |
| Premium | $5 | `<Title> - Premium.zip` |

Create the initial product first. Then return to the Admin product table and use that product's **Edit** action. In Edit Product, refine the slug, description, included-items list, compatibility, download policy, and starting price; upload the approved cover/product image; set the card image mode, detail-page image mode, width, and crop boxes; save; and verify the saved state. Do not treat initial creation as a finished listing.

Next use **Manage Files** or the edition-specific file editor to assign each ZIP to its matching edition. Show a shared description, cover, facts, and comparison table. Make edition selection required. Verify the storefront price change and the admin-side file assignment for every edition. Never attach all files to every purchase.

Record `shop_created` with the product ID/URL, `shop_edited` after the refined listing and imagery are saved, `shop_files_assigned` after all three edition files are verified, and `shop_verified` only after storefront and admin checks pass.

## Patreon contract

Create one coordinated four-post release:

| Order | Post | Audience | Attachment | Notify members |
| ---: | --- | --- | --- | --- |
| 1 | Premium download | Premium | Premium ZIP | No |
| 2 | Deluxe download | Deluxe and Premium | Deluxe ZIP | No |
| 3 | Basic download | Basic, Deluxe, and Premium | Basic ZIP | No |
| 4 | Public announcement | Public/free | None | Yes - the only notified post |

Post access is explicit; price hierarchy never implies inherited access. Verify every selected tier, filename, and notification setting in the published post. Place all posts in the configured collection. Use consistent artwork and tags. Keep fulfillment copy short. Disable email and push notifications on all three fulfillment posts. The announcement must include clearly labeled, working links to the authoritative Basic, Deluxe, and Premium fulfillment posts plus the shop product. Enable notifications on the announcement only; unless the owner explicitly overrides this contract, no release may notify members more than once.

Publish the announcement last so no marketing points to incomplete fulfillment. Before publishing it, verify all three fulfillment URLs and their tier restrictions. After publishing it, verify its links and confirm that it is the release's only notified post.

## State phases

Advance in this exact order:

`validated -> content_staged -> shop_created -> shop_edited -> shop_files_assigned -> shop_verified -> patreon_premium -> patreon_deluxe -> patreon_basic -> patreon_announcement -> homepage_deferred -> verified -> complete`

For each remote phase, store the URL or stable ID. Do not advance when only a draft, upload spinner, toast, or navigation attempt is visible.

## Recovery

On retry, compare source hashes with the ledger, verify each recorded remote object, and continue at the first incomplete phase. If an unrecorded matching remote object exists, verify it and attach its ID to the ledger rather than creating a duplicate. Stop when identity or access is ambiguous.

## Verification

Confirm shop edition names, prices, file assignments, product URL, cover, and description. Confirm all four Patreon URLs, audience selections, attachments, collection, and artwork. Confirm homepage is intentionally deferred. Mark complete only after every required check passes.
