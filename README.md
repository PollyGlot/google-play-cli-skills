# google-play-cli-skills

[![skills.sh](https://skills.sh/b/PollyGlot/google-play-cli-skills)](https://skills.sh/PollyGlot/google-play-cli-skills)

Agent skills for [**gplay**](https://github.com/PollyGlot/google-play-cli), a
single-binary CLI for the Google Play Developer API. Each skill is a `SKILL.md`
that tells an AI agent (Claude Code, or any agent that reads skills) how to
drive `gplay`: which command to run for a task, in what order, and what the
`--help` text leaves out, such as which commands are irreversible or which
Play features have no API at all.

> The skills drive the `gplay` CLI and do not replace it. Install `gplay`
> first, from the [CLI repo](https://github.com/PollyGlot/google-play-cli).

## Install

```bash
npx skills add PollyGlot/google-play-cli-skills
```

This copies the skills below into your agent's skill directory, from the
current `main`. An agent then loads a skill by name (e.g. *gplay-release-flow*)
when the task matches its "Use when" clause.

`gplay install-skills` installs the same skills without Node. It fetches a
commit pinned inside the binary, so a given gplay version always installs the
same files, which can lag behind `main`.

## Catalogue

Start with **gplay-cli-usage**: it holds the conventions every other skill
assumes. Each of the others covers one `gplay` command group.

| Skill | Use when |
|---|---|
| [`gplay-cli-usage`](skills/gplay-cli-usage/SKILL.md) | Running any gplay command or wiring gplay into CI: credential and `--package` resolution, output formats, exit codes, the `--dry-run`/`--confirm`/`GPLAY_READONLY` gates, the implicit Edit lifecycle, and `gplay schema` for offline API introspection. |
| [`gplay-setup`](skills/gplay-setup/SKILL.md) | Setting up gplay auth for the first time, switching, rotating or removing a service account, or diagnosing an auth failure. |
| [`gplay-apps`](skills/gplay-apps/SKILL.md) | Registering or pinning packages, finding which apps a credential can reach, editing app details (default language, contact info), or sweeping the account for drift with `apps audit`. |
| [`gplay-release-flow`](skills/gplay-release-flow/SKILL.md) | Uploading an AAB or APK, promoting a build from internal to production, steering a staged rollout (halt, resume, complete), downloading the APKs Play generates, attaching a ProGuard/R8 mapping, sharing a build through Internal App Sharing, or managing legacy OBB files. |
| [`gplay-tracks`](skills/gplay-tracks/SKILL.md) | Checking what a track holds, creating a closed-testing track before an upload, reading country availability, or setting the Google Groups that test a closed track. |
| [`gplay-reviews`](skills/gplay-reviews/SKILL.md) | Triaging recent reviews (the API only returns the last 7 days), reading one review's thread, replying singly or in batch from a TSV, or pulling older reviews from the monthly GCS reports with `reviews history`. |
| [`gplay-metadata-sync`](skills/gplay-metadata-sync/SKILL.md) | Editing a store listing or its screenshots, adding a locale, pulling the listing into version control, or gating a listing change in CI. |
| [`gplay-monetization`](skills/gplay-monetization/SKILL.md) | Putting subscriptions and one-time products under version control, editing prices, offers or listings, checking catalog drift in CI, promoting a legacy in-app product to v2, or repricing live subscribers. Unlike `metadata`, a live product with no file on disk becomes a delete in the plan, and a plan with deletes needs `--confirm`. |
| [`gplay-compliance`](skills/gplay-compliance/SKILL.md) | Pushing or validating the Data Safety declaration from a versioned CSV. It is the only Play compliance form with an API. |
| [`gplay-team`](skills/gplay-team/SKILL.md) | Inviting or off-boarding a Developer account member, granting per-app access, or looking up a permission alias or role bundle. |
| [`gplay-customapps`](skills/gplay-customapps/SKILL.md) | Creating a private app for an organisation on managed Google Play, the only API call that creates an app record. Irreversible and `--confirm`-gated. |
| [`gplay-vitals`](skills/gplay-vitals/SKILL.md) | Checking crash, ANR, slow-start, rendering, wakeup or LMK rates after a rollout, reading error reports and clustered issues, or listing anomalies Play detected. Read-only, and it needs its own OAuth scope. |
| [`gplay-orders`](skills/gplay-orders/SKILL.md) | Looking up an order by its ID from a buyer complaint or a payout report, or refunding it. A refund moves money: it is `--confirm`-gated and needs a money permission that no role bundle includes. |
| [`gplay-games`](skills/gplay-games/SKILL.md) | Creating, editing or deleting a game's Play Games Services achievements and leaderboards, addressed by the Play Games application ID rather than the package. Publishing them to players stays in the Console. |
| [`gplay-recovery`](skills/gplay-recovery/SKILL.md) | Forcing users off a broken versionCode: drafting an app recovery, deploying it, widening its audience (it can only grow), or cancelling it. |
| [`gplay-device-tiers`](skills/gplay-device-tiers/SKILL.md) | Creating or inspecting device tier configs for tiered asset delivery. A config cannot be updated or deleted, so a change means a new config ID. |
| [`gplay-appstore`](skills/gplay-appstore/SKILL.md) | Running a third-party Android app store: mirroring Play's catalog or its update-event feed, submitting a hosted app to Google's review (irrevocable), or withdrawing it. |
| [`gplay-signing`](skills/gplay-signing/SKILL.md) | Enrolling an app in Play App Signing with a key held in your own Cloud KMS, or rotating that key. Google-managed signing has no API. Irreversible and `--confirm`-gated. |

## Coverage

Every `gplay` command that operates on Play is named by at least one skill.
The check below walks the binary's command tree and fails on any such command
no skill names, so a gplay release that adds a command group turns CI red
until a skill covers it. Local plumbing (`completion`, `version`,
`install-skills`, `exit-codes`) is exempt.
Commands marked `[experimental]` in `gplay --help` sit outside gplay's
stability contract, and `gplay-cli-usage` says what that means for CI.

What the CLI plans to cover next lives in its
[`docs/BACKLOG.md`](https://github.com/PollyGlot/google-play-cli/blob/main/docs/BACKLOG.md).

## Repo layout

One folder per skill. Each holds a `SKILL.md`, and sometimes a companion file
the skill links to for a rare case (`gplay-release-flow/obb.md`):

```
skills/
  gplay-release-flow/
    SKILL.md
    obb.md
```

Every `SKILL.md` opens with YAML frontmatter carrying exactly two fields:

```yaml
---
name: gplay-release-flow
description: <what it does>. Use when <the trigger phrasing>.
---
```

`name` is kebab-case and matches the folder. `description` is one line ending
in a "Use when" clause, which the agent reads to decide whether to load the
skill. If the description contains `: `, quote it: unquoted, the YAML is
invalid and `npx skills add` skips the skill without an error.

## Checking a change

```bash
python3 scripts/check-skills.py            # needs gplay on PATH
python3 scripts/check-skills.py --offline  # frontmatter, links and style only
```

The script resolves every `gplay` invocation in the skills against the
installed binary's commands and flags. A removed flag, an invented subcommand
or a frontmatter typo fails the run instead of shipping. CI runs it on every
pull request and every Monday, because drift usually comes from a gplay
release rather than from a commit here.

## License

[MIT](LICENSE) © 2026 Pavlo Trinko
