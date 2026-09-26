---
name: gplay-appstore
description: Alternative app store operations with gplay `appstore`. Use when operating a third-party Android app store, mirroring Play's catalog or its update-event feed, submitting an app the store hosts to Google's review, or withdrawing it.
---

# gplay appstore (alternative app store operations)

`gplay appstore` acts for the **operator of a third-party Android app store**:
the catalog that store mirrors from Play, and the apps it hosts and must send to
Google for review. Publishing your own app to Google Play is `gplay-release-flow`.

Shared conventions are in `gplay-cli-usage`. Read the current flags from
`gplay appstore <command> --help`: it is long and complete, and this skill
carries the order the commands go in and the traps between them.

## Caller and subject: two packages, one command

| Flag | Role | Falls back to |
|---|---|---|
| `--store-package` | the **caller**, your app store's own package | `$GPLAY_APP_STORE_PACKAGE` (ADR-0043) |
| `--package` | the **subject**, the hosted app acted on | the repo's `.gplay/config.json` pin |

Swapping the two is the standard failure here. The catalog reads take the
**caller** only, and address the Play app as a positional argument: they ignore
the repo pin, so a resolved `.gplay/config.json` still leaves `--store-package`
required.

## Mirror Play's catalog

```bash
gplay appstore catalog view com.example.app --store-package com.mystore.app

gplay appstore catalog events list \
  --since 2026-07-01T00:00:00Z --until 2026-07-08T00:00:00Z
```

`catalog events list` is the **incremental sync** feed, and the reason to script
this surface at all: each event is a `MODIFICATION` (re-fetch that app with
`catalog view`) or a `DELETION` (delist it). Persist each run's `--until` and
feed it back as the next run's `--since`.

## Take a hosted app through review

The four writes are an ordered path: Google refuses everything else for an app
until its record exists.

```bash
# 1. Once per hosted app: the record.
gplay appstore create --package com.example.app --store-package com.mystore.app

# 2. Upload each artifact; the printed id is the point of the call.
gplay appstore apk upload    ./base.apk    --package com.example.app   # → apkId
gplay appstore image upload  ./icon.png    --package com.example.app   # → imageId
gplay appstore policy upload ./privacy.pdf --package com.example.app   # → fileId

# 3. Assemble those ids into one JSON body and submit to review.
gplay appstore submit --file ./hosted-app.json --dry-run     # rehearse, zero HTTP
gplay appstore submit --file ./hosted-app.json --confirm     # irrevocable

# 4. Later, to withdraw the app from the store, or put it back:
gplay appstore publish-status set unpublished --package com.example.app
gplay appstore publish-status set published   --package com.example.app
```

Two traps span the path: upload ids cannot be listed back, so store them the
moment they print; `create` has no delete and a second run is exit 60, so a
script that runs twice guards it.

The `submit` body is one JSON file whose shape `gplay appstore submit --help`
prints. Keep it in version control: the API answers with no fields and offers
no read-back, so the file is the only record of what was submitted and the
base for the next one.
