---
name: gplay-monetization
description: Manage the monetization catalog, subscriptions and one-time products, as declarative files with gplay `subscriptions` and `iap`. Use when putting a catalog under version control, editing a product's prices/offers/listings, reviewing catalog drift in CI, promoting a legacy in-app product to the v2 model, or migrating live subscribers to a new price.
---

# gplay monetization (subscriptions + one-time products)

`gplay subscriptions` and `gplay iap` own the **monetization catalog** as
declarative, version-controlled files (ADR-0041). Shared conventions (auth,
`--package` pinning, output, exit codes, `--dry-run`/`--confirm`) are in
`gplay-cli-usage`. Both namespaces are `[experimental]`.

| Namespace | What it holds | Default `--dir` |
|---|---|---|
| `subscriptions` | subscriptions, their base plans (config + per-territory prices), their offers, lifecycle state | `./monetization/subscriptions` |
| `iap` | one-time products, v2 `monetization.onetimeproducts` **∪** legacy `inappproducts` | `./monetization/iap` |

Both sit **outside the Edit lifecycle** (like `compliance`, `device-tiers`,
`recovery`, `orders`), direct package-scoped writes, no `editId`, so
`gplay edits begin` does not batch them.

## The loop

```
pull  →  edit the .json files  →  apply --dry-run  →  apply [--confirm]
```

One `<productId>.json` per product, holding the **API resource verbatim**
minus server-derived noise. `pull` then `apply` with no edits is a guaranteed
no-op. Commit the directory; the diff in review *is* the catalog change.

## Mirror semantics: the trap if you know `metadata`

`metadata apply` is **additive**: a locale live online but absent on disk is
left alone. Monetization is the opposite. **The directory is the complete
declared catalog**, a live subscription, product or offer with no file is a
**delete in the plan**. A monetization catalog is a closed set whose omissions
must be visible; a store listing tree is a partial view.

Consequences to internalize before running anything:

- **Never point `--dir` at a fresh/empty directory.** `apply` refuses when the
  directory holds no `.json` while the app has live products (it would delete
  them all), but a *partially* populated directory is a legitimate plan full
  of deletes. Always `pull` first.
- **`pull` is destructive locally too.** It removes stale `.json` files so the
  directory mirrors Play. It refuses to erase a populated directory when the
  live catalog reads back empty (a mis-set `--package` or a scope loss);
  that refusal is a signal, not an obstacle to work around. Non-`.json` files
  are never touched.
- Deleting a subscription is additionally guarded server-side: Google refuses
  to delete one with a published base plan.

## Gates

| Situation | Gate | Exit without it |
|---|---|---|
| Plan contains any delete (product or offer) | `--confirm` | `3` |
| `iap apply` promotes a live legacy product to v2 | `--migrate` | `3` |
| `subscriptions prices migrate` (reprices live subscribers) | `--confirm` | `3` |
| Creates, patches, state changes | *none*, they run directly | n/a |

`CI=true` never auto-confirms. `GPLAY_READONLY` refuses every `apply` and
`migrate` outright (exit `4`, not resolvable by adding a flag).

State changes are **not** gated (activate/deactivate are reversible), but
they are listed prominently in every plan view because they move buyer
availability.

## Subscriptions

```bash
gplay subscriptions pull                              # → ./monetization/subscriptions/*.json
# …edit the files…
gplay subscriptions apply --dry-run                   # ONLINE read, prints the plan, changes nothing
gplay subscriptions apply                             # creates/patches/state changes
gplay subscriptions apply --confirm                   # …when the plan also deletes
```

- **Base plans ride the parent patch.** Base plan config (billing type,
  per-territory `regionalConfigs` prices) is declared inline under `basePlans`
  and patched with the subscription; the API has no create/patch on the
  sub-resource. Its endpoints only manage *state* and subscriber price
  migration.
- **Offers are embedded but real.** `pull` nests each offer under
  `basePlans[].offers`, a **file construct the API resource does not carry**.
  `apply` splits them back out and reconciles them through the offers
  endpoints under the key `productId/basePlanId/offerId`. Don't expect that
  array in an API response.
- **`state:` declares lifecycle, reconciled via `:activate`/`:deactivate`,
  never a patch.** Declare `ACTIVE` or `INACTIVE`. **Omitting the field leaves
  state unmanaged**, the metadata stance. An unreachable transition (`DRAFT`
  from anything, `INACTIVE` from `DRAFT`) is a usage error naming it.
