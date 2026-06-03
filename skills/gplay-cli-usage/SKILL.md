---
name: gplay-cli-usage
description: The cross-cutting conventions every gplay command shares — credential/account resolution order, package targeting and `.gplay/` pinning, output formats (table/json/markdown), semantic exit codes, the `--dry-run`/`--confirm` safety gates, stdout-is-data/stderr-is-logs, and the implicit Edit lifecycle. Use when running or designing any gplay command, wiring gplay into CI, branching on its exit codes, or building a more specific gplay workflow on top of these rules.
---

# gplay CLI conventions (foundation)

This is the **foundation skill**: the conventions that hold for *every* gplay
command, factored out once so the workflow skills (`gplay-release-flow`,
`gplay-setup`, `gplay-apps`, `gplay-tracks`, `gplay-reviews`,
`gplay-metadata-sync`, `gplay-compliance`, `gplay-team`) can reference it
instead of repeating them. The normative source of truth is
[`docs/DESIGN.md`](https://github.com/PollyGlot/google-play-cli/blob/main/docs/DESIGN.md)
in the CLI repo; this skill summarizes it for agents and does **not** freeze
per-command flag lists.

## `--help` is the source of truth

gplay's commands are self-describing. Confirm the current verbs, flags, and
defaults from the binary, never from memory:

```bash
gplay --help                       # the whole command tree
gplay <group> --help               # a namespace (releases, tracks, team, …)
gplay <group> <command> --help     # one command, with its real flags
gplay exit-codes                   # the semantic exit-code table
```

If this skill and `--help` ever disagree, trust `--help`.

## Which credential / account (resolution order)

Every authenticated command resolves the service-account credential in this
order, highest priority first:

1. `--service-account <path-or-inline-json>` — a JSON file path **or** inline
   JSON content. Overrides everything below.
2. `--account <name>` — a specific stored Account. Overrides env + the active
   Account.
3. `GPLAY_SERVICE_ACCOUNT` env var — a path or inline JSON.
4. The **active** stored Account (set up via `gplay auth login`).

Setting this up from scratch is the `gplay-setup` skill. Auth problems exit
`10` (bad/again credential) or `11` (the service account is not invited on the
app/account).

## Which app (`--package` + project pinning)

Most commands need a target package. Resolution (ADR-0004):

1. `--package com.example.app` on the command, else
2. the package pinned in `.gplay/config.json` for the current repo.

Pin once with `gplay init` (or `gplay apps init`) so day-to-day commands need
no `--package`. Managing the registry of packages is the `gplay-apps` skill.

## Output: table on a TTY, JSON in a pipe

`--output` takes `table`, `json`, or `markdown`. The default is **auto**
(ADR-0005): a human table on a terminal, JSON when piped or in CI. For
machine consumption, ask for `--output json` explicitly — read commands pass
the API payload through (ADR-0003), and write commands return the request/diff
body, so a CI gate is usually one `jq` line.

**stdout is data, stderr is logs.** Parse stdout; warnings, progress, and
`-v/--verbose` flow steps go to stderr and never pollute the JSON. (Example:
`reviews list` prints its "last 7 days only" warning to stderr.)

## Exit codes — branch on the number, not the text

`gplay exit-codes` prints the full table. The semantic codes:

| Code | Meaning | Retry-safe |
|---|---|---|
| 0 | Success | — |
| 1 | Generic error (fallback) | no |
| 2 | CLI misuse (unknown flag/command, bad value, missing arg) | no |
| 3 | A named safety flag is missing (`--confirm` / `--grant-admin`) — re-run with it | yes, with the flag |
| 10 | Authentication failure | no |
| 11 | Authorization (403 — SA not invited) | no |
| 20 | Client-side validation (bad AAB, unknown locale, …) | no |
| 30 | API 4xx (not found, conflict, gone, …) | no |
| 40 | API 5xx (upstream unhealthy) | **yes** |
| 50 | Network (timeout, DNS, refused) | **yes** |
| 60 | State conflict (open edit, rate-limited, ambiguous target) | sometimes |

Agents should treat `3` as "append the named flag and re-run", `40`/`50` as
"back off and retry", and `2`/`10`/`11`/`20`/`30` as "fix the input, do not
retry blindly".

## Safety: `--dry-run` everywhere, `--confirm` for live writes

- **`--dry-run`** is available on write commands: it validates inputs and
  prints the payload/diff it *would* send, with no HTTP call (and usually no
  auth needed). Reach for it before any production-affecting write.
- **`--confirm`** gates the writes that reach real users or the live store —
  production releases, `metadata apply`, `compliance datasafety set`. Omitting
  it fails with exit `3` and names the flag. `CI=true` never auto-confirms.
- **`--grant-admin`** is the stronger gate for conferring admin in
  `gplay-team`.

When a write refuses, the message names the missing flag — that refusal is
*agent-resolvable* (ADR-0017): re-run with the flag it asked for.

## The Edit lifecycle is abstracted

Google Play mutations run inside a transactional **Edit**
(`edits.insert → change → edits.commit`). gplay performs the whole three-step
dance **implicitly** in a single command: each write opens its own Edit, makes
the change, and commits, discarding the Edit automatically on failure. You do
not manage Edit IDs by hand. `--keep-edit-on-failure` skips that auto-discard
for debugging. (A couple of surfaces sit *outside* the Edit model on purpose —
e.g. `compliance datasafety` is a direct write — their skills call that out.)

## Map of skills

| Surface | Skill |
|---|---|
| Auth onboarding | `gplay-setup` |
| App registry + details | `gplay-apps` |
| Releases (upload/promote/rollout) | `gplay-release-flow` |
| Tracks + testers | `gplay-tracks` |
| Reviews | `gplay-reviews` |
| Store listings + images | `gplay-metadata-sync` |
| Data Safety | `gplay-compliance` |
| Team users + grants | `gplay-team` |
