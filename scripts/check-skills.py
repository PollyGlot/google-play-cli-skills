#!/usr/bin/env python3
"""Check every skill against the gplay binary and the repo's own rules.

The skills document a CLI they do not ship, so the failure that matters is
drift: a flag that no longer exists, a command declared absent that shipped
three versions ago, a frontmatter typo that makes `npx skills add` skip the
skill silently. Nothing else in this repo catches those.

Usage:
    python3 scripts/check-skills.py            # all checks
    python3 scripts/check-skills.py --offline  # skip the checks needing gplay

Exit code is 1 when any check fails, and every failure names a file:line.
"""

from __future__ import annotations

import argparse
import functools
import glob
import os
import re
import shlex
import subprocess
import sys

GPLAY = os.environ.get("GPLAY_BIN", "gplay")
SKILLS_GLOB = "skills/**/*.md"
# Commands whose --help is not a gplay surface a skill would document.
SKIP_SUBCOMMANDS = {"help", "completion", "version", "install-skills", "exit-codes"}
PLACEHOLDER = re.compile(r"[<>…\[\]{}$]")
# A bare lowercase word: what a subcommand looks like, unlike a package name,
# a path or a flag value.
COMMAND_WORD = re.compile(r"^[a-z][a-z0-9-]*$")


class Findings(list):
    def add(self, path: str, line: int, message: str) -> None:
        self.append(f"{path}:{line}: {message}")


# --- the gplay binary, memoised -------------------------------------------


@functools.lru_cache(maxsize=None)
def help_text(path: tuple[str, ...]) -> tuple[int, str]:
    proc = subprocess.run(
        [GPLAY, *path, "--help"], capture_output=True, text=True, timeout=30
    )
    return proc.returncode, proc.stdout + proc.stderr


@functools.lru_cache(maxsize=None)
def subcommands(path: tuple[str, ...]) -> frozenset[str]:
    _, text = help_text(path)
    found, inside = set(), False
    for line in text.splitlines():
        if line.startswith(("Available Commands:", "Additional help topics:")):
            inside = True
            continue
        if inside:
            if not line.strip():
                inside = False
                continue
            match = re.match(r"^\s{2}([a-z][a-z0-9-]*)\s", line)
            if match:
                found.add(match.group(1))
    return frozenset(found)


@functools.lru_cache(maxsize=None)
def flags(path: tuple[str, ...]) -> frozenset[str]:
    """Flags this command accepts, read from the Flags sections only.

    Matching the whole help text would count flags merely discussed in the
    prose ("there is no --confirm here"), which is the opposite of the point.
    """
    _, text = help_text(path)
    return frozenset(
        re.findall(r"^\s+(?:-[a-zA-Z], )?(--[a-z0-9][a-z0-9-]*)", text, re.M)
    )


# --- checks ----------------------------------------------------------------


def check_frontmatter(findings: Findings) -> None:
    """name/description present, name matches the folder, YAML actually parses.

    An unquoted ": " in a description makes the YAML invalid, and `npx skills
    add` skips the skill without a word. That has bitten this repo before.
    """
    for path in sorted(glob.glob("skills/*/SKILL.md")):
        folder = os.path.basename(os.path.dirname(path))
        text = open(path, encoding="utf-8").read()
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not match:
            findings.add(path, 1, "no YAML frontmatter")
            continue
        keys = {}
        for offset, line in enumerate(match.group(1).split("\n"), start=2):
            pair = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line)
            if not pair:
                findings.add(path, offset, f"frontmatter line is not `key: value`: {line!r}")
                continue
            key, value = pair.group(1), pair.group(2)
            keys[key] = value
            if ": " in value and not value.startswith(('"', "'")):
                findings.add(
                    path, offset,
                    f"unquoted ': ' in `{key}` breaks the YAML, so `npx skills add` "
                    f"skips this skill; rephrase or quote the value",
                )
        if set(keys) != {"name", "description"}:
            findings.add(path, 2, f"frontmatter keys are {sorted(keys)}, expected name + description")
        if keys.get("name") != folder:
            findings.add(path, 2, f"name is {keys.get('name')!r}, folder is {folder!r}")


def check_relative_links(findings: Findings) -> None:
    for path in sorted(glob.glob(SKILLS_GLOB, recursive=True)):
        for number, line in enumerate(open(path, encoding="utf-8"), start=1):
            for target in re.findall(r"\]\(([a-zA-Z0-9._/-]+\.md)\)", line):
                if not os.path.exists(os.path.join(os.path.dirname(path), target)):
                    findings.add(path, number, f"relative link points at a missing file: {target}")


