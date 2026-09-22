---
name: gplay-recovery
description: App recovery actions with gplay `recovery`, the incident-response path that force-updates users stuck on a bad release to a safe version. Use when a shipped build is broken and affected users must be pushed off it, or when inspecting, deploying, widening or cancelling an existing recovery.
---

# gplay recovery (incident response for a bad release)

`gplay recovery` force-updates the users stuck on a bad `versionCode` to a
safe version. Shared conventions are in `gplay-cli-usage`. The whole namespace
is `[experimental]`.

A recovery is keyed by package + `versionCode`, lives outside the Edit model
(no `editId`), and follows a draft → active → canceled lifecycle.

## The lifecycle, in order

```bash
# 1. Stage a DRAFT (harmless, nothing is pushed yet, so no --confirm):
gplay recovery create --version-code 431 --all-users
gplay recovery create --version-code 431 --regions US,FR      # or scope it
gplay recovery create --version-code 431 --sdk-levels 30,31

# 2. Inspect the recoveries on that versionCode (find the appRecoveryId):
gplay recovery list --version-code 431

# 3. Activate; this force-updates impacted users. Production-impacting:
gplay recovery deploy <appRecoveryId> --confirm

# 4a. Widen the audience later (append-only, see below):
gplay recovery add-targeting <appRecoveryId> --regions DE,ES --confirm

# 4b. …or stop it (irreversible):
gplay recovery cancel <appRecoveryId> --confirm
```

## The audience only widens

`add-targeting` is append-only; shrinking means `cancel` then a fresh
`create`. Start with the narrowest audience (`--regions`/`--sdk-levels`) that
covers the incident.

## Reading and stopping

`list` is the only read (there is no `view`): it is how you find an
`appRecoveryId` and its status. `cancel` is terminal: the action persists as
`CANCELED`; to target users again, `create` a new recovery.
