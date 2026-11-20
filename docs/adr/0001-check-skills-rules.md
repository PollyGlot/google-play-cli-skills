# What check-skills.py checks, and why

Status: accepted, 2026-11-20.

The skills document a CLI they do not ship, so the failure that matters is drift: a flag that no longer exists, a command declared absent that shipped three versions ago, a namespace the CLI grew that no skill names, a frontmatter typo that makes `npx skills add` skip the skill silently. Nothing else in this repo catches those, so `scripts/check-skills.py` resolves every documented invocation against the installed `gplay` binary, reading only `--help` (no credential). `--offline` skips the checks that need the binary; the exit code is 1 when any check fails, and every failure names a `file:line`.

These rules lived as comments in the script until 2026-11-20. Each names the function or constant that carries it.

## Reading `--help`

- `flags` reads the Flags sections only. Matching the whole help text would count flags merely discussed in the prose ("there is no --confirm here"), which is the opposite of the point.
- `required_flags` reads the command's own Flags section. gplay marks a mandatory flag "(required)" or "(required: <why>)". A conditional marker ("(required when the plan deletes ...)") is not an obligation on every invocation, so it does not count. Global flags are never required.
- `check_invocations`: an unknown word where a group expects a subcommand is an invented verb, the drift that matters most. A group with no subcommands takes positional arguments instead, so the word is left alone.
- `leaves` stops its walk when a child's help text is identical to its parent's. cobra answers an unknown child's `--help` with the parent's help and exit 0, so identical text is the only tell. The case that motivated it, a root help listing `gplay exit-codes` under "Additional help topics" (parsed as a command named `gplay`), no longer occurs with gplay 2.3.2, where `exit-codes` is an ordinary command already in `SKIP_SUBCOMMANDS`; the guard stays because it costs nothing and prevents re-walking the whole tree.

## Required flags

`check_invocations` flags a documented invocation that leaves out a required flag: an agent that copies it gets exit 3 or 2 at once. Two exceptions: an elided invocation ("gplay releases upload …") is a sketch, not a recipe, and a `--dry-run` preview legitimately skips `--confirm`.

## Coverage

- `check_coverage` is the inverse of the invocation check, which only sees what a skill already documents: a whole namespace added by a gplay release (`signing` in v1.3.0) would sail through it. It walks the binary, then looks for each leaf in the skills. A leaf counts as covered when some skill mentions its full path (`gplay signing enroll`, or `signing enroll` in prose) at least once.
- `SKIP_SUBCOMMANDS` lists the commands whose `--help` is not a gplay surface a skill would document.
- `UNCOVERED_OK` lists the leaf commands a skill need not name: the README owns them, or they are gplay's own plumbing rather than a Play surface.

## Skill size

`MAX_WORDS` caps any skill file. A skill that grows past it is caching `--help` output or restating `gplay-cli-usage`; `AGENTS.md` makes gplay the source of truth, so the flags belong to `--help` and the skill keeps only what `--help` does not say. The fix for a skill over the ceiling is a cut, not a bigger ceiling.

## Frontmatter

`check_frontmatter` requires `name` and `description`, a `name` that matches the folder, and YAML that actually parses. An unquoted `": "` in a description makes the YAML invalid, and `npx skills add` skips the skill without a word. That has bitten this repo before.

## README catalogue

`check_catalogue` requires the README table to link exactly the skills the repo ships. A new skill missing from the table is invisible on GitHub and skills.sh, and a row left behind by a rename points at nothing. Only table rows count: a link in a paragraph is not a catalogue entry.
