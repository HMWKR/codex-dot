#!/usr/bin/env python3
"""
Codex-native harness migration.

This reads the local Claude harness only as a separate Claude-native reference
and writes only to Codex-owned locations when --apply is explicitly passed:
- ~/.codex for Codex config, hooks, rules, scripts, and custom agents
- ~/.agents/skills for Codex user skills

Safety properties:
- dry-run is the default, so cloning and running the tool does not mutate home
- strict UTF-8 validation before and after writes
- timestamped backup with SHA-256 manifest before writes
- no auth/session/plugin-cache migration
- no writes to ~/.claude or other non-Codex runtime directories
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import re
import shutil
import stat
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"
CODEX = HOME / ".codex"
AGENTS_SKILLS = HOME / ".agents" / "skills"
WORKSPACE = Path(__file__).resolve().parents[1]
BACKUP_ROOT = WORKSPACE / "codex-harness-backups"

TEXT_EXTS = {
    ".md",
    ".json",
    ".toml",
    ".py",
    ".js",
    ".sh",
    ".yaml",
    ".yml",
    ".txt",
}

SKILL_SYNC_SKIP_DIRS = {"__pycache__", ".git"}
SKILL_SYNC_SKIP_FILES = {".DS_Store"}

ACTIVE_SKILLS = {
    "_core",
    "continuous-qa-loop",
    "domain-researcher",
    "pipeline-orchestrator",
    "project-bootstrapper",
    "project-kickstart",
    "superpowers",
    "ux-pattern-researcher",
    "webapp-testing",
}

READ_ONLY_AGENTS = {
    "ce-reviewer",
    "codebase-explorer",
    "harness-evaluator",
    "infra-auditor",
}

WRITE_AGENT = "thoughts-writer"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text_candidate(path: Path) -> bool:
    return path.is_file() and (path.suffix in TEXT_EXTS or path.name in {"SKILL.md", "skill.md", "AGENTS.md"})


def iter_text_files(*roots: Path):
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if is_text_candidate(root):
                yield root
            continue
        for path in root.rglob("*"):
            if is_text_candidate(path):
                yield path


def validate_utf8(paths: list[Path], *, fail_on_replacement: bool = True) -> list[str]:
    bad: list[str] = []
    replacement: list[str] = []
    for path in paths:
        try:
            text = path.read_bytes().decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            bad.append(f"{path}: {exc}")
            continue
        if "\ufffd" in text:
            replacement.append(str(path))
    if bad or (replacement and fail_on_replacement):
        details = []
        if bad:
            details.append("invalid UTF-8:\n" + "\n".join(bad[:40]))
        if replacement:
            details.append("contains replacement character U+FFFD:\n" + "\n".join(replacement[:40]))
        raise RuntimeError("\n\n".join(details))
    return replacement


def backup_targets() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    targets = [
        (CODEX / "AGENTS.md", backup_dir / ".codex" / "AGENTS.md"),
        (CODEX / "config.toml", backup_dir / ".codex" / "config.toml"),
        (CODEX / "hooks.json", backup_dir / ".codex" / "hooks.json"),
        (CODEX / "agents", backup_dir / ".codex" / "agents"),
        (CODEX / "rules", backup_dir / ".codex" / "rules"),
        (CODEX / "scripts", backup_dir / ".codex" / "scripts"),
        (AGENTS_SKILLS, backup_dir / ".agents" / "skills"),
    ]

    copied: list[dict[str, str]] = []
    for src, dst in targets:
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dst)
            for path in dst.rglob("*"):
                if path.is_file():
                    copied.append(
                        {
                            "source": str(src / path.relative_to(dst)),
                            "backup": str(path),
                            "sha256": sha256(path),
                        }
                    )
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append({"source": str(src), "backup": str(dst), "sha256": sha256(dst)})

    write_text(
        backup_dir / "manifest.json",
        json.dumps(
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "workspace": str(WORKSPACE),
                "items": copied,
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    return backup_dir


def is_codex_owned_path(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    roots = [CODEX.resolve(), AGENTS_SKILLS.resolve()]
    return any(resolved == root or root in resolved.parents for root in roots)


def restore_backup(backup_dir: Path, *, dry_run: bool) -> dict:
    """Validate and optionally restore files from a migration backup manifest.

    Restore is intentionally conservative: it writes only files listed in the
    manifest and never deletes files that appeared after the backup.
    """

    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"missing backup manifest: {manifest_path}")
    manifest = json.loads(read_text(manifest_path))
    items = manifest.get("items")
    if not isinstance(items, list):
        raise RuntimeError(f"invalid backup manifest items: {manifest_path}")

    planned: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            raise RuntimeError("invalid manifest entry: expected object")
        source_raw = item.get("source")
        backup_raw = item.get("backup")
        expected_hash = item.get("sha256")
        if not all(isinstance(value, str) and value for value in (source_raw, backup_raw, expected_hash)):
            raise RuntimeError("invalid manifest entry: missing source, backup, or sha256")
        source = Path(source_raw).expanduser()
        backup = Path(backup_raw).expanduser()
        if not is_codex_owned_path(source):
            raise RuntimeError(f"refusing to restore non-Codex path: {source}")
        if not backup.exists() or not backup.is_file():
            raise RuntimeError(f"missing backup file: {backup}")
        actual_hash = sha256(backup)
        if actual_hash != expected_hash:
            raise RuntimeError(f"backup hash mismatch: {backup}")
        planned.append({"source": str(source), "backup": str(backup), "sha256": actual_hash})

    if not dry_run:
        for item in planned:
            source = Path(item["source"])
            backup = Path(item["backup"])
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, source)

    return {
        "restore": True,
        "dry_run": dry_run,
        "backup_dir": str(backup_dir),
        "files": len(planned),
        "mode": "manifest-files-only",
        "note": "Restore writes only Codex-owned files listed in manifest and never touches ~/.claude.",
    }


def normalize_codex_terms(text: str) -> str:
    replacements = [
        ("IF CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS ≠ 1:", "IF Codex subagents are unavailable:"),
        ("환경 변수 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS 미설정 시:", "Codex subagents를 사용할 수 없을 때:"),
        ("`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`이 설정되지 않은 경우:", "Codex subagents를 사용할 수 없는 경우:"),
        ("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1?", "Codex subagents available?"),
        ('"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"', '"codex_hooks": true'),
        ("| CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | Agent Teams 활성화 | 0 |", "| Codex subagents | 병렬 서브에이전트 사용 가능 여부 | 사용 가능 시 |"),
        ("| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `0` | Agent Teams 활성화 |", "| `Codex subagents` | 사용 가능 시 | 병렬 서브에이전트 활용 |"),
        ("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "Codex subagents"),
        ("CLAUDE_MODEL", "Codex model"),
        ("CLAUDE_MAX_TURNS", "Codex turn budget"),
        ("~/.Codex/skills", "~/.agents/skills"),
        ("~/.Codex/AGENTS.md", "~/.codex/AGENTS.md"),
        ("~/.Codex/agents", "~/.codex/agents"),
        ("~/.Codex/rules", "~/.codex/rules"),
        ("~/.Codex/projects/*/memory/MEMORY.md", "~/.codex/memories"),
        ("~/.Codex/projects", "~/.codex/memories"),
        ("~/.claude/skills", "~/.agents/skills"),
        ("~/.claude/agents", "~/.codex/agents"),
        ("~/.claude/rules", "~/.codex/rules"),
        ("~/.claude/scripts", "~/.codex/scripts"),
        ("~/.claude/CLAUDE.md", "~/.codex/AGENTS.md"),
        ("~/.claude/settings.local.json", "~/.codex/hooks.json"),
        ("~/.claude/settings.json", "~/.codex/config.toml"),
        ("~/.claude/.mcp.json", "~/.codex/config.toml"),
        ("~/.claude/logs/", "~/.codex/logs/"),
        ("~/.claude/teams/", "~/.codex/teams/"),
        ("~/.claude/tasks/", "~/.codex/tasks/"),
        ("~/.claude/projects", "~/.codex/memories"),
        ("~/.claude/", "~/.codex/"),
        ("$HOME/.claude", "$HOME/.codex"),
        ("CLAUDE_DIR", "CODEX_DIR"),
        (".claude/rules", ".codex/rules"),
        (".claude/skills", ".agents/skills"),
        (".claude/agents", ".codex/agents"),
        (".claude/settings.local.json", ".codex/hooks.json"),
        (".claude/settings.json", ".codex/config.toml"),
        (".claude/", ".codex/"),
        ("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1", "Codex subagents available"),
        ("Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1.", "Use Codex subagents only when explicitly delegated."),
        ("CLAUDE.md", "AGENTS.md"),
        ("Claude Code", "Codex"),
        ("AskUserQuestion", "사용자 확인 질문"),
        ("Task tool", "Codex subagent"),
        ("Agent tool", "Codex subagent"),
        ("TodoWrite", "update_plan"),
        ("Delegate Mode", "delegation workflow"),
        ("Shift+Tab", "explicit delegation trigger"),
        ("argument-hint", "argument hint"),
        ("user_invocable", "user invocable"),
        ("CLAUDE_CODE", "Codex runtime"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


INFRA_AUDIT_SCRIPT = r'''#!/usr/bin/env bash
# infra-audit.sh — Codex 인프라 자동화 구조 검사
# 사용법: bash ~/.agents/skills/infra-audit/scripts/infra-audit.sh [--quick|--focus=AREA]

set -euo pipefail

CODEX_DIR="$HOME/.codex"
SKILLS_DIR="$HOME/.agents/skills"
RESULTS=()
PASS=0
WARN=0
FAIL=0

add_result() {
  local area="$1" id="$2" name="$3" status="$4" detail="$5" harness="$6"
  RESULTS+=("{\"area\":\"$area\",\"id\":\"$id\",\"name\":\"$name\",\"status\":\"$status\",\"detail\":\"$detail\",\"harness\":\"$harness\"}")
  case "$status" in
    PASS) ((PASS+=1)) ;;
    WARN) ((WARN+=1)) ;;
    FAIL) ((FAIL+=1)) ;;
  esac
}

file_lines() {
  if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo "0"; fi
}

check_agents_md() {
  local file="$CODEX_DIR/AGENTS.md"
  if [ -f "$file" ]; then
    add_result "AGENTS.md" "1-1" "글로벌 AGENTS.md 존재" "PASS" "$file" "CE"
    local lines
    lines=$(file_lines "$file")
    if [ "$lines" -ge 40 ] && [ "$lines" -le 140 ]; then
      add_result "AGENTS.md" "1-2" "줄 수 적정성" "PASS" "${lines}줄" "CE"
    else
      add_result "AGENTS.md" "1-2" "줄 수 적정성" "WARN" "${lines}줄" "CE"
    fi
    if grep -q "~/.agents/skills/_core" "$file"; then
      add_result "AGENTS.md" "1-3" "_core 참조" "PASS" "공식 user skill 경로 참조" "CE"
    else
      add_result "AGENTS.md" "1-3" "_core 참조" "WARN" "_core 참조 없음" "CE"
    fi
  else
    add_result "AGENTS.md" "1-1" "글로벌 AGENTS.md 존재" "FAIL" "$file 없음" "CE"
  fi
}

check_hooks() {
  local file="$CODEX_DIR/hooks.json"
  if [ -f "$file" ] && python3 -m json.tool "$file" >/dev/null 2>&1; then
    add_result "Hooks" "2-1" "hooks.json 유효성" "PASS" "JSON 파싱 성공" "SI"
  else
    add_result "Hooks" "2-1" "hooks.json 유효성" "FAIL" "JSON 파싱 실패 또는 파일 없음" "SI"
    return
  fi
  for event in SessionStart PreToolUse PostToolUse UserPromptSubmit Stop; do
    if grep -q "\"$event\"" "$file"; then
      add_result "Hooks" "2-$event" "$event 이벤트" "PASS" "이벤트 존재" "AC,SI"
    else
      add_result "Hooks" "2-$event" "$event 이벤트" "WARN" "이벤트 없음" "AC,SI"
    fi
  done
  if grep -q "anti_loop_guard.py" "$file"; then
    add_result "Hooks" "2-safe" "안전/루프 훅" "PASS" "anti_loop_guard.py 연결" "AC,EL"
  else
    add_result "Hooks" "2-safe" "안전/루프 훅" "WARN" "anti_loop_guard.py 미연결" "AC,EL"
  fi
}

check_skills() {
  if [ -d "$SKILLS_DIR" ]; then
    local total
    total=$(find "$SKILLS_DIR" -mindepth 2 \( -name "SKILL.md" -o -name "skill.md" \) | wc -l | tr -d ' ')
    if [ "$total" -ge 40 ]; then
      add_result "Skills" "3-1" "스킬 자산 수" "PASS" "${total}개" "GC"
    else
      add_result "Skills" "3-1" "스킬 자산 수" "WARN" "${total}개" "GC"
    fi
    if [ -d "$SKILLS_DIR/_core" ]; then
      add_result "Skills" "3-2" "_core 존재" "PASS" "$SKILLS_DIR/_core" "CE"
    else
      add_result "Skills" "3-2" "_core 존재" "FAIL" "_core 없음" "CE"
    fi
  else
    add_result "Skills" "3-1" "스킬 디렉터리" "FAIL" "$SKILLS_DIR 없음" "GC"
  fi
}

check_scripts() {
  local scripts="$CODEX_DIR/scripts"
  for script in anti_loop_guard.py checkpoint_save.py codex_gc.sh; do
    if [ -f "$scripts/$script" ]; then
      add_result "Scripts" "5-$script" "$script" "PASS" "존재" "AC"
    else
      add_result "Scripts" "5-$script" "$script" "WARN" "없음" "AC"
    fi
  done
}

check_agents() {
  local dir="$CODEX_DIR/agents"
  if [ -d "$dir" ]; then
    local count
    count=$(find "$dir" -maxdepth 1 -name "*.toml" | wc -l | tr -d ' ')
    if [ "$count" -ge 5 ]; then
      add_result "Agents" "6-1" "커스텀 에이전트" "PASS" "${count}개" "AC"
    else
      add_result "Agents" "6-1" "커스텀 에이전트" "WARN" "${count}개" "AC"
    fi
  else
    add_result "Agents" "6-1" "커스텀 에이전트" "WARN" "디렉터리 없음" "AC"
  fi
}

check_agents_md
check_hooks
check_skills
check_scripts
check_agents

total=$((PASS + WARN + FAIL))
score=0
if [ "$total" -gt 0 ]; then
  score=$(( (PASS * 100 + WARN * 50) / total ))
fi

printf '{"summary":{"pass":%s,"warn":%s,"fail":%s,"score":%s},"results":[%s]}\n' \
  "$PASS" "$WARN" "$FAIL" "$score" "$(IFS=,; echo "${RESULTS[*]}")"
'''


def rewrite_special_skill_assets() -> None:
    infra_script = AGENTS_SKILLS / "infra-audit" / "scripts" / "infra-audit.sh"
    if infra_script.exists():
        write_text(infra_script, INFRA_AUDIT_SCRIPT, executable=True)


def repair_known_skill_corruption(path: Path, text: str) -> str:
    """Repair known U+FFFD damage in existing Claude skill assets.

    The source bytes are valid UTF-8, but one legacy skill already contains
    literal replacement characters. We repair only context-specific phrases whose
    intended Korean wording is clear from surrounding text.
    """
    try:
        rel = path.relative_to(AGENTS_SKILLS)
    except ValueError:
        return text
    if str(rel) not in {"think-teams/skill.md", "think-teams/SKILL.md"}:
        return text
    repairs = {
        "동적 생성\ufffd\ufffd\ufffd고": "동적 생성하고",
        "다관점 병\ufffd\ufffd\ufffd =": "다관점 병렬 =",
        "스킬 시작 시 반드시 \ufffd\ufffd력:": "스킬 시작 시 반드시 출력:",
        "전\ufffd\ufffd\ufffd가 전원": "전문가 전원",
        "팀으로 사고해\ufffd\ufffd": "팀으로 사고해줘",
        "Cynefin \ufffd\ufffd\ufffd천": "Cynefin 추천",
        "도\ufffd\ufffd\ufffd인": "도메인",
        "TM \ufffd\ufffd원": "TM 전원",
        "└────┬────\ufffd\ufffd\ufffd": "└────┬────┘",
        "Cynefin \ufffd\ufffd\ufffd별": "Cynefin 판별",
        "3-6\ufffd\ufffd": "3-6명",
        "토큰 \ufffd\ufffd략": "토큰 전략",
        "유사 역할 병\ufffd\ufffd\ufffd (": "유사 역할 병합 (",
        "선\ufffd\ufffd": "선정",
        "유\ufffd\ufffd성": "유효성",
        "━━\ufffd\ufffd\ufffd━━━━━━━━━━━━━━━━━━━━━━": "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "출력 파\ufffd\ufffd": "출력 파일",
        "이동 제\ufffd\ufffd": "이동 제안",
        "목적 수\ufffd\ufffd": "목적 수정",
        "미지\ufffd\ufffd\ufffd": "미지원",
        "즉시 실\ufffd\ufffd": "즉시 실행",
    }
    for old, new in repairs.items():
        text = text.replace(old, new)
    return text


def write_global_agents_md() -> None:
    content = """# Codex 글로벌 지침 (CE v2.0 최적화)

