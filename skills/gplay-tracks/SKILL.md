---
name: gplay-tracks
description: Inspect and manage Google Play release tracks and their testers with gplay — list tracks, view one track's full state, create custom closed-testing tracks, read a track's country availability (read-only), and replace the Google Groups authorized to test a closed track. Use when checking what's on a track, creating a closed track before an upload, auditing where an app is distributed, or wiring up the tester audience for a closed test.
---

# gplay tracks (+ availability + testers)

Tracks are where releases live; testers are who may install a closed track.
gplay folds the two together because they are operationally coupled
(DESIGN §10). Shared conventions (auth, `--package`, output, exit codes) are
in `gplay-cli-usage`; shipping builds onto tracks is `gplay-release-flow`.

## Inspect tracks

```bash
gplay tracks list --package com.example.app          # every track on the app
gplay tracks view --track production                 # one track's full state
```

`tracks view` answers "is anything wrong on this track right now?" — the latest
release, its status, and rollout fraction. (Post-ADR-0019 this read is `view`,
not the old `status`.)

## Create a closed track

```bash
gplay tracks create qa-team
```

The create endpoint supports **exactly one kind**: a `CLOSED_TESTING` track on
the DEFAULT (phone) form factor — so there is no `--type` / `--form-factor`
flag, and there is **no API path to create open/internal tracks** (those exist
already). Creating a track that already exists surfaces the API error (exit
`30`); gplay does not fake idempotency. Use `--dry-run` to preview the
`TrackConfig`; there is no `--confirm` (a closed test track is low-stakes).

> This is the other half of the release-flow **trackhint**: an
> `upload`/`promote` to a custom closed track that doesn't exist yet fails with
> exit `30` and tells you to run `gplay tracks create <name>` first — gplay
> never auto-creates a track as a side effect. See `gplay-release-flow`.

## Country availability (read-only)

```bash
gplay tracks availability view --track production
```

Availability — which countries a track's artifacts ship to — is **read-only**
at the Developer API level (ADR-0012): there is no writer. To *change* where an
app is available, use the Play Console. The bare `gplay tracks availability`
prints help; the read is `availability view`.

## Testers (closed-track audience)

```bash
gplay testers list --track qa-team
gplay testers set --track qa-team --group qa@googlegroups.com,beta@googlegroups.com
gplay testers set --track qa-team --clear        # close the closed test
```

`testers set` is **declarative**: it replaces the *whole* audience (it maps 1:1
to `testers.update` — there is no add/remove). The API exposes **only Google
Groups**, not individual tester emails. A bare `set` with neither `--group`
nor `--clear` is refused (exit `2`) so a forgotten `--group` can never silently
wipe the list; empty the audience on purpose with `--clear`. No `--confirm`;
`--dry-run` previews. Confirm flags with `gplay testers set --help`.

## Typical closed-test setup

```bash
gplay tracks create qa-team
gplay testers set --track qa-team --group qa@googlegroups.com
gplay releases upload ./app.aab --track qa-team        # see gplay-release-flow
```
