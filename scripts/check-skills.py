#!/usr/bin/env python3

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
PROSE_FILES = ["README.md", ".github/SECURITY.md"]
SKIP_SUBCOMMANDS = {"help", "completion", "version", "install-skills", "exit-codes"}
UNCOVERED_OK = {("init",), ("edits", "status")}
MAX_WORDS = 1500
PLACEHOLDER = re.compile(r"[<>…\[\]{}$]")
COMMAND_WORD = re.compile(r"^[a-z][a-z0-9-]*$")


class Findings(list):
    def add(self, path: str, line: int, message: str) -> None:
        self.append(f"{path}:{line}: {message}")



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
    _, text = help_text(path)
    return frozenset(
        re.findall(r"^\s+(?:-[a-zA-Z], )?(--[a-z0-9][a-z0-9-]*)", text, re.M)
    )


@functools.lru_cache(maxsize=None)
def required_flags(path: tuple[str, ...]) -> frozenset[str]:
    _, text = help_text(path)
    own = text.split("Flags:", 1)[-1].split("Global Flags:", 1)[0]
    return frozenset(
        re.findall(
            r"^\s+(?:-[a-zA-Z], )?(--[a-z0-9][a-z0-9-]*)[^\n]*\(required(?:\)|:)", own, re.M
        )
    )



def check_frontmatter(findings: Findings) -> None:
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
    for path in sorted(glob.glob(SKILLS_GLOB, recursive=True)) + PROSE_FILES:
        inside = False
        for number, line in enumerate(open(path, encoding="utf-8"), start=1):
            if line.startswith("```"):
                inside = not inside
                continue
            if not inside and "—" in line:
                findings.add(path, number, "em dash in prose; use a comma, colon, semicolon or parens")


def check_catalogue(findings: Findings) -> None:
    path = "README.md"
    text = open(path, encoding="utf-8").read()
    listed = set(re.findall(r"^\| \[`[a-z0-9-]+`\]\(skills/([a-z0-9-]+)/SKILL\.md\)", text, re.M))
    shipped = {os.path.basename(os.path.dirname(p)) for p in glob.glob("skills/*/SKILL.md")}
    for name in sorted(shipped - listed):
        findings.add(path, 1, f"catalogue has no row for skills/{name}")
    for name in sorted(listed - shipped):
        findings.add(path, 1, f"catalogue links skills/{name}, which does not exist")


def check_size(findings: Findings) -> None:
    for path in sorted(glob.glob(SKILLS_GLOB, recursive=True)):
        words = len(open(path, encoding="utf-8").read().split())
        if words > MAX_WORDS:
            findings.add(
                path, 1,
                f"{words} words, ceiling is {MAX_WORDS}: cut what --help or "
                f"gplay-cli-usage already says",
            )


def invocations(path: str):
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
            if not PLACEHOLDER.search(segment):
                missing = required_flags(tuple(resolved)) - used
                if "--dry-run" in used:
                    missing -= {"--confirm"}
                for flag in sorted(missing):
                    findings.add(
                        path, number,
                        f"gplay {' '.join(resolved)} requires {flag} (its --help says so)",
                    )
    return checked


def leaves(path: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    found: set[tuple[str, ...]] = set()
    for sub in subcommands(path):
        if not path and sub in SKIP_SUBCOMMANDS:
            continue
        child = (*path, sub)
        if help_text(child)[1] == help_text(path)[1]:
            continue
        below = subcommands(child)
        found |= leaves(child) if below else {child}
    return found


def check_coverage(findings: Findings) -> None:
    corpus = "\n".join(
        open(path, encoding="utf-8").read()
        for path in sorted(glob.glob(SKILLS_GLOB, recursive=True))
    )
    missing = sorted(
        leaf for leaf in leaves()
        if leaf not in UNCOVERED_OK and " ".join(leaf) not in corpus
    )
    if not missing:
        return
    by_group: dict[str, list[str]] = {}
    for leaf in missing:
        by_group.setdefault(leaf[0], []).append(" ".join(leaf))
    for group, cmds in sorted(by_group.items()):
        findings.add(
            "skills", 0,
            f"no skill documents: {', '.join('gplay ' + c for c in cmds)} "
            f"(add it to a skill, or to UNCOVERED_OK in this script)",
        )


def check_exit_code_table(findings: Findings) -> None:
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



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="skip the checks that need gplay")
    args = parser.parse_args()

    findings = Findings()
    check_frontmatter(findings)
    check_relative_links(findings)
    check_no_em_dash(findings)
    check_catalogue(findings)
    check_size(findings)

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
        check_coverage(findings)
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
