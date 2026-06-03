# google-play-cli-skills

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
| [`gplay-apps`](skills/gplay-apps/SKILL.md) | Onboarding a package into gplay's local registry, listing/viewing/removing registered apps, pinning one to the repo, or editing app details (default language, contact info). |
| [`gplay-release-flow`](skills/gplay-release-flow/SKILL.md) | Uploading a build, cutting a release, promoting a build up the track ladder (internal → alpha → beta → production), running or steering a staged production rollout (rollout / halt / resume / complete), or inspecting which releases sit on a track. |
| [`gplay-tracks`](skills/gplay-tracks/SKILL.md) | Inspecting tracks, creating a closed-testing track before an upload, auditing country availability (read-only), or setting the Google Groups authorized to test a closed track. |
| [`gplay-reviews`](skills/gplay-reviews/SKILL.md) | Triaging recent reviews, filtering by star rating, replying to a user, or bulk-answering reviews from a TSV in CI (the API exposes the last 7 days). |
| [`gplay-metadata-sync`](skills/gplay-metadata-sync/SKILL.md) | Editing store listings or screenshots, migrating listing text into version control, localizing a listing, or gating a listing change in CI before it goes live. |
| [`gplay-compliance`](skills/gplay-compliance/SKILL.md) | Pushing or validating the Data Safety declaration from a versioned CSV (the only Play compliance surface with an API). |
| [`gplay-team`](skills/gplay-team/SKILL.md) | Inviting or off-boarding a Developer-account member, granting or adjusting per-app access, or looking up which permission alias / role bundle to use. |

## Roadmap

The v1 set above tracks the current `gplay` GA surface. Skills for gated
surfaces land as those CLI surfaces ship:

- **gplay-vitals** — Android vitals (crashes / ANRs) — gated on
  [`#49`](https://github.com/PollyGlot/google-play-cli/issues/49).
- **gplay-subscription-management** — subscriptions & IAP (+ RevenueCat) —
  gated on [`#51`](https://github.com/PollyGlot/google-play-cli/issues/51).

See [`PollyGlot/google-play-cli#53`](https://github.com/PollyGlot/google-play-cli/issues/53)
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

CI lints this frontmatter on every push (see
[`.github/workflows/lint-skills.yml`](.github/workflows/lint-skills.yml)) and
fails the build if a `name` or `description` is missing or malformed. Run the
check locally with:

```bash
python3 scripts/lint_skill_frontmatter.py
```

## License

[MIT](LICENSE) © 2026 Pavlo Trinko