> 모든 프로젝트 공통. 프로젝트별 지침은 각 `AGENTS.md`를 우선한다.
> 개인 스킬 위치: `~/.agents/skills`
> Codex 설정 위치: `~/.codex`

## CE 원칙

- **적정 고도**: 너무 추상적이지도, 너무 구체적이지도 않은 수준으로 지시를 유지한다.
- **토큰 위치**: 중요한 지시는 문서 상단과 마지막 요약 위치에 둔다.
- **신호 대 잡음비**: 행동 변화에 기여하지 않는 중복과 장식 문구를 제거한다.
- **4대 실패 모드 방지**: Poisoning, Distraction, Confusion, Clash를 항상 점검한다.
- **Progressive Disclosure**: 상세 절차는 `~/.agents/skills/_core/`와 `~/.codex/rules/`로 분리한다.

## 언어

- 기본 출력은 한국어로 한다.
- 기술문서 스타일을 유지하되, 필요한 설명만 명확하고 간결하게 쓴다.

## 세션 연속성

- 멀티세션 작업은 `checkpoint.md` 또는 `session-handoff.md`를 먼저 확인한다.
- 3단계 이상 작업은 진행 상태를 명시적으로 관리하고, 완료 시 임시 handoff를 정리한다.
- Stop 훅은 `checkpoint.md`를 UTF-8로 저장한다.

