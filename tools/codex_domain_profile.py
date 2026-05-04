#!/usr/bin/env python3
"""
Recommend Codex-only development domain profiles.

This tool is read-only. It does not install MCP servers, plugins, or edit any
Claude/Codex home configuration.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]

PROFILES = {
    "ide": {
        "name": "IDE / Developer Tool",
        "path": "docs/domain-profiles/ide-devtool.md",
        "keywords": ["ide", "editor", "lsp", "language server", "refactor", "debugger", "developer tool"],
        "codex_only_candidates": ["GitHub", "Playwright", "Context7", "Serena/LSP"],
    },
    "app": {
        "name": "App / Program",
        "path": "docs/domain-profiles/app-program.md",
        "keywords": ["app", "program", "saas", "dashboard", "cli", "desktop", "mobile"],
        "codex_only_candidates": ["GitHub", "Playwright", "Vercel", "Supabase/Firebase"],
    },
    "game": {
        "name": "Game Development",
        "path": "docs/domain-profiles/game-dev.md",
        "keywords": ["game", "webgl", "canvas", "phaser", "three", "r3f", "sprite"],
        "codex_only_candidates": ["Game Studio", "Playwright", "browser-use"],
    },
    "media": {
        "name": "Video / Media Tool",
        "path": "docs/domain-profiles/media-tool.md",
        "keywords": ["video", "media", "timeline", "ffmpeg", "audio", "codec", "render", "preview", "cache", "export"],
        "codex_only_candidates": ["Playwright", "GitHub", "ffmpeg/media MCP"],
    },
}


def score_profile(query: str, profile: dict[str, object]) -> int:
    normalized = query.lower()
    score = 0
    for keyword in profile["keywords"]:  # type: ignore[index]
        keyword_text = str(keyword).lower()
        if " " in keyword_text:
            score += int(keyword_text in normalized)
        else:
            score += int(bool(re.search(r"\b" + re.escape(keyword_text) + r"\b", normalized)))
    return score


def recommend(query: str) -> list[dict[str, object]]:
    scored = []
    for key, profile in PROFILES.items():
        score = score_profile(query, profile)
        scored.append({"id": key, "score": score, **profile})
    return sorted(scored, key=lambda item: (-int(item["score"]), str(item["id"])))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Describe the project, for example: 'browser game with level editor'.")
    parser.add_argument("--profile", choices=sorted(PROFILES), help="Print one profile.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    if args.profile:
        items = [{"id": args.profile, "score": 1, **PROFILES[args.profile]}]
    elif args.query:
        items = recommend(args.query)
    else:
        items = [{"id": key, "score": 0, **value} for key, value in PROFILES.items()]

    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0

    for item in items:
        profile_path = WORKSPACE / str(item["path"])
        print(f"{item['id']}: {item['name']} (score={item['score']})")
        print(f"  doc: {profile_path}")
        print("  Codex-only candidates: " + ", ".join(item["codex_only_candidates"]))  # type: ignore[arg-type]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
