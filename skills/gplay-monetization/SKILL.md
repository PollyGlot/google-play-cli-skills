---
name: gplay-monetization
description: Subscriptions and one-time products (in-app purchases) as declarative files with gplay `subscriptions` and `iap`. Use when editing a product's prices, offers or listings, deriving per-region prices from one base price, pulling the catalog into version control, checking catalog drift in CI, promoting a legacy in-app product to v2, or repricing live subscribers.
---

# gplay monetization (subscriptions + one-time products)

`gplay subscriptions` and `gplay iap` own the **monetization catalog** as
declarative, version-controlled files (ADR-0041). Shared conventions are in
`gplay-cli-usage`. Both namespaces are `[experimental]`.

| Namespace | What it holds |
|---|---|
| `subscriptions` | subscriptions, their base plans (config + per-territory prices), their offers, lifecycle state |
| `iap` | one-time products, v2 `monetization.onetimeproducts` **∪** legacy `inappproducts` |

Both sit **outside the Edit lifecycle** (no `editId`): `gplay edits begin`
does not batch them.

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
declared catalog**: a live subscription, product or offer with no file is a
**delete in the plan**.

- **`pull` before every `apply`.** `apply` refuses an empty directory when
  the app has live products, but a *partially* populated one is a legitimate
  plan full of deletes.
- **`pull` is destructive locally too**, and refuses to erase a populated
  directory when the live catalog reads back empty (a mis-set `--package` or
  a scope loss): that refusal is a signal, not an obstacle to work around.
- Deleting a subscription is additionally guarded server-side: Google refuses
  to delete one with a published base plan.

## Gates

| Situation | Gate | Exit without it |
|---|---|---|
| Plan contains any delete (product, base plan or offer) | `--confirm` | `3` |
| `iap apply` cancels a pre-order offer (irreversible) | `--confirm` | `3` |
| `iap apply` promotes a live legacy product to v2 | `--migrate` | `3` |
| `subscriptions prices migrate` (reprices live subscribers) | `--confirm` | `3` |
| Creates, patches, state changes (reversible) | *none*, they run directly | n/a |

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
  sub-resource. Its endpoints only manage *state*, subscriber price
  migration, and deletion.
- **Only a DRAFT base plan deletes** (a published one comes back as
  `BASE_PLAN_NOT_DRAFT`): retire it in two applies, `state: INACTIVE` first,
  then drop it from the file.
- **Offers are embedded but real.** `pull` nests each offer under
  `basePlans[].offers`, a **file construct the API resource does not carry**.
  `apply` splits them back out and reconciles them through the offers
  endpoints under the key `productId/basePlanId/offerId`.
- **`state:`** (`ACTIVE`/`INACTIVE`, omit to leave it unmanaged) reconciles
  via `:activate`/`:deactivate`. `DRAFT` from anything, or `INACTIVE` from
  `DRAFT`, is a usage error naming the transition.
- **Reconciled fields only.** `listings`, `taxAndComplianceSettings`,
  `restrictedPaymentCountries`, `basePlans`. The `updateMask` is exactly the
  changed managed fields; nothing outside that projection drifts or diffs.
  `archived` is **not** reconciled (deprecated/output-only upstream).

### Prices

```bash
# Derive per-region prices from one base price:
gplay subscriptions prices convert --price 4.99 --currency USD --output json
```

Paste the returned `Money` objects into a base plan's `regionalConfigs`, then
`apply --dry-run`. `convert` is online (today's rates via
`convertRegionPrices`): it needs a credential and the package axis, and
mutates nothing.

```bash
# Reprice EXISTING subscribers, money-moving, one base plan per call:
gplay subscriptions prices migrate \
  --product premium --base-plan monthly \
  --region FR --region DE \
  --oldest 2026-01-01T00:00:00Z \
  --price-increase-type opt-in \
  --dry-run                                  # offline preview, unlike apply --dry-run

gplay subscriptions prices migrate … --confirm
```

**This is the one deliberate exception to "editing files never touches a live
purchaser."** `apply` changes what **new** buyers pay; `migrate` changes what
**existing** subscribers pay. An `apply` diff never triggers a migration.

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

**Purchase options and offers carry `state` too**, same stance as
subscriptions; `CANCELLED` (pre-order offer) is the one-way case gated in
the table above.

**Legacy is inert**: gplay never creates, edits or deletes a legacy product,
the only gesture is the **one-way promotion** to v2 (rewrite the file with
`productId` and apply with `--migrate`; rehearse with `--dry-run` first).
When a legacy file is involved (an unexpected refusal, or the question of
why `pull` reads two surfaces), read [iap-legacy.md](iap-legacy.md).

## CI gate

```bash
gplay subscriptions apply --dry-run --output json    # the plan, a gplay-owned shape
gplay iap apply --dry-run --output json
```

`apply --output json` emits the **plan**, not an API echo:
`{package, dryRun, changes[], summary{…}, requires[]}`, where each change
carries `op` (`create`/`patch`/`delete`/`activate`/`deactivate`, plus
`migrate` and `cancel` on `iap`) and its identity.

A drift check is one line, fail the job when the plan is non-empty:

```bash
gplay subscriptions apply --dry-run --output json | jq -e '.changes | length == 0'
```

## Permissions

No permission alias maps to monetization, so the 403 hint (exit `11`) names
no capability: grant the service account **Monetization setup** on the app in
Play Console (Users & permissions), then retry.
