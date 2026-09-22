---
name: gplay-metadata-sync
description: Store listing text and images as an on-disk tree synced with Play via `gplay metadata`. Use when editing a store listing or its screenshots, adding a locale, pulling the listing into version control, or gating a listing change in CI.
---

# gplay metadata sync (listings + images)

Manage the store front: per-locale listing **text** and **images**, kept as an
on-disk tree and reconciled with Play. Shared conventions are in
`gplay-cli-usage`.

## The sync model

gplay treats a local `./metadata` tree as the desired state and reconciles it
with Play (ADR-0011). The loop:

```
pull  →  edit on disk  →  validate (offline)  →  apply --dry-run  →  apply --confirm
```

On disk, text is `<locale>/<field>.txt` (`title`, `short_description`,
`full_description`, `video`). Images sit under `<locale>/images/`: a singular
slot (`icon`, `featureGraphic`, `tvBanner`, `promoGraphic`) is
`<type>.<ext>`; a gallery slot (the `*Screenshots` types) is
`<type>/1.<ext>…N.<ext>` in display order.

- **`metadata pull`** copies the live Listings into the tree; additive, so
  `pull` then `apply` is a no-op.
- **`metadata validate`** lints the tree offline (no auth, no network); any
  violation exits `20`, so it fits a pre-commit hook or CI gate.
- **`metadata apply`** reconciles disk → Play, additive by default; `--prune`
  is the destructive opt-in (read `apply --help` before using it).
- **`metadata list`** summarizes what is live on Play, per locale.

## Apply safely

```bash
gplay metadata pull --dir ./metadata
# …edit the .txt files…
gplay metadata validate --dir ./metadata          # offline lint, exit 20 on error
gplay metadata apply --dir ./metadata --dry-run    # ONLINE diff, prints per-locale delta
gplay metadata apply --dir ./metadata --confirm    # publishes, live immediately
```

`apply --dry-run` is online and prints the delta; `--output json` is the diff
schema `{package, changes[], summary}`, so a CI gate is
`jq -e '.summary.create + .summary.update > 0'`. The real `apply` is
`--confirm`-gated and atomic: one Edit, any locale failure publishes nothing.

### The tree stays inside the repo

Every file gplay reads or writes under `--dir` must resolve inside the repo
once symlinks are followed: a `title.txt` symlinked to a file outside the
tree, or a pre-placed link where `pull` will write, is refused. Locale names
are checked in BCP 47 (`en-US`, not `en_US`) before an Edit opens. Monorepos
that share translations or assets through symlinks can set
`GPLAY_ALLOW_EXTERNAL_SYMLINKS=1`: symlink egress is then followed, one `NOTE`
per outbound path on stderr, while a `..` escape and any path derived from API
data (a locale Play returns, a package name) stay contained regardless.

## Images

```bash
gplay metadata images list --package com.example.app
gplay metadata images list --type icon                    # one image type, all locales
gplay metadata images pull --dir ./metadata
gplay metadata images validate --dir ./metadata           # offline lint, exit 20 on error
gplay metadata images apply --dir ./metadata --dry-run    # ONLINE per-slot delta
gplay metadata images apply --dir ./metadata --confirm    # publishes, live immediately
```

`metadata images` follows the same loop for per-locale image slots (ADR-0013):

- `images list` walks the 9 slot types across every locale; `--type` narrows
  to one.
- `images validate` is the same offline lint, exit `20`.
- `images apply` is additive like the text side; `--prune` deletes online-only
  images (destructive, `--confirm`); `--locale`/`--type` scope the run.
- The CI gate is `jq -e '.summary.upload + .summary.delete + .summary.reorder
  > 0'` over `apply --dry-run --output json` (`{package, slots[], summary}`).
