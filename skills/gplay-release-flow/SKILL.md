---
name: gplay-release-flow
description: Ship Android releases through Google Play with the gplay CLI — upload an AAB (or a legacy APK) to a track (large artifacts upload resumably), promote a build up the track ladder without re-uploading, run and steer a staged production rollout (halt / resume / complete), inspect what is live on a track, list or download the signed APKs Play generates from an uploaded AAB, attach ProGuard/R8 deobfuscation mappings for vitals symbolication, push a private Internal App Sharing build, and manage legacy OBB expansion files. Use when uploading a build, cutting or shipping a release, promoting internal → alpha → beta → production, starting/ramping/pausing/finishing a staged rollout, checking which releases sit on a track, fetching the exact split/standalone/universal artifacts Play serves, symbolicating vitals crash stacks, sharing a QA build link, or working with OBB files.
---

# gplay release flow

Drive the Google Play release lifecycle from the command line with `gplay`:
**upload** a build to a track, **promote** it up the ladder, run a staged
**rollout** on production (and `halt` / `resume` / `complete` it), and **list**
what is currently on a track. gplay hides Google's three-step Edit transaction
(`edits.insert → change → edits.commit`) behind a single call per command.

Shared conventions — auth setup (`gplay auth doctor`, see `gplay-setup`),
`--package` pinning via `gplay init`, `--output json` for machines, and the
semantic exit-code table — are in `gplay-cli-usage`. The codes that matter
most here: `3` a required `--confirm` is missing (re-run with it), `30` an API
4xx such as a missing track, `60` an ambiguous target (two releases coexist),
`40`/`50` retry-safe (5xx / network).

## The `--help` is the source of truth

Flags and defaults evolve with the CLI. **This skill pins the command shapes,
the mental model, and the gotchas — not an exhaustive flag list.** Before you
build an invocation, confirm the current flags with:

```bash
gplay releases --help              # the whole release cluster
gplay releases <command> --help    # one command (upload, promote, rollout, …)
```

If a flag you expect is absent, trust `--help`, not this document.

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
`--release-notes-dir` of `<locale>.txt` files, and a ProGuard/R8
`--mapping mapping.txt` so vitals can symbolicate this build's crash stacks
(see *Deobfuscation mappings* below). Run `gplay releases upload --help` for
the full set.

Large-artifact uploads are **resumable** (v0.16.0): gplay transfers the
AAB/APK over Google's resumable upload protocol, so a transient interruption
during a big upload resumes instead of restarting from zero. It is automatic —
there is no flag to set (and no `--timeout` cap applies to the upload leg).

`upload` also accepts a **legacy `.apk`** (`[experimental]`, via
`edits.apks.upload`): AAB vs APK is auto-detected by extension, and
`--format apk|bundle` overrides when the extension is ambiguous. The rest of
the pipeline (track, notes, `--mapping`, draft-by-default on production,
`--dry-run`/`--confirm`) is identical. Google has required the AAB for new
apps since August 2021, so APK uploads only serve existing apps still
distributed as APKs — if the app requires an App Bundle, Google's rejection
passes through verbatim.

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

## Generated APKs: list + download what Play signs from your AAB

After an upload, Play **generates and signs** the APKs it actually serves to
devices from your AAB — split, standalone, and universal APKs, plus asset-pack
and recovery-module slices. The `generated` sub-surface (`[experimental]`)
lists their download metadata and fetches the raw signed bytes — to verify the
signing identity, sideload, or archive the exact artifacts Play serves.

```bash
gplay releases generated list --version-code 42
gplay releases generated download <downloadId> --version-code 42 --dest ./universal.apk
gplay releases generated download <downloadId> --version-code 42 --dest -   # stream to stdout
```

Points to know:

- **Edit-free reads.** The `generatedapks` endpoints are application-scoped
  (not under an Edit) — gplay issues a direct GET; don't pattern-match
  `releases list` and expect an Edit. Only requires the service account to be
  invited on the app.
