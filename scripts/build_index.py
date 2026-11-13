#!/usr/bin/env python3
"""Rebuild the skill index in README.md and skills.json from skills/*/SKILL.md.

Stdlib only, no dependencies, no network. Two modes:

    python scripts/build_index.py           # rewrite README table + skills.json
    python scripts/build_index.py --check   # exit 1 if either is stale (CI)
    python scripts/build_index.py --lint    # exit 1 if a SKILL.md is malformed (CI)

The frontmatter parser here is deliberately dumb: it reads flat `key: value`
lines until the closing `---`. That is exactly the subset these skills use, and
it means the repo never needs a YAML library to keep its own index honest.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"
INDEX = ROOT / "skills.json"
START = "<!-- SKILLS:START -->"
END = "<!-- SKILLS:END -->"
REPO_URL = "https://github.com/nghialele/hermes-skills"


def parse_frontmatter(path: Path) -> dict:
    """Flat `key: value` pairs from a SKILL.md frontmatter block."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value[:1] in {'"', "'"} and value[-1:] == value[:1] and len(value) > 1:
            value = value[1:-1]
        data[key] = value
    return data


def collect() -> list[dict]:
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        meta = parse_frontmatter(skill_md)
        files = sorted(
            str(p.relative_to(skill_md.parent)).replace("\\", "/")
            for p in skill_md.parent.rglob("*")
            if p.is_file()
        )
        skills.append({
            "dir": skill_md.parent.name,
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "version": meta.get("version", ""),
            "author": meta.get("author", ""),
            "license": meta.get("license", ""),
            "files": files,
            "path": f"skills/{skill_md.parent.name}",
        })
    return skills


def shorten(text: str, limit: int = 150) -> str:
    """First sentence, capped. Keeps the table readable without lying about it."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in (". ", " — ", "; "):
        idx = cut.rfind(sep)
        if idx > 60:
            return cut[: idx + 1].rstrip() + " …"
    return cut.rstrip() + " …"


def render_table(skills: list[dict]) -> str:
    lines = [
        "| Skill | What it does | v |",
        "| --- | --- | --- |",
    ]
    for s in skills:
        link = f"[`{s['dir']}`]({REPO_URL}/tree/main/{s['path']})"
        lines.append(f"| {link} | {shorten(s['description']) or '—'} | {s['version'] or '—'} |")
    lines.append("")
    lines.append(f"*{len(skills)} skills, indexed by `scripts/build_index.py`. "
                 "CI fails if this table drifts from `skills/`.*")
    return "\n".join(lines)


def write_readme(skills: list[dict]) -> bool:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        sys.exit(f"README.md is missing the {START} / {END} markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{START}\n{render_table(skills)}\n{END}{tail}"
    if new == text:
        return False
    README.write_text(new, encoding="utf-8", newline="\n")
    return True


def write_index(skills: list[dict]) -> bool:
    payload = {
        "repo": REPO_URL,
        "count": len(skills),
        "skills": [
            {k: s[k] for k in ("name", "path", "version", "author", "license", "description", "files")}
            for s in skills
        ],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if INDEX.exists() and INDEX.read_text(encoding="utf-8") == text:
        return False
    INDEX.write_text(text, encoding="utf-8", newline="\n")
    return True


def lint(skills: list[dict]) -> list[str]:
    problems = []
    for s in skills:
        if not s["name"]:
            problems.append(f"{s['path']}: frontmatter has no `name`")
        elif s["name"] != s["dir"]:
            problems.append(f"{s['path']}: name '{s['name']}' != directory '{s['dir']}'")
        if not s["description"]:
            problems.append(f"{s['path']}: frontmatter has no `description`")
        if not s["license"]:
            problems.append(f"{s['path']}: frontmatter has no `license`")
        if "SKILL.md" not in s["files"]:
            problems.append(f"{s['path']}: no SKILL.md")
    if not skills:
        problems.append("skills/: nothing found — is the layout skills/<name>/SKILL.md?")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if the index is stale")
    ap.add_argument("--lint", action="store_true", help="fail if a SKILL.md is malformed")
    args = ap.parse_args()

    skills = collect()

    if args.lint:
        problems = lint(skills)
        if problems:
            print("\n".join(f"✗ {p}" for p in problems))
            return 1
        print(f"✓ {len(skills)} skills look well-formed")
        return 0

    if args.check:
        stale = []
        before_index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        before_readme = README.read_text(encoding="utf-8")
        write_index(skills)
        write_readme(skills)
        after_index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        after_readme = README.read_text(encoding="utf-8")
        if before_index != after_index:
            stale.append("skills.json")
        if before_readme != after_readme:
            stale.append("README.md")
        if stale:
            print(f"✗ stale index: {', '.join(stale)} — run `python scripts/build_index.py`")
            return 1
        print(f"✓ index is up to date ({len(skills)} skills)")
        return 0

    changed = []
    if write_index(skills):
        changed.append("skills.json")
    if write_readme(skills):
        changed.append("README.md")
    print(f"{len(skills)} skills; updated: {', '.join(changed) or 'nothing (already current)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
