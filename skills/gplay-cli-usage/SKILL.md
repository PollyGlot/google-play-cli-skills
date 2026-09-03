---
name: gplay-cli-usage
description: The cross-cutting conventions every gplay command shares (credential and package resolution, output formats, semantic exit codes, the `--dry-run`/`--confirm` safety gates, and the Edit lifecycle). Use when running or designing any gplay command, wiring gplay into CI, branching on its exit codes, or introspecting the Android Publisher API offline with `gplay schema`.
---

# gplay CLI conventions (foundation)

This is the **foundation skill**: the conventions that hold for *every* gplay
command, factored out once so the workflow skills (see the **Map of skills**
table at the end) can reference it
instead of repeating them. The normative source of truth is
[`docs/DESIGN.md`](https://github.com/PollyGlot/google-play-cli/blob/main/docs/DESIGN.md)
in the CLI repo; this skill summarizes it for agents and does **not** freeze
per-command flag lists.

## `--help` is the source of truth

gplay's commands are self-describing. Confirm the current verbs, flags, and
defaults from the binary, never from memory:

```bash
gplay --help                       # the whole command tree
gplay <group> --help               # a namespace (releases, tracks, team, …)
gplay <group> <command> --help     # one command, with its real flags
gplay exit-codes                   # the semantic exit-code table + diagnostic codes
```

If this skill and `--help` ever disagree, trust `--help`.

## Stability: the `[experimental]` banner

gplay is **GA since v1.0.0**. A command whose `--help` opens with no
`[experimental]` banner is covered by the Public contract: its name, flags,
semantics and exit codes hold until a major bump, so CI can pin `v1`.

The banner marks the exceptions, per command; those surfaces sit outside the
contract and can change in any release, so CI that depends on one pins an
**exact** version ([stability](https://gplay.sh/docs/concepts/stability/)).

## `gplay schema`: the offline API map

Where `--help` documents gplay's own surface, `gplay schema` introspects the
underlying **Android Publisher API** offline (no credential, no HTTP call) from
an index compiled into the binary: does a method exist, what does it send and
return, what fields and enums does a type carry:

```bash
gplay schema --list                 # compact catalog: id · http · path
gplay schema tracks                 # match across method id, REST path, type name
gplay schema Track                  # expand a schema's fields, types, enums
gplay schema edits.tracks.update    # a method's request/response, one hop deep
gplay schema --method PATCH         # filter the method surface by HTTP verb
gplay schema --codes                # gplay's own diagnostic-code catalog (see Exit codes)
```

`[experimental]`: confirm the surface with `gplay schema --help`.

## Which credential / account (resolution order)

Every authenticated command resolves the service-account credential in this
order, highest priority first:

1. `--service-account <path-or-inline-json>`, a JSON file path **or** inline
   JSON content. Overrides everything below.
2. `--account <name>`, a specific stored Account. Overrides env + the active
   Account.
3. `GPLAY_SERVICE_ACCOUNT` env var, a path or inline JSON.
4. The **active** stored Account (set up via `gplay auth login`).

Setting this up from scratch is the `gplay-setup` skill. Auth problems exit
`10` (bad/again credential) or `11` (the service account is not invited on the
app/account).

## Which app (`--package` + project pinning)

Most commands need a target package. Resolution (ADR-0004):

1. `--package com.example.app` on the command, else
2. the package pinned in `.gplay/config.json` for the current repo.

Pin once with `gplay init` (or `gplay apps init`) so day-to-day commands need
no `--package`. Managing the registry of packages is the `gplay-apps` skill.

Two surfaces address elsewhere: `customapps` and `team` key on the **developer
account** (`--developer-id`), and `appstore` carries a second package,
`--store-package`, the app store making the call, alongside the app it acts on.

## Output: table on a TTY, JSON in a pipe

`--output` takes `table`, `json`, or `markdown`. Resolution, most explicit
first: the `--output` flag, then `$GPLAY_DEFAULT_OUTPUT`, then **auto**
(ADR-0005): a human table on a terminal, JSON when piped or in CI. The env var
beats the `CI` heuristic too (it is a value someone typed, `CI`/TTY are
guesses); an unknown value is a usage error (exit `2`) naming the variable. For
machine consumption, ask for `--output json` explicitly; read commands pass
the API payload through (ADR-0003), and write commands return the request/diff
body, so a CI gate is usually one `jq` line. The pass-through promise is about
*not reshaping the API*, not that every `--output json` is an API echo: the
**offline reference** commands that wrap no API call, `team permissions` and
`schema`, synthesize their own (gplay-owned, documented) JSON instead.

**stdout is data, stderr is logs.** Parse stdout; warnings, progress, and
`-v/--verbose` flow steps go to stderr and never pollute the JSON. (Example:
`reviews list` prints its "last 7 days only" warning to stderr.)

Two stderr signals worth reading before trusting a listing:

- **Truncation.** When `--limit` cuts a list, gplay prints a `warning:` line
  on stderr; stdout is byte-for-byte what it would be without the warning. An
  agent that only parses stdout cannot tell "that's all" from "capped", so
  read stderr, or pass `--limit 0` where the command allows it.
- **Redaction.** Credentials (PEM blocks, service-account secrets,
  `Authorization` headers, JWTs, Google tokens) are masked on stderr; stdout
  stays verbatim. Do not expect a secret to appear in a diagnostic line.

**Every single-value flag is accepted once.** A repeated flag (`--account a
--account b`, and even `-vv`) fails with exit `2` before auth and before any
HTTP call; only list-valued flags such as `--check` or `--stars` repeat. When
building a command line incrementally, replace a flag, never append it twice.

## Exit codes: branch on the number, not the text

`gplay exit-codes` prints the full table. The semantic codes:

| Code | Meaning | Retry-safe |
|---|---|---|
| 0 | Success | n/a |
| 1 | Generic error (fallback) | no |
| 2 | CLI misuse (unknown flag/command, bad value, missing arg) | no |
| 3 | A named safety flag is missing (`--confirm` / `--grant-admin`), re-run with it | yes, with the flag |
| 4 | Denied by environment policy (`GPLAY_READONLY`), a mutating command was refused | no, change the environment |
| 10 | Authentication failure | no |
| 11 | Authorization (403, SA not invited) | no |
| 20 | Client-side validation (bad AAB, unknown locale, …) | no |
| 30 | API 4xx (not found, conflict, gone, …) | no |
| 40 | API 5xx (upstream unhealthy) | **yes** |
| 50 | Network (timeout, DNS, refused) | **yes** |
| 60 | State conflict (open edit, rate-limited, ambiguous target) | sometimes |
| 70 | Findings present: a read-only check ran to completion and reported drift (`apps audit`) | n/a, not an error |

Agents should treat `3` as "append the named flag and re-run", `4` as "the
environment forbids this write; do not retry, change the deployment", `40`/`50`
as "back off and retry", `2`/`10`/`11`/`20`/`30` as "fix the input, do not
retry blindly", and `70` as "the check worked, act on its report". `70` is a
gate result, not a failure: the command read everything it meant to read.
When a check command could not read some target, the ordinary API or network
code wins over `70`, so a sweep with holes never returns a clean `0`.

### Diagnostic codes: discriminate failures that share an exit code

Under `--output json` a failure carries a stable, machine-readable envelope on
**stdout** (ADR-0044; stderr keeps the human prose):

```json
{"error":{"code":"EDIT_ALREADY_EXISTS","exitCode":60,"retryable":false,"message":"..."}}
```

`code` is SCREAMING_SNAKE and append-only; `retryable` is the bit to branch
on. The value of the envelope is where one exit code hides several causes:
`60` covers `STATE_CONFLICT`, `EDIT_ALREADY_EXISTS` (commit or discard the
open Edit), `EDIT_EXPIRED` (begin a new Edit and replay) and
`RATE_LIMIT_EXCEEDED` (the only retryable one). `30` splits into
`INVALID_ARGUMENT`, `NOT_FOUND` and `API_ERROR`. `gplay schema --codes`
prints the whole catalog offline (`--output json` for a machine).

## Safety: `--dry-run` everywhere, `--confirm` for live writes

- **`--dry-run`** is available on write commands: it validates inputs and
  prints the payload/diff it *would* send, with no HTTP call (and usually no
  auth needed). Reach for it before any production-affecting write.
- **`--confirm`** gates the writes that reach real users or the live store,
  production releases, `metadata apply`, `compliance datasafety set`, and
  destructive local writes like `auth logout`. Omitting it fails with exit `3`
  and names the flag (in the JSON error envelope: `requires: ["confirm"]`).
  `CI=true` never auto-confirms.
- **`--grant-admin`** is the stronger gate for conferring admin in
  `gplay-team`.
- **`GPLAY_READONLY=1`** (truthy = enforced) is the environment-level guard for
  agent deployments that must only read. Because the safety flags above are
  *advisory*, an agent holding the credential can pass them itself; set this in
  the environment and the kernel refuses **every mutating command** before
  credential resolution and before any network call, regardless of flags, while
  read commands and `--dry-run` previews keep working. Its refusal exits **`4`**
  (denied by environment policy), which, unlike `3`, is **not** resolvable by
  adding a flag; the only fix is to change the environment.

When a write refuses for a missing flag, the message names it; that refusal is
*agent-resolvable* (ADR-0017): re-run with the flag it asked for. The
`GPLAY_READONLY` refusal (exit `4`) is the deliberate exception: it is **not**
agent-resolvable.

## The Edit lifecycle: implicit by default, explicit when you batch

Google Play mutations run inside a transactional **Edit**
(`edits.insert → change → edits.commit`). gplay offers two ways to drive it.

**Implicit (the default).** Each write command performs the whole three-step
dance on its own: it opens its own Edit, makes the change, and commits,
discarding the Edit automatically on failure. You do not manage Edit IDs by
hand. `--keep-edit-on-failure` skips that auto-discard for debugging.

**Explicit (`gplay edits …`, when several changes must land together).** To
batch multiple writes into **one atomic commit**, open an Edit yourself:

```bash
gplay edits begin            # opens an Edit, pins its id to .gplay/edit-<package>.json
gplay metadata apply …       # these writes detect the pin and reuse the open Edit
gplay releases upload … --release-notes-dir ./notes
gplay edits status           # local read (no auth/network): shows the open edit, or none
gplay edits commit           # publish everything at once, and clear the pin
# gplay edits discard        # …or abandon the whole batch, clearing the pin
```

While the pin exists, subsequent write commands reuse the open Edit instead of
opening their own, so the changes commit together or not at all. In explicit
mode there is **no** auto-commit and **no** auto-discard; the lifecycle is
yours until you `commit` or `discard`. Notes: a project (`gplay init`) is
required since the pin lives under `.gplay/`; opening a second Edit while one is
pinned is refused (**exit 60**); if `commit` fails (e.g. a validation error) the
Edit stays open and the pin remains, fix and re-run, or `discard`.

(A few surfaces sit *outside* the Edit model on purpose: `compliance
datasafety`, `device-tiers`, `recovery`, `orders`, `vitals`, `games`,
`subscriptions`, `iap`, `appstore` are direct writes/reads with no `editId`, so
`edits begin` does not batch them; their skills call that out.)

## Map of skills

| Surface | Skill |
|---|---|
| Auth onboarding | `gplay-setup` |
| App registry + details | `gplay-apps` |
| Releases (upload/promote/rollout) | `gplay-release-flow` |
| Tracks + testers | `gplay-tracks` |
| Reviews | `gplay-reviews` |
| Store listings + images | `gplay-metadata-sync` |
| Data Safety | `gplay-compliance` |
| Team users + grants | `gplay-team` |
| Managed Play private apps | `gplay-customapps` |
| Post-launch vitals (crashes/ANRs) | `gplay-vitals` |
| Orders (view/refund) | `gplay-orders` |
| Play Games config (achievements/leaderboards) | `gplay-games` |
| App recovery (bad-release remediation) | `gplay-recovery` |
| Device tier configs | `gplay-device-tiers` |
| Subscriptions + one-time products (catalog) | `gplay-monetization` |
| Alternative app stores (catalog export, hosted app review) | `gplay-appstore` |
