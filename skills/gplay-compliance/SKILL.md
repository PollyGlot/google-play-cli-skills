---
name: gplay-compliance
description: Push and validate an app's Google Play Data Safety declaration with gplay — `compliance datasafety validate` (offline structural check of the canonical CSV) and `compliance datasafety set` (POST the declaration live). Use when updating the Data Safety form from a versioned CSV or gating it in CI. Note this is the ONLY Play compliance surface with an API — content rating, target audience, and ads/news declarations have no endpoint and stay manual in the Play Console.
---

# gplay compliance (Data Safety)

Manage the app's **Data Safety** declaration from a canonical CSV. Shared
conventions (auth, `--package`, output, exit codes) are in `gplay-cli-usage`.

## What is and isn't automatable (the hard wall)

Data Safety is the **only** Play compliance surface with a Developer API
endpoint. These neighbouring declarations have **no API** and cannot be driven
by gplay — they remain manual in the Play Console:

- Content rating (IARC questionnaire)
- Target audience & content / Families
- Ads declaration, News-app declaration, Government-app status, COVID-19, etc.

Treat those as a documented manual step in your release runbook; gplay does not
and will not automate them. This skill is strictly about Data Safety.

## Data Safety is write-only

The declaration is **write-only** (ADR-0014): a direct POST **outside** the
Edits model that **replaces the whole document**. gplay cannot read it back —
there is no `get`, only `set` and an offline `validate`. The live POST is the
only thing that validates the contents against Google's schema.

```bash
gplay compliance datasafety validate                       # offline structural check
gplay compliance datasafety set --dry-run                  # rehearse: validate + resolve target + size
gplay compliance datasafety set --confirm                  # the real write — replaces the live declaration
```

- **`validate`** structurally checks the CSV **offline** (no network, no auth).
- **`set`** pushes the canonical CSV (`--file`, default
  `./compliance/data-safety.csv`). It runs `validate` implicitly first, so a
  structurally invalid CSV never reaches the network. `--dry-run` rehearses —
  validates, resolves the target package/Account, and reports "would POST N
  bytes / N rows" with no HTTP call (and no `--confirm` needed).
- The real write **requires `--confirm`** (a stale or wrong declaration can
  block releases or misstate your data practices); without it `set` refuses,
  exits `2`, and points you at the flag. `CI=true` does not auto-confirm.

`--output json` passes the API response through verbatim. Confirm flags with
`gplay compliance datasafety set --help`.

## CI shape

```bash
gplay compliance datasafety validate || exit $?           # offline gate, fails on bad CSV
gplay compliance datasafety set --confirm --output json   # publish from versioned CSV
```