## 코드 작성

- 기존 구조와 스타일을 우선한다.
- 파일/심볼/라인을 언급하기 전 실제 파일을 확인한다.
- Magic Number를 피하고, 입력 검증과 호환성 영향을 함께 본다.
- 새 추상화는 중복 감소나 복잡도 축소가 명확할 때만 추가한다.

## 서브에이전트

- 소스 코드 대량 탐색은 가능한 경우 `explorer` 또는 Codex custom agent에 위임한다.
- 직접 읽기 허용: `AGENTS.md`, `session-handoff.md`, `package.json`, 설정 파일, 짧은 문서.
- 위임 결과는 사실 요약으로 받고, 구현 판단은 현재 작업 맥락에서 통합한다.

## 문제 해결

1. 목표를 한 문장으로 재정의한다.
2. 현재 상태와 실패 조건을 실제 파일/로그로 확인한다.
3. 원인을 좁히고, 대안 2개 이상을 비교한다.
4. 승인된 범위 안에서 구현하고 검증한다.
5. 남은 리스크와 후속 작업을 짧게 기록한다.

## 리뷰/테스트/보안

- 리뷰: 정확성, 예외처리, 가독성, 중복, 보안, 성능, 확장성 순서로 본다.
- 테스트: 정상/예외/경계값과 Mock 필요성을 판단한다.
- 보안: 파괴적 명령, 민감정보, 외부 서비스 호출은 사전 확인한다.