- **`--version-code N` is required on both** — it addresses the uploaded
  bundle. `list` flattens the API's signing-key groups into one row per
  artifact (*type · module · split/variant/slice id · downloadId · cert*);
  `--output json` stays the verbatim `GeneratedApksListResponse` (ADR-0003).
- The **Download ID** from `list` is the positional handle `download` takes.
  It is **not a URL** and **not stable** across re-generation — read a fresh
  one from `list`, never cache it.
- `download` writes to **`--dest PATH`** (required; `-` streams to stdout) —
  the payload is opaque bytes, so there is no `--output` here (ADR-0034).
  Bytes are streamed, a `✓` line on stderr reports count and destination, and
  a **failed transfer leaves no partial file behind**.
- Exit codes: `11` (403 — not invited), `30` (404 — unknown
  package/version/Download ID), `40`/`50` retry-safe; `download` adds `20`
  when `--dest` can't be written. Missing required args are usage (exit `2`).

## Deobfuscation mappings (symbolicate vitals crash stacks)

A ProGuard/R8 **`mapping.txt`** lets Play vitals de-obfuscate a release's crash
stacks. There are two ways to attach one:

```bash
# The common case — with the artifact, in the same Edit:
gplay releases upload ./app.aab --track production --mapping ./mapping.txt --confirm

# After the fact — attach to an already-published versionCode:
gplay releases mappings upload ./mapping.txt --version-code 42
gplay releases mappings upload ./native.txt  --version-code 42 --type nativeCode
```

Prefer `--mapping` on `upload` when the mapping exists at build time.
`releases mappings upload` covers the case where the version is already live and
you only later need symbolication — it runs its own Edit lifecycle
(`edits.insert → deobfuscationfiles.upload → edits.commit`). `--version-code` is
required; `--type` is `proguard` (default) or `nativeCode`; `--dry-run` previews
without a call. See the `gplay-vitals` skill for reading the symbolicated stacks.

## Internal App Sharing (private shareable build links)

```bash
gplay releases sharing upload ./app.aab            # prints a private downloadUrl
gplay releases sharing upload ./app.apk --output json
gplay releases sharing upload ./app.aab --dry-run
```

`releases sharing upload` (`[experimental]`) pushes an APK or AAB to Google Play
**Internal App Sharing** and prints the private, shareable `downloadUrl` an
authorized tester follows to install it. It **bypasses tracks and the Edit
lifecycle entirely** — a QA/preview gesture, not a release: no track, no
rollout, no `versionCode` promotion. APK vs AAB is auto-detected by extension
(`--format apk|bundle` overrides). No `--confirm` is needed (the link is private
and creates no release), but `GPLAY_READONLY=1` still refuses it (exit `4`).
`--output json` passes the `InternalAppSharingArtifact` through verbatim
(`downloadUrl`, `certificateFingerprint`, `sha256`).

## Legacy OBB expansion files

**Legacy surface.** Expansion files are the pre-AAB mechanism for >150 MB
out-of-APK assets, and only APK-based apps use them — most apps use **Play Asset
Delivery** instead. The whole `expansion-files` namespace is `[experimental]`.

```bash
gplay releases expansion-files upload ./main.obb --version-code 42 --type main
gplay releases expansion-files set --version-code 43 --references-version 42 --type main
gplay releases expansion-files view --version-code 42 --type main
```

- `upload` attaches an `.obb` to an already-published APK `--version-code`
  (`--type main|patch`, the two files an APK can have), via the full Edit
  lifecycle.
- `set` points one APK's expansion config at **another** APK's already-uploaded
  file (`--references-version N`) — no new binary uploaded.
- `view` reads an APK's expansion config (its own `fileSize`, or the
  `referencesVersion` it points at) inside a read-only Edit.

All three take `--dry-run` and are refused under `GPLAY_READONLY`.

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

# After an upload: see what Play generated, then archive one artifact
gplay releases generated list --version-code 42
gplay releases generated download <downloadId> --version-code 42 --dest ./universal.apk

# Symbolicate a version already live — attach its mapping after the fact
gplay releases mappings upload ./mapping.txt --version-code 42

# Hand a QA reviewer a private install link (no track, no release)
gplay releases sharing upload ./app.aab
```
