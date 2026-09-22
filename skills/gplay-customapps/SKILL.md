---
name: gplay-customapps
description: Create a private enterprise app for managed Google Play with `customapps create`, the only API path that creates an app record (public apps are Console-only). Use when creating a custom app for an organisation.
---

# gplay customapps (managed Google Play private apps)

One `[experimental]` command. Shared conventions are in `gplay-cli-usage`.

## Create a custom app

```bash
# Rehearse first (reports the gate):
gplay customapps create ./app-release.aab \
  --title "Acme Internal" --default-language en-US --dry-run

# Live (irreversible):
gplay customapps create ./app-release.aab \
  --title "Acme Internal" --default-language en-US --confirm

# Restrict to specific organizations (repeatable; default: the account's):
gplay customapps create ./app-release.aab \
  --title "Acme Internal" --default-language en-US \
  --organization 04f4m6gc --organization 7e9k2p1 --confirm
```

Irreversible (the API has no delete and no read): `--confirm` gated,
rehearse with `--dry-run` first. Capture `packageName` from `--output json`:
there is no read endpoint to look it up later.

## Capability + enrollment

A 403 names what is missing: managed Google Play enrollment on the account,
or the account-level `CAN_CREATE_MANAGED_PLAY_APPS` capability on the service
account (granted on its own, outside any role). Both fixes live in the Play
Console (enrollment, then Users & permissions); retry after.

## Developer account addressing

Developer-account axis (`--developer-id`, same as `gplay team`, ADR-0015):
resolution in `gplay-cli-usage`.
