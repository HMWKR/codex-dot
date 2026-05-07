#!/usr/bin/env python3
"""Sync curated workspace skills into the active Codex user skill root.

Dry-run is the default. Use --apply only after inspecting the plan.
"""

from __future__ import annotations

import argparse
import json
import shutil
import stat
from pathlib import Path


HOME = Path.home()
WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = WORKSPACE / "codex" / "skills"
DEFAULT_TARGET = HOME / ".agents" / "skills"
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".toml", ".py", ".sh", ".txt"}
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_FILES = {".DS_Store"}


def is_text(path: Path) -> bool:
    return path.name == "SKILL.md" or path.suffix in TEXT_SUFFIXES


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def iter_skill_dirs(source: Path) -> list[Path]:
    if not source.exists():
        return []
    return sorted(
        path
        for path in source.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def iter_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        files.append(path)
    return files


def validate_utf8(skill_dirs: list[Path]) -> None:
    bad: list[str] = []
    replacement: list[str] = []
    for skill_dir in skill_dirs:
        for path in iter_files(skill_dir):
            if not is_text(path):
                continue
            try:
                text = read_utf8(path)
            except UnicodeDecodeError as exc:
                bad.append(f"{path}: {exc}")
                continue
            if "\ufffd" in text:
                replacement.append(str(path))
    if bad or replacement:
        detail = {"invalid_utf8": bad, "replacement_character": replacement}
        raise SystemExit(json.dumps(detail, ensure_ascii=False, indent=2))


def copy_skill(src: Path, target_root: Path) -> int:
    count = 0
    dst_root = target_root / src.name
    for path in iter_files(src):
        rel = path.relative_to(src)
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--apply", action="store_true", help="write into the target skill root")
    args = parser.parse_args()

    skill_dirs = iter_skill_dirs(args.source)
    validate_utf8(skill_dirs)

    result = {
        "dry_run": not args.apply,
        "source": str(args.source),
        "target": str(args.target),
        "skills": [path.name for path in skill_dirs],
        "files": sum(len(iter_files(path)) for path in skill_dirs),
    }

    if args.apply:
        args.target.mkdir(parents=True, exist_ok=True)
        copied = 0
        for skill_dir in skill_dirs:
            copied += copy_skill(skill_dir, args.target)
        for script in args.target.glob("*/scripts/*.sh"):
            mode = script.stat().st_mode
            script.chmod(mode | stat.S_IXUSR)
        result["copied_files"] = copied

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
