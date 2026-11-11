---
name: gplay-release-flow
description: Ship Android releases through Google Play with `gplay releases`. Use when uploading an AAB or APK to a track, promoting a build up the track ladder, steering a staged rollout, inspecting or downloading what a track holds, building a system APK for a device image, attaching a ProGuard/R8 mapping, sharing a build via Internal App Sharing, or managing legacy OBB expansion files.
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
draft ──► inProgress (userFraction f, 0 < f < 1) ──► completed (no fraction)
               │  ▲
            halt│  │resume
               ▼  │
             halted (fraction preserved)
```

`rollout` sets the fraction, `halt` freezes it, `resume` un-freezes it, and
`complete` ramps to 100%. `--staged` takes a fraction strictly between 0 and
1: `--staged 1.0` exits `2` before any call; a full rollout is `--complete`
(on `upload`/`promote`) or `releases complete`. When a track holds two
releases (e.g. `inProgress` plus `halted`), every verb refuses to guess (exit `60`): pin one with
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

### Several artifacts, one release

```bash
gplay releases upload phone.aab wear.aab --track beta --retain-version-code 41
```

Several positional artifacts (per-ABI APKs, a phone plus a Wear bundle) land in
one Edit and one release listing every versionCode, all or nothing: any failure
discards the Edit. `--retain-version-code` keeps an already-uploaded build
serving alongside them; gplay passes it unchecked, so a wrong code fails with
Google's error. `--mapping` takes a single artifact: for a multi-artifact
release, attach mappings afterwards with `releases mappings upload`.

`--externally-hosted <file.json>` (`[experimental]`) registers an APK served
from your own host instead of uploading one: Managed Play private apps only
(see `gplay-customapps`), shape in `gplay schema ExternallyHostedApk`.

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
gplay releases rollout  --track production --staged 0.25 --confirm   # set fraction → inProgress
gplay releases halt     --track production                           # freeze at current fraction
gplay releases resume   --track production --confirm                 # un-freeze, continue
gplay releases complete --track production --confirm                 # ramp to 100% → completed
```

`halt` needs no `--confirm` even on production: it reaches no new user.

A track holds one `completed` release at most. `complete` therefore drops the
previous full rollout in the same update, as the Play Console does, and names
its versionCodes as `superseded` on the ✓ line (`--output json` stays the
verbatim `tracks.update` body). Halted, draft and other `inProgress` releases
stay untouched; `rollout`, `halt` and `resume` never drop a release.

### Read the live track first with `--plan`

`--dry-run` stays offline, so it cannot say which release a transition hits or
replaces. `--plan` (`[experimental]`, on the four verbs above, not on
`promote`) reads the live track and writes nothing: run it before any
production transition, then re-run the same line with `--confirm` instead of
`--plan`.

```bash
gplay releases complete --track production --plan
gplay releases complete --track production --confirm
```

- It names the target release, the status and fraction it would end in, and
  the releases it would supersede or keep. `--output json` is gplay-shaped
  and carries `"plan": true`, never a `tracks.update` body.
- No `--confirm` needed. It needs a credential: it reads inside the pinned
  Edit when `gplay edits begin` opened one, else in a throwaway Edit it always
  discards.
- An ambiguous track fails with exit `60`, as the live call would: add the
  `--version-code` or `--release-name` the plan should use, and keep it on the
  live call.
- `--plan` with `--dry-run` exits `2`. Under `GPLAY_READONLY` it runs, like
  `--dry-run`: it reads the live track and writes nothing.

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
gplay releases artifacts list --format bundle
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

## System APK variants (device system images)

`system-apks` (`[experimental]`) asks Play to build an APK for an OEM or
preload system image from an uploaded AAB, then lists, reads and downloads it.

```bash
gplay releases system-apks create --version-code 42 --abi arm64-v8a --screen-density 480 --locale en-US --dry-run
gplay releases system-apks list --version-code 42
gplay releases system-apks view <variantId> --version-code 42
gplay releases system-apks download <variantId> --version-code 42 --dest ./system.apk
```

A direct call outside the Edit lifecycle. `create` only adds a variant (no
`--confirm`), and Play assigns the `variantId` that `view` and `download`
take: read it from `create` or `list`.

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
there, and `rollout`, `resume` and `complete` on production, reach real users,
so each requires `--confirm`. `halt` is exempt.

## Track must exist first (trackhint)

`upload`/`promote` to a custom track that does not exist fails with exit
`30` and names the fix: `gplay tracks create <name>` (see `gplay-tracks`),
then re-run. Creating a track is always that explicit step; the standard
tracks always exist.