def check_no_em_dash(findings: Findings) -> None:
    """Prose carries no em dash (repo convention).

    Fenced blocks are exempt: they quote what the binary prints, and gplay does
    emit an em dash (see the trackhint message). Rewriting a quote would
    document output that does not exist.
    """
    for path in sorted(glob.glob(SKILLS_GLOB, recursive=True)):
        inside = False
        for number, line in enumerate(open(path, encoding="utf-8"), start=1):
            if line.startswith("```"):
                inside = not inside
                continue
            if not inside and "—" in line:
                findings.add(path, number, "em dash in prose; use a comma, colon, semicolon or parens")


def invocations(path: str):
    """Yield (line number, argv) for every `gplay ...` line in a fenced block."""
    text = open(path, encoding="utf-8").read()
    inside, buffer, start = False, "", 0
    for number, line in enumerate(text.split("\n"), start=1):
        if line.startswith("```"):
            inside = line.startswith("```bash") or line.startswith("```sh")
            continue
        if not inside:
            continue
        stripped = line.rstrip()
        if buffer:
            stripped = buffer + " " + stripped.strip()
            buffer = ""
        else:
            start = number
        if stripped.endswith("\\"):
            buffer = stripped[:-1].rstrip()
            continue
        command = stripped.split("#")[0].strip()
        if "gplay" not in command:
            continue
        for segment in command.split("|"):
            segment = segment.strip()
            if not segment.startswith("gplay "):
                continue
            try:
                argv = shlex.split(segment)[1:]
            except ValueError:
                continue
            yield start, segment, argv


def check_invocations(findings: Findings) -> int:
    """Every documented command and flag exists in the installed binary."""
    checked = 0
    for path in sorted(glob.glob(SKILLS_GLOB, recursive=True)):
        for number, segment, argv in invocations(path):
            resolved: list[str] = []
            for token in argv:
                if token.startswith("-") or PLACEHOLDER.search(token):
                    break
                if token in subcommands(tuple(resolved)):
                    resolved.append(token)
                    continue
                # An unknown word where the group expects a subcommand is an
                # invented verb, the drift that matters most. A group with no
                # subcommands takes positional arguments instead, so leave it.
                if COMMAND_WORD.match(token) and subcommands(tuple(resolved)) and resolved:
                    findings.add(
                        path, number,
                        f"no such command: gplay {' '.join(resolved)} {token}",
                    )
                break
            if not resolved:
                continue
            checked += 1
            code, _ = help_text(tuple(resolved))
            if code != 0:
                findings.add(path, number, f"no such command: gplay {' '.join(resolved)}")
                continue
            accepted = flags(tuple(resolved))
            used = set(re.findall(r"(?<![\w-])(--[a-z0-9][a-z0-9-]+)", segment))
            for unknown in sorted(used - accepted):
                findings.add(
                    path, number,
                    f"gplay {' '.join(resolved)} does not accept {unknown}",
                )
    return checked


def check_exit_code_table(findings: Findings) -> None:
    """The table in gplay-cli-usage lists exactly the codes `gplay exit-codes` prints."""
    path = "skills/gplay-cli-usage/SKILL.md"
    if not os.path.exists(path):
        return
    printed = subprocess.run([GPLAY, "exit-codes"], capture_output=True, text=True).stdout
    from_cli = {int(m.group(1)) for m in re.finditer(r"^(\d+)\s{2,}", printed, re.M)}
    text = open(path, encoding="utf-8").read()
    from_skill = {int(m.group(1)) for m in re.finditer(r"^\|\s*(\d+)\s*\|", text, re.M)}
    missing, invented = sorted(from_cli - from_skill), sorted(from_skill - from_cli)
    line = next(
        (n for n, l in enumerate(text.split("\n"), start=1) if l.startswith("| Code |")), 1
    )
    if missing:
        findings.add(path, line, f"exit-code table is missing codes the CLI prints: {missing}")
    if invented:
        findings.add(path, line, f"exit-code table lists codes the CLI does not print: {invented}")


# --- entry point -----------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="skip the checks that need gplay")
    args = parser.parse_args()

    findings = Findings()
    check_frontmatter(findings)
    check_relative_links(findings)
    check_no_em_dash(findings)

    online = not args.offline
    if online:
        try:
            help_text(())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(
                f"error: {GPLAY} is not on PATH. Install it "
                "(curl -fsSL https://gplay.sh/install | sh) or pass --offline.",
                file=sys.stderr,
            )
            return 1

    checked = 0
    if online:
        checked = check_invocations(findings)
        check_exit_code_table(findings)

    files = len(glob.glob(SKILLS_GLOB, recursive=True))
    if online:
        version = subprocess.run([GPLAY, "version"], capture_output=True, text=True).stdout.strip()
        print(f"checked {files} files and {checked} gplay invocations against {version}")
    else:
        print(f"checked {files} files (offline: command and flag checks skipped)")

    if findings:
        print(f"\n{len(findings)} problem(s):\n", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1
    print("no drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())
