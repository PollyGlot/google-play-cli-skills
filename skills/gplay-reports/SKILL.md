---
name: gplay-reports
description: "Monthly Bulk reports with gplay `reports`: installs, ratings, crashes, Store listing performance, subscription statistics, earnings and estimated sales, read from the Reporting bucket (read-only). Use when asked for install or uninstall counts, acquisition by traffic source or country, revenue, payouts or sales per app, or any figure the Play Console only offers under Download reports."
---

# gplay reports (monthly Bulk reports)

`gplay reports` reads the CSV exports Play deposits every month in the
developer account's Reporting bucket on Cloud Storage. It is the only
programmatic source for installs, uninstalls, ratings over time, Store listing
acquisition and revenue. Shared conventions are in `gplay-cli-usage`.

The whole group is `[experimental]`: pin an exact gplay release before a CI
job depends on its flags or output.

## Pick the right source

| Question | Command |
|---|---|
| Installs, uninstalls, active devices | `gplay reports installs` |
| Average rating over time | `gplay reports ratings` |
| Crash and ANR counts per month | `gplay reports crashes` |
| Store listing visitors and conversions | `gplay reports store-performance` |
| One subscription's subscribers and churn | `gplay reports subscription-stats --product <id>` |
| What Google paid out (charges, fees, taxes, refunds) | `gplay reports earnings` |
| Orders as they happen (estimates, low latency) | `gplay reports sales` |

Crash and ANR **rates** after a rollout, day by day, belong to `gplay vitals`
(`gplay-vitals`), not here. Reviews older than 7 days are `gplay reviews
history` (`gplay-reviews`), which reads the same bucket.

## Start with the inventory

```bash
gplay reports list
gplay reports list --family installs --package com.example.app --since 2026-01
```

It shows which families, months, dimensions and subscription product ids the
bucket holds. Read it before choosing `--month`, `--dimension` or `--product`
instead of guessing them: a dimension the bucket lacks fails with exit `2`,
and the message lists the ones present.

## Read one family

```bash
gplay reports installs --month 2026-09 --dimension country
gplay reports store-performance --dimension traffic_source
gplay reports earnings --month 2026-09 --package com.example.app
gplay reports installs --since 2026-01 --until 2026-06 --dimension country --output json
```

- Without `--month`, the latest month present is read.
- `--since`/`--until` merge a range into one result set; a missing month is
  skipped with a stderr warning, so check the `report` object for the months
  actually read.
- `earnings` and `sales` cover every app of the account: `--package` filters
  their rows, and the Project pin does not apply to them.

## Columns come from Google's CSV

`--output json` emits `report`, `columns` and `rows`. Row keys derive from
the CSV header and every value is the CSV's string, verbatim (numbers too).
Google adds and renames columns without notice: read `columns` from the
output instead of assuming field names, and convert values yourself.

## Buyer location stays hidden

`earnings` and `sales` hide the buyer's city, state and postcode by default
(the country always shows). Pass `--include-buyer-location` only when the user
explicitly asks for that data, and do not copy it into logs or tickets.

## Failures that need a human

- **Permission (exit `11`)**: the error names the Play Console permission to
  grant the service account, "View app information" for statistics, "View
  financial data" for `earnings` and `sales`, both global. A `list` that can
  read some families warns about the others and still prints.
- **Wrong bucket**: the default is `pubsite_prod_rev_<developerId>`. When the
  Console issued another name, ask the user for it ("Copy Cloud Storage URI"
  on the Console's Download reports page) and pass `--bucket`.
- **Month not published yet (exit `30`)**: statistics land 3 to 7 days after
  the month ends, earnings around the 5th of the next month. Report the delay;
  retrying sooner does not help.
- **Too large (exit `20`)**: a range over the read bounds fails whole, never
  truncated. Narrow `--since`/`--until`.
