---
name: gplay-games
description: Configure a game's Play Games Services achievements and leaderboards with gplay `games`, keyed by the numeric `--application-id`; writes touch the draft only (publishing to players is Console-only). Use when creating or editing achievements or leaderboards, scripting their config in CI, or round-tripping a configuration as JSON.
---

# gplay games (Play Games Services configuration)

`gplay games` configures a game's **Play Games Services** resources —
**achievement** and **leaderboard** configurations, each with the full CRUD set
(`list` / `view` / `create` / `update` / `delete`). It is an Admin API surface:
the developer *configures* the game. It is **not** the Play Games Services
runtime the game itself calls (sign-in, score submission) — that is out of
scope. Shared conventions (auth, output, exit codes, `--dry-run`/`--confirm`)
are in `gplay-cli-usage`. The whole namespace is `[experimental]`.

## Addressing: `--application-id`, not `--package`

This is the trap. Play Games resources are keyed by the **numeric Play Games
application ID** (a distinct ID space), *not* the Android package name.
**`--application-id <numeric-id>` is required on `list` and `create`**; the
per-resource commands `view` / `update` / `delete` are addressed by the
achievement/leaderboard id alone (no `--application-id`). The
`.gplay/config.json` package pin does **not** apply anywhere here.

```bash
gplay games achievements list --application-id 1234567890
gplay games leaderboards list --application-id 1234567890
```

## Draft-only — there is no publish

The single most important gotcha: every write here edits the **draft**
configuration. The `published` copy players see is **read-only**, and the API
exposes **no publish method** — pushing a draft live to players is **Play
Console-only**. So `gplay games … create/update` stages the change; a human
finishes it in the Console. Don't expect a CLI command to make it live.

## Achievements

```bash
gplay games achievements view <achievementId> --output json     # read one
gplay games achievements create --application-id 123 \
  --name "First Blood" --description "Win your first match" \
  --type STANDARD --initial-state REVEALED --point-value 10
```

- Field flags: `--name` / `--description` (localized, under `--locale`, default
  `en-US`), `--type STANDARD|INCREMENTAL`, `--initial-state HIDDEN|REVEALED`,
  `--point-value`, and `--steps-to-unlock` (**INCREMENTAL only**).
- Or `--from-json <file|->` for a full `AchievementConfiguration` body — the
  round-trip of `view --output json`, and the way to set **multiple locales at
  once**. `--from-json` and the field flags are **mutually exclusive**.

## Leaderboards

```bash
gplay games leaderboards create --application-id 123 \
  --name "High Scores" --score-order LARGER_IS_BETTER \
  --score-min 0 --score-max 1000000
```

- Field flags: `--name` (localized, `--locale`), `--score-order
  LARGER_IS_BETTER|SMALLER_IS_BETTER`, `--score-min` / `--score-max`.
- Or `--from-json <file|->` for a full `LeaderboardConfiguration` — the way to
  set `scoreFormat` or multiple locales. Mutually exclusive with the field flags.

## `update` replaces — fetch, edit, resend

`update <id>` is a **full PUT replace**: the body *replaces* the draft. For a
partial edit, read the current config, edit it, and resend it whole:

```bash
gplay games achievements view <id> --output json > ach.json
# edit ach.json …
gplay games achievements update <id> --from-json ach.json
```

The field flags on `update` send only what they name, so `--name` alone is fine
for a one-field change; reach for the fetch-edit-resend round-trip when you need
to preserve a rich body (multiple locales, nested fields).

## Safety

- `create` / `update` are **routine draft writes** — no `--confirm`. Rehearse
  with `--dry-run` (no HTTP; `--output json` prints the request body).
- `delete <id>` is **irreversible** → requires **`--confirm`** (missing → exit
  `3`); `CI=true` never auto-confirms.
- `GPLAY_READONLY` refuses every live write (exit `4`); `--dry-run` is exempt.
- `--output json` mirrors the API response verbatim (ADR-0003); `list` paging is
  `--max-results` + `--page-token` (read `nextPageToken` from the response).

Confirm the current verbs and flags with `gplay games --help` and
`gplay games <group> <command> --help` — the surface is `[experimental]`
(ADR-0033) and may still evolve.
