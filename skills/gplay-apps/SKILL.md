---
name: gplay-apps
description: Manage the apps gplay knows about and their app-level details — register a package in gplay's local registry with `apps add` (which validates access against the Play API), list/view/remove registered apps, pin one to the repo with `apps init`, and read or patch app details (default language, contact email/phone/website) with `apps details view` / `apps details set`. Use when onboarding a new package into gplay, checking which apps are registered, or editing an app's default language or contact info.
---

# gplay apps (registry + app details)

Two jobs: gplay's **local registry** of packages, and an app's **App details**
record. Shared conventions (auth, `--package`, output, exit codes) live in
`gplay-cli-usage`.

## Why a local registry

The Google Play Developer API has **no `apps.list` endpoint** — there is no way
to ask Play "which apps do I own?". gplay works around this by keeping a local
registry of packages you have registered under the active Account. `apps list`
reads that local registry, not Play.

## Registering and managing packages

```bash
gplay apps add com.example.app     # register (validates access via the API)
gplay apps list                    # list packages in the local registry
gplay apps view --package com.example.app   # default language, title, contact email
gplay apps remove com.example.app  # drop from the registry (does not touch Play)
gplay init                         # pin a package to ./.gplay for this repo
```

`apps add` **validates by default** (ADR-0006): it opens and immediately
discards a Play Edit on the package — a cheap probe that catches a typo'd
package name or a missing per-app permission grant *now*, at registration,
instead of weeks later in a CI release. Pass `--no-verify` to skip the API
round-trip and record the package unconditionally (offline or preparatory
registration). `gplay apps init` scaffolds the `.gplay/` pin (same idea as the
top-level `gplay init`).

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
