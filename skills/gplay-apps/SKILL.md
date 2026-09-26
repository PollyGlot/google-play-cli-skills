---
name: gplay-apps
description: Registry, app details and drift audit with `gplay apps`. Use when registering or pinning packages, discovering which apps a credential can reach, reading or patching app details (default language, contact info), or sweeping the account for drift (lingering drafts, empty release notes, locale drift, no production release).
---

# gplay apps (registry + app details)

Two jobs: gplay's **local registry** of packages, and an app's **App details**
record. Shared conventions are in `gplay-cli-usage`.

## Local registry vs. server-side discovery

Two different questions, two commands:

- `apps list`: gplay's local registry, the packages you `apps add`-ed (the
  Publisher API has no list endpoint).
- `apps accessible list`: what the credential can reach, server-side. The two
  sets need not coincide: bootstrap from the second, then `apps add` what you
  drive.

## Registering and managing packages

```bash
gplay apps accessible list             # server-side: apps this credential can reach
gplay apps add com.example.app         # register one (validates access via the API)
gplay apps add com.a com.b com.c       # register several: independent, partial success
gplay apps list                        # list packages in the local registry
gplay apps view --package com.example.app   # default language, title, contact email, icon
gplay apps remove com.example.app      # drop from the registry (does not touch Play)
gplay init --package com.example.app   # pin a package to ./.gplay for this repo
```

## App details (read + write)

```bash
gplay apps details view --package com.example.app
gplay apps details set --contact-email support@example.com
gplay apps details set --default-language en-US --contact-phone ""   # "" clears the field
```

## `apps audit`: a read-only consistency sweep

`apps audit` (`[experimental]`) sweeps apps for drift and reports it.

```bash
gplay apps audit                                   # every app the credential can see
gplay apps audit com.example.a com.example.b       # only these (skips discovery)
gplay apps audit --check lingering-drafts --check empty-release-notes
gplay apps audit --skip-check locale-drift --output json
```

Exit `70` means findings (a gate, not a failure); read the report's `ran` key
before trusting an empty `findings`.
