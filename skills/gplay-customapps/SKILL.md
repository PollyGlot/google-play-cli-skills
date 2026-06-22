---
name: gplay-customapps
description: Create a managed Google Play private app with gplay — `customapps create` uploads an AAB/APK on the developer-account axis via the one Play Developer API path that creates an app record (public apps are Console-only). Creation is irreversible (the API has no delete and no read), so it is gated behind `--confirm` and requires the account enrolled in managed Google Play with the account-level `CAN_CREATE_MANAGED_PLAY_APPS` capability. Use when creating a private, organisation-scoped enterprise app for managed Google Play distribution.
---

# gplay customapps (managed Google Play private apps)

One experimental command: **`customapps create`** — create a **Custom app**, a
private Android app distributed to one organisation through **managed Google
Play**. This is the *only* Play Developer API path that creates an app *record*
(public apps can only be created in the Play Console). Shared conventions
(auth, output, exit codes, `--dry-run`/`--confirm`) are in `gplay-cli-usage`.

## Create a custom app

```bash
# Rehearse first — validates inputs + artifact, no HTTP, reports the gate:
gplay customapps create ./app-release.aab \
  --title "Acme Internal" --default-language en-US --dry-run

# Live (irreversible) — requires --confirm:
gplay customapps create ./app-release.aab \
  --title "Acme Internal" --default-language en-US --confirm

# Restrict to specific organizations (repeatable; omit to default to the
# organization linked to the developer account):
gplay customapps create ./app-release.aab \
  --title "Acme Internal" --default-language en-US \
  --organization 04f4m6gc --organization 7e9k2p1 --confirm
```

`--title` and `--default-language` (BCP 47, e.g. `en-US`) are required; the
artifact path is a positional AAB or APK. `--output json` mirrors the created
`CustomApp` verbatim, including the **output-only `packageName`** Google
assigns — capture it, since there is no read endpoint to look it up later.

## Irreversible — the named safety gate

The API exposes **no delete** (and **no read** — no `get`, no `list`), so a
created custom app permanently occupies the account. `create` is therefore the
**destructive/irreversible tier**: it requires the named **`--confirm`** flag.

- Missing `--confirm` on the live path → **exit 3**, naming the flag. `CI=true`
  never auto-confirms — gplay never auto-confirms (the flag is the only way).
- `--dry-run` rehearses with zero HTTP and, with `--output json`, emits a
  **`requires`** array (`["confirm"]`) so an agent learns the gate before
  hitting it. Read `requires`, add `--confirm`, re-run.
- `GPLAY_READONLY` refuses the live write (exit 4); `--dry-run` is exempt.

## Capability + enrollment

The Developer account must be **enrolled in managed Google Play**, and the
service account must hold the account-level **`CAN_CREATE_MANAGED_PLAY_APPS`**
capability (never bundled into a role). If either is missing, the API returns
403 and gplay surfaces an agent-resolvable refusal naming **both** — enroll in
managed Google Play and grant the capability in the Play Console
(Users & permissions), then retry.

## Developer account addressing

Custom apps live on the **developer-account axis** (`accounts/{account}`), not a
package — the app does not yet exist to be keyed by a package name. The account
id resolves through the gplay cascade (later wins): the active Account's
developer-id → `.gplay/config.local.json` → `GPLAY_DEVELOPER_ID` →
`--developer-id <id>`. An unresolved id fails with **exit 10**. This is the same
addressing `gplay team` uses (ADR-0015).

Confirm the interface with `gplay customapps create --help` — the command is
`[experimental]`; its surface may still evolve.
