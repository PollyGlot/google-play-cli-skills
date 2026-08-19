---
name: gplay-appstore
description: Alternative app store operations with gplay `appstore`. Use when operating a third-party Android app store — mirroring Play's catalog export or its update-event feed, or taking an app the store hosts through Google's review path (create, upload, update, publish-status).
---

# gplay appstore (alternative app store operations)

`gplay appstore` acts for the **operator of a third-party Android app store**:
the catalog that store mirrors from Play, and the apps it hosts and must send to
Google for review. Publishing your own app to Google Play is `gplay-release-flow`.

Shared conventions (auth, output, exit codes, `--dry-run`/`--confirm`, the
`[experimental]` contract) are in `gplay-cli-usage`. Read the current flags from
`gplay appstore <command> --help` — it is long and complete; this skill carries
the order the commands go in and the traps between them.

## Caller and subject — two packages, one command

| Flag | Role | Falls back to |
|---|---|---|
| `--store-package` | the **caller**, your app store's own package | `$GPLAY_APP_STORE_PACKAGE` (ADR-0043) |
| `--package` | the **subject**, the hosted app acted on | the repo's `.gplay/config.json` pin |

Swapping the two is the standard failure here. The catalog reads take the
**caller** only, and address the Play app as a positional argument: they ignore
the repo pin, so a resolved `.gplay/config.json` still leaves `--store-package`
required. A missing caller is a usage error (**exit 2**) before any HTTP call.

A 403 (**exit 11**) on any of these commands means the caller is not enrolled
for alternative distribution; the message names the enrollment.

## Mirror Play's catalog

```bash
gplay appstore catalog view com.example.app --store-package com.mystore.app

gplay appstore catalog events list \
  --start-time 2026-07-01T00:00:00Z --end-time 2026-07-08T00:00:00Z
```

`catalog events list` is the **incremental sync** feed, and the reason to script
this surface at all: each event is a `MODIFICATION` (re-fetch that app with
`catalog view`) or a `DELETION` (delist it). Persist each run's `--end-time` and
feed it back as the next run's `--start-time`; both bounds are required, the
range is `[start, end)`, and an end at or before the start is **exit 2**.

Pagination is one page per invocation, and the page token is only valid against
**identical** parameters: carry `--start-time`, `--end-time` and `--page-size`
unchanged into every follow-up call with `--page-token`. In table output the
next token arrives on stderr, in `--output json` as `nextPageToken`.

An app not eligible for catalog inclusion fails with **exit 30**.

## Take a hosted app through review

The four writes are an ordered path: Google refuses everything else for an app
until its record exists.

```bash
# 1. Once per hosted app — the record.
gplay appstore create --package com.example.app --store-package com.mystore.app

# 2. Upload each artifact; the printed id is the point of the call.
gplay appstore upload apk    ./base.apk    --package com.example.app   # → apkId
gplay appstore upload image  ./icon.png    --package com.example.app   # → imageId
gplay appstore upload policy ./privacy.pdf --package com.example.app   # → fileId

# 3. Assemble those ids into one JSON body and submit to review.
gplay appstore update --file ./hosted-app.json --dry-run     # rehearse, zero HTTP
gplay appstore update --file ./hosted-app.json --confirm     # irrevocable

# 4. Later, to withdraw the app from the store — or put it back:
gplay appstore publish-status unpublished --package com.example.app
gplay appstore publish-status published   --package com.example.app
```

**`create` is permanent.** The API exposes no delete, so the record outlives any
mistake; only its publish status can still change. A second `create` is a
conflict (**exit 60**) — safe to retry after a transport failure, worth guarding
in a script that runs more than once.

**Uploads are inert.** An APK, image or document sits unused until an `update`
cites its id, which is why no upload needs `--confirm`. Store the ids the moment
they print: re-uploading gigabytes for a metadata change buys nothing, and there
is no endpoint to list them back.

**`update` is the one-way door.** It submits to Google review immediately, with
no staging step and no recall, so `--confirm` is mandatory (**exit 3** without
it) and `CI=true` never auto-confirms. Rehearse with `--dry-run`, which
validates the file and resolves the target with zero HTTP calls. The request
body shape and its resolution rules are in
[`update-body.md`](update-body.md) — read it before writing the file.

**`publish-status` is reversible in both directions**, so it carries no
`--confirm`. Google treats an app as published once `update` succeeds; this
command exists to take one back out of the store, and later to restore it.
