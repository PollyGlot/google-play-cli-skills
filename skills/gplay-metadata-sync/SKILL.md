---
name: gplay-metadata-sync
description: Sync a Google Play store listing, per-locale text and images, between an on-disk tree and Play with `gplay metadata`. Use when editing store listings or screenshots, migrating listing text into version control, localizing a listing, or gating a listing change in CI before it goes live.
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
  reads inside a **read-only Edit** (nothing committed) and is **additive**, a
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
  if its directory holds at least one recognized field file, a folder with
  only a README is **not** managed, and under `--prune` would be deleted
  online.
- **`metadata list`** summarizes what is live on Play, per locale.

## Apply safely

```bash
gplay metadata pull --dir ./metadata
# …edit the .txt files…
gplay metadata validate --dir ./metadata          # offline lint, exit 20 on error
gplay metadata apply --dir ./metadata --dry-run    # ONLINE diff, prints per-locale delta
gplay metadata apply --dir ./metadata --confirm    # publishes, live immediately
```

`metadata apply --dry-run` reads live Play and prints the delta **without
committing**, `--output json` is the diff schema `{package, changes[],
summary}`, so a CI gate is one line: `jq -e '.summary.create + .summary.update
> 0'`. A real `apply` **requires `--confirm`** (every committed Listing is live
on the store immediately); without it apply refuses and points you at the
flag. `CI=true` does not auto-confirm. The publish is **atomic**: all
locales patch inside one Edit committed once, and any per-locale failure
discards the Edit (nothing published).

### The tree stays inside the repo

Every file gplay reads or writes under `--dir` must resolve **inside the
repo** once symlinks are followed: a `title.txt` symlinked to a file outside
the tree, or a pre-placed link where `pull` will write, is refused rather than
followed. Locale names are checked in BCP 47 (`en-US`, not `en_US`) before an
Edit opens, with every offending file named at once. Monorepos that share
translations or assets through symlinks can set
`GPLAY_ALLOW_EXTERNAL_SYMLINKS=1` (same shape as `GPLAY_READONLY`): symlink
egress is then followed, one `NOTE` per outbound path on stderr, while a `..`
escape and any path derived from API data (a locale Play returns, a package
name) stay contained regardless.

## Images

```bash
gplay metadata images list --package com.example.app
gplay metadata images list --type icon                    # one image type, all locales
gplay metadata images pull --dir ./metadata
gplay metadata images validate --dir ./metadata           # offline lint, exit 20 on error
gplay metadata images apply --dir ./metadata --dry-run    # ONLINE per-slot delta
gplay metadata images apply --dir ./metadata --confirm    # publishes, live immediately
```

`metadata images` mirrors the same `list/pull/validate/apply` verbs for
per-locale image **slots** (ADR-0013), with the same discipline, validate
offline, `--dry-run`, then `apply --confirm` (atomic: all slots reconcile in
one Edit; any per-slot failure discards it, nothing published).

- **Slots.** The 9 image types are `icon`, `featureGraphic`, `tvBanner`,
  `promoGraphic`, `phoneScreenshots`, `sevenInchScreenshots`,
  `tenInchScreenshots`, `tvScreenshots`, `wearScreenshots`. `images list`
  walks all 9 across every locale that has a Listing; `--type`
  (`[experimental]`) narrows to one type (an unknown value is refused
  client-side, exit `20`).
- **`validate` limits** (versioned in-code table; Play's commit stays the
  authority): exact dimensions (icon 512×512, feature graphic 1024×500, TV
  banner 1280×720); screenshot sides 320–3840 px with 2:1 aspect ratio;
  PNG/JPEG only (read from the bytes); ≤8 images per slot.
  `apply --no-validate` bypasses this pre-check.
- **Additive, like the text side.** `apply` uploads on-disk images and
  reorders a gallery whose order changed; an online-only image in a managed
  slot is left intact unless `--prune` (destructive, also `--confirm`-gated).
  A slot absent or empty on disk is unmanaged and never touched.
- **Scoped applies.** `--locale` and `--type` (both repeatable) restrict the
  reconciliation to a subset of slots.
- **CI gate.** `apply --dry-run --output json` is the diff schema
  `{package, slots[], summary}`, one line:
  `jq -e '.summary.upload + .summary.delete + .summary.reorder > 0'`.
