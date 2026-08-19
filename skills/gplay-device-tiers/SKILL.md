---
name: gplay-device-tiers
description: Manage device tier configs with gplay `device-tiers`, immutable device-targeting for tiered content delivery (create/view/list only, no update or delete). Use when defining or inspecting device tiers for tiered asset delivery, or scripting a config into CI.
---

# gplay device-tiers (device-targeting for tiered delivery)

`gplay device-tiers` manages **device tier configs**, the app-scoped
configuration that drives **tiered content delivery**: which devices fall into
which tier, so Play can serve different assets to high-end and low-end devices.
Shared conventions (auth, output, exit codes, `--dry-run`, `--package` pinning)
are in `gplay-cli-usage`. The whole namespace is `[experimental]`.

A config bundles three things (all expressed in the JSON body):

- **device groups**, named sets of device selectors (over RAM, device IDs,
  SoCs, system features),
- an ordered **device tier set**, tiers by descending priority,
- **user country sets**.

## Immutable: create / get / list only

The defining property: a device tier config is **immutable**. The API exposes
**only** `create`, `get`, and `list`: **no update, no patch, no delete**. Two
consequences:

- **`create` needs no `--confirm`.** It can never overwrite or destroy an
  existing config, so it isn't a destructive write. (`GPLAY_READONLY` still
  refuses it, since it is a write, with exit `4`.)
- **To "change" targeting, you create a new config** and point delivery at the
  new `deviceTierConfigId`. Old configs stay around; there is nothing to edit or
  clean up here.

This also puts device tier configs **outside the Edit lifecycle** (like the Data
Safety declaration and app recovery), a direct application-scoped write, no
`editId`.

## Create

```bash
# From a file:
gplay device-tiers create --file config.json

# From stdin (default when --file is omitted or "-"):
cat config.json | gplay device-tiers create

# Rehearse, validate the body, resolve the target, no HTTP:
gplay device-tiers create --file config.json --dry-run
```

- The server **assigns the `deviceTierConfigId`**, do **not** put an id in the
  body.
- `--allow-unknown-devices` sets `allowUnknownDevices=true` (let devices Play
  doesn't recognize into the config).
- Don't know the body shape? `gplay schema DeviceTierConfig` expands its fields
  and enums offline (see `gplay-cli-usage`), or round-trip an existing config
  with `view --output json`.

## Read

```bash
gplay device-tiers list                       # newest first; --page-size / --page-token to page
gplay device-tiers view <deviceTierConfigId>  # one config by its server-assigned id
gplay device-tiers view <id> --output json    # DeviceTierConfig, verbatim
```

`--output json` passes the API response through verbatim (ADR-0003), the
`list` response carries `nextPageToken` for paging (capped at 100 per page).

