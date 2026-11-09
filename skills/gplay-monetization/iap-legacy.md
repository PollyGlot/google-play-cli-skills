# Legacy `inappproducts`: the v2 ∪ legacy union and its refusals

## Why `iap pull` reads two surfaces

Google auto-migrated one-time products to the v2 model only for Console-only
accounts. Any account that ever wrote through the `inappproducts` API keeps
unmigrated products that are **invisible to the v2 list**, and gplay's users
are by definition API-managed. So `pull` reads both surfaces and unions them by
product ID. A product live in both keeps the v2 file; the legacy row is its
pre-migration shadow.

When Google has retired the legacy API for an app, the `inappproducts` list
answers 403 "Please migrate to the new publishing API". gplay reads that one
message as an empty legacy inventory, not a permission error: every product
is v2. Any other 403 stays exit `11`. A legacy file left in `--dir` is then
refused by `apply` (exit `2`), because planning without it would delete its
v2 product; `pull` rewrites it as v2.

## Legacy is inert: each attempt is a distinct refusal

gplay never creates, edits or deletes a legacy product. Each attempt is a
self-explaining usage error:

- declaring a legacy product that isn't live → declare it as v2 instead
- editing a legacy file in place → rewrite it as v2 and `--migrate`
- omitting a legacy file → gplay won't delete legacy; restore the file with
  `pull` or remove the product in the Console
