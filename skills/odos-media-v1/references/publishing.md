# Publishing adapters and safety

Read this file only when the user asks to schedule, upload, or publish campaign items.

## Universal gate

Require `validate --phase publish` to pass. Confirm the user-approved scope, target account, audience/tier, local time zone, scheduled time, media, copy, CTA, and spoiler level immediately before posting. Never store credentials in the campaign. Reuse authenticated browser sessions or approved connectors only after verifying the visible account identity.

Persist one idempotency key per item: `<campaign-id>:<deliverable-id>`. Search for an existing matching draft/post before creating another. After submission, capture the remote ID/URL, reopen it, and verify media, copy, audience, and schedule. Record `failed` when verification fails; do not retry blindly.

## Instagram

Prefer an authenticated Instagram/Meta publishing adapter that supports both feed images/carousels and Reels. Verify current API/account capabilities at run time. Existing local ODOS marketing code may support image URL publishing but does not prove Reel support; do not route videos through an image endpoint.

If using browser control, verify the profile, upload all carousel panels in order, set accessible alt text when available, preview crop/safe zones, add caption, and confirm schedule. Record the resulting permalink or scheduled-item ID.

## Video generation service

When a video generation connector is available and the user has not named a model, request a current model recommendation. Retrieve pricing before any billable generation and obtain user approval for the estimated three-video cost. Prefer image-to-video using source-approved adventure art. Submit long-running jobs once, store endpoint/request/status/response identifiers under `publishing/video-jobs.json`, poll existing jobs, and fetch results only when complete.

## Patreon

Verify the creator identity and exact tier visibility. Create drafts first. Attach the approved hero media, apply the spoiler label and tags, set the scheduled date, and visually re-open the draft. Do not reuse the ODOS release-post tier mapping without verifying that these editorial posts target the intended audience.

## DiceStory blog

The current website implementation stores blog posts in browser `localStorage` and has no durable server CMS. A generated Markdown file or single JSON object is not live content.

To publish safely, choose one verified path:

1. Export the current full blog array from the editor, merge the new object by unique `id`/`slug`, import the merged array, and verify in the same browser profile; or
2. Migrate/patch the website to a durable content source, add the article and optimized hero asset there, deploy, and verify from a clean browser.

Updating `seedPosts` alone does not update browsers that already hold the storage key. FTP deployment is an external mutation and requires explicit approval plus configured credentials. Verify the public article URL after deployment before recording `published`.
