---
name: gplay-apps
description: Manage gplay's local app registry and app-level details. Use when onboarding packages into gplay, discovering which apps a credential can reach (`apps accessible list`), listing or removing registered apps, pinning a package to the repo, or reading/patching app details (default language, contact info).
---

# gplay apps (registry + app details)

Two jobs: gplay's **local registry** of packages, and an app's **App details**
record. Shared conventions (auth, `--package`, output, exit codes) live in
`gplay-cli-usage`.

## Local registry vs. server-side discovery

Two different questions, two commands:

- **"What have I chosen to work on?"** → `apps list` reads gplay's **local
  registry**: the packages you have `apps add`-ed under the active Account. The
  classic Android Publisher API has no `apps.list` endpoint, so this working set
  is gplay's own record, not a Play read.
- **"What can this credential actually reach?"** → `apps accessible list` is a
  **server-authoritative** inventory, straight from Google via the Play
  Developer Reporting `apps.search` method (least-privilege reporting scope, no
  local-registry fallback).

The two sets do **not** necessarily coincide (ADR-0039): a credential may be
able to `apps add` a package it cannot see here, or see org apps it does not
drive. Use `apps accessible list` to **bootstrap** — discover package names,
then `apps add` the ones you want to work on.

Pagination is one page per call: `--page-size` / `--page-token`, and
`--output json` passes the `SearchAccessibleAppsResponse` through verbatim
(`nextPageToken` included, ADR-0003); table/markdown output notes the next
`--page-token` on stderr when more apps are available.

## Registering and managing packages

```bash
gplay apps accessible list             # server-side: apps this credential can reach
gplay apps add com.example.app         # register one (validates access via the API)
gplay apps add com.a com.b com.c       # register several — independent, partial success
gplay apps list                        # list packages in the local registry
gplay apps view --package com.example.app   # default language, title, contact email, icon
gplay apps remove com.example.app      # drop from the registry (does not touch Play)
gplay init                             # pin a package to ./.gplay for this repo
```

`apps add` takes **one or more** packages and **validates by default**
(ADR-0006): for each it opens and immediately discards a Play Edit — a cheap
probe that catches a typo'd package name or a missing per-app permission grant
*now*, at registration, instead of weeks later in a CI release. Multiple
packages are **independent units of work**: a failure on one does not stop or
roll back the others (partial success), each gets a ✓/✗ line on stderr, and the
exit code reflects the most serious failure (a batch carrying any non-retryable
failure exits non-retryable, so an automated caller won't blindly retry it).
Duplicate arguments are collapsed. Pass `--no-verify` to skip the API
round-trip and record every package unconditionally (offline or preparatory
registration). `gplay apps init` scaffolds the `.gplay/` pin (same idea as the
top-level `gplay init`).

`apps view` also reports the **store icon** when the default language has one
(`[experimental]`): the icon's content **sha256** in table/markdown, and an
`"icon"` key `{"url":..,"sha256":..}` in the JSON envelope (omitted when the
slot is empty). The sha256 is the durable content-identity handle; the `url`
is an **ephemeral preview link — never persist it** (fetch the bytes with
`gplay metadata images pull`). Each run is a live read; nothing is cached.

## App details (read + write)

App details is the app-global record holding `defaultLanguage` and the
user-visible `contactEmail`, `contactPhone`, and `contactWebsite` — writable
via the API (ADR-0012):

```bash
gplay apps details view --package com.example.app
gplay apps details set --contact-email support@example.com
gplay apps details set --default-language en-US --contact-phone ""
```

`apps details set` is a **partial patch at flag granularity**: a field you
pass is written, a field you omit is left intact, and an explicit empty value
**clears** a field (e.g. `--contact-phone ""` removes the number). A bare
`set` with no field flag is refused (exit `2`) so a forgotten flag can never
emit an empty patch. There is no `--confirm` (contact info is low-stakes and
reversible); use `--dry-run` to preview the patch with no HTTP call. Confirm
the field flags with `gplay apps details set --help`.

> The bare `gplay apps details` command prints help — it groups `view` + `set`,
> it is not itself a read (post-ADR-0019: no verb-less reads).

## Next steps

With an app registered and pinned, move on to `gplay-release-flow` (ship a
build), `gplay-tracks` (tracks + testers), or `gplay-metadata-sync` (store
listing). Auth not set up yet? Start with `gplay-setup`.
