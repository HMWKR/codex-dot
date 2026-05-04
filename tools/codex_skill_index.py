#!/usr/bin/env python3
"""
Generate an AI-readable index for the active Codex user skills.

The script reads $HOME/.agents/skills/*/SKILL.md and writes a Markdown guide
plus a JSON index into this repository. It is read-only for the skill root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


HOME = Path.home()
WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS_ROOT = HOME / ".agents" / "skills"
DEFAULT_MARKDOWN = WORKSPACE / "docs" / "skills-index.md"
DEFAULT_JSON = WORKSPACE / "docs" / "skills-index.json"


@dataclass
class SkillEntry:
    directory: str
    name: str
    description: str
    category: str
    priority: str
    path: str
    line_count: int
    sha256: str


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.DOTALL)
    if not match:
        return {}
    values: dict[str, str] = {}
    current_key: str | None = None
    block_lines: list[str] = []
    for line in match.group(1).splitlines():
        if current_key and (line.startswith(" ") or line.startswith("\t")):
            block_lines.append(line.strip())
            continue
        if current_key:
            values[current_key] = " ".join(block_lines).strip()
            current_key = None
            block_lines = []
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            current_key = key
            block_lines = []
        else:
            values[key] = value.strip("'\"")
    if current_key:
        values[current_key] = " ".join(block_lines).strip()
    return values


def category_for(directory: str, description: str) -> str:
    text = f"{directory} {description}".lower()
    if directory == "_core":
        return "core"
    if directory.startswith("source-command-"):
        return "command-bridge"
    if directory.startswith("think-") or directory in {"what", "what-ce", "cynefin", "ooda", "first-principles", "ce-advisor", "deep-analysis-mode"}:
        return "reasoning"
    if directory.startswith("agent-teams") or directory in {"agent-architect", "pipeline-orchestrator", "project-bootstrapper", "project-kickstart", "continuous-qa-loop", "insight-sentinel"}:
        return "orchestration"
    if directory.startswith("playwright") or directory in {"infra-audit", "security-audit", "webapp-testing", "web-design-guidelines"}:
        return "validation"
    if directory in {"docx", "pdf", "ppt-study", "xlsx"}:
        return "documents"
    if directory.startswith("vercel") or "next.js" in text or "react" in text:
        return "web-platform"
    if directory in {"architect", "js-refactor-cleanup-skill", "unused-code-refactor-suggester", "domain-researcher", "domain-expert-analysis", "ux-pattern-researcher"}:
        return "engineering"
    return "support"


def priority_for(directory: str, category: str) -> str:
    if directory in {"_core", "what", "architect"} or directory.startswith("source-command-"):
        return "P0"
    if category in {"reasoning", "orchestration", "validation"}:
        return "P1"
    if category in {"engineering", "web-platform", "documents"}:
        return "P2"
    return "P3"


def scan_skills(root: Path) -> list[SkillEntry]:
    entries: list[SkillEntry] = []
    if not root.exists():
        return entries
    for skill_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue
        text = read_utf8(skill_path)
        values = parse_frontmatter(text)
        directory = skill_dir.name
        description = " ".join((values.get("description") or "").split())
        category = category_for(directory, description)
        entries.append(
            SkillEntry(
                directory=directory,
                name=values.get("name") or directory,
                description=description,
                category=category,
                priority=priority_for(directory, category),
                path=f"$HOME/.agents/skills/{directory}/SKILL.md",
                line_count=text.count("\n") + (1 if text else 0),
                sha256=sha256(skill_path),
            )
        )
    return entries


def build_json(entries: list[SkillEntry]) -> dict[str, object]:
    categories = Counter(entry.category for entry in entries)
    priorities = Counter(entry.priority for entry in entries)
    return {
        "schema_version": "1.0.0",
        "source": "$HOME/.agents/skills",
        "generated_by": "tools/codex_skill_index.py",
        "skills_count": len(entries),
        "categories": dict(sorted(categories.items())),
        "priorities": dict(sorted(priorities.items())),
        "entries": [asdict(entry) for entry in entries],
    }


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def build_markdown(entries: list[SkillEntry]) -> str:
    grouped: dict[str, list[SkillEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.category].append(entry)

    lines: list[str] = [
        "# Codex Skill Index",
        "",
        "이 문서는 활성 Codex 사용자 스킬을 AI가 빠르게 라우팅할 수 있도록 만든 인덱스다.",
        "원본 스킬 본문은 Git에 복사하지 않고, `$HOME/.agents/skills/*/SKILL.md`의 frontmatter와 해시만 기록한다.",
        "",
        "## Summary",
        "",
        f"- Skills: {len(entries)}",
        f"- Source root: `$HOME/.agents/skills`",
        "- Machine-readable index: `docs/skills-index.json`",
        "- Regenerate: `python3 tools/codex_skill_index.py`",
        "",
        "## Category Map",
        "",
        "| Category | Count | Primary use |",
        "|---|---:|---|",
    ]
    category_use = {
        "core": "공통 SSoT와 하네스 핵심 규칙",
        "command-bridge": "Claude command 의도를 Codex skill로 호출하는 bridge",
        "reasoning": "문제 정의, 사고 프레임, 의사결정",
        "orchestration": "멀티 에이전트, 프로젝트 부트스트랩, QA 루프",
        "validation": "테스트, 보안, 인프라, UI/UX 검증",
        "documents": "문서, PDF, PPT, 스프레드시트 작업",
        "web-platform": "Vercel, React, Next.js, 웹 배포",
        "engineering": "아키텍처, 리팩터링, 도메인 리서치",
        "support": "특수 보조 작업",
    }
    for category in sorted(grouped):
        lines.append(f"| {category} | {len(grouped[category])} | {category_use.get(category, '보조 작업')} |")

    lines.extend(
        [
            "",
            "## Routing Rules",
            "",
            "- 사용자가 `$skill` 또는 명시적 스킬명을 말하면 해당 `SKILL.md`를 먼저 연다.",
            "- 여러 스킬이 맞으면 `reasoning → orchestration → validation → implementation` 순서로 최소 조합만 사용한다.",
            "- 스킬 본문 전체를 한꺼번에 복사하지 말고, frontmatter와 직접 참조된 파일만 progressive disclosure로 읽는다.",
            "- Claude 전용 런타임 표현은 Codex 행동 지침으로 해석하고, Claude 경로에는 쓰지 않는다.",
            "- 스킬 변경 후에는 `python3 tools/codex_skill_index.py`와 verifier를 같이 실행한다.",
            "",
            "## Skills",
            "",
        ]
    )

    for category in sorted(grouped):
        lines.extend([f"### {category}", "", "| Priority | Directory | Skill name | Description | Lines |", "|---|---|---|---|---:|"])
        for entry in sorted(grouped[category], key=lambda item: (item.priority, item.directory)):
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_escape(entry.priority),
                        f"`{markdown_escape(entry.directory)}`",
                        markdown_escape(entry.name),
                        markdown_escape(entry.description),
                        str(entry.line_count),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(
        [
            "## Maintenance",
            "",
            "스킬은 개인 자산이므로 Git에는 본문 전체를 복사하지 않는다. 이 저장소에는 검색, 라우팅, stale 감지를 위한 인덱스만 둔다.",
            "인덱스의 `sha256`은 로컬 활성 스킬과 문서가 맞는지 검증하기 위한 값이며 인증 정보나 세션 정보가 아니다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=DEFAULT_SKILLS_ROOT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()

    entries = scan_skills(args.skills_root)
    if not entries:
        raise SystemExit(f"No SKILL.md files found under {args.skills_root}")

    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(build_markdown(entries), encoding="utf-8")
    args.json_output.write_text(json.dumps(build_json(entries), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"skills": len(entries), "markdown": str(args.markdown_output), "json": str(args.json_output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
