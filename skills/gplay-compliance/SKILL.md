---
name: gplay-compliance
description: Data Safety declaration from a versioned CSV with `gplay compliance`, the only Play compliance surface with an API. Use when updating or CI-gating the Data Safety form, or when asked to automate content rating or another Console-only declaration.
---

# gplay compliance (Data Safety)

Manage the app's **Data Safety** declaration from a canonical CSV. Shared
conventions are in `gplay-cli-usage`.

## Only Data Safety has an API

Content rating (IARC), target audience/Families, ads, news-app,
government-app and the other declarations stay manual in Play Console: list
them as a manual step in the release runbook.

## Data Safety is write-only

The declaration is **write-only** (ADR-0014): a direct POST **outside** the
Edits model that **replaces the whole document**. gplay cannot read it back;
there is no `get`, only `set` and an offline `validate`. `validate` passing
means well-formed, not accepted: only the live `set` POST arbitrates against
Google's schema.

```bash
gplay compliance datasafety validate                       # offline structural check, no auth
gplay compliance datasafety set --dry-run                  # rehearse: validate + resolve target + size, no HTTP
gplay compliance datasafety set --confirm                  # the real write, replaces the live declaration
```

## CI shape

```bash
gplay compliance datasafety validate || exit $?           # offline gate, fails on bad CSV
gplay compliance datasafety set --confirm --output json   # publish from versioned CSV
```
