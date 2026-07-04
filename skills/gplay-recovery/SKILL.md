---
name: gplay-recovery
description: Drive Google Play app recovery actions with gplay `recovery` — the incident-response remediation that force-updates users stuck on a bad release back to a safe version via a remote in-app update. `create` stages a harmless draft; `deploy` activates it (production-impacting); `cancel` stops it (irreversible); `add-targeting` widens the audience (append-only); `list` shows a versionCode's recoveries. Keyed by package + versionCode, outside the Edit model. Use when a shipped build is broken and you need to push affected users off it, or to inspect/steer an existing recovery.
---

# gplay recovery (incident response for a bad release)

`gplay recovery` manages **app recovery actions** — Google's targeted
incident-response remediation. When a shipped `versionCode` turns out to be bad,
a recovery **force-updates the impacted users** to a safe version via a remote
in-app update. Shared conventions (auth, output, exit codes,
`--dry-run`/`--confirm`, `--package` pinning) are in `gplay-cli-usage`. The whole
namespace is `[experimental]`.

Two structural facts to hold onto:

- **Keyed by package + `versionCode`**, and it lives **outside the Edit model**
  (no `editId`) — a recovery has its own `appRecoveryId` and a **draft → active
  → canceled** lifecycle.
- **`--version-code` is the bad version** — the one users are stuck on that you
  want them off.

## The lifecycle, in order

```bash
# 1. Stage a DRAFT (harmless — nothing is pushed yet, so no --confirm):
gplay recovery create --version-code 431 --all-users
gplay recovery create --version-code 431 --regions US,FR      # or scope it
gplay recovery create --version-code 431 --sdk-levels 30,31

# 2. Inspect the recoveries on that versionCode (find the appRecoveryId):
gplay recovery list --version-code 431

# 3. Activate — this force-updates impacted users. Production-impacting:
gplay recovery deploy <appRecoveryId> --confirm

# 4a. Widen the audience later (append-only — see below):
gplay recovery add-targeting <appRecoveryId> --regions DE,ES --confirm

# 4b. …or stop it (irreversible):
gplay recovery cancel <appRecoveryId> --confirm
```

## `create` — a harmless draft

`create` stages a draft; **nothing reaches a user** until `deploy`. Because a
draft is harmless it needs **no `--confirm`** (use `--dry-run` to validate
inputs with no HTTP call). It requires `--version-code` **and at least one
audience selector**: `--all-users`, `--regions <CC,CC>` (CLDR codes), or
`--sdk-levels <N,N>`. The recovery type defaults to a remote in-app update
(`--remote-in-app-update`, the only type Play models today).

## `deploy` / `cancel` — the gated writes

- **`deploy <id>`** activates the draft — the production-impacting step that
  force-pushes users off the bad build. Requires **`--confirm`** (missing → exit
  `3`); rehearse with `--dry-run`.
- **`cancel <id>`** stops the action: it persists with status `CANCELED` and
  **cannot be resumed** — this is irreversible. Requires **`--confirm`**. To
  target users again after a cancel you must **create a new recovery**.
- `GPLAY_READONLY` refuses both (exit `4`).

## `add-targeting` is append-only — it can only widen

The audience of a recovery can be **widened but never narrowed**.
`add-targeting <id>` adds users/regions/SDK levels (`--all-users`, `--regions`,
`--sdk-levels`), requires `--confirm`, and is **append-only** at the API level.
There is no "remove targeting". **To shrink the blast radius, you must `cancel`
the recovery and `create` a fresh one** — plan the initial audience
conservatively for exactly this reason.

## `list`, and the missing `view`

`recovery list --version-code <N>` shows each recovery's id, status, and
creation time (`--version-code` required — recoveries are keyed by version).
There is **no `recovery view`** — the API exposes only `list`, so `list` is how
you read a recovery's state and find its `appRecoveryId`. `--output json`
passes `ListAppRecoveriesResponse` through verbatim.

Confirm the current verbs and flags with `gplay recovery --help` and
`gplay recovery <command> --help` — the surface is `[experimental]` (ADR-0030)
and may still evolve.
