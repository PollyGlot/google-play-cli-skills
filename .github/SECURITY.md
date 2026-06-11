# Security Policy

## Supported versions

Skills in this repo are distributed from `main` — there are no versioned
releases. Only the current `main` is supported; reinstall with
`npx skills add PollyGlot/google-play-cli-skills` to pick up fixes.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security reports.**

Report privately through **GitHub Private Vulnerability Reporting** —
[open an advisory](https://github.com/PollyGlot/google-play-cli-skills/security/advisories/new).
It keeps the report private and in the repo with proper coordination. If you
can't use GitHub advisories, reach the maintainer privately via their
[GitHub profile](https://github.com/PollyGlot).

Please include:

- The skill affected (directory name, e.g. `gplay-release-flow`).
- A description of the vulnerability and its impact (what a misled agent
  could do).
- The instructions or scenario that trigger it.
- Any suggested remediation.

You'll get an acknowledgement within **72 hours** and a status update within
**7 days**. Coordinated disclosure is the default; we'll agree on a public
disclosure date together once a fix is ready.

## Scope

These skills are instructions executed by AI agents, so "vulnerability" here
means content that could steer an agent into unsafe behaviour.

In-scope:

- Skill instructions that could lead an agent to expose credentials
  (service account JSON, access tokens) in logs, files, or command output.
- Instructions that perform destructive Play Console actions (publishing,
  rollouts, deletions) without the confirmation steps the skill claims.
- Instructions that make an agent follow injected directives from untrusted
  data (e.g. review text, app metadata) — prompt injection paths.

Out of scope (please file with the relevant project instead):

- The `gplay` CLI itself — report via the
  [google-play-cli security policy](https://github.com/PollyGlot/google-play-cli/security/policy).
- The `skills` installer (`npx skills`) — report to its upstream project.

## Credit

Reporters who follow this policy will be credited (by handle of their choice)
in the fix's commit or release notes, unless they prefer to remain anonymous.