- **Reconciled fields only.** `listings`, `taxAndComplianceSettings`,
  `restrictedPaymentCountries`, `basePlans`. The `updateMask` is exactly the
  changed managed fields; nothing outside that projection drifts or diffs.
  `archived` is **not** reconciled (deprecated/output-only upstream).

### Prices

```bash
# Derive per-region prices from one base price, a computation, no write:
gplay subscriptions prices convert --price 4.99 --currency USD --output json
```

Paste the returned `Money` objects into a base plan's `regionalConfigs`, then
rehearse with `apply --dry-run`. `--output json` is the
`ConvertRegionPricesResponse` verbatim. "Not a write" does not mean offline:
`convert` calls the `convertRegionPrices` API (today's exchange rates), so it
needs a credential and the package axis; it just never mutates anything.

```bash
# Reprice EXISTING subscribers, money-moving, one base plan per call:
gplay subscriptions prices migrate \
  --product premium --base-plan monthly \
  --region FR --region DE \
  --oldest 2026-01-01T00:00:00Z \
  --price-increase-type opt-in \
  --dry-run                                  # offline preview, lists the gate in "requires"

gplay subscriptions prices migrate … --confirm
```

**This is the one deliberate exception to "editing files never touches a live
purchaser."** `apply` changes what **new** buyers pay; `migrate` changes what
**existing** subscribers pay. An `apply` diff never triggers a migration;
that separation is pinned by a test upstream, so don't expect a price edit to
propagate to current subscribers.

- Cohorts **older than `--oldest`** (RFC-3339) migrate, scoped to the
  `--region`s you repeat.
- `--price-increase-type opt-in` requires subscribers to accept or churn;
  `opt-out` (where Google allows it) applies automatically with notice.
- **No bulk migration**, the batch sibling is deliberately not wrapped. One
  base plan per invocation.

## One-time products (`iap`)

```bash
gplay iap pull                       # v2 ∪ legacy → ./monetization/iap/*.json
gplay iap apply --dry-run
gplay iap apply [--confirm] [--migrate]
```

`pull` unions the v2 and legacy surfaces by product ID, and **a file's origin
is its shape**; no gplay-invented marker:

| Field present | Model |
|---|---|
| `sku` | legacy `inappproducts` |
| `productId` | v2 `onetimeproducts` |

**Legacy is inert**: gplay never creates, edits or deletes a legacy product,
the only gesture is the **one-way promotion** to v2 (rewrite the file with
`productId` and apply with `--migrate`; rehearse with `--dry-run` first).
When a legacy file is involved (an unexpected refusal, a promotion to plan,
or the question of why `pull` reads two surfaces), read
[iap-legacy.md](iap-legacy.md).

## `--regions-version`

`create`/`patch` require Google's regions version string. gplay pins the
current published value (`2022/02`) and exposes `--regions-version` to
override when Google publishes a new one, a flag, not a config knob, so the
pin stays visible in CI logs.

## CI gate

```bash
gplay subscriptions apply --dry-run --output json    # the plan, a gplay-owned shape
gplay iap apply --dry-run --output json
```

`apply --output json` emits the **plan**, not an API echo, a recorded
ADR-0003 exception, like `metadata apply`, `[experimental]` until it
graduates: `{package, dryRun, changes[], summary{…}, requires[]}`, where each
change carries `op` (`create`/`patch`/`delete`/`activate`/`deactivate`, plus
`migrate` on `iap`) and its identity. `pull --output json` is the API
pass-through (the merged `ListSubscriptionsResponse`, or the composite
`{"oneTimeProducts":[…],"inappproduct":[…]}`), but the *files* are the real
output there.

A drift check is one line, fail the job when the plan is non-empty:

```bash
gplay subscriptions apply --dry-run --output json | jq -e '.changes | length == 0'
```

## Permissions

The Discovery snapshot ties **no specific Play permission enum** to the
monetization methods, so gplay's 403 hint points at the surface rather than
naming a capability: grant the service account access to the app's
**monetization setup** in Play Console (Users & permissions), then retry.
403 → exit `11`, 404 on the package → exit `30` (verify `--package` or the pin).

