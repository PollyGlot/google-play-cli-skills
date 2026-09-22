---
name: gplay-device-tiers
description: Device tier configs with gplay `device-tiers`, immutable device-targeting for tiered asset delivery. Use when creating or inspecting a device tier config, scripting one into CI, or asked to update or delete one.
---

# gplay device-tiers (device-targeting for tiered delivery)

`gplay device-tiers` manages **device tier configs**, the app-scoped
configuration that drives **tiered content delivery**: which devices fall into
which tier, so Play can serve different assets to high-end and low-end devices.
Shared conventions are in `gplay-cli-usage`. The whole namespace is
`[experimental]`.

## Immutable

A config is **immutable**: to change targeting, create a new one and point
delivery at the new `deviceTierConfigId`; old configs stay. That is why
`create` needs no `--confirm`. Outside the Edit lifecycle (no `editId`):
`gplay edits begin` does not batch it.

## Create

```bash
gplay device-tiers create --file config.json              # from a file
cat config.json | gplay device-tiers create               # from stdin (default when --file is omitted or "-")
gplay device-tiers create --file config.json --dry-run    # rehearse: validate the body, resolve the target, no HTTP
```

Body shape: `gplay schema DeviceTierConfig` expands its fields and enums
offline (see `gplay-cli-usage`), or round-trip an existing config with
`view --output json`.

## Read

```bash
gplay device-tiers list                       # newest first; --page-size / --page-token to page
gplay device-tiers view <deviceTierConfigId>  # one config by its server-assigned id
gplay device-tiers view <id> --output json    # DeviceTierConfig, verbatim
```
