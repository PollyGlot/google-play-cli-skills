---
name: gplay-metadata-sync
description: Sync a Google Play store listing — per-locale title/description/video text and per-locale images (icon, feature graphic, screenshots) — between a local on-disk tree and Play, using gplay's pull → edit → validate → apply model. Covers `metadata list/pull/validate/apply` and `metadata images list/pull/validate/apply`. Use when editing store listings or screenshots, migrating listing text into version control, localizing a listing, or gating a listing change in CI before it goes live.
---

# gplay metadata sync (listings + images)

Manage the store front: per-locale listing **text** and **images**, kept as an
on-disk tree and reconciled with Play. Shared conventions (auth, `--package`,
output, exit codes) are in `gplay-cli-usage`.

## The sync model

gplay treats a local `./metadata` tree (`<locale>/<field>.txt`, plus image
files) as the desired state and reconciles it with Play (ADR-0011). The loop:

```
pull  →  edit on disk  →  validate (offline)  →  apply --dry-run  →  apply --confirm
```

- **`metadata pull`** rapatriates the live Listings into the tree
  (`<locale>/title.txt`, `short_description`, `full_description`, `video`). It
  reads inside a **read-only Edit** (nothing committed) and is **additive** — a
  field empty online writes no file, a local locale absent online is left
  intact. A `metadata apply` immediately after a `pull` is a guaranteed no-op.
- **`metadata validate`** lints the tree **offline** (no auth, no network):
  character limits (title 30, short 80, full 4000), required non-empty fields
  (title + full description), and known Play locale codes. Any violation exits
  `20`. Safe in a pre-commit hook or CI gate. (`--allow-locale xx-YY`
  whitelists a locale Google added after this gplay release.)
- **`metadata apply`** reconciles disk → Play. **Additive by default**: it
  upserts the locales/fields on disk and leaves online-only locales intact
  (reported). `--prune` also deletes online-only locales (it refuses to remove
  the app's `defaultLanguage`). Note a locale counts as "present on disk" only
  if its directory holds at least one recognized field file — a folder with
  only a README is **not** managed, and under `--prune` would be deleted
  online.
- **`metadata list`** summarizes what is live on Play, per locale.

## Apply safely

```bash
gplay metadata pull --dir ./metadata
# …edit the .txt files…
gplay metadata validate --dir ./metadata          # offline lint, exit 20 on error
gplay metadata apply --dir ./metadata --dry-run    # ONLINE diff, prints per-locale delta
gplay metadata apply --dir ./metadata --confirm    # publishes — live immediately
```

`metadata apply --dry-run` reads live Play and prints the delta **without
committing** — `--output json` is the diff schema `{package, changes[],
summary}`, so a CI gate is one line: `jq -e '.summary.create + .summary.update
> 0'`. A real `apply` **requires `--confirm`** (every committed Listing is live
on the store immediately); without it apply refuses and points you at the
flag. `CI=true` does not auto-confirm. The publish is **atomic**: all
locales patch inside one Edit committed once, and any per-locale failure
discards the Edit (nothing published).

## Images

```bash
gplay metadata images list --package com.example.app
gplay metadata images pull --dir ./metadata
gplay metadata images validate --dir ./metadata
gplay metadata images apply --dir ./metadata --dry-run
```

`metadata images` mirrors the same `list/pull/validate/apply` verbs for
per-locale icon, feature graphic, and screenshots, reconciling image **slots**
(ADR-0013). Same discipline: validate offline, `--dry-run` before a real
apply. Confirm flags with `gplay metadata images <command> --help`.
