---
name: gplay-release-flow
description: Ship Android releases through Google Play with `gplay releases`. Use when uploading an AAB or APK to a track, promoting a build up the track ladder, steering a staged rollout, inspecting or downloading what a track holds, attaching a ProGuard/R8 mapping, sharing a build via Internal App Sharing, or managing legacy OBB expansion files.
---

# gplay release flow

Drive the Google Play release lifecycle with `gplay releases`: **upload** a
build to a track, **promote** it up the ladder, run a staged **rollout** on
production (`halt` / `resume` / `complete` it), and **list** what a track
holds.

Shared conventions are in `gplay-cli-usage`; onboarding auth is `gplay-setup`.

## Mental model: the track ladder + the rollout state machine

A build is uploaded to one **track** (`internal`, `alpha`, `beta`,
`production`, or any custom closed-track name) and then **promoted** up the
ladder: the same `versionCode`, no AAB re-upload. On a track, the latest
release moves through a small state machine:

```
draft ──► inProgress (userFraction f) ──► completed (f = 1.0)
               │  ▲
            halt│  │resume
               ▼  │
             halted (fraction preserved)
```

`rollout` sets the fraction, `halt` freezes it, `resume` un-freezes it, and
`complete` ramps to 100%. When a track holds two releases (e.g. `inProgress`
plus `halted`), every verb refuses to guess (exit `60`): pin one with
`--version-code` or `--release-name`.

## Upload a build to a track

```bash
gplay releases upload ./app.aab --track internal
gplay releases upload ./app.aab --track production --staged 0.1 --confirm
gplay releases upload ./app.aab --track production --complete --confirm
```

Any string is a valid `--track`, but the track must already exist (see
*Track must exist first* below). Flags: `gplay releases upload --help`.

AAB/APK uploads are resumable: a transient interruption resumes instead of
restarting from zero. Automatic, no flag.

`upload` also takes a legacy `.apk` (`[experimental]`, same pipeline;
`--format apk|bundle` overrides an ambiguous extension).

### Local preflight

Before any byte leaves, gplay checks the artifact by structure (container
format plus declared package name), whatever its extension says: a mismatch
fails offline with exit `20`, no Edit opened. An unreadable manifest degrades
to a stderr `NOTE` and the upload proceeds. `--dry-run` reports the result;
`--mapping` passes unchecked. Same guard on every artifact upload.

Name release-notes files in BCP 47 (`en-US.txt`): an underscore form
(`en_US.txt`) is refused before the Edit opens, every offending file in one
error.

## Promote a build up the ladder (no re-upload)

```bash
gplay releases promote --from internal --to alpha
gplay releases promote --from beta --to production --staged 0.1 --confirm
```

## Staged rollout: rollout / halt / resume / complete

These four act on the **latest** release of `--track`.

```bash
gplay releases rollout  --track production --to 0.25 --confirm   # set fraction → inProgress
gplay releases halt     --track production --confirm             # freeze at current fraction
gplay releases resume   --track production --confirm             # un-freeze, continue
gplay releases complete --track production --confirm             # ramp to 1.0 → completed
```

## Inspect what is on a track

```bash
gplay releases list --track production
gplay releases list --track production --output json
gplay releases list --track production --columns name,status,userFraction
```

`releases list` shows every release on one track; cross-track views are
`gplay-tracks`. `releases artifacts list` (`[experimental]`) lists every
APK/AAB attached to the app with the versionCode `promote` and `rollout`
accept:

```bash
gplay releases artifacts list --kind bundle
```

## Generated APKs (what Play signs from your AAB)

`generated` (`[experimental]`) lists and downloads the APKs Play signs and
serves from your bundle: verify the signing identity, sideload, archive.

```bash
gplay releases generated list --version-code 42
gplay releases generated download <downloadId> --version-code 42 --dest ./universal.apk
```

Read a fresh Download ID from `list` each time: it changes across
re-generation. A failed download leaves no partial file.

## Deobfuscation mappings (symbolicate vitals crash stacks)

```bash
# With the artifact, in the same Edit (the common case):
gplay releases upload ./app.aab --track production --mapping ./mapping.txt --confirm

# After the fact, on an already-published versionCode:
gplay releases mappings upload ./mapping.txt --version-code 42
```

Symbolicated stacks are read in `gplay-vitals`.

## Internal App Sharing (private shareable build links)

```bash
gplay releases sharing upload ./app.aab            # prints a private downloadUrl
gplay releases sharing upload ./app.aab --dry-run
```

`releases sharing upload` (`[experimental]`) bypasses tracks and the Edit
lifecycle: a private QA link, not a release. No `--confirm`.

## Legacy OBB expansion files

APK-only, legacy. When the task touches `.obb` files, read [obb.md](obb.md).

## Production safety

Production defaults to a **draft** (ADR-0002): `--complete` / `--staged`
there, and every rollout verb on production, reach real users, so each
requires `--confirm`.

## Track must exist first (trackhint)

`upload`/`promote` to a custom track that does not exist fails with exit
`30` and names the fix: `gplay tracks create <name>` (see `gplay-tracks`),
then re-run. Creating a track is always that explicit step; the standard
tracks always exist.
