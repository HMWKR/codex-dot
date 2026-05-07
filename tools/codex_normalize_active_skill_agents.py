#!/usr/bin/env python3
"""
Move an active skill's oversized AGENTS.md reference into references/.

Codex skills use SKILL.md as the executable entrypoint. Some imported skills
also carry a large AGENTS.md as a compiled reference, which trips the Codex
validator's AGENTS.md size warning. This tool preserves that content under
references/ and updates the skill entrypoint reference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ACTIVE_SKILLS = Path.home() / ".agents" / "skills"
DEFAULT_REFERENCE = Path("references/full-compiled-document.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", help="Active skill directory name under ~/.agents/skills")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE, help="Relative destination for the compiled reference")
    parser.add_argument("--apply", action="store_true", help="Mutate the active skill. Defaults to dry-run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.reference.is_absolute() or ".." in args.reference.parts:
        raise SystemExit("--reference must be a safe relative path")

    skill_dir = ACTIVE_SKILLS / args.skill
    skill_md = skill_dir / "SKILL.md"
    source = skill_dir / "AGENTS.md"
    destination = skill_dir / args.reference
    actions: list[str] = []

    if not skill_dir.is_dir():
        raise SystemExit(f"missing skill directory: {skill_dir}")
    if not skill_md.is_file():
        raise SystemExit(f"missing SKILL.md: {skill_md}")

    text = skill_md.read_text(encoding="utf-8")
    old_reference = "`AGENTS.md`"
    new_reference = f"`{args.reference.as_posix()}`"
    updated_text = text.replace(old_reference, new_reference)
    if updated_text != text:
        actions.append(f"update {skill_md} reference to {args.reference.as_posix()}")

    if source.exists():
        if destination.exists() and source.read_bytes() != destination.read_bytes():
            raise SystemExit(f"destination already exists with different content: {destination}")
        actions.append(f"move {source} to {destination}")
    elif not destination.exists():
        raise SystemExit(f"neither source nor destination reference exists for {args.skill}")

    if args.apply:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.exists() and not destination.exists():
            source.replace(destination)
        elif source.exists() and destination.exists():
            source.unlink()
        if updated_text != text:
            skill_md.write_text(updated_text, encoding="utf-8")

    print(json.dumps({"apply": args.apply, "skill": args.skill, "actions": actions}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
