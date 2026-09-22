---
name: gplay-setup
description: gplay authentication with `gplay auth`. Use when setting up gplay for the first time, switching, rotating or removing a stored service account, or diagnosing an auth failure (exit 10/11) on any gplay command.
---

# gplay setup (auth)

Covers the `auth` namespace. Shared conventions are in `gplay-cli-usage`.

## The credential

gplay authenticates as a **Google Cloud service account** with the
*Android Publisher* role, invited to your Play Console. Supply its JSON key
via `gplay auth login` (a stored Account in the OS keystore, with a file
fallback in CI containers), `GPLAY_SERVICE_ACCOUNT`, or `--service-account`;
precedence in `gplay-cli-usage`.

## First-run flow

```bash
# 1. Register the service account as the active Account. --developer-id records
#    the Play Console developer account id that `gplay team` and `customapps` address.
gplay auth login --service-account ./service_account.json --developer-id <id>

# 2. Confirm what gplay will use, and where the credential lives.
gplay auth status

# 3. Ordered diagnostics; --package adds the "is the SA invited on this app" round-trip.
gplay auth doctor --package com.example.app
```

`auth doctor` is the first move when an authenticated command fails: it stops
at the first failing check, so the report says whether the key is bad (exit
`10`) or valid but not invited on the app (exit `11`, tested only with
`--package`).

## Managing stored accounts

```bash
gplay auth list                     # every registered Account
gplay auth logout <name> --confirm  # remove an Account from the config + keystore
```

Rotate or switch by running `gplay auth login` again (the new Account becomes
active; `--activate=false` only adds it), or target one per command with
`--account <name>`.

## Verify, then hand off

Once `auth doctor` is green, move to `gplay-apps`: `gplay apps add <package>`,
then `gplay init` to pin it.
