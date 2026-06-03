---
name: gplay-reviews
description: List recent Google Play user reviews and post developer replies with gplay — `reviews list` (filter by star rating, cap the count, pick columns) and `reviews reply` (one review at a time, or a batch of replies from a TSV file or stdin). Use when triaging recent reviews, filtering low-star feedback, replying to a user, or bulk-answering many reviews in CI. Note the API only exposes the last 7 days of reviews.
---

# gplay reviews

List and reply to user reviews. Shared conventions (auth, `--package`, output,
exit codes) are in `gplay-cli-usage`.

## The 7-day window

The Google Play API only returns reviews from the **last 7 days**. `reviews
list` always prints a WARN line to stderr to that effect; older history is not
reachable through this command (long-history retrieval via GCS CSV reports is
on the backlog). Plan triage cadences around that window.

## List reviews

```bash
gplay reviews list --package com.example.app
gplay reviews list --stars 1-2                 # only 1- and 2-star reviews
gplay reviews list --stars 1,3,5 --limit 20    # a set of ratings, capped at 20
gplay reviews list --columns stars,reviewId,summary --output json
```

`--stars` filters **client-side** and accepts a single rating (`1`), an
inclusive range (`1-2`), or a set (`1,3,5`); each rating is `1..5`. `--limit N`
caps the count after filtering (`0` = no cap). Results auto-paginate until the
window is exhausted. `--output json` is a `{"reviews":[...]}` pass-through of
the filtered set — grab `reviewId` from there to feed `reviews reply`.

## Reply to reviews

```bash
# Single reply
gplay reviews reply --review-id <REVIEW_ID> --reply "Thanks for the feedback!"

# Batch: a TSV of <review-id><TAB><reply text>, one per line
gplay reviews reply --batch replies.tsv
gplay reviews reply --batch -        # read the TSV from stdin
```

`--review-id`/`--reply` (single) and `--batch` are mutually exclusive. In the
batch TSV, blank lines and `#` comments are skipped, and a reply containing
tabs or newlines must be double-quoted (RFC 4180). Replies post
**sequentially**; a per-line failure is reported on stderr and does **not**
abort the rest — the process exits with the highest exit code seen across rows,
so a CI job still fails loudly if any reply failed. Use `--dry-run` to parse
and print the planned replies without calling the API. Confirm flags with
`gplay reviews reply --help`.
