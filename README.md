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

| Skill | Use when |
|---|---|
| [`gplay-release-flow`](skills/gplay-release-flow/SKILL.md) | Uploading a build, cutting a release, promoting a build up the track ladder (internal → alpha → beta → production), running or steering a staged production rollout (rollout / halt / resume / complete), or inspecting which releases sit on a track. |

## Roadmap

The v1 set tracks the `gplay` GA surface; skills land as each CLI surface
stabilizes. Planned (not yet in this repo):

- **gplay-setup** — service-account onboarding (`auth login` / `auth doctor`).
- **gplay-tracks** — read-only track inspection and closed-track creation.
- **gplay-reviews** — list and reply to user reviews.
- **gplay-metadata-sync** — store listings and images.

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