## 커밋 메시지

필수 섹션:

```text
## What
## Why
## Impact
Co-Authored-By:
```

## 참조

- 공통 프로토콜: `~/.agents/skills/_core/protocols.md`
- 전문가 역할: `~/.agents/skills/_core/roles.md`
- 안전 규칙: `~/.codex/rules/safety.md`
- 환각 방지: `~/.codex/rules/anti-hallucination.md`
"""
    write_text(CODEX / "AGENTS.md", content)


def copy_rules() -> None:
    src_dir = CLAUDE / "rules"
    dst_dir = CODEX / "rules"
    if not src_dir.exists():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in src_dir.glob("*.md"):
        content = normalize_codex_terms(read_text(src))
        write_text(dst_dir / src.name, content)


def clean_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    front = text[4:end].splitlines()
    body = text[end + 5 :].lstrip("\n")
    kept: list[str] = []
    keep_block = False
    for line in front:
        if line and not line[0].isspace() and ":" in line:
            key = line.split(":", 1)[0].strip()
            keep_block = key in {"name", "description"}
        if keep_block:
            kept.append(line)
    return "---\n" + "\n".join(kept).rstrip() + "\n---\n\n" + body


def is_top_level_skill_entrypoint(path: Path) -> bool:
    return path.name in {"SKILL.md", "skill.md"} and path.parent.parent == AGENTS_SKILLS


def canonicalize_skill_entrypoints() -> None:
    """Ensure top-level user skills use SKILL.md, not skill.md.

    macOS default filesystems are usually case-insensitive, so changing only the
    spelling requires a two-step rename through a temporary filename.
    """

    if not AGENTS_SKILLS.exists():
        return
    for skill_dir in sorted(path for path in AGENTS_SKILLS.iterdir() if path.is_dir()):
        actual_names = {child.name for child in skill_dir.iterdir() if child.is_file()}
        if "SKILL.md" in actual_names:
            continue
        if "skill.md" not in actual_names:
            continue
        lower = skill_dir / "skill.md"
        tmp = skill_dir / ".skill-md-casefix.tmp"
        upper = skill_dir / "SKILL.md"
        if tmp.exists():
            tmp.unlink()
        lower.rename(tmp)
        tmp.rename(upper)


def ensure_skill_frontmatter(path: Path, text: str) -> str:
    if text.startswith("---\n"):
        return clean_frontmatter(text)
    name = path.parent.name
    title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else name
    description = (
        f"{title}. Codex-native skill migrated from Claude source. "
        f"Use when the user asks for {name}, {title}, or the matching workflow."
    )
    return f"---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n\n{text.lstrip()}"


def normalize_skills() -> None:
    if not AGENTS_SKILLS.exists():
        return
    for path in iter_text_files(AGENTS_SKILLS):
        original = read_text(path)
        updated = normalize_codex_terms(original)
        updated = repair_known_skill_corruption(path, updated)
        if is_top_level_skill_entrypoint(path):
            updated = ensure_skill_frontmatter(path, updated)
        if updated != original:
            write_text(path, updated)


def sync_claude_skills() -> dict[str, int]:
    """Copy every Claude skill asset into ~/.agents/skills without deleting Codex-only skills.

    The user's Claude skills are treated as durable source assets. Text files are copied
    byte-for-byte first, then normalized in a later pass so the Codex version keeps the
    same content while using Codex-native paths and naming.
    """
    src_root = CLAUDE / "skills"
    dst_root = AGENTS_SKILLS
    stats = {"copied": 0, "skipped": 0}
    if not src_root.exists():
        return stats
    for src in src_root.rglob("*"):
        rel = src.relative_to(src_root)
        if any(part in SKILL_SYNC_SKIP_DIRS for part in rel.parts):
            stats["skipped"] += 1
            continue
        if src.name in SKILL_SYNC_SKIP_FILES:
            stats["skipped"] += 1
            continue
        dst = dst_root / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        stats["copied"] += 1
    return stats


def migrate_source_commands() -> None:
    commands_dir = CLAUDE / "commands"
    if not commands_dir.exists():
        return
    for src in sorted(commands_dir.glob("*.md")):
        name = src.stem
        raw = normalize_codex_terms(read_text(src))
        desc = "Migrated source command"
        original_body = raw
        if raw.startswith("---\n"):
            end = raw.find("\n---", 4)
            if end != -1:
                front = raw[4:end]
                original_body = raw[end + 5 :].lstrip("\n")
                m = re.search(r"^description:\s*(.+)$", front, flags=re.MULTILINE)
                if m:
                    desc = m.group(1).strip().strip('"')
        skill_dir = AGENTS_SKILLS / f"source-command-{name}"
        content = build_source_command_skill(name, desc, original_body)
        write_text(skill_dir / "SKILL.md", content)


def build_source_command_skill(name: str, desc: str, original_body: str) -> str:
    """Rewrite a Claude command Markdown file as a Codex-native skill."""

    custom = {
        "analyze": source_command_analyze,
        "journal": source_command_journal,
        "orchestrate": source_command_orchestrate,
        "pdca": source_command_pdca,
        "rules": source_command_rules,
    }.get(name)
    if custom:
        return custom(desc)
    return f"""---
name: "source-command-{name}"
description: {json.dumps(desc + " Use when the user asks for the migrated Claude command '" + name + "'.", ensure_ascii=False)}
---

# source-command-{name}

Use this skill when the user asks to run the migrated Claude command `{name}`.

## Codex Invocation

- Natural language trigger: `source-command-{name} 실행`
- Legacy slash syntax such as `/{name}` is treated as a user phrase, not as automatic runtime expansion.
- If the original command expected arguments, infer them from the current request or ask one short question.

## Original Command Body

