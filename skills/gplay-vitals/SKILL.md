---
name: gplay-vitals
description: Read an app's post-launch quality signals with gplay `vitals` — crash rate, ANR rate, slow start/rendering, excessive wakeups, low-memory kills, stuck wakelocks, plus error reports (counts/issues/reports) and Play-detected anomalies. Backed by the Play Developer Reporting service (a distinct Google service from the Android Publisher API, with its own OAuth scope), so it is entirely READ-ONLY — nothing under `vitals` mutates Play state. Use when checking crash/ANR health after a rollout, investigating a spike, pulling vitals into a CI gate, or reading clustered crash issues and stack traces.
---

# gplay vitals (post-launch quality signals)

`gplay vitals` reads **Android vitals** — the post-launch quality signals you
know from the Play Console: crash rate, ANR rate, slow cold start, slow
rendering, excessive wakeups, low-memory kills, stuck background wakelocks, plus
error reports and Play-detected anomalies. Shared conventions (auth, output,
exit codes, `--package` pinning) are in `gplay-cli-usage`.

Two things make this namespace different from the rest of gplay:

- **A distinct Google service.** Vitals is backed by the **Play Developer
  Reporting API** (`playdeveloperreporting`), *not* the Android Publisher API.
  Same service-account file, but a **different OAuth scope**
  (`…/auth/playdeveloperreporting`). If the service account was invited only for
  publishing, vitals calls fail with a 403 (exit `11`) until the reporting scope
  is granted — that is an environment fix, not a flag.
- **Read-only, always.** Every `vitals` command only reads metrics. There is no
  write here, so `GPLAY_READONLY` never blocks it, and no command needs
  `--confirm`.

## Preset rate commands — the fast path

Each vital has an opinionated preset that needs no metric/dimension knowledge —
it reports the set's primary metric over a **default 28-day DAILY window**:

```bash
gplay vitals crashes           # crash rate (on the pinned package)
gplay vitals anr               # ANR rate
gplay vitals slowstart         # slow cold-start rate
gplay vitals slowrendering     # janky-frames rate
gplay vitals excessivewakeup   # excessive wakeup rate
gplay vitals lmk               # low-memory-kill rate
gplay vitals stuckbgwakelock   # stuck background wakelock rate
```

All the presets share the same knobs:

```bash
gplay vitals crashes --by versionCode --version 123   # slice, then filter to one build
gplay vitals crashes --by country                     # or by country / device
gplay vitals anr --since 7d --period DAILY             # window: 28d default; HOURLY opt-in
```

- `--by country|device|versionCode` slices the timeline (availability depends on
  the metric set); `--version` filters to a single versionCode.
- `--since 28d` / `--period DAILY|HOURLY|FULL_RANGE` set the window.

## `vitals query` — full control

When a preset's single primary metric isn't enough, `vitals query <metric-set>`
wraps the metric set directly and lets you pick metrics and dimensions:

```bash
gplay vitals query crashrate --metrics crashRate,distinctUsers --dimensions versionCode
gplay vitals query anrrate --period HOURLY --since 24h
```

`--metrics` and `--dimensions` are **validated offline** against the API schema
embedded in the binary — an unknown name is rejected with the valid set listed
(gplay never invents a metric or dimension). With no `--metrics`, the set's
primary metric is used. The metric-set ids are `crashrate`, `anrrate`,
`slowstartrate`, `slowrenderingrate`, `excessivewakeuprate`, `lmkrate`,
`stuckbackgroundwakelockrate` — the same ones the presets wrap.

## `vitals errors` — reports, issues, counts

Error reporting is a sub-tree, not a single metric:

```bash
gplay vitals errors counts      # error report counts over a window (errorCount metric set)
gplay vitals errors issues      # clustered issues — crashes/ANRs grouped by cause
gplay vitals errors reports     # individual error reports (the stack traces)
```

**Deobfuscation gotcha:** for an obfuscated (R8/ProGuard) app, error reports and
issues are unreadable stack traces until the matching **mapping** is uploaded.
That upload is an Android Publisher **Edit** artifact keyed by versionCode and
lives under `releases`, **not** here:

```bash
gplay releases upload app.aab --mapping mapping.txt   # or: releases mappings upload
```

Upload the mapping under `releases`; read the symbolicated result under `vitals`.

## `vitals anomalies` — what Play flagged itself

```bash
gplay vitals anomalies --since 90d
gplay vitals anomalies --filter 'activeBetween("2026-01-01T00:00:00Z", UNBOUNDED)'
```

Lists the metric anomalies (unexpected crash/ANR spikes, …) Play detected.
`--since` builds an `activeBetween(...)` window for you; `--filter` passes a raw
AIP-160 predicate and **overrides** `--since` when you need an open-ended range.
`--limit 0` returns all (no cap).

## Freshness — an empty window is not zero

The reporting service reports metrics with a lag. Every rate/query command
prints a **freshness note to stderr** (the latest date carrying data) so an
empty or short window is not mistaken for "zero crashes". When you ask for
`--since 24h` right after a release, expect the window to be empty until the
data lands — read the freshness line, don't conclude the app is clean.

## Output

`--output json` mirrors the reporting API response **verbatim** (ADR-0003) — a
CI gate is usually one `jq` line over the timeline. `table`/`markdown` render
the timeline (dates × metrics, sliced by your dimension). Remember stdout is
data; the freshness note and warnings go to stderr and never pollute the JSON.

`vitals` is `playdeveloperreporting`, not "androidvitals" (no such host).
Confirm the current verbs and flags with `gplay vitals --help` and
`gplay vitals <command> --help`.
