# Content contract

## Source authority

Select the newest `Ready.txt` adventure by the timestamp inside the marker, descending. Require exact title-matched Basic, Deluxe, and Premium ZIPs; shared run ID; valid ODOS manifest; safe ZIP paths; CRC success; and strict tier inclusion. Stop if the newest candidate is invalid.

Match a Text Studio project only by one exact working title, `status: complete`, completed section hashes, and an update time no later than the Ready timestamp. Record missing or ambiguous text matching instead of guessing. Use text Markdown for facts and design analysis, and the Premium manifest/media for visual claims. Cite each factual or mechanical claim with a source path or packet page.

## Instagram inventory

Create exactly 12 posts. Exactly 3 must be video/Reels and 9 must be image or carousel posts. Use this adaptable mix:

| ID | Default pillar | Format |
|---|---|---|
| IG-01 | Launch trailer | video |
| IG-02 | Character spotlight | carousel |
| IG-03 | Adventure-design education | image |
| IG-04 | Adventure-specific meme | image |
| IG-05 | Monster/encounter spotlight | video |
| IG-06 | Meet the monster | carousel |
| IG-07 | Product/adventure ad | image |
| IG-08 | Clue, prop, map, or handout teaser | carousel |
| IG-09 | Designer/developer insight | video |
| IG-10 | Developer education | carousel |
| IG-11 | Scene/location spotlight | image |
| IG-12 | Community/final CTA | image |

Adapt a pillar when the source lacks a strong subject, but retain variety and the format counts. A carousel is one post. Schedule Monday, Wednesday, and Friday across four weeks by default.

Each caption must contain a hook, useful context, exactly one primary CTA, and 3–8 relevant hashtags. Put hashtags in accessible CamelCase where practical. Include 80–250 words unless the concept needs a shorter meme caption. Do not expose premium-only solutions or stat blocks in public posts.

### Image requirements

- PNG or JPEG, 1080×1350, 4:5.
- Use consistent carousel dimensions and visual language.
- Keep the hook clear on the first panel and the CTA on the last.
- Keep critical meaning out of decorative text alone; restate it in the caption.
- Provide alt text for every single image/panel.

### Video requirements

- MP4 with H.264 video, 1080×1920, 9:16, 15–45 seconds, 24 or 30 fps.
- Hook within two seconds; readable safe-zone typography; one closing CTA.
- Provide a poster, transcript, synchronized SRT/VTT, and burned-in captions.
- Use original/licensed audio or silence. Record the rights basis.
- Avoid flashes above three per second.

## Patreon inventory

Create exactly three posts and schedule one per week for three weeks. Write 700–1,200 words each. Make each article materially distinct and source-grounded:

1. Design promise, structure, constraints, and creative intent.
2. Mechanics, clues, pacing, encounters, or table usability.
3. Development retrospective, production decisions, and reusable lessons.

Include title, excerpt, hero media, tier, spoiler label, tags, alt text, source references, one design takeaway, one table-use takeaway, and one primary CTA. Do not fabricate personal anecdotes, playtest feedback, iteration history, or quotes.

## DiceStory blog inventory

Create exactly one 1,000–1,600-word article per adventure run for the next weekly blog slot. Keep it public and spoiler-light. Cover the premise, central design challenge, standout design feature, exciting play possibilities, and restrained behind-the-scenes analysis.

Provide title, slug, excerpt/dek, author, draft status, category, tags, hero/OG image, hero alt text, SEO title, 140–160-character meta description, internal links, one product/Patreon CTA, Markdown, and a blog object with:

```text
id, title, slug, dek, author, status, category, tags[], image,
featured, publishedAt, updatedAt, body[]
```

The current DiceStory editor stores a whole post array in browser `localStorage`. Treat the generated object as a patch. Merge it with an exported array or a durable website data source before publishing.

## CTA and accessibility

Choose one primary CTA per deliverable from `play`, `download`, `buy`, `join`, `read`, `comment`, `save`, or `share`. Require a valid target and campaign-specific `utm_source`, `utm_medium`, `utm_campaign`, and `utm_content`. Map Instagram links to a real profile/link-in-bio route.

Require descriptive alt text for visuals; transcripts, captions, and flashing checks for video; adequate contrast; and captions that carry essential visual meaning. Avoid emoji walls, all-caps paragraphs, and inaccessible hashtag casing.

## Hard QA gates

Do not pass a campaign unless:

1. Source selection, timestamp, run ID, hashes, and fingerprint are recorded.
2. Counts are exactly 12 Instagram, 3 video, 9 image/carousel, 3 Patreon, and 1 blog.
3. Claims resolve to real sources and content is non-duplicative.
4. Dimensions, codecs, duration, cropping, legibility, and audio rights pass.
5. Alt text, captions, transcripts, contrast, and flashing checks pass.
6. Spoiler, premium-content, brand-voice, and rights checks pass.
7. Links, tier mappings, dates, time zone, and UTM values validate.
8. Every final render receives visual inspection.
9. Human approval exists before scheduling or publishing.
10. Publication returns a verified remote ID/URL; otherwise record a blocker or failure.
