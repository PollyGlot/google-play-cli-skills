---
name: gplay-release-flow
description: Ship Android releases through Google Play with the gplay CLI — upload an AAB to a track, promote a build up the track ladder without re-uploading, run and steer a staged production rollout (halt / resume / complete), and inspect what is live on a track. Use when uploading a build, cutting or shipping a release, promoting internal → alpha → beta → production, starting/ramping/pausing/finishing a staged rollout, or checking which releases sit on a track.
---

# gplay release flow

Drive the Google Play release lifecycle from the command line with `gplay`:
**upload** a build to a track, **promote** it up the ladder, run a staged
**rollout** on production (and `halt` / `resume` / `complete` it), and **list**
what is currently on a track. gplay hides Google's three-step Edit transaction
(`edits.insert → change → edits.commit`) behind a single call per command.

## The `--help` is the source of truth

Flags and defaults evolve with the CLI. **This skill pins the command shapes,
the mental model, and the gotchas — not an exhaustive flag list.** Before you
build an invocation, confirm the current flags with:

```bash
gplay releases --help              # the whole release cluster
gplay releases <command> --help    # one command (upload, promote, rollout, …)
```

If a flag you expect is absent, trust `--help`, not this document.

## Before you run anything

1. **Auth.** Every command needs a working service-account credential. If you
   are not sure it is wired up, run `gplay auth doctor` (and see the
   `gplay-setup` skill for onboarding). Auth failures exit `10` (bad
   credential) or `11` (the service account is not invited on the app).
2. **Which app.** Pin the package once with `gplay init` (writes
   `.gplay/config.json`), or pass `--package com.example.app` on each call.
3. **Output for machines.** In CI or when parsing, add `--output json`. On a
   TTY the default is a human table; piped/non-TTY defaults to JSON already.
4. **Branch on exit codes, not text.** gplay returns semantic exit codes
   (`gplay exit-codes` prints the table). The ones that matter here:
   `3` a required `--confirm` is missing, `30` an API 4xx such as a missing
   track, `60` an ambiguous target (two releases coexist). `40`/`50` are
   retry-safe (5xx / network).

## Mental model: the track ladder + the rollout state machine

A build is uploaded to one **track** (`internal`, `alpha`, `beta`,
`production`, or any custom closed-track name) and then **promoted** up the
ladder — the same `versionCode`, no AAB re-upload. On a track, the latest
release moves through a small state machine:

```
draft ──► inProgress (userFraction f) ──► completed (f = 1.0)
               │  ▲
            halt│  │resume
               ▼  │
             halted (fraction preserved)
```

`rollout` sets the fraction, `halt` freezes it, `resume` un-freezes it, and
`complete` ramps to 100%.

## Upload a build to a track

```bash
gplay releases upload ./app.aab --track internal
gplay releases upload ./app.aab --track production --staged 0.1 --confirm
gplay releases upload ./app.aab --track production --complete --confirm
```

One call runs the full Edit lifecycle (`edits.insert → bundles.upload →
tracks.update → edits.commit`). Any string is a valid `--track`, so custom
closed tracks "just work" — **as long as the track already exists** (see
*Track must exist first* below). Attach notes with `--release-notes` or a
`--release-notes-dir` of `<locale>.txt` files. Run
`gplay releases upload --help` for the full set.

## Promote a build up the ladder (no re-upload)

```bash
gplay releases promote --from internal --to alpha
gplay releases promote --from beta --to production --staged 0.1 --confirm
```

`promote` copies the latest release on `--from` to `--to`, keeping the same
`versionCode`. Release notes carry over from the source unless you override
with `--release-notes` / `--release-notes-dir`. If the source track holds more
than one release (e.g. an `inProgress` plus a `halted` one), disambiguate with
`--version-code N` or `--release-name <name>` — otherwise the command refuses
rather than guess (exit `60`).

## Staged rollout: rollout / halt / resume / complete

These four act on the **latest** release of `--track`. On `production` each one
reaches real users, so each requires `--confirm`.

```bash
gplay releases rollout  --track production --to 0.25 --confirm   # set fraction → inProgress
gplay releases halt     --track production --confirm             # freeze at current fraction
gplay releases resume   --track production --confirm             # un-freeze, continue
gplay releases complete --track production --confirm             # ramp to 1.0 → completed
```

- `rollout --to <f>` sets the staged fraction (`0 < f ≤ 1.0`) and flips status
  to `inProgress`.
- `halt` sets `status=halted` while **preserving** the current `userFraction`,
  so a later `resume` picks up exactly where it left off.
- `resume` returns the release to `inProgress` at the halted fraction.
- `complete` ramps to `userFraction=1.0`, `status=completed`, ending the
  rollout.

When two releases coexist on the track, pin one with `--version-code` or
`--release-name` (same rule as `promote`).

## Inspect what is on a track

```bash
gplay releases list --track production
gplay releases list --track production --output json
gplay releases list --track production --columns name,status,userFraction
```

`releases list` reads the track inside a read-only Edit (nothing is committed)
and shows every release on it — draft, inProgress, halted, completed. For a
cross-track or whole-track view use the `gplay-tracks` skill (`gplay tracks
list` / `gplay tracks view`).

## Production safety is built in

gplay defaults to the cautious choice on `production` (ADR-0002): an upload or
promote that targets production becomes a **draft** release unless you ask for
a live one with `--complete` or `--staged`, and those — plus every
`rollout`/`halt`/`resume`/`complete` on production — require an explicit
`--confirm`. If you omit it, the command fails with **exit `3`** and names the
flag it wants; re-run with that flag added. Treat exit `3` as "safe to retry
verbatim once `--confirm` is appended", never as a hard failure.

Every write command also takes **`--dry-run`**: it validates inputs and prints
the payload it *would* send without making any HTTP call. Use it to preview a
production change before committing to it.

## Track must exist first (the `trackhint` behavior)

gplay **never** auto-creates a track as a side effect of an upload or promote —
a typo'd `--track` must fail loudly, not silently spawn a phantom track. When
`upload` or `promote` targets a custom closed track that has not been created
yet, the command fails with **exit `30`** and a hint naming the fix:

```
track "qa-team" does not exist — create it first with
`gplay tracks create qa-team`, then re-run …
```

Recovery: create the track once (`gplay tracks create <name>` — see the
`gplay-tracks` skill), then re-run the upload/promote. The standard tracks
(`internal`, `alpha`, `beta`, `production`) always exist and never need this.

## Quick recipes

```bash
# CI: upload to internal, fail the job on any non-zero exit
gplay releases upload ./app.aab --track internal --output json || exit $?

# Cut a cautious production release: 10% staged, then ramp once metrics look OK
gplay releases upload ./app.aab --track production --staged 0.1 --confirm
gplay releases rollout --track production --to 0.5 --confirm
gplay releases complete --track production --confirm

# Something looks wrong mid-rollout — freeze, investigate, then resume
gplay releases halt   --track production --confirm
gplay releases resume --track production --confirm

# Preview a production promote without sending anything
gplay releases promote --from beta --to production --staged 0.1 --confirm --dry-run
```
