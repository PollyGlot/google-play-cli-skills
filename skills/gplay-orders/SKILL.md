---
name: gplay-orders
description: Look up and refund Google Play orders by order ID with gplay `orders` (admin diagnostics, not purchase-token verification). Use when holding an order ID from a buyer complaint or payout report, or when refunding an order.
---

# gplay orders (admin commerce: view + refund)

`gplay orders` is the **admin commerce** surface: look up an order by its order
ID, and, when warranted, refund it. Both commands are `[experimental]`.
Shared conventions are in `gplay-cli-usage`.

## Read an order: `orders view`

```bash
gplay orders view GPA.1234-5678-9012-34567          # orders.get
gplay orders view GPA.1111-... GPA.2222-...         # orders.batchget: one package per call, all-or-nothing
gplay orders view GPA.1234-... --output json        # full Order, verbatim, with the fields the summary omits
```

## Refund an order: `orders refund` (money-moving, irreversible)

```bash
gplay orders refund GPA.1234-5678-9012-34567 --dry-run             # rehearse, no HTTP
gplay orders refund GPA.1234-5678-9012-34567 --confirm             # money back, access kept
gplay orders refund GPA.1234-5678-9012-34567 --revoke --confirm    # money back, entitlement revoked
```

Pick `--revoke` before running: it is the only choice the command leaves to
you (money back and access kept, or money back and entitlement revoked, a
subscription's future billing stopping too). One order per call.

## Capabilities

Money capabilities live in no Role bundle (`viewer` … `admin`): grant them
explicitly (`gplay-team`). `orders view` needs `CAN_VIEW_FINANCIAL_DATA`,
`orders refund` needs `CAN_MANAGE_ORDERS`; a 403 (exit `11`) names the
missing one.
