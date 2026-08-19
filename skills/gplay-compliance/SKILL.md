---
name: gplay-compliance
description: Push and validate the app's Google Play Data Safety declaration from a versioned CSV, the only Play compliance surface with an API (content rating and the other declarations stay Console-manual). Use when updating the Data Safety form or gating it in CI.
---

# gplay compliance (Data Safety)

Manage the app's **Data Safety** declaration from a canonical CSV. Shared
conventions (auth, `--package`, output, exit codes) are in `gplay-cli-usage`.

## What is and isn't automatable (the hard wall)

Data Safety is the **only** Play compliance surface with a Developer API
endpoint. These neighbouring declarations have **no API** and cannot be driven
by gplay; they remain manual in the Play Console:

- Content rating (IARC questionnaire)
- Target audience & content / Families
- Ads declaration, News-app declaration, Government-app status, COVID-19, etc.

Treat those as a documented manual step in your release runbook; gplay does not
and will not automate them. This skill is strictly about Data Safety.

## Data Safety is write-only

The declaration is **write-only** (ADR-0014): a direct POST **outside** the
Edits model that **replaces the whole document**. gplay cannot read it back;
there is no `get`, only `set` and an offline `validate`. The live POST is the
only thing that validates the contents against Google's schema.

```bash
gplay compliance datasafety validate                       # offline structural check
gplay compliance datasafety set --dry-run                  # rehearse: validate + resolve target + size
gplay compliance datasafety set --confirm                  # the real write, replaces the live declaration
```

- **`validate`** structurally checks the CSV **offline** (no network, no auth).
- **`set`** pushes the canonical CSV (`--file`, default
  `./compliance/data-safety.csv`). It runs `validate` implicitly first, so a
  structurally invalid CSV never reaches the network. `--dry-run` rehearses,
  validates, resolves the target package/Account, and reports "would POST N
  bytes / N rows" with no HTTP call (and no `--confirm` needed).
- The real write **requires `--confirm`** (a stale or wrong declaration can
  block releases or misstate your data practices); without it `set` refuses
  with **exit `3`**, and the `--output json` error envelope names the flag in
  `requires: ["confirm"]`, add it and re-run. `CI=true` does not
  auto-confirm.

`--output json` passes the API response through verbatim.

## CI shape

```bash
gplay compliance datasafety validate || exit $?           # offline gate, fails on bad CSV
gplay compliance datasafety set --confirm --output json   # publish from versioned CSV
```
