#!/usr/bin/env python3
"""
Inventory Claude harness assets and Codex-native target readiness.

This is intentionally read-only. It scans local Claude/Codex configuration,
checks skill entrypoints and frontmatter, and emits a Markdown report that can
be committed as the rebuild baseline.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


HOME = Path.home()

CLAUDE_ROOT = HOME / ".claude"
CODEX_ROOT = HOME / ".codex"
SOURCE_SKILL_ROOT = CLAUDE_ROOT / "skills"
TARGET_SKILL_ROOT = HOME / ".agents" / "skills"

TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".sh",
}

IGNORED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "cache",
    "logs",
    "projects",
    "sessions",
    "shell-snapshots",
    "shell_snapshots",
    "statsig",
    "todos",
    "codex-runs",
    "plugins",
    "vendor_imports",
}

CLAUDE_RUNTIME_MARKERS = {
    "AskUserQuestion": "interactive question tool",
    "Task tool": "Claude task/subagent tool",
    "Agent tool": "Claude agent tool",
    "TodoWrite": "Claude todo tool",
    "allowed-tools": "Claude tool allowlist frontmatter",
    "argument-hint": "Claude command argument hint",
    "user_invocable": "Claude user invocation flag",
    "CLAUDE_CODE": "Claude environment variable",
    "CLAUDE.md": "Claude instruction filename",
    ".claude": "Claude config path",
    "Shift+Tab": "Claude UI shortcut",
    "Delegate Mode": "Claude UI mode",
}

CODEX_FRONTMATTER_KEYS = {"name", "description"}


@dataclass
class TextFileStatus:
    path: Path
    utf8_ok: bool
    replacement_count: int = 0
    error: str | None = None


@dataclass
class SkillStatus:
    root: Path
    name: str
    entrypoint: Path | None
    entrypoint_case: str
    has_frontmatter: bool
    has_name: bool
    has_description: bool
    description: str = ""
    frontmatter_keys: set[str] = field(default_factory=set)
    unsupported_keys: set[str] = field(default_factory=set)
    marker_counts: Counter[str] = field(default_factory=Counter)
    replacement_count: int = 0
    line_count: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def needs_entrypoint_normalization(self) -> bool:
        return self.entrypoint_case == "skill.md"

    @property
    def needs_frontmatter(self) -> bool:
        return not (self.has_frontmatter and self.has_name and self.has_description)

    @property
    def needs_runtime_rewrite(self) -> bool:
        return bool(self.marker_counts)

    @property
    def status(self) -> str:
        if self.entrypoint is None:
            return "missing"
        if self.needs_frontmatter:
            return "frontmatter"
        if self.needs_entrypoint_normalization or self.needs_runtime_rewrite:
            return "normalize"
        return "ready"

    @property
    def quality_score(self) -> int:
        score = 100
        if self.entrypoint is None:
            return 0
        if self.needs_frontmatter:
            score -= 35
        if self.needs_entrypoint_normalization:
            score -= 15
        if self.needs_runtime_rewrite:
            score -= 30
        if self.unsupported_keys:
            score -= min(15, 5 * len(self.unsupported_keys))
        if self.replacement_count:
            score -= 40
        if self.line_count > 260:
            score -= 8
        if self.has_description and len(self.description) < 40:
            score -= 8
        return max(0, score)

    @property
    def quality_grade(self) -> str:
        score = self.quality_score
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        return "D"


def iter_text_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        if path.suffix in TEXT_SUFFIXES:
            yield path


def read_text_status(path: Path) -> tuple[TextFileStatus, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return TextFileStatus(path=path, utf8_ok=False, error=str(exc)), ""
    return (
        TextFileStatus(
            path=path,
            utf8_ok=True,
            replacement_count=text.count("\ufffd"),
        ),
        text,
    )


def exact_child_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {child.name for child in path.iterdir() if child.is_file()}


def choose_skill_entrypoint(skill_dir: Path) -> tuple[Path | None, str]:
    names = exact_child_names(skill_dir)
    if "SKILL.md" in names:
        return skill_dir / "SKILL.md", "SKILL.md"
    if "skill.md" in names:
        return skill_dir / "skill.md", "skill.md"
    return None, "missing"


def parse_frontmatter(text: str) -> tuple[bool, dict[str, str], set[str]]:
    if not text.startswith("---"):
        return False, {}, set()
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.DOTALL)
    if not match:
        return False, {}, set()
    body = match.group(1)
    values: dict[str, str] = {}
    keys: set[str] = set()
    block_key: str | None = None
    block_lines: list[str] = []
    for line in body.splitlines():
        if block_key and (line.startswith(" ") or line.startswith("\t")):
            block_lines.append(line.strip())
            continue
        if block_key:
            values[block_key] = "\n".join(block_lines).strip()
            block_key = None
            block_lines = []
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        keys.add(key)
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            block_key = key
            block_lines = []
            continue
        values[key] = value.strip("'\"")
    if block_key:
        values[block_key] = "\n".join(block_lines).strip()
    return True, values, keys


def marker_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for marker in CLAUDE_RUNTIME_MARKERS:
        count = text.count(marker)
        if count:
            counts[marker] = count
    return counts


def scan_skill_root(root: Path) -> list[SkillStatus]:
    statuses: list[SkillStatus] = []
    if not root.exists():
        return statuses
    for skill_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if skill_dir.name == "_shared":
            continue
        entrypoint, entrypoint_case = choose_skill_entrypoint(skill_dir)
        text = ""
        replacement_count = 0
        line_count = 0
        has_frontmatter = False
        values: dict[str, str] = {}
        keys: set[str] = set()
        markers: Counter[str] = Counter()
        notes: list[str] = []

        if entrypoint is not None:
            status, text = read_text_status(entrypoint)
            if not status.utf8_ok:
                notes.append(f"invalid utf-8: {status.error}")
            replacement_count = status.replacement_count
            line_count = text.count("\n") + (1 if text else 0)
            has_frontmatter, values, keys = parse_frontmatter(text)
            markers = marker_counts(text)
        else:
            notes.append("missing SKILL.md/skill.md entrypoint")

        unsupported_keys = keys - CODEX_FRONTMATTER_KEYS
        statuses.append(
            SkillStatus(
                root=root,
                name=skill_dir.name,
                entrypoint=entrypoint,
                entrypoint_case=entrypoint_case,
                has_frontmatter=has_frontmatter,
                has_name=bool(values.get("name")),
                has_description=bool(values.get("description")),
                description=values.get("description", ""),
                frontmatter_keys=keys,
                unsupported_keys=unsupported_keys,
                marker_counts=markers,
                replacement_count=replacement_count,
                line_count=line_count,
                notes=notes,
            )
        )
    return statuses


def classify_claude_file(path: Path) -> str:
    rel = path.relative_to(CLAUDE_ROOT)
    first = rel.parts[0] if rel.parts else ""
    if first == "skills":
        return "skills"
    if first == "commands":
        return "commands"
    if first == "agents":
        return "agents"
    if first == "rules":
        return "rules"
    if first == "scripts":
        return "scripts"
    if path.name.startswith("settings"):
        return "settings"
    if path.name == "CLAUDE.md":
        return "global-instructions"
    return "other"


def summarize_text_files(root: Path) -> tuple[Counter[str], list[TextFileStatus]]:
    counts: Counter[str] = Counter()
    statuses: list[TextFileStatus] = []
    for path in iter_text_files(root):
        status, _ = read_text_status(path)
        statuses.append(status)
        if root == CLAUDE_ROOT:
            counts[classify_claude_file(path)] += 1
        else:
            counts[path.suffix or "no-suffix"] += 1
    return counts, statuses


def command_files() -> list[Path]:
    root = CLAUDE_ROOT / "commands"
    if not root.exists():
        return []
    return sorted(root.glob("*.md"))


def agent_files() -> list[Path]:
    root = CLAUDE_ROOT / "agents"
    if not root.exists():
        return []
    return sorted(root.glob("*.md"))


def json_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report validation context.
        return f"invalid: {exc}"
    return "valid"


def status_count(skills: list[SkillStatus]) -> Counter[str]:
    return Counter(skill.status for skill in skills)


def marker_totals(skills: list[SkillStatus]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for skill in skills:
        totals.update(skill.marker_counts)
    return totals


def format_marker_counts(counts: Counter[str]) -> str:
    if not counts:
        return "-"
    return ", ".join(f"{name}:{count}" for name, count in counts.most_common())


def priority_group(name: str) -> str:
    if name.startswith("source-command-"):
        return "P0 command bridge"
    if name.startswith("think-") or name in {"what", "what-ce", "cynefin", "ooda", "first-principles"}:
        return "P1 reasoning"
    if name.startswith("agent-teams") or name in {"agent-architect", "architect"}:
        return "P1 agent teams"
    if name in {"infra-audit", "security-audit", "continuous-qa-loop"} or "qa" in name:
        return "P2 validation"
    return "P3 support"


def build_report() -> str:
    claude_counts, claude_text_statuses = summarize_text_files(CLAUDE_ROOT)
    codex_counts, codex_text_statuses = summarize_text_files(CODEX_ROOT)
    source_skills = scan_skill_root(SOURCE_SKILL_ROOT)
    target_skills = scan_skill_root(TARGET_SKILL_ROOT)

    source_names = {skill.name for skill in source_skills}
    target_names = {skill.name for skill in target_skills}
    target_only = sorted(target_names - source_names)
    source_only = sorted(source_names - target_names)

    target_lowercase = [skill for skill in target_skills if skill.entrypoint_case == "skill.md"]
    target_frontmatter = [skill for skill in target_skills if skill.needs_frontmatter]
    target_runtime = [skill for skill in target_skills if skill.needs_runtime_rewrite]
    replacement_files = [status for status in claude_text_statuses + codex_text_statuses if status.replacement_count]
    utf8_failures = [status for status in claude_text_statuses + codex_text_statuses if not status.utf8_ok]

    grouped: dict[str, list[SkillStatus]] = defaultdict(list)
    for skill in target_skills:
        if skill.status != "ready":
            grouped[priority_group(skill.name)].append(skill)

    lines: list[str] = []
    lines.append("# Claude/Codex Harness Inventory")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("This report is generated from local Claude/Codex files and is used as the rebuild baseline without modifying either harness.")
    lines.append("")
    lines.append("| Area | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Claude text files scanned | {sum(claude_counts.values())} |")
    lines.append(f"| Codex text files scanned | {sum(codex_counts.values())} |")
    lines.append(f"| Claude skill directories | {len(source_skills)} |")
    lines.append(f"| Codex active skill directories | {len(target_skills)} |")
    lines.append(f"| Claude command files | {len(command_files())} |")
    lines.append(f"| Claude agent files | {len(agent_files())} |")
    lines.append(f"| UTF-8 failures | {len(utf8_failures)} |")
    lines.append(f"| Files containing `U+FFFD` | {len(replacement_files)} |")
    lines.append("")

    lines.append("## Claude Corpus Shape")
    lines.append("")
    lines.append("| Category | Files |")
    lines.append("|---|---:|")
    for category, count in sorted(claude_counts.items()):
        lines.append(f"| {category} | {count} |")
    lines.append("")

    lines.append("## Codex Active Skill Readiness")
    lines.append("")
    counts = status_count(target_skills)
    lines.append("| Status | Count | Meaning |")
    lines.append("|---|---:|---|")
    lines.append(f"| ready | {counts['ready']} | Codex entrypoint/frontmatter are clean and no Claude runtime markers were found in entrypoint |")
    lines.append(f"| normalize | {counts['normalize']} | File case or Claude runtime language needs Codex-native rewrite |")
    lines.append(f"| frontmatter | {counts['frontmatter']} | Missing or incomplete Codex skill metadata |")
    lines.append(f"| missing | {counts['missing']} | No `SKILL.md` or `skill.md` entrypoint |")
    lines.append("")

    lines.append("## Main Findings")
    lines.append("")
    lines.append(f"- Codex active harness has {len(target_lowercase)} skill entrypoints named `skill.md`; these should be renamed or regenerated as `SKILL.md`.")
    lines.append(f"- Codex active harness has {len(target_frontmatter)} skills with missing or incomplete frontmatter.")
    lines.append(f"- Codex active harness has {len(target_runtime)} skills whose entrypoint still contains Claude runtime markers.")
    lines.append(f"- Codex-only skills: {', '.join(target_only) if target_only else '-'}")
    lines.append(f"- Claude-only skills: {', '.join(source_only) if source_only else '-'}")
    lines.append(f"- `~/.claude/settings.json`: {json_status(CLAUDE_ROOT / 'settings.json')}")
    lines.append(f"- `~/.claude/settings.local.json`: {json_status(CLAUDE_ROOT / 'settings.local.json')}")
    lines.append(f"- `~/.codex/hooks.json`: {json_status(CODEX_ROOT / 'hooks.json')}")
    lines.append("")

    lines.append("## Codex Skill Quality Signals")
    lines.append("")
    if target_skills:
        average_score = sum(skill.quality_score for skill in target_skills) / len(target_skills)
        low_score = [skill for skill in target_skills if skill.quality_score < 90]
        lines.append(f"- Average quality score: {average_score:.1f} / 100")
        lines.append(f"- Skills below A grade: {len(low_score)}")
        lines.append("")
        lines.append("| Skill | Grade | Score | Signals |")
        lines.append("|---|---:|---:|---|")
        for skill in sorted(target_skills, key=lambda item: (item.quality_score, item.name))[:12]:
            signals: list[str] = []
            if skill.needs_frontmatter:
                signals.append("frontmatter")
            if skill.needs_entrypoint_normalization:
                signals.append("entrypoint case")
            if skill.needs_runtime_rewrite:
                signals.append("runtime markers")
            if skill.unsupported_keys:
                signals.append("unsupported keys")
            if skill.replacement_count:
                signals.append("U+FFFD")
            if skill.line_count > 260:
                signals.append("large entrypoint")
            if skill.has_description and len(skill.description) < 40:
                signals.append("short description")
            lines.append(f"| `{skill.name}` | {skill.quality_grade} | {skill.quality_score} | {', '.join(signals) if signals else '-'} |")
    else:
        lines.append("No Codex skills found.")
    lines.append("")

    lines.append("## Claude Runtime Marker Totals")
    lines.append("")
    totals = marker_totals(target_skills)
    lines.append("| Marker | Count | Codex rewrite |")
    lines.append("|---|---:|---|")
    if totals:
        for marker, count in totals.most_common():
            lines.append(f"| `{marker}` | {count} | {CLAUDE_RUNTIME_MARKERS[marker]} |")
    else:
        lines.append("| - | 0 | - |")
    lines.append("")

    lines.append("## Normalization Queue")
    lines.append("")
    lines.append("| Priority | Skill | Status | Entrypoint | Runtime markers | Notes |")
    lines.append("|---|---|---|---|---|---|")
    for group in sorted(grouped):
        for skill in sorted(grouped[group], key=lambda item: item.name):
            notes = list(skill.notes)
            if skill.needs_entrypoint_normalization:
                notes.append("rename/regenerate as SKILL.md")
            if skill.needs_frontmatter:
                notes.append("add name/description frontmatter")
            if skill.unsupported_keys:
                notes.append("review frontmatter keys: " + ", ".join(sorted(skill.unsupported_keys)))
            if skill.replacement_count:
                notes.append(f"contains U+FFFD x{skill.replacement_count}")
            lines.append(
                "| "
                + " | ".join(
                    [
                        group,
                        f"`{skill.name}`",
                        skill.status,
                        skill.entrypoint_case,
                        format_marker_counts(skill.marker_counts),
                        "; ".join(notes) if notes else "-",
                    ]
                )
                + " |"
            )
    lines.append("")

    lines.append("## Claude Commands")
    lines.append("")
    lines.append("| Command file | Codex skill |")
    lines.append("|---|---|")
    for path in command_files():
        target = f"source-command-{path.stem}"
        lines.append(f"| `{path.relative_to(CLAUDE_ROOT)}` | `{target}` |")
    lines.append("")

    lines.append("## Claude Agents")
    lines.append("")
    lines.append("| Agent file | Codex agent |")
    lines.append("|---|---|")
    for path in agent_files():
        lines.append(f"| `{path.relative_to(CLAUDE_ROOT)}` | `~/.codex/agents/{path.stem}.toml` |")
    lines.append("")

    lines.append("## Encoding Exceptions")
    lines.append("")
    if utf8_failures or replacement_files:
        lines.append("| File | Issue |")
        lines.append("|---|---|")
        for status in utf8_failures:
            lines.append(f"| `{status.path}` | invalid UTF-8: {status.error} |")
        for status in replacement_files:
            lines.append(f"| `{status.path}` | contains U+FFFD x{status.replacement_count} |")
    else:
        lines.append("No UTF-8 failures or replacement characters were found in scanned files.")
    lines.append("")

    lines.append("## Next Actions")
    lines.append("")
    if not target_lowercase and not target_frontmatter and not target_runtime:
        lines.append("1. Treat the structural Codex skill migration as complete.")
        lines.append("2. Continue semantic 3-pass reviews for high-value skills before changing behavior.")
        lines.append("3. Keep Claude-native and Codex-native active harnesses separate.")
        lines.append("4. Defer external GitHub harness imports until the Codex active harness is judged stable.")
        lines.append("5. Re-run this inventory and update this report after each rebuild batch.")
    else:
        lines.append("1. Run the 3-pass review for each rebuild batch.")
        lines.append("2. Normalize Codex skill entrypoints to `SKILL.md`.")
        lines.append("3. Add missing Codex frontmatter, starting with P1 agent/team skills.")
        lines.append("4. Rewrite Claude runtime markers into Codex-native instructions.")
        lines.append("5. Re-run this inventory and update this report after each rebuild batch.")
    lines.append("")

    lines.append("## 3-Pass Review Gate")
    lines.append("")
    lines.append("| Pass | Purpose | Output |")
    lines.append("|---|---|---|")
    lines.append("| Pass 1 | Extract original intent from Claude Markdown without rewriting it. | Trigger, workflow, tools, outputs, confirmation points. |")
    lines.append("| Pass 2 | Map the extracted intent to Codex-native primitives. | Skill metadata, subagent policy, hook/script behavior, unsupported semantics. |")
    lines.append("| Pass 3 | Check omissions, misunderstandings, and conflicts. | Final rewrite checklist and residual risks. |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write Markdown report to this path.")
    args = parser.parse_args()

    report = build_report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
