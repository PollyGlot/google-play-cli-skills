---
name: gplay-orders
description: Look up and refund Google Play orders by order ID with gplay `orders`, admin diagnostics, not runtime purchase-token verification. Use when a buyer complaint or payout report hands you an order ID and you need its state, or when issuing a money-moving `--confirm`-gated refund.
---

# gplay orders (admin commerce: view + refund)

`gplay orders` is the **admin commerce** surface: look up an order by its order
ID, and, when warranted, refund it. Both commands are `[experimental]`.
Shared conventions (auth, output, exit codes, `--package` pinning,
`--dry-run`/`--confirm`) are in `gplay-cli-usage`.

**The admin/runtime boundary.** `orders` is for when a human or agent already
**holds an order ID** (from a buyer complaint, a chargeback, a payout report)
and wants to read or reverse it. That is an admin diagnostic. It is *not*
real-time **purchase-token verification** (`purchases.products` /
`purchases.subscriptionsv2`), which is a runtime API gplay does not wrap. If the
task is "verify this in-app purchase token from my backend", this is the wrong
surface.

An order ID looks like `GPA.1234-5678-9012-34567`. Orders are keyed by
**package**, so the pinned package (or `--package`) scopes the lookup.

## Read an order: `orders view`

```bash
gplay orders view GPA.1234-5678-9012-34567                 # one order (orders.get)
gplay orders view GPA.1111-... GPA.2222-... GPA.3333-...   # a batch (orders.batchget)
gplay orders view GPA.1234-... --output json               # full Order, verbatim
```

- One ID → a detailed `orders.get`. Several IDs → `orders.batchget`, **1–1000
  per request** (more is a usage error, exit `2`).
- **Batch is all-or-nothing:** if any ID is unknown or belongs to another
  package, the whole request fails; don't mix packages in one call.
- The human view is a compact summary (id, state, total, creation time, line
  items). `--output json` passes the `Order` (single) or
  `BatchGetOrdersResponse` (batch) through verbatim (ADR-0003), including the
  fields the summary omits: buyer address, tax, order history, sales channel.
- An unknown order ID fails with **exit 30** (API 4xx).

## Refund an order: `orders refund` (money-moving, irreversible)

```bash
# Rehearse first, no HTTP; under --output json the gate shows in "requires":
gplay orders refund GPA.1234-5678-9012-34567 --dry-run

# Live (moves money), so --confirm is required:
gplay orders refund GPA.1234-5678-9012-34567 --confirm

# Also terminate the entitlement (buyer loses access; a subscription stops
# billing too). Default is refund-money-but-keep-access:
gplay orders refund GPA.1234-5678-9012-34567 --revoke --confirm
```

- **Destructive tier.** Refunding moves money and cannot be undone, so it
  refuses without **`--confirm`** (exit `3`, naming the flag). `CI=true` never
  auto-confirms; `GPLAY_READONLY` refuses it outright (exit `4`).
- **`--revoke`** is the meaningful choice: without it, the buyer is refunded but
  keeps what they bought; with it, the entitlement is revoked (and a
  subscription's future payments stop). Decide before you run.
- **No bulk refund**, one order per call, on purpose. (`view` batches; `refund`
  does not.)
- Google rejects refunds for orders **older than 3 years**; that surfaces as a
  specific refusal, not a generic error.

## Capabilities: never bundled into a role

Money capabilities are deliberately **excluded from every Role bundle**
(`viewer` … `admin`), so a service account granted a role still cannot touch
orders. They must be granted as explicit permissions (see `gplay-team`):

- `orders view` → **`CAN_VIEW_FINANCIAL_DATA`**
- `orders refund` → **`CAN_MANAGE_ORDERS`**

A missing capability returns 403 (exit `11`) and the message names the one it
needs; grant it in the Play Console (Users & permissions) or via `gplay team`,
then retry.