{original_body.rstrip()}
"""


def source_command_header(name: str, desc: str, triggers: str) -> str:
    return f"""---
name: "source-command-{name}"
description: {json.dumps(desc + " " + triggers, ensure_ascii=False)}
---

# source-command-{name}

> Claude command asset rebuilt as a Codex-native skill.

## Invocation

- Preferred: `source-command-{name} 실행`
- Natural language is supported; slash syntax such as `/{name}` is treated as plain prompt text.
- Claude reference entry: `commands/{name}.md`

"""


def source_command_analyze(desc: str) -> str:
    return source_command_header(
        "analyze",
        desc,
        "Use when the user asks for deep analysis, 심층 분석, careful review, root-cause analysis, or a more rigorous current-task analysis.",
    ) + """## Purpose

Activate a rigorous analysis posture for the current turn. This is not a hidden global mode; it is a skill workflow applied to the current request.

## Codex-native Workflow

1. Restate the goal in one sentence.
2. Identify success criteria, constraints, and likely failure modes.
3. Separate evidence from inference using these markers when useful:
   - `[검증됨]`: confirmed from files, logs, command output, or cited source.
   - `[추정]`: reasonable inference from observed patterns.
   - `[미확인]`: not verified yet.
4. Inspect the relevant files, logs, docs, or command output before making claims.
5. Consider assumptions, counterarguments, hidden variables, and confidence.
6. Present 2 or more options when there is a meaningful design choice.
7. If implementation is requested, use `update_plan` for 3+ step work and verify the result.

## Codex Adjustments

- Do not claim Plan Mode has been entered. Use the current Codex collaboration mode and `update_plan` when useful.
- Do not require exhaustive testing for tiny documentation-only changes; scale verification to risk.
- Follow Codex approval and sandbox rules for destructive commands or writes outside the workspace.

## Output

Use concise Korean technical writing. Put findings and decisions before supporting detail.
"""


def source_command_journal(desc: str) -> str:
    return source_command_header(
        "journal",
        desc,
        "Use when the user asks to write a CE journey, 사고 여정, thinking log, 작업 기록, or post-work context-engineering record.",
    ) + """## Purpose

Create a durable CE(Context Engineering) work journal for the current task.

## When To Write

- The user explicitly asks for `journal`, `source-command-journal`, `사고 여정`, or `CE 기록`.
- A significant implementation, migration, or harness change was completed and the user asks to preserve the reasoning.

## Codex-native Workflow

1. Gather the actual changed files, commands run, and verification results.
2. Summarize context selection: what was read, what was ignored, and why.
3. Record CE failure-mode checks: Poisoning, Distraction, Confusion, Clash.
4. Compare options and state the decision.
5. Record the CE strategies used: Write, Select, Compress, Isolate.
6. Save the journal under `.thoughts/YYYY-MM-DD-{subject}.md` when writing is appropriate.

## File Rules

- Use UTF-8.
- Keep the entry factual and reusable.
- Do not include secrets, session-only noise, or unsupported speculation.
- If `.thoughts/` does not exist, create it only when the user asked to write the journal.

## Template

```markdown
# CE 사고여정: [subject]

## 1. 컨텍스트 수집
## 2. 정보 선택/폐기
## 3. 실패 모드 감지
## 4. 대안 비교 및 결정
## 5. 적용된 CE 전략
## 6. 핵심 통찰
```
"""


def source_command_orchestrate(desc: str) -> str:
    return source_command_header(
        "orchestrate",
        desc,
        "Use when the user explicitly asks for Agent Teams, orchestration, parallel agents, subagents, 팀 구성, or multi-agent delegation.",
    ) + """## Purpose

Coordinate a complex task with an explicit agent-team or orchestration workflow.

## Codex-native Constraint

Use Codex subagents only when the user explicitly asks for subagents, delegation, parallel agent work, or Agent Teams. Complexity alone is not enough.

## Workflow

1. Restate the task and decide whether orchestration is actually requested.
2. Score the work across independence, sequential dependency, risk, size, and file-conflict risk.
3. Choose one pattern:
   - Parallel Specialists: independent work with disjoint file ownership.
   - Pipeline: research or analysis must precede implementation.
   - Research + Implementation: one sidecar explores while the main thread continues.
   - Plan Approval: design needs user approval before writes.
   - Swarm: only for explicitly requested large multi-agent work.
4. Define each agent's role, scope, write ownership, and completion criteria.
5. Continue useful local work while agents run; do not wait unless blocked.
6. Integrate results, verify, and summarize residual risks.

## Rewrites From Claude

- Claude delegation UI modes and keyboard shortcuts are not required Codex controls.
- Claude task/agent tool names map to Codex `spawn_agent` only under the explicit-delegation rule.
- If subagents are unavailable or not allowed, run the same reasoning sequentially in the main thread and say so briefly.

## Agent Prompt Shape

Use four blocks when delegating:

1. Context
2. Role
3. Task and ownership
4. Completion criteria
"""


def source_command_pdca(desc: str) -> str:
    return source_command_header(
        "pdca",
        desc,
        "Use when the user asks for PDCA, gap analysis, 설계 vs 구현 비교, implementation drift, match rate, or iterative improvement.",
    ) + """## Purpose

Compare design intent with actual implementation, quantify the gap, and optionally drive iterative improvement.

## Input Handling

- If the target feature is clear from the user's request, use it.
- If the target is unclear, ask one short question for the feature, design doc, or implementation path.
- Do not rely on Claude command argument placeholders; Codex does not expand them.

## Workflow

1. Find design sources:
   - `docs/`, `design/`, `spec/`, `*.design.md`, `*.spec.md`, `README.md`.
   - If no design source exists, stop and ask the user to provide or select one.
2. Find implementation sources relevant to the target.
3. Compare 7 categories:
   - API endpoints
   - Data model
   - Core features
   - UI/UX flow
   - Environment variables
   - Architecture
   - Coding rules
4. Classify gaps:
   - Missing: designed but not implemented.
   - Added: implemented but not designed.
   - Changed: implemented differently from design.
5. Calculate match rate.
6. If match rate is below 90%, propose prioritized fixes.
7. Implement fixes only when the user requested implementation or approves the proposed changes.
8. Re-run comparison up to 3 loops when implementation is in scope.

## Output

```text
PDCA Gap Analysis
Target: [feature]
Match Rate: [N]%
Compared Items: [N]
Matched: [N]
Missing: [N]
Added: [N]
Changed: [N]
Iterations: [N]/3
```

