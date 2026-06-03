---
name: gplay-team
description: Manage a Google Play Developer account's members and their permissions with gplay — account-wide members (`team users add/list/remove/set`), per-app access grants (`team grants list/remove/set`), and the offline permission catalog (`team permissions`). Permissions are expressed as friendly role bundles or aliases, with a named safety gate for conferring admin. Use when inviting or off-boarding a member, granting or adjusting per-app access, or looking up which permission alias or role bundle to use.
---

# gplay team (users + grants + permissions)

Two write surfaces and one offline reference: **account-wide** membership
(`team users`), **per-app** access (`team grants`), and the **permission
vocabulary** (`team permissions`). Shared conventions (auth, output, exit
codes) are in `gplay-cli-usage`.

## Permission vocabulary (start here)

```bash
gplay team permissions                 # account-scope aliases + role bundles
gplay team permissions --scope app     # the per-app enum family
gplay team permissions --output json   # marks the admin-conferring alias/bundle
```

`team permissions` is **offline** (no API call, no credential) and is the
single source of truth the write commands resolve `--role` / `--permissions`
through (ADR-0016). It lists the curated **aliases** and the frozen **role
bundles**: `viewer`, `reviewer`, `tester-manager`, `release-manager`, `admin`.
Writes express permissions in friendly form — **`--role <bundle>` XOR
`--permissions <alias,…>`** — and any raw `CAN_*` enum is also accepted.
`--scope account` resolves the account-wide `_GLOBAL` family (for `team
users`); `--scope app` resolves the bare per-app family (for `team grants`).

## Account-wide members

```bash
gplay team users list
gplay team users add alice@example.com --role release-manager
gplay team users set bob@example.com --permissions CAN_REPLY_TO_REVIEWS_GLOBAL
gplay team users remove carol@example.com
```

`add` invites a member (`users.create`); `set` **declaratively replaces** a
member's account-wide permissions; `remove` off-boards them. These are the
routine tier — CI-scriptable, no confirmation gate — **except** conferring
admin: `--role admin` (or a permission set including the all-permissions enum)
requires the named **`--grant-admin`** flag. Handing out full control is never
silent (ADR-0017).

> There is intentionally **no `team users view`** — the Play API has no
> `users.get`, only `users.list`. Use `team users list` (a client-side
> `team users view <email>` is a separate, still-parked proposal).

## Per-app access grants

```bash
gplay team grants list
gplay team grants set alice@example.com --package com.example.app --role reviewer
gplay team grants remove alice@example.com --package com.example.app
```

`grants set` is an **upsert** scoped to one app: gplay reads the member's
current grants, then creates the grant if absent or updates it if present.
`grants remove` removes access to one app while **keeping** the membership.
(Post-ADR-0019 the delete verb is `remove`, **not** `revoke`.) Admin-conferring
grants likewise require `--grant-admin` (exit `3` if missing).

## Agent-resolvable safety gates

The write commands are designed so an agent can discover a gate **before**
hitting it: `--dry-run` rehearses with no write, and with `--output json` it
emits a **`requires`** array naming the safety flags the live write needs (and,
for grants, the resolved create/update verb plus the permission diff). Read
`requires`, add the named flags, re-run.

## Developer account addressing

Commands act on the active Account's developer id by default; override it with
`--developer-id <id>` (it beats env and the project-local pin) per ADR-0015.
Confirm flags with `gplay team <group> <command> --help`.
