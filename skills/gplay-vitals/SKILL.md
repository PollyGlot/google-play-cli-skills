---
name: gplay-vitals
description: "Android vitals with gplay `vitals`: crash/ANR and other rates, error reports, Play-detected anomalies (read-only). Use when checking crash or ANR health after a rollout, investigating a spike, gating CI on vitals, or reading clustered crash issues and stack traces."
---

# gplay vitals (post-launch quality signals)

`gplay vitals` reads Android vitals: the rate presets below, error reports, and
Play-detected anomalies. Shared conventions are in `gplay-cli-usage`.

Two things set this namespace apart:

- **A distinct Google service.** Vitals is backed by the Play Developer
  Reporting API, with its own OAuth scope. A service account invited only for
  publishing gets a 403 (exit `11`) on every vitals call until the reporting
  scope is granted: an environment fix, not a flag.
- **Read-only throughout:** no `--confirm`, and `GPLAY_READONLY` never blocks
  it.

## Preset rate commands: the fast path

One preset per vital, 28-day DAILY window by default:

```bash
gplay vitals crashes           # crash rate (on the pinned package)
gplay vitals anr               # ANR rate
gplay vitals slowstart         # slow cold-start rate
gplay vitals slowrendering     # janky-frames rate
gplay vitals excessivewakeup   # excessive wakeup rate
gplay vitals lmk               # low-memory-kill rate
gplay vitals stuckbgwakelock   # stuck background wakelock rate
```

All presets share the same knobs:

```bash
gplay vitals crashes --by versionCode --version 123   # slice, then filter to one build
gplay vitals anr --since 7d --period HOURLY           # window: 28d default; HOURLY opt-in
```

## `vitals query`: full control

When you need more than a preset's primary metric, `vitals query <metric-set>`
wraps the metric set directly:

```bash
gplay vitals query crashrate --metrics crashRate,distinctUsers --dimensions versionCode
gplay vitals query anrrate --period HOURLY --since 24h
gplay vitals query bitmapmemoryusage --since 28d --dimensions versionCode
```

`--metrics`/`--dimensions`/`--period` are validated offline against the
embedded schema (an unknown name lists the valid set). Two memory sets have no
preset and are `query`-only, DAILY only: `anonrssandswapmemoryusage` and
`bitmapmemoryusage`.

## `vitals errors`: reports, issues, counts

```bash
gplay vitals errors counts      # error report counts over a window
gplay vitals errors issues      # clustered issues, crashes/ANRs grouped by cause
gplay vitals errors reports     # individual error reports (the stack traces)
```

Obfuscated (R8/ProGuard) stacks stay unreadable until the versionCode's mapping
is uploaded under `releases` (`--mapping` on `releases upload`, or `releases
mappings upload`): see `gplay-release-flow`.

## `vitals anomalies`: what Play flagged itself

```bash
gplay vitals anomalies --since 90d
gplay vitals anomalies --filter 'activeBetween("2026-01-01T00:00:00Z", UNBOUNDED)'
```

`--filter` (raw AIP-160) overrides `--since` for an open-ended range;
`--limit 0` returns all.

## Freshness: an empty window means unknown

Metrics land with a lag: every rate/query command prints a freshness note to
stderr (the latest date carrying data). A short window right after a release
stays empty until data lands; the freshness line is the bound, and an empty
window means unknown, not zero. `--describe` on a preset or `query` returns
the set's latest available end time instead of a timeline: ask it before
choosing a window.

## CI gate

One `jq` line over `--output json` (the API timeline verbatim).