Use `[검증됨]`, `[추정]`, and `[미확인]` markers for comparison claims.
"""


def source_command_rules(desc: str) -> str:
    return source_command_header(
        "rules",
        desc,
        "Use when the user asks for harness rules, rule references, 하니스 규칙, Codex environment structure, or where instructions live.",
    ) + """## Purpose

Explain the active Codex harness rule hierarchy and where to inspect each source of truth.

## Codex Rule Hierarchy

```text
Layer 0: ~/.codex/AGENTS.md
  Global Codex instructions and CE principles.

Layer 1: ~/.agents/skills/_core/
  Shared roles, protocols, confirmation loops, and team patterns.

Layer 2: ~/.codex/rules/
  Safety, anti-hallucination, loop prevention, insight distribution, and sync rules.

Layer 3: ~/.agents/skills/*/SKILL.md
  Executable skill instructions and domain workflows.

Layer 4: project AGENTS.md
  Project-specific instructions, which override broad global guidance when applicable.
```

## Response Workflow

1. Read the relevant rule file before claiming a specific rule.
2. Prefer paths over paraphrase when the user asks where something lives.
3. Mention that Claude paths belong to the separate Claude-native harness, not active Codex runtime paths.
4. If a referenced path is missing, report it as missing rather than inventing a rule.

## Common References

| Topic | Active Codex path |
|------|-------------------|
| Global instructions | `~/.codex/AGENTS.md` |
| User skills | `~/.agents/skills` |
| Shared protocols | `~/.agents/skills/_core/protocols.md` |
| Expert roles | `~/.agents/skills/_core/roles.md` |
| Safety rules | `~/.codex/rules/safety.md` |
| Anti-hallucination | `~/.codex/rules/anti-hallucination.md` |
| Hooks | `~/.codex/hooks.json` |
| Custom agents | `~/.codex/agents/*.toml` |
"""


def parse_agent_toml(path: Path) -> dict[str, str]:
    try:
        import tomllib

        return tomllib.loads(read_text(path))
    except Exception:
        text = read_text(path)
        name = path.stem
        desc_match = re.search(r'^description\s*=\s*"((?:\\"|[^"])*)"', text, re.MULTILINE)
        body_match = re.search(r'developer_instructions\s*=\s*"""(.*)"""', text, re.DOTALL)
        return {
            "name": name,
            "description": desc_match.group(1) if desc_match else name,
            "developer_instructions": body_match.group(1) if body_match else "",
        }


def toml_literal(value: str) -> str:
    if "'''" not in value:
        return "'''\n" + value.rstrip() + "\n'''"
    return json.dumps(value, ensure_ascii=False)


def normalize_agents() -> None:
    agents_dir = CODEX / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(agents_dir.glob("*.toml")):
        name = path.stem
        data = parse_agent_toml(path)
        body = normalize_codex_terms(str(data.get("developer_instructions", "")))
        sandbox = "read-only" if name in READ_ONLY_AGENTS else "workspace-write"
        note = f"""# Codex-native constraints

- This custom agent runs under Codex subagent semantics.
- Claude `tools` allowlists are preserved as behavior guidance only; they are not a permission boundary.
- Use `~/.agents/skills` for user skills and `~/.codex` for Codex configuration.
- Default sandbox intent for this agent: `{sandbox}`.
"""
        if "Codex-native constraints" not in body:
            body = note + "\n" + body.lstrip()
        if name == WRITE_AGENT and ".thoughts/" not in body[:400]:
            body = body.replace(
                "- Default sandbox intent for this agent: `workspace-write`.",
                "- Default sandbox intent for this agent: `workspace-write`; write only `.thoughts/` artifacts unless explicitly asked otherwise.",
            )
        desc = normalize_codex_terms(str(data.get("description", name)))
        content = (
            f'name = "{name}"\n'
            f'description = {json.dumps(desc, ensure_ascii=False)}\n'
            f'sandbox_mode = "{sandbox}"\n'
            f"developer_instructions = {toml_literal(body)}\n"
        )
        write_text(path, content)


def ensure_toml_table_keys(content: str, table: str, required: dict[str, str]) -> str:
    lines = content.splitlines()
    out: list[str] = []
    in_table = False
    seen = {key: False for key in required}
    table_header = f"[{table}]"
    found_table = False

    for line in lines:
        if re.match(r"^\[.+\]\s*$", line):
            if in_table:
                for key, value in required.items():
                    if not seen[key]:
                        out.append(f"{key} = {value}")
            in_table = line.strip() == table_header
            if in_table:
                found_table = True
                seen = {key: False for key in required}
            out.append(line)
            continue

        if in_table:
            replaced = False
            for key, value in required.items():
                if re.match(rf"^\s*{re.escape(key)}\s*=", line):
                    out.append(f"{key} = {value}")
                    seen[key] = True
                    replaced = True
                    break
            if replaced:
                continue
        out.append(line)

    if in_table:
        for key, value in required.items():
            if not seen[key]:
                out.append(f"{key} = {value}")

    content = "\n".join(out).rstrip()
    if not found_table:
        if content:
            content += "\n\n"
        content += table_header + "\n"
        content += "\n".join(f"{key} = {value}" for key, value in required.items())
    return content.rstrip() + "\n"


def update_config() -> None:
    config_path = CODEX / "config.toml"
    content = read_text(config_path) if config_path.exists() else ""
    content = ensure_toml_table_keys(content, "agents", {"max_threads": "128"})
    content = ensure_toml_table_keys(content, "features", {"codex_hooks": "true", "goals": "true"})
    write_text(config_path, content)


def write_hooks() -> None:
    scripts = CODEX / "scripts"
    hooks = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "printf '프로젝트: %s\\n' \"$(basename \"$PWD\")\"; git status --short 2>/dev/null || printf 'Git 저장소 아님\\n'",
                            "timeout": 5,
                        },
                        {
                            "type": "command",
                            "command": f"python3 {scripts / 'anti_loop_guard.py'} sessionstart",
                            "timeout": 5,
                        },
                    ],
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash|shell|exec_command",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python3 {scripts / 'anti_loop_guard.py'} pretooluse",
                            "timeout": 5,
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash|shell|exec_command",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python3 {scripts / 'anti_loop_guard.py'} posttooluse",
                            "timeout": 5,
                        }
                    ],
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "if [ -f checkpoint.md ]; then printf '[checkpoint] 이전 세션 체크포인트 발견 - checkpoint.md를 읽고 작업을 이어가세요.\\n'; fi",
                            "timeout": 5,
                        }
                    ]
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python3 {scripts / 'checkpoint_save.py'} stop",
                            "timeout": 5,
                            "statusMessage": "세션 종료 체크포인트 저장...",
                        }
                    ]
                }
            ],
        }
    }
    write_text(CODEX / "hooks.json", json.dumps(hooks, ensure_ascii=False, indent=2) + "\n")


ANTI_LOOP_SCRIPT = r'''#!/usr/bin/env python3
"""Codex-native anti-loop and destructive-command guard."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

