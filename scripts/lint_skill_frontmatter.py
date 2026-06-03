#!/usr/bin/env python3
"""Lint the YAML frontmatter of every skills/*/SKILL.md.

The contract (see README.md "Repo layout") is two required frontmatter
fields:

    ---
    name: <kebab-case, matches the folder name>
    description: <one line, ends with a "Use when …" clause>
    ---

This linter fails (exit 1) if any SKILL.md is missing the frontmatter block
or has a missing / malformed `name` or `description`. It has no third-party
dependencies — stdlib only — so CI needs nothing but `python3`.

Usage:
    python3 scripts/lint_skill_frontmatter.py            # lint the repo
    python3 scripts/lint_skill_frontmatter.py --self-test  # prove the rules
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A skill `name` (and its folder) is a kebab-case slug: lowercase
# alphanumerics joined by single hyphens.
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Descriptions must carry a "Use when" trigger clause so an agent can decide
# relevance — matched case-insensitively, tolerating a hyphen ("use-when").
USE_WHEN_RE = re.compile(r"use[\s-]?when", re.IGNORECASE)

MIN_DESCRIPTION_LEN = 40


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    """Return ({key: value}, None) for the top-level frontmatter block, or
    (None, reason) if the block is absent or unterminated.

    Only simple `key: value` lines are understood (the format this repo
    uses); that is enough to validate `name` and `description`.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing frontmatter: file must start with a '---' line"

    fields: dict[str, str] = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            return fields, None
        m = re.match(r"^([A-Za-z0-9_-]+):\s?(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2)
            # Strip matching surrounding quotes, if any.
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
    return None, "missing frontmatter: no closing '---' line found"


def validate(text: str, expected_name: str | None) -> list[str]:
    """Validate one SKILL.md's text. Returns a list of error strings (empty
    list == valid). `expected_name` is the folder name the `name` field must
    match; pass None to skip the folder-match check (used by --self-test).
    """
    errors: list[str] = []
    fields, reason = parse_frontmatter(text)
    if fields is None:
        return [reason or "unparseable frontmatter"]

    # name --------------------------------------------------------------
    name = fields.get("name")
    if name is None:
        errors.append("missing required field: name")
    elif name == "":
        errors.append("field 'name' is empty")
    elif not NAME_RE.match(name):
        errors.append(
            f"field 'name' is not a kebab-case slug: {name!r}"
        )
    elif expected_name is not None and name != expected_name:
        errors.append(
            f"field 'name' ({name!r}) does not match folder name "
            f"({expected_name!r})"
        )

    # description -------------------------------------------------------
    description = fields.get("description")
    if description is None:
        errors.append("missing required field: description")
    elif description == "":
        errors.append("field 'description' is empty")
    elif len(description) < MIN_DESCRIPTION_LEN:
        errors.append(
            f"field 'description' is too short "
            f"({len(description)} < {MIN_DESCRIPTION_LEN} chars)"
        )
    elif not USE_WHEN_RE.search(description):
        errors.append(
            "field 'description' must contain a 'Use when …' trigger clause"
        )

    return errors


def lint_repo(root: Path) -> int:
    skill_files = sorted(root.glob("skills/*/SKILL.md"))
    if not skill_files:
        print("error: no skills/*/SKILL.md files found", file=sys.stderr)
        return 1

    failed = 0
    for path in skill_files:
        rel = path.relative_to(root)
        expected_name = path.parent.name
        errors = validate(path.read_text(encoding="utf-8"), expected_name)
        if errors:
            failed += 1
            print(f"✗ {rel}")
            for err in errors:
                print(f"    - {err}")
        else:
            print(f"✓ {rel}")

    print()
    total = len(skill_files)
    if failed:
        print(f"FAIL: {failed}/{total} SKILL.md file(s) have frontmatter errors")
        return 1
    print(f"OK: {total}/{total} SKILL.md file(s) pass frontmatter lint")
    return 0


# --- self-test: proves the linter actually rejects malformed frontmatter ---

_GOOD = (
    "---\n"
    "name: gplay-release-flow\n"
    "description: Ship Android releases with gplay. Use when uploading a "
    "build or promoting a release.\n"
    "---\n\n# body\n"
)

_BAD_CASES = {
    "no-frontmatter": "# just a heading\n\nno frontmatter here\n",
    "unterminated": "---\nname: x\ndescription: y\n\n# never closed\n",
    "missing-name": (
        "---\ndescription: A long enough description that mentions Use when "
        "doing things.\n---\n"
    ),
    "missing-description": "---\nname: gplay-release-flow\n---\n",
    "empty-description": "---\nname: gplay-release-flow\ndescription:\n---\n",
    "bad-name-case": (
        "---\nname: Gplay_ReleaseFlow\ndescription: A long enough description "
        "that says Use when.\n---\n"
    ),
    "no-use-when": (
        "---\nname: gplay-release-flow\ndescription: Ship Android releases "
        "through Google Play but this never says the trigger clause.\n---\n"
    ),
    "short-description": (
        "---\nname: gplay-release-flow\ndescription: Use when.\n---\n"
    ),
}


def self_test() -> int:
    failures = 0

    good_errors = validate(_GOOD, "gplay-release-flow")
    if good_errors:
        failures += 1
        print(f"✗ self-test: a valid SKILL.md was rejected: {good_errors}")
    else:
        print("✓ self-test: valid frontmatter accepted")

    for label, text in _BAD_CASES.items():
        # expected_name None for the bad cases that aren't about folder match.
        errors = validate(text, None)
        if errors:
            print(f"✓ self-test: malformed case '{label}' rejected")
        else:
            failures += 1
            print(f"✗ self-test: malformed case '{label}' was NOT rejected")

    # Folder-name mismatch is its own rule.
    mismatch = validate(_GOOD, "some-other-folder")
    if mismatch:
        print("✓ self-test: name/folder mismatch rejected")
    else:
        failures += 1
        print("✗ self-test: name/folder mismatch was NOT rejected")

    print()
    if failures:
        print(f"SELF-TEST FAILED: {failures} assertion(s) failed")
        return 1
    print("SELF-TEST OK")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    # Repo root is the parent of this script's directory (scripts/).
    root = Path(__file__).resolve().parent.parent
    return lint_repo(root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
