# Legacy `inappproducts` — the v2 ∪ legacy union, refusals, and promotion

## Why `iap pull` reads two surfaces

Google auto-migrated one-time products to the v2 model only for Console-only
accounts. Any account that ever wrote through the `inappproducts` API keeps
unmigrated products that are **invisible to the v2 list** — and gplay's users
are by definition API-managed. So `pull` reads both surfaces and unions them by
product ID. A product live in both keeps the v2 file; the legacy row is its
pre-migration shadow.

## Legacy is inert — each attempt is a distinct refusal

gplay never creates, edits or deletes a legacy product. Each attempt is a
self-explaining usage error:

- declaring a legacy product that isn't live → declare it as v2 instead
- editing a legacy file in place → rewrite it as v2 and `--migrate`
- omitting a legacy file → gplay won't delete legacy; restore the file with
  `pull` or remove the product in the Console

## Promotion is the only gesture, and it's one-way

Rewrite the file in the v2 schema (`productId` instead of `sku`) and apply with
`--migrate`. It shows as a distinct `migrate` op in the plan. Once promoted, a
product can **never** return to `inappproducts` — rehearse with `--dry-run`
first.

## v2 write mechanics

A v2 create is a `patch` with `allowMissing` (the API has no insert); offer
writes ride the per-purchase-option batch endpoints; and purchase-option and
offer lifecycle **states are not yet reconciled** (normalized out of the diff).