STATE_FILE_NAME = ".codex/anti-loop-state.json"
PERSISTENT_FILE = Path.home() / ".codex" / "anti-loop-persistent.json"
TOOL_REPEAT_WARN_THRESHOLD = 2
TOOL_REPEAT_BLOCK_THRESHOLD = 4
HISTORY_MAX = 80

DANGEROUS_RE = re.compile(
    r"(rm\s+(-rf|-fr|-r\s+-f)|"
    r"git\s+(reset\s+--hard|push\s+(-f|--force)|clean\s+-f)|"
    r"DROP\s+(TABLE|DATABASE)|TRUNCATE\s+TABLE|"
    r"DELETE\s+FROM\s+\w+\s*;|find\s+.*-delete|chmod\s+777)",
    re.IGNORECASE,
)


def read_hook_input() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def command_from_payload(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    value = payload.get("command") or os.environ.get("TOOL_INPUT_COMMAND", "")
    return value if isinstance(value, str) else ""


def state_path() -> Path:
    return Path.cwd() / STATE_FILE_NAME


def load_json(path: Path, default: dict) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        # Hooks must not fail just because the current directory cannot persist state.
        try:
            fallback = Path.home() / ".codex" / "anti-loop-state-fallback.json"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            fallback.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


def deny(reason: str) -> None:
    print(json.dumps({"permissionDecision": "deny", "reason": reason}, ensure_ascii=False))
    sys.exit(2)


def allow(message: str = "") -> None:
    if message:
        print(message)
    sys.exit(0)


def update_history(event: str, command: str) -> dict:
    state = load_json(state_path(), {"history": [], "updated_at": None})
    history = state.setdefault("history", [])
    history.append({"event": event, "command": command, "time": int(time.time())})
    del history[:-HISTORY_MAX]
    state["updated_at"] = int(time.time())
    save_json(state_path(), state)
    persistent = load_json(PERSISTENT_FILE, {"projects": {}})
    project = str(Path.cwd())
    pdata = persistent.setdefault("projects", {}).setdefault(project, {"events": 0, "last_seen": 0})
    pdata["events"] = int(pdata.get("events", 0)) + 1
    pdata["last_seen"] = int(time.time())
    save_json(PERSISTENT_FILE, persistent)
    return state


def repeated_command_count(history: list, command: str) -> int:
    if not command:
        return 0
    count = 0
    for item in reversed(history):
        if item.get("command") == command:
            count += 1
        else:
            break
    return count


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    payload = read_hook_input()
    command = command_from_payload(payload)

    if event == "pretooluse":
        if DANGEROUS_RE.search(command):
            deny("위험한 명령어 감지: 사용자 확인이 필요합니다.")
        state = update_history(event, command)
        repeat_count = repeated_command_count(state.get("history", []), command)
        if repeat_count == TOOL_REPEAT_WARN_THRESHOLD:
            print("[anti-loop] 같은 명령이 반복되고 있습니다. 실패 원인을 확인하세요.")
        elif repeat_count >= TOOL_REPEAT_BLOCK_THRESHOLD:
            deny("같은 명령이 과도하게 반복되어 루프 가능성이 있습니다.")
        return 0

    update_history(event, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


CHECKPOINT_SCRIPT = r'''#!/usr/bin/env python3
"""Codex-native checkpoint writer for Stop hooks."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git(*args: str, timeout: int = 3) -> str:
    try:
        result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def project_root() -> Path:
    root = run_git("rev-parse", "--show-toplevel")
    return Path(root) if root else Path.cwd()


def git_changes() -> str:
    parts = []
    unstaged = run_git("diff", "--stat", "HEAD")
    staged = run_git("diff", "--stat", "--cached")
    untracked = run_git("ls-files", "--others", "--exclude-standard")
    if unstaged:
        parts.append("### 수정됨 (unstaged)\n```\n" + unstaged + "\n```")
    if staged:
        parts.append("### 스테이징됨\n```\n" + staged + "\n```")
    if untracked:
        files = untracked.splitlines()
        if len(files) > 10:
            files = files[:10] + [f"... 외 {len(files) - 10}개"]
        parts.append("### 새 파일 (untracked)\n```\n" + "\n".join(files) + "\n```")
    return "\n\n".join(parts) if parts else "변경 사항 없음"


def main() -> int:
    trigger = sys.argv[1] if len(sys.argv) > 1 else "manual"
    root = project_root()
    branch = run_git("branch", "--show-current") or "unknown"
    commits = run_git("log", "-3", "--oneline", "--no-decorate") or "git log 실패"
    content = f"""# Checkpoint - 작업 상태 스냅샷

> 자동 생성됨 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 트리거: {trigger}
> 다음 세션에서 이 파일을 읽고 작업을 이어가세요.

## 브랜치: `{branch}`

## 최근 커밋
```
{commits}
```

## 변경 사항
{git_changes()}

---
*이 파일은 Codex Stop 훅에 의해 자동 갱신됩니다. 필요하면 `.gitignore`에 추가하세요.*
"""
    (root / "checkpoint.md").write_text(content, encoding="utf-8")
    print(f"[checkpoint] saved: {root / 'checkpoint.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


CODEX_GC_SCRIPT = r'''#!/bin/bash
set -euo pipefail

# Codex GC helper. Conservative by default; pass --apply to delete old local cache files.

CODEX_DIR="$HOME/.codex"
DRY_RUN=true
if [ "${1:-}" = "--apply" ]; then
  DRY_RUN=false
fi

echo "=== Codex GC ${DRY_RUN:+dry-run} ==="

if [ -d "$CODEX_DIR/tmp" ]; then
  count=$(find "$CODEX_DIR/tmp" -type f -mtime +14 2>/dev/null | wc -l | tr -d ' ')
  echo "tmp/: 14일 이전 파일 ${count}개"
  if [ "$DRY_RUN" = false ] && [ "$count" -gt 0 ]; then
    find "$CODEX_DIR/tmp" -type f -mtime +14 -delete 2>/dev/null
  fi
fi

find "$CODEX_DIR/scripts" "$HOME/.agents/skills" -name "__pycache__" -type d 2>/dev/null | while read -r dir; do
  echo "__pycache__: $dir"
  if [ "$DRY_RUN" = false ]; then
    rm -rf "$dir"
  fi
done
'''


INSIGHT_SCRIPT = r'''#!/usr/bin/env python3
"""Codex insight collector placeholder.

Automatic LLM-based insight extraction is intentionally disabled in the Codex-native
harness because Claude prompt hooks are not a 1:1 lifecycle match. Use the
source-command-journal skill or thoughts-writer agent for explicit CE journaling.
"""

print("[insight] 자동 인사이트 수집은 비활성화되어 있습니다. 필요 시 source-command-journal을 사용하세요.")
'''


def write_scripts() -> None:
    scripts = CODEX / "scripts"
    write_text(scripts / "anti_loop_guard.py", ANTI_LOOP_SCRIPT, executable=True)
    write_text(scripts / "checkpoint_save.py", CHECKPOINT_SCRIPT, executable=True)
    write_text(scripts / "codex_gc.sh", CODEX_GC_SCRIPT, executable=True)
    write_text(scripts / "insight_collector.py", INSIGHT_SCRIPT, executable=True)


def validate_formats() -> None:
    toml_files = [CODEX / "config.toml", *sorted((CODEX / "agents").glob("*.toml"))]
    try:
        import tomllib

        for path in toml_files:
            tomllib.loads(read_text(path))
    except ModuleNotFoundError:
        bundled_py = HOME / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "bin" / "python3"
        if not bundled_py.exists():
            raise RuntimeError("TOML validation needs Python 3.11+ tomllib or bundled Codex Python")
        code = "import pathlib, sys, tomllib\nfor p in sys.argv[1:]: tomllib.loads(pathlib.Path(p).read_text(encoding='utf-8'))\n"
        result = subprocess.run([str(bundled_py), "-c", code, *map(str, toml_files)], text=True, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"TOML validation failed: {result.stdout}{result.stderr}")
    except Exception as exc:
        raise RuntimeError(f"TOML validation failed: {exc}") from exc
    json.loads(read_text(CODEX / "hooks.json"))
    for path in (CODEX / "scripts").glob("*.py"):
        py_compile.compile(str(path), doraise=True)
    for path in (CODEX / "scripts").glob("*.sh"):
        subprocess.run(["bash", "-n", str(path)], check=True)


def simulate_hooks() -> None:
    guard = CODEX / "scripts" / "anti_loop_guard.py"
    safe_command = f"printf codex-hook-safe-{datetime.now().strftime('%H%M%S%f')}"
    safe = subprocess.run(
        ["python3", str(guard), "pretooluse"],
        input=json.dumps({"tool_input": {"command": safe_command}}),
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if safe.returncode != 0:
        raise RuntimeError(f"safe hook command failed: {safe.stderr} {safe.stdout}")
    for command in ("rm -rf /tmp/example", "git reset --hard", "DROP TABLE users"):
        result = subprocess.run(
            ["python3", str(guard), "pretooluse"],
            input=json.dumps({"tool_input": {"command": command}}),
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
        if result.returncode != 2:
            raise RuntimeError(f"dangerous command was not denied: {command!r} rc={result.returncode}")


def residue_scan() -> dict[str, list[str]]:
    patterns = [".claude", "CLAUDE.md", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "~/.Codex/skills"]
    findings: dict[str, list[str]] = {p: [] for p in patterns}
    roots = [CODEX / "AGENTS.md", CODEX / "hooks.json", CODEX / "config.toml", CODEX / "agents", CODEX / "rules", CODEX / "scripts", AGENTS_SKILLS]
    for path in iter_text_files(*roots):
        text = read_text(path)
        for pattern in patterns:
            if pattern in text:
                findings[pattern].append(str(path))
    return {k: v for k, v in findings.items() if v}


def run_codex_validator() -> str:
    py = HOME / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "bin" / "python3"
    migrator = CODEX / "vendor_imports" / "skills" / "skills" / ".curated" / "migrate-to-codex" / "scripts" / "migrate-to-codex.py"
    if not py.exists() or not migrator.exists():
        return "skipped: bundled Python or migrate-to-codex script not found"
    result = subprocess.run([str(py), str(migrator), "--validate-target", str(CODEX)], text=True, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def migrate(dry_run: bool) -> dict:
    pre_paths = list(iter_text_files(CLAUDE / "agents", CLAUDE / "commands", CLAUDE / "rules", CLAUDE / "scripts", CLAUDE / "skills", CODEX / "AGENTS.md", CODEX / "config.toml", CODEX / "hooks.json", CODEX / "agents", AGENTS_SKILLS))
    source_replacements = validate_utf8(pre_paths, fail_on_replacement=False)
    if dry_run:
        return {
            "dry_run": True,
            "preflight_files": len(pre_paths),
            "reference_replacement_characters": source_replacements,
            "note": "Claude reference U+FFFD characters are allowed in dry-run; Codex active harness validation still fails if any remain after apply.",
        }

    backup_dir = backup_targets()
    write_global_agents_md()
    copy_rules()
    write_scripts()
    skill_sync = sync_claude_skills()
    canonicalize_skill_entrypoints()
    normalize_skills()
    rewrite_special_skill_assets()
    migrate_source_commands()
    normalize_agents()
    update_config()
    write_hooks()

    post_paths = list(iter_text_files(CODEX / "AGENTS.md", CODEX / "config.toml", CODEX / "hooks.json", CODEX / "agents", CODEX / "rules", CODEX / "scripts", AGENTS_SKILLS))
    validate_utf8(post_paths, fail_on_replacement=True)
    validate_formats()
    simulate_hooks()
    codex_validator = run_codex_validator()
    residue = residue_scan()
    report = {
        "dry_run": False,
        "backup_dir": str(backup_dir),
        "postflight_files": len(post_paths),
        "skill_sync": skill_sync,
        "codex_validator": codex_validator,
        "residue": residue,
    }
    write_text(backup_dir / "migration-report.json", json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Read and validate only. This is also the default.")
    parser.add_argument("--apply", action="store_true", help="Write to Codex-owned home paths after backup and validation.")
    parser.add_argument("--restore", type=Path, metavar="BACKUP_DIR", help="Validate and optionally restore a previous Codex backup manifest.")
    args = parser.parse_args()
    if args.dry_run and args.apply:
        parser.error("--dry-run and --apply cannot be used together")
    if args.restore:
        result = restore_backup(args.restore, dry_run=not args.apply)
    else:
        result = migrate(dry_run=not args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
