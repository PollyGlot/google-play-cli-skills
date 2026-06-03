---
name: gplay-setup
description: Onboard gplay authentication from zero — point it at a Google Play service-account JSON (via GPLAY_SERVICE_ACCOUNT or --service-account), register it with `auth login`, verify the wiring with `auth status` / `auth doctor`, and manage stored accounts with `auth list` / `auth logout`. Use when setting up gplay auth for the first time, switching or rotating service accounts, or diagnosing why an authenticated gplay command fails with an auth error (exit 10/11).
---

# gplay setup (auth onboarding)

Get gplay talking to the Google Play Developer API. This skill covers the
`auth` namespace end to end; for the conventions every command shares
(credential resolution order, exit codes, output), see `gplay-cli-usage`.

## The credential

gplay authenticates as a **Google Cloud service account** with the
*Android Publisher* role, invited to your Play Console. You supply its JSON
key one of three ways (resolution order in `gplay-cli-usage`):

- `GPLAY_SERVICE_ACCOUNT` — a **path** to the JSON file *or* the **inline
  JSON** itself (handy for CI secrets).
- `--service-account <path-or-json>` on any command — overrides the env.
- A stored **Account** registered with `gplay auth login` (the credential
  lands in the OS keystore — see `gplay auth status` for where).

## First-run flow

```bash
# 1. Register the service account as the active Account.
gplay auth login --service-account ./service_account.json

# 2. Confirm what gplay will use, and where the credential lives.
gplay auth status

# 3. Run ordered diagnostics (credential valid? scopes? developer id?).
gplay auth doctor
```

`auth status` prints the active Account, the keystore backend, and the
credential's location. `auth doctor` runs ordered checks and is the first
thing to reach for when an authenticated command fails — it pinpoints whether
the problem is a bad key (exit `10`) or a service account that is valid but
not invited on the app/account (exit `11`).

## Managing stored accounts

```bash
gplay auth list      # every registered Account
gplay auth logout    # remove an Account from the config + keystore
```

Use `--account <name>` on later commands to target a specific stored Account
when you have more than one. Confirm the exact flags with
`gplay auth <command> --help` — this skill does not freeze them.

## Verify, then hand off

Once `gplay auth doctor` is green, auth is done. The next step is to make
gplay aware of an app to act on:

> **→ Continue with the `gplay-apps` skill** to register a package
> (`gplay apps add <package>`) and pin it to the repo (`gplay init`).

From there, `gplay-release-flow`, `gplay-tracks`, `gplay-reviews`,
`gplay-metadata-sync`, `gplay-compliance`, and `gplay-team` all assume a
working credential set up here.
