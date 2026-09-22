---
name: gplay-tracks
description: Release tracks and their testers with `gplay tracks` and `gplay testers`. Use when checking what a track holds, creating a closed-testing track, reading country availability, or setting a closed track's tester groups.
---

# gplay tracks (+ availability + testers)

Shared conventions are in `gplay-cli-usage`; shipping builds onto tracks is
`gplay-release-flow`.

## Inspect tracks

```bash
gplay tracks list --package com.example.app          # every track on the app
gplay tracks view --track production                 # one track's full state
```

## Create a closed track

```bash
gplay tracks create qa-team
```

Creates a closed-testing track; open/internal tracks have no API path (they
always exist). An upload or promote to a missing custom track fails with exit
`30`: create it here first (`gplay-release-flow`, trackhint).

## Country availability (read-only)

```bash
gplay tracks availability view --track production
```

Read-only at the API level (ADR-0012); changing availability is a Play
Console job.

## Testers (closed-track audience)

```bash
gplay testers list --track qa-team
gplay testers set --track qa-team --group qa@googlegroups.com,beta@googlegroups.com
gplay testers set --track qa-team --clear        # close the closed test
```

`testers set` replaces the whole audience (no add/remove) and takes Google
Groups only.

## Typical closed-test setup

```bash
gplay tracks create qa-team
gplay testers set --track qa-team --group qa@googlegroups.com
gplay releases upload ./app.aab --track qa-team        # see gplay-release-flow
```
