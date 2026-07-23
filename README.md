# google-play-cli-skills

[![skills.sh](https://skills.sh/b/PollyGlot/google-play-cli-skills)](https://skills.sh/PollyGlot/google-play-cli-skills)

Agent skills for [**gplay**](https://github.com/PollyGlot/google-play-cli) — a
fast, single-binary CLI for the Google Play Developer API. Each skill is a
`SKILL.md` of plain-Markdown instructions that teaches an AI agent (Claude Code
and friends) how to drive `gplay` at the prompt: how to think about the release
lifecycle, which command shapes to reach for, and the gotchas the `--help`
text alone won't warn you about.

> These skills drive the `gplay` CLI; they do not replace it. Install `gplay`
> first — see the [CLI repo](https://github.com/PollyGlot/google-play-cli).

## Install

```bash
npx skills add PollyGlot/google-play-cli-skills
```

This pulls the skills below into your agent's skill directory. After
installing, an agent can invoke a skill by name (e.g. *gplay-release-flow*)
whenever the task matches its "Use when".

## Catalogue

Start with **gplay-cli-usage** — it holds the cross-cutting conventions the
other skills build on. The rest map one-to-one to a `gplay` surface.

| Skill | Use when |
|---|---|
| [`gplay-cli-usage`](skills/gplay-cli-usage/SKILL.md) | Running or designing any gplay command — credential/account resolution, `--package` pinning, output formats, semantic exit codes, `--dry-run`/`--confirm`, the implicit Edit lifecycle. The foundation the other skills reference. |
| [`gplay-setup`](skills/gplay-setup/SKILL.md) | Setting up gplay auth for the first time, switching or rotating service accounts, or diagnosing an auth failure (`auth login` / `status` / `doctor` / `list` / `logout`). |
| [`gplay-apps`](skills/gplay-apps/SKILL.md) | Onboarding one or more packages into gplay's local registry, discovering which apps a credential can reach (`apps accessible list`), listing/viewing/removing registered apps, pinning one to the repo, or editing app details (default language, contact info). |
| [`gplay-release-flow`](skills/gplay-release-flow/SKILL.md) | Uploading a build (AAB, or a legacy APK; large artifacts upload resumably), cutting a release, promoting a build up the track ladder (internal → alpha → beta → production), running or steering a staged production rollout (rollout / halt / resume / complete), inspecting which releases sit on a track, downloading the APKs Play generates, attaching ProGuard/R8 mappings for vitals symbolication, sharing a private Internal App Sharing build, or managing legacy OBB expansion files. |
| [`gplay-tracks`](skills/gplay-tracks/SKILL.md) | Inspecting tracks, creating a closed-testing track before an upload, auditing country availability (read-only), or setting the Google Groups authorized to test a closed track. |
| [`gplay-reviews`](skills/gplay-reviews/SKILL.md) | Triaging recent reviews, filtering by star rating, viewing one review's full user↔developer thread, replying to a user, or bulk-answering reviews from a TSV in CI (the API exposes the last 7 days), or reading the full review history from the monthly GCS CSV reports (one month or a `--from`/`--to` range) with `reviews history`. |
| [`gplay-metadata-sync`](skills/gplay-metadata-sync/SKILL.md) | Editing store listings or screenshots, migrating listing text into version control, localizing a listing, or gating a listing change in CI before it goes live. |
| [`gplay-compliance`](skills/gplay-compliance/SKILL.md) | Pushing or validating the Data Safety declaration from a versioned CSV (the only Play compliance surface with an API). |
| [`gplay-team`](skills/gplay-team/SKILL.md) | Inviting or off-boarding a Developer-account member, granting or adjusting per-app access, or looking up which permission alias / role bundle to use. |
| [`gplay-customapps`](skills/gplay-customapps/SKILL.md) | Creating a managed Google Play private (organisation-scoped) app from an AAB/APK — the one Play API path that creates an app record. Irreversible, so `--confirm`-gated and capability-gated. |
| [`gplay-vitals`](skills/gplay-vitals/SKILL.md) | Reading post-launch quality signals — crash / ANR / slow-start / rendering / wakeup / LMK rates, error reports and clustered issues, and Play-detected anomalies. Read-only, on the distinct Play Developer Reporting service (its own OAuth scope). |
| [`gplay-orders`](skills/gplay-orders/SKILL.md) | Looking up a Google Play order by its order ID (single or batch) from a complaint or payout report, or issuing a refund. Refund moves money and is `--confirm`-gated; both need explicit financial capabilities never bundled into a role. |
| [`gplay-games`](skills/gplay-games/SKILL.md) | Configuring a game's Play Games Services achievements and leaderboards (list/view/create/update/delete), addressed by the numeric Play Games application ID (not the package). Draft-only — publishing to players stays Console-only. |
| [`gplay-recovery`](skills/gplay-recovery/SKILL.md) | Responding to a bad release: staging a draft app recovery, deploying it to force-update impacted users off the broken versionCode, widening its audience (append-only), or cancelling it. Deploy/cancel/add-targeting are `--confirm`-gated. |
| [`gplay-device-tiers`](skills/gplay-device-tiers/SKILL.md) | Creating or inspecting device tier configs for tiered content delivery (device groups, an ordered tier set, country sets). Immutable — create/get/list only, no update or delete — so a new config is a new id. |

> **Also covered by the foundation skill:** `gplay schema` — the offline,
> no-auth Android Publisher API introspection command (shipped in gplay
> v0.5.0, `[experimental]`). It has no dedicated skill yet; `gplay-cli-usage`
> documents it next to `--help`.

## Roadmap

The v1 set above tracks the current `gplay` GA surface. Skills for gated
surfaces land as those CLI surfaces ship:

- **gplay-subscription-management** — subscriptions & IAP (+ RevenueCat) —
  gated on [`#51`](https://github.com/PollyGlot/google-play-cli/issues/51).

See the CLI's [`docs/BACKLOG.md`](https://github.com/PollyGlot/google-play-cli/blob/main/docs/BACKLOG.md)
for the full roster and gating.

## Repo layout

One folder per skill, each holding a `SKILL.md`:

```
skills/
  gplay-release-flow/
    SKILL.md
```

Every `SKILL.md` opens with YAML frontmatter carrying two required fields:

```yaml
---
name: gplay-release-flow
description: <what it does> … Use when <the trigger phrasing>.
---
```

- **`name`** — kebab-case, matches the skill's folder name.
- **`description`** — one line, ends with a "Use when …" clause so an agent
  can decide relevance. This is the same text shown in the catalogue above.

A missing or malformed `name`/`description` breaks `npx skills add`, so keep
both fields present and well-formed when adding a skill.

## License

[MIT](LICENSE) © 2026 Pavlo Trinko
