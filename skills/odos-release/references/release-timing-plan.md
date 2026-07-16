# Release timing plan

## Current policy

- Treat `Ready.txt` as eligibility for the next scheduled release, never as an immediate publish trigger.
- Start the weekly release workflow Sunday at 9:00 PM in `America/Los_Angeles` until the user explicitly approves a different slot.
- Keep the schedule stable while the release system proves operationally reliable.
- Never change the production schedule automatically from research or a single strong release.

The Patreon account had zero posts on 2026-07-16, so it had no account-specific engagement history. Sunday 9:00 PM is therefore a baseline chosen by the owner, not a data-proven optimum.

## Evidence summary

- Patreon says weekdays typically outperform weekends and recommends a predictable release rhythm: <https://www.patreon.com/PatreonforCreators/posts/ultimate-guide-128495182>
- Patreon Post Insights exposes impressions, seen, email click rate, push click rate, conversions, and post-attributed revenue. Data updates hourly and displays in UTC; email open rate is only a rough signal: <https://support.patreon.com/hc/en-us/articles/360042841711-Post-Insights>
- Patreon sends email and push notifications by default and schedules according to the publishing device timezone: <https://support.patreon.com/hc/en-us/articles/115004048046-Posting-to-your-Patreon>
- StartPlaying reports that U.S. TTRPG play and booking is strongest on nights and weekends, especially around 4–5 PM Pacific, and that many bookings happen in the final 48 hours before play: <https://startplaying.games/blog/posts/best-time-schedule-ttrpg-dnd-games-dm>
- Kickstarter's analysis of two years of campaign data favors Tuesday, with activity peaking near 4 PM Eastern / 1 PM Pacific, and reports lower weekend engagement: <https://updates.kickstarter.com/best-time-to-launch/>
- Mailchimp's large email dataset identifies roughly 10 AM recipient-local time as a common optimum, finds Sunday least often optimal, and recommends audience-specific testing: <https://mailchimp.com/resources/insights-from-mailchimps-send-time-optimization-system/>
- U.S. Google Trends for the Dungeons & Dragons topic showed substantially higher attention on weekends in the 90 days ending 2026-07-16. This is normalized search interest, not purchase intent: <https://trends.google.com/trends/explore?date=today%203-m&geo=US&q=%2Fm%2F026q9&hl=en>

Inference: Sunday 9:00 PM Pacific catches high D&D attention but reaches Eastern members at midnight. Sunday 5:00 PM preserves the owner's Sunday cadence while reaching all continental U.S. zones at a more usable hour. Tuesday afternoon is the strongest later challenger for discovery and purchasing several days before weekend play.

## Candidate order

1. Baseline: Sunday 9:00 PM Pacific.
2. First challenger: Sunday 5:00 PM Pacific.
3. Day-of-week challenger: Tuesday 3:00 PM Pacific.
4. Reserve candidate: Thursday 4:00 PM Pacific.

## Measurement rollout

### Phase 1: establish the baseline

- Run 6 successfully completed Sunday 9:00 PM releases.
- Record snapshots 24 hours, 72 hours, and 7 days after each release.
- Keep title pattern, cover treatment, CTA, prices, notification settings, and external promotion as consistent as practical.
- Track adventure theme, holidays, audience size, tier mix, outages, and special promotion as confounders.

### Phase 2: add measurement plumbing

- Give every shop link a release-specific UTM campaign and a timing-slot value.
- Add shop analytics for unique product sessions, product views, checkout starts, purchases, refunds, and edition mix.
- Add non-sensitive `release_id`, `edition`, and `timing_slot` metadata to Stripe checkout records.
- Use Patreon click and push-click rates as the primary Patreon signals; do not use email opens as the deciding metric.
- Ask members for preferred windows with a non-binding poll. Treat preferences as candidate selection, not proof.

The shop did not contain GA4 or equivalent session/conversion instrumentation when audited on 2026-07-16. Implement and verify this before drawing shop-conversion conclusions.

### Phase 3: test time within Sunday

- Compare Sunday 9:00 PM with Sunday 5:00 PM using balanced, precommitted blocks.
- Collect at least 6 completed releases per slot; 8 is preferable.
- Do not assign slots after seeing the adventure theme or artwork.
- If a scheduled release has no eligible adventure, carry the assigned slot forward.

### Phase 4: test the weekday

- Compare the winning Sunday slot with Tuesday 3:00 PM using the same rules.
- Use Thursday 4:00 PM only if Tuesday is inconclusive or members strongly prefer Thursday.
- Announce any permanent day change at least two releases in advance.

## Metrics and decision rule

Primary metrics:

- Patreon: 24-hour email click rate and push-notification click rate.
- Shop: purchases per 100 unique product sessions.

Secondary metrics:

- Patreon: 72-hour and 7-day seen rate, comments, paid/free member conversions, and attributed revenue.
- Shop: product views, checkout starts, revenue per 100 sessions, edition mix, refunds, and failed payments.

Do not declare a winner before the minimum sample. Recommend a schedule change only when the challenger shows a repeatable 15–20% practical lift, has at least 90% estimated probability of outperforming baseline, and does not materially harm the other channel. If results remain inconclusive, retain the predictable current schedule.

## Notification hygiene

The owner approved this policy on 2026-07-16: disable notifications on the Basic, Deluxe, and Premium download posts, then enable notifications on one cohesive public announcement that links to all three correctly gated posts. Treat the announcement as the release's only notified post.

Always verify that the publishing device is set to Pacific time. Patreon schedules from the device timezone, while its Insights reports use UTC.
