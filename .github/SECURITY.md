# Security Policy

## Supported versions

Skills in this repo ship from `main`, with no versioned releases. Only the
current `main` is supported: reinstall with
`npx skills add PollyGlot/google-play-cli-skills` to pick up fixes. A copy
installed by `gplay install-skills` is pinned to the commit baked into that
gplay version, so a fix reaches it with the next gplay release.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security reports.**

Report privately through GitHub Private Vulnerability Reporting:
[open an advisory](https://github.com/PollyGlot/google-play-cli-skills/security/advisories/new).
If you can't use GitHub advisories, contact the maintainer through their
[GitHub profile](https://github.com/PollyGlot).

Please include:

- The skill affected (directory name, e.g. `gplay-release-flow`).
- A description of the vulnerability and its impact (what a misled agent
  could do).
- The instructions or scenario that trigger it.
- Any suggested remediation.

You'll get an acknowledgement within 72 hours and a status update within
7 days. Once a fix is ready, we agree on a public disclosure date together.

## Scope

These skills are instructions executed by AI agents, so "vulnerability" here
means content that could steer an agent into unsafe behaviour.

In-scope:

- Skill instructions that could lead an agent to expose credentials
  (service account JSON, access tokens) in logs, files, or command output.
- Instructions that perform destructive Play Console actions (publishing,
  rollouts, deletions) without the confirmation steps the skill claims.
- Instructions that make an agent follow injected directives from untrusted
  data, such as review text or app metadata (prompt injection).

Out of scope (please file with the relevant project instead):

- The `gplay` CLI itself: report it through the
  [google-play-cli security policy](https://github.com/PollyGlot/google-play-cli/security/policy).
- The `skills` installer (`npx skills`): report it to its upstream project.

## Credit

Reporters who follow this policy will be credited (by handle of their choice)
in the fix's commit or release notes, unless they prefer to remain anonymous.
