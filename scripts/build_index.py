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


def body_intro(text: str) -> tuple[str, str]:
    """(first H1, first paragraph after it) from a SKILL.md body.

    Used as the per-skill README's subtitle, so a human landing on the folder
    sees the same promise the agent sees, instead of a second hand-written
    summary that quietly disagrees with the skill.
    """
    end = text.find("\n---", 3)
    body = text[end + 4:] if end > 0 else text
    title = ""
    para: list[str] = []
    seen_heading = False
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            if para:
                break
            continue
        if line.startswith("#"):
            if para:
                break
            if line.startswith("# ") and not seen_heading:
                title = line[2:].strip()
                seen_heading = True
            continue
        if line.startswith(("|", "```", ">", "-", "*")):
            if para:
                break
            continue
        para.append(line)
    return title, " ".join(para)


def human_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


ROLE_BY_DIR = {
    "references": "reference notes the agent loads when it needs the detail",
    "scripts": "helper scripts the skill runs",
    "templates": "templates it fills in",
    "assets": "assets",
}


def role_of(rel: str) -> str:
    if rel == "SKILL.md":
        return "the skill itself — the agent reads this"
    if rel == "README.md":
        return "this page"
    head = rel.split("/")[0]
    return ROLE_BY_DIR.get(head, "supporting file")


def collect() -> list[dict]:
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(skill_md)
        title, intro = body_intro(text)
        files = sorted(
            str(p.relative_to(skill_md.parent)).replace("\\", "/")
            for p in skill_md.parent.rglob("*")
            if p.is_file() and p.name != "README.md"
        )
        entries = [
            {
                "path": f,
                "size": human_size((skill_md.parent / f).stat().st_size),
                "role": role_of(f),
            }
            for f in files
        ]
        skills.append({
            "dir": skill_md.parent.name,
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "version": meta.get("version", ""),
            "author": meta.get("author", ""),
            "license": meta.get("license", ""),
            "title": title,
            "intro": shorten(intro, 420),
            "files": files,
            "entries": entries,
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
        # relative link: GitHub renders the folder's README, which is the point
        link = f"[`{s['dir']}`]({s['path']}/)"
        lines.append(f"| {link} | {shorten(s['description']) or '—'} | {s['version'] or '—'} |")
    lines.append("")
    lines.append(f"*{len(skills)} skills, indexed by `scripts/build_index.py`. "
                 "Every skill folder has its own README; CI fails if any of them "
                 "drifts from `skills/`.*")
    return "\n".join(lines)


def render_skill_readme(s: dict) -> str:
    """One README per skill folder — the human front door for an agent-facing file."""
    meta_bits = [f"`{s['version']}`" if s["version"] else "", s["license"], s["author"]]
    meta = " · ".join(b for b in meta_bits if b)

    parts = [f"# {s['title'] or s['dir']}", ""]
    if s["description"]:
        parts += [f"> {s['description']}", ""]
    if s["intro"]:
        parts += [s["intro"], ""]
    if meta:
        parts += [meta, ""]

    parts += [
        f"**You read this. The agent reads [`SKILL.md`](SKILL.md).** That file is the",
        "actual skill — the trigger, the commands, the pitfalls. This page is the front",
        "door: what it is, how to install it, and what else is in the folder.",
        "",
        "## Install",
        "",
        "```bash",
        f"hermes skills install nghialele/hermes-skills/{s['dir']}",
        "```",
        "",
        "Or just copy the folder:",
        "",
        "```bash",
        f"cp -r skills/{s['dir']} ~/.hermes/skills/{s['dir']}",
        "```",
        "",
        "## What's inside",
        "",
        "| File | Size | Role |",
        "| --- | --- | --- |",
    ]
    for e in s["entries"]:
        parts.append(f"| [`{e['path']}`]({e['path']}) | {e['size']} | {e['role']} |")

    parts += [
        "",
        "## Part of",
        "",
        f"[hermes-skills]({REPO_URL}) — my agent's skill shelf. WTFPL, do what you want;",
        "read it before you run it, because these are instructions for something with a",
        "terminal.",
        "",
    ]
    return "\n".join(parts)


def write_skill_readmes(skills: list[dict]) -> list[str]:
    """Write skills/<name>/README.md for each skill. Returns the changed paths."""
    changed = []
    for s in skills:
        target = SKILLS_DIR / s["dir"] / "README.md"
        text = render_skill_readme(s)
        if target.exists() and target.read_text(encoding="utf-8") == text:
            continue
        target.write_text(text, encoding="utf-8", newline="\n")
        changed.append(str(target.relative_to(ROOT)).replace("\\", "/"))
    return changed


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
        stale += write_skill_readmes(skills)
        after_index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        after_readme = README.read_text(encoding="utf-8")
        if before_index != after_index:
            stale.append("skills.json")
        if before_readme != after_readme:
            stale.append("README.md")
        if stale:
            print(f"✗ stale: {', '.join(stale)} — run `python scripts/build_index.py`")
            return 1
        print(f"✓ index and {len(skills)} skill READMEs are up to date")
        return 0

    changed = []
    if write_index(skills):
        changed.append("skills.json")
    if write_readme(skills):
        changed.append("README.md")
    changed += write_skill_readmes(skills)
    print(f"{len(skills)} skills; updated: {', '.join(changed) or 'nothing (already current)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
