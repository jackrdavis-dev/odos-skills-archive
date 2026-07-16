# Campaign state and manifest

## Directory contract

```text
<campaign-id>/
  campaign-manifest.json
  run-state.json
  source/context.json
  source/media-inventory.json
  source/media/...
  source/text/...
  instagram/images/
  instagram/videos/
  instagram/captions/
  instagram/covers/
  instagram/transcripts/
  instagram/subtitles/
  patreon/
  blog/
  publishing/
  working/briefs/
  working/prompts/
  working/candidates/
  working/qa/
  working/contact-sheets/
```

Keep release ZIPs and `Ready.txt` immutable. Put drafts and rejected candidates under `working/`; put only final, reviewed assets under platform folders.

## Campaign identity

Use `<slug>--<run_id>` as `campaign.id`. Lock the three tier ZIP hashes, Ready marker contents, Premium manifest inventory, and matched text-stage hashes into `source.fingerprint`. Resume only when the fingerprint matches.

## Deliverable fields

Each `deliverables[]` entry must retain:

```text
id, concept_id, platform, channel, week, slot, format, content_pillar,
title, hook, status, publish_at, audience, tier, spoiler_level,
source_refs[], asset_refs[], output_files[],
copy: caption, body_file, excerpt, hashtags[], tags[], seo_title,
      meta_description, slug, internal_links[],
accessibility: alt_text, panel_alt_text[], transcript_file, subtitle_file,
               poster_file, burned_in_captions, flashing_check, contrast_check,
cta: type, label, target_url, route, utm_source, utm_medium,
     utm_campaign, utm_content,
rights: source_media, audio, fonts,
publication: target_account, remote_id, remote_url, published_at, error,
qa: checks[], result, reviewed_at, reviewer, media_probe
```

Use campaign-relative paths in manifest fields. Keep credentials and session material out of files and logs.

## State transitions

Use these deliverable states:

```text
planned -> drafted -> media_ready -> qa_passed -> approved -> scheduled -> published
```

Use `blocked` when required access, approval, source, or tooling is unavailable. Use `failed` after an attempted operation returns an error. A blocked or failed item may return to its prior valid state only after recording the resolution in `qa.checks` or `publication.error`.

Use these campaign phases in `run-state.json`:

```text
source_locked -> brief_complete -> copy_complete -> media_complete ->
qa_complete -> approved -> publishing -> complete
```

Advance one phase at a time. Never infer a phase from filenames alone; validate first and append a timestamped history entry.

Approve only through `odos_media_manager.py approve`. The command requires a passing ready validation and records a hash of the exact copy, media references, schedule, accessibility, rights, source, and QA snapshot. Publishing validation must reject any later content drift until the changed campaign is reviewed and approved again.

## Atomic updates

Write proposed per-deliverable changes to a small JSON patch and merge them through `odos_media_manager.py update`. The manager refuses unknown IDs and changed source fingerprints. Re-run `validate --phase plan` after structural changes and `validate --phase ready` before approval.

## Extending platforms

Keep `concept_id`, factual message, source references, reusable assets, and CTA platform-neutral. Add future platform variants as new deliverables and channel configuration rather than changing source discovery. Version schema changes and supply migrations before altering existing campaign manifests.
