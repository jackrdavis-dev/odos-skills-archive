---
name: odos-media-v1
description: Turn the newest completed ODOS adventure into a source-grounded, resumable marketing campaign with exactly 12 Instagram posts including 3 videos, 3 weekly Patreon design/development articles, and 1 weekly DiceStory blog article. Use when Codex needs to discover the latest Ready.txt ODOS packet, create or continue ODOS social media, produce Instagram Reels/images/carousels/memes/ads/educational/monster/character posts, draft Patreon behind-the-scenes content, prepare a DiceStory website article, QA a campaign, or package approved content for publishing.
---

# odosMediav1

Operate as the ODOS media campaign manager. Select the newest ready adventure, lock its sources, create the complete campaign, checkpoint every deliverable, and report truthfully whether assets are drafted, approved, scheduled, or published.

## Start or resume a campaign

1. Read [references/content-contract.md](references/content-contract.md) before planning or creating content.
2. Run the manager with the available Python runtime:

   ```powershell
   python scripts/odos_media_manager.py init --output-root <workspace>/outputs/odos-media
   ```

   Use an explicit `--new-adventures`, `--text-root`, or `--start-date` only when the user supplies an override. Never silently select an older adventure if the newest `Ready.txt` candidate is invalid.
3. Read the returned `context.json`, `campaign-manifest.json`, and matched Text Studio source files. Treat the completed text-stage Markdown as factual authority and the Premium manifest/extracted media as visual authority. If text matching is missing or ambiguous, use the packet PDF/pages and omit unsupported development claims.
4. Resume an existing campaign when its campaign ID and source fingerprint match. Refuse changed source hashes. Keep previous campaigns intact when a newer ready adventure appears.
5. Use the campaign folder returned by the script for every output. Do not write into the release folder; it must retain exactly `Ready.txt` and its three ZIPs.

## Build the creative brief

Write `working/briefs/creative-brief.md` before individual posts. Include:

- premise, player-facing promise, tone, level/party facts, and spoiler boundary;
- three to five design pillars grounded in named source files;
- reusable cast, monster, scene, map, handout, and mechanic hooks;
- approved public claims and claims that must remain Patreon-only;
- one campaign CTA route and UTM campaign slug;
- a source ledger mapping every claim to a Markdown file, packet page, or media asset.

Inspect source media with the image-viewing tool before selecting, cropping, or editing it. Never infer playtest results, sales results, developer intent, quotes, or production history that the sources do not support. Label reasoned commentary as analysis.

## Plan the fixed inventory

Create all 16 deliverables in one editorial matrix before rendering media:

- `IG-01` through `IG-12`: exactly 3 videos and 9 image/carousel posts over four weeks.
- `PAT-01` through `PAT-03`: three distinct Patreon articles, one per week for three weeks.
- `BLOG-01`: one public, spoiler-light DiceStory article in the next weekly blog slot.

Use the concepts seeded in `campaign-manifest.json` as a balanced default, then adapt subjects to the adventure without changing counts. A carousel counts as one Instagram post. Covers, thumbnails, Story crops, subtitles, transcripts, and alternate exports are supporting assets, not extra posts.

For each deliverable, populate its title, hook, copy, one CTA, source references, asset references, accessibility fields, output files, and QA record. Read [references/campaign-schema.md](references/campaign-schema.md) before editing the manifest. Merge a completed deliverable atomically with:

```powershell
python scripts/odos_media_manager.py update --campaign <campaign-folder> --id IG-01 --data <deliverable-patch.json>
```

## Produce Instagram media

For the nine image/carousel posts:

1. Reuse the adventure's cover, page art, NPC/monster pages, handouts, maps, or tokens as the visual source.
2. Use image generation/editing for creative raster transformations after inspecting every referenced source. Preserve recognizable adventure details; do not invent contradictory characters, monsters, props, or text.
3. Export PNG or JPEG at 1080 by 1350. Keep key text inside safe margins, use readable contrast, and make the first carousel panel carry the hook and the last carry the CTA.
4. Save copy separately under `instagram/captions/`. Add concise alt text and restate essential image text in the caption.

For exactly three videos:

1. Create a storyboard, narration/on-screen script, poster, transcript, and SRT before rendering.
2. Produce 15–45 second, 1080 by 1920 MP4/H.264 videos from the adventure media. Put the hook in the first two seconds and one CTA at the end. Use licensed/original audio or silence.
3. If using a billable video service, obtain a current model recommendation and price, then obtain user approval before submitting jobs. Submit each job once, persist its request ID, poll the same job, and never restart a pending billable job.
4. If no suitable renderer or encoder is available, finish the three production-ready storyboards and mark only those deliverables `blocked_missing_video_renderer`. Never rename a GIF, WebM, storyboard, or placeholder as an MP4.

## Write Patreon and blog content

Write three materially different Patreon posts:

- `PAT-01`: design promise, creative constraints, and adventure structure.
- `PAT-02`: mechanics, pacing, clues, encounters, or table usability.
- `PAT-03`: development choices, iteration lessons, and reusable design takeaways.

Write each as 700–1,200 words with a title, excerpt, hero image, alt text, tier, spoiler label, source references, one table-use takeaway, one design takeaway, and one CTA. Release them weekly rather than claiming three were published in one week.

Write `BLOG-01` as a 1,000–1,600-word public, spoiler-light article. Include a premise, design challenge, standout design feature, exciting table possibilities, restrained behind-the-scenes analysis, hero/OG media, alt text, slug, SEO title, a 140–160 character meta description, excerpt, tags, internal links, and one product/Patreon CTA. Save both Markdown and a single DiceStory blog object matching the website schema. Do not use the current editor's whole-array import without first merging against an export; it would replace existing browser-local posts.

## Checkpoint and QA

Keep raw candidates, prompts, and QA artifacts under `working/`; keep only approved exports in the platform folders. Record source paths and hashes, not credentials.

Run plan validation during drafting:

```powershell
python scripts/odos_media_manager.py validate --campaign <campaign-folder> --phase plan
```

Generate a contact sheet for visual review:

```powershell
python scripts/build_contact_sheet.py --campaign <campaign-folder>
```

Inspect every final image and representative frames from every video. Then run:

```powershell
python scripts/odos_media_manager.py validate --campaign <campaign-folder> --phase ready
```

Do not mark the campaign complete while any count, source, copy, media, accessibility, rights, spoiler, link, or visual check fails. Use `blocked` for missing access or tooling and `failed` for an attempted operation that returned an error.

After the user reviews and explicitly approves the complete campaign, lock the exact approved snapshot:

```powershell
python scripts/odos_media_manager.py approve --campaign <campaign-folder> --approved-by <name>
```

## Publish only when authorized

Creation means a complete publish-ready package; it does not imply live publication. Read [references/publishing.md](references/publishing.md) only when the user asks to schedule, upload, or publish.

Require explicit approval of the reviewed campaign before external posting. Verify the destination account, visibility/tier, date/time, attachment, caption, and CTA immediately before each post. Persist remote IDs/URLs and verify them after publishing. Never claim success from a button click alone.

## Finish a manager run

Report the selected adventure and why it was selected, campaign path, counts by state, blockers, next scheduled item, and whether anything was actually published. Keep this task as the manager: future requests such as “continue the ODOS campaign,” “make this week's posts,” or “publish the approved items” must resume the source-locked campaign rather than reconstructing it.
