#!/usr/bin/env python3
"""
Detailed verification suite for the Codex-native harness.

This script is read-only for the real harness target. Hook simulations run in
temporary directories so Stop/session files do not touch the current project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 on some macOS installs.
    tomllib = None


HOME = Path.home()
WORKSPACE = Path(__file__).resolve().parents[1]
CODEX = HOME / ".codex"
CLAUDE = HOME / ".claude"
SKILLS = HOME / ".agents" / "skills"

TEXT_SUFFIXES = {".md", ".json", ".toml", ".yaml", ".yml", ".py", ".js", ".sh", ".txt", ".html"}
TARGET_TEXT_SUFFIXES = {".md", ".json", ".toml", ".yaml", ".yml", ".py", ".js", ".sh", ".txt"}
KNOWN_SOURCE_REPLACEMENT = {CLAUDE / "skills" / "think-teams" / "skill.md"}

RUNTIME_MARKERS = [
    "AskUserQuestion",
    "Task tool",
    "Agent tool",
    "TodoWrite",
    "allowed-tools",
    "argument-hint",
    "user_invocable",
    "CLAUDE_CODE",
    "CLAUDE.md",
    "Shift+Tab",
    "Delegate Mode",
]

ALLOWED_HOOK_EVENTS = {"PreToolUse", "PostToolUse", "SessionStart", "UserPromptSubmit", "Stop"}
REQUIRED_HOOK_EVENTS = {"PreToolUse", "PostToolUse", "SessionStart", "UserPromptSubmit", "Stop"}
RESIDUE_PATTERNS = [
    r"\.claude",
    r"CLAUDE\.md",
    r"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
    r"~/.Codex/skills",
    r"~/.Codex/rules",
    r"~/.Codex",
]

SECRET_PATTERNS = {
    "OpenAI API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Anthropic API key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "Stripe live secret": re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
}


@dataclass
class Check:
    area: str
    name: str
    status: str
    detail: str


class HtmlSmokeParser(HTMLParser):
    pass


def add(checks: list[Check], area: str, name: str, status: str, detail: str) -> None:
    checks.append(Check(area=area, name=name, status=status, detail=detail))


def iter_files(root: Path, suffixes: set[str]) -> Iterable[Path]:
    if not root.exists():
        return
    if root.is_file():
        if root.suffix in suffixes or root.name in {"SKILL.md", "AGENTS.md"}:
            yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in suffixes or path.name in {"SKILL.md", "AGENTS.md"}:
            yield path


def read_utf8(path: Path) -> tuple[bool, str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return False, "", str(exc)
    return True, text, ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_frontmatter(text: str) -> tuple[bool, dict[str, str]]:
    if not text.startswith("---\n"):
        return False, {}
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.DOTALL)
    if not match:
        return False, {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return True, values


def parse_toml_text(text: str) -> dict[str, object]:
    if tomllib is not None:
        return tomllib.loads(text)

    data: dict[str, object] = {}
    current: dict[str, object] = data
    multiline_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if multiline_key:
            if '"""' in line:
                multiline_key = None
            continue
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]")
            current = data.setdefault(section, {})  # type: ignore[assignment]
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"""') and not value.endswith('"""'):
            current[key] = value
            multiline_key = key
        elif value in {"true", "false"}:
            current[key] = value == "true"
        elif re.fullmatch(r"-?\d+", value):
            current[key] = int(value)
        else:
            current[key] = value.strip("'\"")
    return data


def exact_file_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {child.name for child in path.iterdir() if child.is_file()}


def check_workspace_files(checks: list[Check]) -> None:
    paths = [
        WORKSPACE / "README.md",
        WORKSPACE / "AI_BOOTSTRAP.md",
        WORKSPACE / "codex-harness.manifest.json",
        WORKSPACE / ".gitignore",
    ]
    paths += sorted((WORKSPACE / "docs").glob("*"))
    paths += sorted((WORKSPACE / "docs" / "templates").glob("*"))
    paths += sorted((WORKSPACE / "docs" / "domain-profiles").glob("*"))
    paths += sorted((WORKSPACE / ".github" / "workflows").glob("*.yml"))
    paths += sorted((WORKSPACE / ".github" / "workflows").glob("*.yaml"))
    paths += sorted((WORKSPACE / "tools").glob("*.py"))
    bad: list[str] = []
    replacement: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        ok, text, error = read_utf8(path)
        if not ok:
            bad.append(f"{path}: {error}")
        elif "\ufffd" in text:
            replacement.append(str(path))
    if bad or replacement:
        add(checks, "workspace", "UTF-8 and replacement characters", "FAIL", "; ".join(bad + replacement[:10]))
    else:
        add(checks, "workspace", "UTF-8 and replacement characters", "PASS", f"{len([p for p in paths if p.is_file()])} files checked")

    html_files = sorted((WORKSPACE / "docs").glob("*.html"))
    html_errors: list[str] = []
    for path in html_files:
        try:
            parser = HtmlSmokeParser()
            parser.feed(path.read_text(encoding="utf-8"))
            parser.close()
        except Exception as exc:  # noqa: BLE001 - report parser context.
            html_errors.append(f"{path}: {exc}")
    if html_errors:
        add(checks, "workspace", "HTML smoke parse", "FAIL", "; ".join(html_errors))
    else:
        add(checks, "workspace", "HTML smoke parse", "PASS", f"{len(html_files)} html files parsed")


def check_documentation_sync(checks: list[Check]) -> None:
    required = {
        WORKSPACE / "README.md": ["AI_BOOTSTRAP.md", "codex-harness.manifest.json", "codex_harness_verify.py", "harness-verification-report.md", "external-harness-import-notes.md", "agents.max_threads", "harness-boundary-classification.md", "codex_domain_profile.py"],
        WORKSPACE / "AI_BOOTSTRAP.md": ["macOS", "Windows", "dry-run", "--apply", "Do not modify `~/.claude`", "codex-harness.manifest.json"],
        WORKSPACE / "codex-harness.manifest.json": ["ai_first", "owned_targets", "expected_hook_events", "mcp_policy", "macos_dry_run", "windows_dry_run"],
        WORKSPACE / "docs" / "github-workflow.md": ["codex_harness_verify.py", "harness-verification-report.md", "external-harness-import-notes.md", "release-checklist.md"],
        WORKSPACE / "docs" / "codex-native-rebuild-plan.md": ["harness-verification-report.md", "external-harness-import-notes.md", "harness-boundary-classification.md", "agents.max_threads", "goals", "FAIL"],
        WORKSPACE / "docs" / "migration-summary.md": ["codex_harness_verify.py", "Harness Verification Report", "external-harness-import-notes.md", "agents.max_threads"],
        WORKSPACE / "docs" / "github-harness-candidate-analysis.html": ["external-harness-import-notes.md"],
        WORKSPACE / "docs" / "external-harness-import-notes.md": ["Batch 4A", "Batch 4B", "Batch 4C", "Batch 4D"],
        WORKSPACE / "docs" / "harness-boundary-classification.md": ["Claude-native active harness", "Codex-native active harness", "Project control plane", "Codex-only apply policy"],
        WORKSPACE / "docs" / "release-checklist.md": ["Secret/PII preflight", "Restore dry-run", "Idempotency", "MCP"],
        WORKSPACE / "docs" / "macos-terminal-codex-setup.md": ["AppTranslocation", "/Applications/Codex.app", "/opt/homebrew/bin/codex", "codex mcp list"],
        WORKSPACE / "docs" / "developer-domain-extension-review.md": ["IDE", "게임", "영상", "Codex-only"],
        WORKSPACE / "docs" / "codex-only-mcp-plugin-catalog.md": ["Codex-only", "MCP", "Plugin", "Reject"],
        WORKSPACE / "docs" / "domain-profiles" / "ide-devtool.md": ["Symbol graph", "Serena", "Codex-only"],
        WORKSPACE / "docs" / "domain-profiles" / "app-program.md": ["Spec", "rollback", "Codex"],
        WORKSPACE / "docs" / "domain-profiles" / "game-dev.md": ["render loop", "Game Studio", "Playwright"],
        WORKSPACE / "docs" / "domain-profiles" / "media-tool.md": ["Timeline", "ffmpeg", "Large file"],
        WORKSPACE / "docs" / "templates" / "spec.md": ["Problem", "Success Criteria"],
        WORKSPACE / "docs" / "templates" / "design.md": ["Architecture", "Verification"],
        WORKSPACE / "docs" / "templates" / "tasks.md": ["Task", "Validation"],
        WORKSPACE / "docs" / "templates" / "pdca-status.schema.json": ["plan", "do", "check", "act"],
    }
    missing: list[str] = []
    for path, needles in required.items():
        ok, text, error = read_utf8(path)
        if not ok:
            missing.append(f"{path}: {error}")
            continue
        for needle in needles:
            if needle not in text:
                missing.append(f"{path}: missing {needle!r}")
    if missing:
        add(checks, "workspace", "documentation sync", "FAIL", "; ".join(missing))
    else:
        add(checks, "workspace", "documentation sync", "PASS", "verification tool, report, and GitHub gate are documented")


def check_ai_bootstrap_contract(checks: list[Check]) -> None:
    bootstrap_path = WORKSPACE / "AI_BOOTSTRAP.md"
    manifest_path = WORKSPACE / "codex-harness.manifest.json"
    readme_path = WORKSPACE / "README.md"
    issues: list[str] = []

    ok, bootstrap_text, error = read_utf8(bootstrap_path)
    if not ok:
        issues.append(f"{bootstrap_path}: {error}")
        bootstrap_text = ""

    ok, readme_text, error = read_utf8(readme_path)
    if not ok:
        issues.append(f"{readme_path}: {error}")
        readme_text = ""

    if bootstrap_text:
        for phrase in (
            "Read Order",
            "Non-Negotiable Safety Rules",
            "macOS Path",
            "Windows Path",
            "Do not modify `~/.claude`",
            "python3 tools/codex_native_harness_migrate.py --apply",
            "py -3 tools/codex_native_harness_migrate.py",
            "U+FFFD",
        ):
            if phrase not in bootstrap_text:
                issues.append(f"{bootstrap_path}: missing {phrase!r}")

    if readme_text:
        for phrase in ("AI_BOOTSTRAP.md", "codex-harness.manifest.json", "clone → dry-run → validate → explicit apply", "Windows PowerShell"):
            if phrase not in readme_text:
                issues.append(f"{readme_path}: missing {phrase!r}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        manifest = {}
        issues.append(f"{manifest_path}: JSON parse failed {exc}")

    if manifest:
        expected_scalars = {
            "schema_version": "1.0.0",
            "repository": "https://github.com/HMWKR/codex-dot",
            "ai_first": True,
            "default_mode": "dry-run",
            "apply_requires_explicit_user_approval": True,
        }
        for key, expected in expected_scalars.items():
            if manifest.get(key) != expected:
                issues.append(f"{manifest_path}: expected {key}={expected!r}, got {manifest.get(key)!r}")

        read_order = manifest.get("read_order")
        if not isinstance(read_order, list):
            issues.append(f"{manifest_path}: read_order must be a list")
        else:
            required_order = ["AI_BOOTSTRAP.md", "codex-harness.manifest.json", "README.md", "tools/codex_native_harness_migrate.py", "tools/codex_harness_verify.py"]
            for item in required_order:
                if item not in read_order:
                    issues.append(f"{manifest_path}: read_order missing {item!r}")
            for item in read_order:
                if isinstance(item, str) and not (WORKSPACE / item).exists():
                    issues.append(f"{manifest_path}: read_order file missing {item!r}")

        owned_targets = manifest.get("owned_targets")
        if not isinstance(owned_targets, dict):
            issues.append(f"{manifest_path}: owned_targets must be an object")
        else:
            for os_key in ("macos_linux", "windows"):
                if os_key not in owned_targets:
                    issues.append(f"{manifest_path}: owned_targets missing {os_key!r}")

        forbidden = manifest.get("forbidden_targets")
        if not isinstance(forbidden, list) or "~/.claude" not in forbidden:
            issues.append(f"{manifest_path}: forbidden_targets must include '~/.claude'")

        expected_config = manifest.get("expected_codex_config")
        if not isinstance(expected_config, dict) or expected_config.get("agents.max_threads") != 128 or expected_config.get("features.codex_hooks") is not True:
            issues.append(f"{manifest_path}: expected_codex_config missing required Codex settings")

        expected_events = manifest.get("expected_hook_events")
        if set(expected_events or []) != REQUIRED_HOOK_EVENTS:
            issues.append(f"{manifest_path}: expected_hook_events must match supported command hook events")

        mcp_policy = manifest.get("mcp_policy")
        if not isinstance(mcp_policy, dict) or mcp_policy.get("scope") != "Codex-only" or mcp_policy.get("do_not_run_external_install_scripts") is not True:
            issues.append(f"{manifest_path}: mcp_policy must be Codex-only and reject external install scripts")

        commands = manifest.get("commands")
        if not isinstance(commands, dict) or not commands.get("macos_dry_run") or not commands.get("windows_dry_run"):
            issues.append(f"{manifest_path}: commands must include macos_dry_run and windows_dry_run")

    if issues:
        add(checks, "workspace", "AI bootstrap contract", "FAIL", "; ".join(issues[:30]))
    else:
        add(checks, "workspace", "AI bootstrap contract", "PASS", "AI entrypoint, manifest, macOS/Windows split, and safety gates are machine-checkable")


def check_secret_preflight(checks: list[Check]) -> None:
    roots = [WORKSPACE / "README.md", WORKSPACE / "AI_BOOTSTRAP.md", WORKSPACE / "codex-harness.manifest.json", WORKSPACE / ".gitignore", WORKSPACE / "docs", WORKSPACE / "tools", WORKSPACE / ".github"]
    offenders: list[str] = []
    scanned = 0
    for root in roots:
        for path in iter_files(root, TEXT_SUFFIXES):
            if "harness-verification-report.json" in path.name:
                continue
            ok, text, error = read_utf8(path)
            if not ok:
                offenders.append(f"{path}: {error}")
                continue
            scanned += 1
            for line_number, line in enumerate(text.splitlines(), start=1):
                for label, pattern in SECRET_PATTERNS.items():
                    if pattern.search(line):
                        offenders.append(f"{path}:{line_number}: {label}")
    if offenders:
        add(checks, "workspace", "Secret/PII preflight", "FAIL", "; ".join(offenders[:20]))
    else:
        add(checks, "workspace", "Secret/PII preflight", "PASS", f"{scanned} workspace text files scanned")


def check_harness_boundary_classification(checks: list[Check]) -> None:
    boundary_doc = WORKSPACE / "docs" / "harness-boundary-classification.md"
    gitignore = WORKSPACE / ".gitignore"
    issues: list[str] = []

    ok, boundary_text, error = read_utf8(boundary_doc)
    if not ok:
        issues.append(f"{boundary_doc}: {error}")
    else:
        required_phrases = [
            "Claude-native active harness",
            "Codex-native active harness",
            "Project control plane",
            "Codex-only apply policy",
            "MCP",
            "clone만으로 홈 디렉터리를 수정하지 않는다",
            "Claude 경로에는 쓰지 않는다",
            "Codex 경로에만 쓴다",
        ]
        for phrase in required_phrases:
            if phrase not in boundary_text:
                issues.append(f"{boundary_doc}: missing {phrase!r}")

    if gitignore.exists():
        gitignore_text = gitignore.read_text(encoding="utf-8")
        for pattern in (".claude/", ".codex/", "checkpoint.md", "session-handoff.md", "codex-harness-backups/"):
            if pattern not in gitignore_text:
                issues.append(f"{gitignore}: missing {pattern!r}")
    else:
        issues.append(f"{gitignore}: missing")

    github_workflow = WORKSPACE / "docs" / "github-workflow.md"
    ok, github_text, error = read_utf8(github_workflow)
    if not ok:
        issues.append(f"{github_workflow}: {error}")
    else:
        for phrase in ("clone만으로 홈 디렉터리를 수정하지 않는다", "--apply", "Codex 환경만"):
            if phrase not in github_text:
                issues.append(f"{github_workflow}: missing {phrase!r}")

    default_run = subprocess.run(
        [sys.executable, str(WORKSPACE / "tools" / "codex_native_harness_migrate.py")],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
    )
    if default_run.returncode != 0:
        issues.append("migrator default run failed: " + default_run.stdout + default_run.stderr)
    else:
        try:
            payload = json.loads(default_run.stdout)
            if payload.get("dry_run") is not True:
                issues.append("migrator default run is not dry_run=true")
        except json.JSONDecodeError as exc:
            issues.append(f"migrator default run did not return JSON: {exc}")

    if issues:
        add(checks, "boundary", "Claude/Codex harness classification", "FAIL", "; ".join(issues[:20]))
    else:
        add(checks, "boundary", "Claude/Codex harness classification", "PASS", "Claude and Codex are separate active harnesses; repo defaults are non-mutating")


def check_target_encoding(checks: list[Check]) -> None:
    roots = [CODEX / "AGENTS.md", CODEX / "config.toml", CODEX / "hooks.json", CODEX / "agents", CODEX / "rules", CODEX / "scripts", SKILLS]
    files: list[Path] = []
    for root in roots:
        files.extend(iter_files(root, TARGET_TEXT_SUFFIXES))
    invalid: list[str] = []
    replacement: list[str] = []
    for path in files:
        ok, text, error = read_utf8(path)
        if not ok:
            invalid.append(f"{path}: {error}")
        elif "\ufffd" in text:
            replacement.append(str(path))
    if invalid or replacement:
        add(checks, "encoding", "Codex active harness UTF-8 strict", "FAIL", "; ".join(invalid + replacement[:20]))
    else:
        add(checks, "encoding", "Codex active harness UTF-8 strict", "PASS", f"{len(files)} active Codex text files checked")

    source_replacement: list[str] = []
    unexpected: list[str] = []
    for path in iter_files(CLAUDE / "skills", TARGET_TEXT_SUFFIXES):
        ok, text, _ = read_utf8(path)
        if ok and "\ufffd" in text:
            source_replacement.append(str(path))
            if path not in KNOWN_SOURCE_REPLACEMENT:
                unexpected.append(str(path))
    if unexpected:
        add(checks, "encoding", "Claude reference replacement allowlist", "FAIL", "; ".join(unexpected))
    elif source_replacement:
        add(checks, "encoding", "Claude reference replacement allowlist", "WARN", "known reference-only U+FFFD: " + ", ".join(source_replacement))
    else:
        add(checks, "encoding", "Claude reference replacement allowlist", "PASS", "no Claude reference replacement characters")


def is_allowed_residue(path: Path, line: str) -> bool:
    if path == CODEX / "config.toml" and "claude-plugins-official" in line:
        return True
    if path == CODEX / "scripts" / "insight_collector.py" and "Claude prompt hooks" in line:
        return True
    if SKILLS / "superpowers" in path.parents:
        return True
    return False


def check_active_residue(checks: list[Check]) -> None:
    roots = [
        CODEX / "AGENTS.md",
        CODEX / "config.toml",
        CODEX / "hooks.json",
        CODEX / "agents",
        CODEX / "rules",
        CODEX / "scripts",
        SKILLS,
    ]
    offenders: list[str] = []
    allowed = 0
    pattern = re.compile("|".join(RESIDUE_PATTERNS))
    for root in roots:
        for path in iter_files(root, TARGET_TEXT_SUFFIXES):
            ok, text, error = read_utf8(path)
            if not ok:
                offenders.append(f"{path}: {error}")
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not pattern.search(line):
                    continue
                if is_allowed_residue(path, line):
                    allowed += 1
                else:
                    offenders.append(f"{path}:{line_number}: {line.strip()[:160]}")
    if offenders:
        add(checks, "encoding", "Codex active harness Claude-residue boundary", "FAIL", "; ".join(offenders[:30]))
    else:
        add(checks, "encoding", "Codex active harness Claude-residue boundary", "PASS", f"no active residue outside allowlist; {allowed} historical/plugin references allowed")


def check_skills(checks: list[Check]) -> None:
    if not SKILLS.exists():
        add(checks, "skills", "skill root exists", "FAIL", f"missing {SKILLS}")
        return
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir() and path.name != "_shared")
    lower: list[str] = []
    missing: list[str] = []
    frontmatter: list[str] = []
    markers: list[str] = []
    names: list[str] = []
    for skill_dir in skill_dirs:
        names_exact = exact_file_names(skill_dir)
        if "skill.md" in names_exact:
            lower.append(skill_dir.name)
        if "SKILL.md" not in names_exact:
            missing.append(skill_dir.name)
            continue
        path = skill_dir / "SKILL.md"
        ok, text, error = read_utf8(path)
        if not ok:
            frontmatter.append(f"{skill_dir.name}: invalid UTF-8 {error}")
            continue
        has_frontmatter, values = parse_frontmatter(text)
        if not has_frontmatter or not values.get("name") or not values.get("description"):
            frontmatter.append(skill_dir.name)
        else:
            names.append(values["name"])
        found = [marker for marker in RUNTIME_MARKERS if marker in text]
        if found:
            markers.append(f"{skill_dir.name}: {', '.join(found)}")

    if len(names) != len(set(names)):
        duplicate_names = sorted(name for name in set(names) if names.count(name) > 1)
        add(checks, "skills", "unique skill names", "FAIL", ", ".join(duplicate_names))
    else:
        add(checks, "skills", "unique skill names", "PASS", f"{len(names)} unique names")

    if lower or missing or frontmatter or markers:
        detail = []
        if lower:
            detail.append("lowercase skill.md: " + ", ".join(lower))
        if missing:
            detail.append("missing SKILL.md: " + ", ".join(missing))
        if frontmatter:
            detail.append("frontmatter issues: " + ", ".join(frontmatter))
        if markers:
            detail.append("runtime markers: " + " | ".join(markers[:12]))
        add(checks, "skills", "Codex skill entrypoints", "FAIL", "; ".join(detail))
    else:
        add(checks, "skills", "Codex skill entrypoints", "PASS", f"{len(skill_dirs)} skills have SKILL.md, frontmatter, and no runtime markers")


def check_config_and_hooks(checks: list[Check]) -> None:
    hooks_path = CODEX / "hooks.json"
    try:
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
        events = sorted((hooks.get("hooks") or {}).keys())
        add(checks, "config", "hooks.json parse", "PASS", ", ".join(events))
    except Exception as exc:  # noqa: BLE001
        add(checks, "config", "hooks.json parse", "FAIL", str(exc))
        hooks = {}

    config_path = CODEX / "config.toml"
    try:
        config = parse_toml_text(config_path.read_text(encoding="utf-8"))
        add(checks, "config", "config.toml parse", "PASS", str(config_path))
    except Exception as exc:  # noqa: BLE001
        config = {}
        add(checks, "config", "config.toml parse", "FAIL", str(exc))

    if config.get("features", {}).get("codex_hooks") is True:
        add(checks, "config", "codex_hooks enabled", "PASS", str(config_path))
    else:
        add(checks, "config", "codex_hooks enabled", "FAIL", "missing [features].codex_hooks = true")

    agents_config = config.get("agents", {})
    max_threads = agents_config.get("max_threads") if isinstance(agents_config, dict) else None
    if max_threads == 128:
        add(checks, "config", "agent thread cap", "PASS", "agents.max_threads = 128")
    else:
        add(checks, "config", "agent thread cap", "FAIL", f"expected agents.max_threads = 128, got {max_threads!r}")

    goals_enabled = config.get("features", {}).get("goals") is True
    if goals_enabled:
        add(checks, "config", "goals feature enabled", "PASS", "[features].goals = true")
    else:
        add(checks, "config", "goals feature enabled", "FAIL", "missing [features].goals = true")

    hook_issues: list[str] = []
    hook_events = set((hooks.get("hooks") or {}).keys())
    unknown_events = sorted(hook_events - ALLOWED_HOOK_EVENTS)
    missing_events = sorted(REQUIRED_HOOK_EVENTS - hook_events)
    if unknown_events:
        hook_issues.append("unsupported events: " + ", ".join(unknown_events))
    if missing_events:
        hook_issues.append("missing events: " + ", ".join(missing_events))
    for event_name, blocks in (hooks.get("hooks") or {}).items():
        if not isinstance(blocks, list):
            hook_issues.append(f"{event_name}: blocks must be a list")
            continue
        for block_index, block in enumerate(blocks):
            for hook_index, hook in enumerate(block.get("hooks", [])):
                prefix = f"{event_name}[{block_index}].hooks[{hook_index}]"
                if hook.get("type") != "command":
                    hook_issues.append(f"{prefix}: non-command hook")
                command = hook.get("command")
                if not isinstance(command, str) or not command.strip():
                    hook_issues.append(f"{prefix}: empty command")
                if not isinstance(hook.get("timeout"), int) or hook.get("timeout") <= 0:
                    hook_issues.append(f"{prefix}: invalid timeout")
                if isinstance(command, str) and "prettier" in command.lower():
                    hook_issues.append(f"{prefix}: automatic prettier rewrite hook is disabled by policy")
    if hook_issues:
        add(checks, "config", "hook event policy", "FAIL", "; ".join(hook_issues))
    else:
        add(checks, "config", "hook event policy", "PASS", "only supported command hooks with explicit timeouts")

    command_paths: list[str] = []
    for event in (hooks.get("hooks") or {}).values():
        for block in event:
            for hook in block.get("hooks", []):
                command = hook.get("command", "")
                command_paths.extend(re.findall(r"(/Users/[^ '\"]+)", command))
    missing = [path for path in command_paths if not Path(path).exists()]
    if missing:
        add(checks, "config", "hook command paths", "FAIL", "; ".join(missing))
    else:
        add(checks, "config", "hook command paths", "PASS", f"{len(command_paths)} referenced absolute paths exist")

    expected_agents = {
        "ce-reviewer": "read-only",
        "codebase-explorer": "read-only",
        "harness-evaluator": "read-only",
        "infra-auditor": "read-only",
        "thoughts-writer": "workspace-write",
    }
    agent_issues: list[str] = []
    for name, sandbox in expected_agents.items():
        path = CODEX / "agents" / f"{name}.toml"
        if not path.exists():
            agent_issues.append(f"{name}: missing")
            continue
        agent_text = path.read_text(encoding="utf-8")
        try:
            agent_data = parse_toml_text(agent_text)
        except Exception as exc:  # noqa: BLE001
            agent_issues.append(f"{name}: TOML parse failed {exc}")
            continue
        for field in ("name", "description", "sandbox_mode", "developer_instructions"):
            if field not in agent_data:
                agent_issues.append(f"{name}: missing {field}")
        if agent_data.get("sandbox_mode") != sandbox:
            agent_issues.append(f"{name}: wrong sandbox")
    if agent_issues:
        add(checks, "config", "custom agents", "FAIL", "; ".join(agent_issues))
    else:
        add(checks, "config", "custom agents", "PASS", "5 expected agents with expected sandbox modes")

    feature_list = subprocess.run(["codex", "features", "list"], cwd=WORKSPACE, text=True, capture_output=True)
    if feature_list.returncode != 0:
        add(checks, "config", "local goals feature flag", "WARN", "codex features list unavailable: " + (feature_list.stdout + feature_list.stderr).strip())
    elif re.search(r"(?m)^goals\s+under development\s+true\b", feature_list.stdout):
        add(checks, "config", "local goals feature flag", "PASS", "goals under development true")
    elif re.search(r"(?m)^goals\s+under development\s+false\b", feature_list.stdout):
        add(checks, "config", "local goals feature flag", "FAIL", "goals feature exists but effective state is false")
    elif re.search(r"(?m)^goals\s+", feature_list.stdout):
        add(checks, "config", "local goals feature flag", "WARN", "goals feature exists with unexpected state")
    else:
        add(checks, "config", "local goals feature flag", "WARN", "goals feature not reported by local Codex CLI")


def compile_python(path: Path, temp_root: Path) -> str | None:
    try:
        cfile = temp_root / (str(path).strip("/").replace("/", "__") + ".pyc")
        cfile.parent.mkdir(parents=True, exist_ok=True)
        py_compile.compile(str(path), cfile=str(cfile), doraise=True)
        return None
    except Exception as exc:  # noqa: BLE001
        return str(exc)


def check_scripts(checks: list[Check]) -> None:
    python_files = sorted((WORKSPACE / "tools").glob("*.py")) + sorted((CODEX / "scripts").glob("*.py"))
    py_errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-harness-pycompile-") as tmp:
        temp_root = Path(tmp)
        for path in python_files:
            error = compile_python(path, temp_root)
            if error:
                py_errors.append(f"{path}: {error}")
    if py_errors:
        add(checks, "scripts", "Python compile", "FAIL", "; ".join(py_errors))
    else:
        add(checks, "scripts", "Python compile", "PASS", f"{len(python_files)} files")

    shell_files = sorted((CODEX / "scripts").glob("*.sh"))
    infra = SKILLS / "infra-audit" / "scripts" / "infra-audit.sh"
    if infra.exists():
        shell_files.append(infra)
    shell_errors: list[str] = []
    for path in shell_files:
        result = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True)
        if result.returncode != 0:
            shell_errors.append(f"{path}: {result.stderr.strip()}")
    if shell_errors:
        add(checks, "scripts", "Shell syntax", "FAIL", "; ".join(shell_errors))
    else:
        add(checks, "scripts", "Shell syntax", "PASS", f"{len(shell_files)} files")


def check_hook_simulation(checks: list[Check]) -> None:
    guard = CODEX / "scripts" / "anti_loop_guard.py"
    checkpoint = CODEX / "scripts" / "checkpoint_save.py"
    with tempfile.TemporaryDirectory(prefix="codex-hook-sim-") as tmp:
        cwd = Path(tmp)
        safe = subprocess.run(
            [sys.executable, str(guard), "pretooluse"],
            input=json.dumps({"tool_input": {"command": "printf codex-safe"}}),
            cwd=cwd,
            text=True,
            capture_output=True,
        )
        dangerous_results = []
        for command in ("rm -rf /tmp/example", "git reset --hard", "DROP TABLE users"):
            result = subprocess.run(
                [sys.executable, str(guard), "pretooluse"],
                input=json.dumps({"tool_input": {"command": command}}),
                cwd=cwd,
                text=True,
                capture_output=True,
            )
            dangerous_results.append((command, result.returncode, result.stdout + result.stderr))
        stop = subprocess.run([sys.executable, str(checkpoint), "stop"], cwd=cwd, text=True, capture_output=True)
        checkpoint_exists = (cwd / "checkpoint.md").exists()

    failures: list[str] = []
    if safe.returncode != 0:
        failures.append(f"safe command rc={safe.returncode}: {safe.stdout}{safe.stderr}")
    for command, returncode, output in dangerous_results:
        if returncode != 2:
            failures.append(f"dangerous command not denied {command!r}: rc={returncode} {output}")
    if stop.returncode != 0 or not checkpoint_exists:
        failures.append(f"checkpoint stop failed rc={stop.returncode}: {stop.stdout}{stop.stderr}")

    if failures:
        add(checks, "hooks", "hook simulations", "FAIL", "; ".join(failures))
    else:
        add(checks, "hooks", "hook simulations", "PASS", "safe allow, dangerous deny, checkpoint write in temp dir")


def check_migration_tools(checks: list[Check], *, workspace_only: bool = False) -> None:
    dry = subprocess.run(
        [sys.executable, str(WORKSPACE / "tools" / "codex_native_harness_migrate.py"), "--dry-run"],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
    )
    if dry.returncode != 0:
        add(checks, "migration", "dry-run", "FAIL", dry.stdout + dry.stderr)
    else:
        add(checks, "migration", "dry-run", "PASS", dry.stdout.strip())

    dry_second = subprocess.run(
        [sys.executable, str(WORKSPACE / "tools" / "codex_native_harness_migrate.py")],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
    )
    try:
        first_payload = json.loads(dry.stdout)
        second_payload = json.loads(dry_second.stdout)
        deterministic = dry.returncode == 0 and dry_second.returncode == 0 and first_payload == second_payload
    except json.JSONDecodeError:
        deterministic = False
    if deterministic:
        add(checks, "migration", "dry-run idempotency", "PASS", "two default dry-runs returned the same JSON payload")
    else:
        add(checks, "migration", "dry-run idempotency", "FAIL", dry_second.stdout + dry_second.stderr)

    migrator = WORKSPACE / "tools" / "codex_native_harness_migrate.py"
    with tempfile.TemporaryDirectory(prefix="codex-restore-probe-") as tmp:
        backup_dir = Path(tmp)
        backup_file = backup_dir / ".codex" / "__restore_probe__.txt"
        backup_file.parent.mkdir(parents=True)
        backup_file.write_text("restore probe\n", encoding="utf-8")
        manifest = {
            "created_at": "restore-probe",
            "workspace": str(WORKSPACE),
            "items": [
                {
                    "source": str(CODEX / "__restore_probe__.txt"),
                    "backup": str(backup_file),
                    "sha256": sha256(backup_file),
                }
            ],
        }
        (backup_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        restore = subprocess.run(
            [sys.executable, str(migrator), "--restore", str(backup_dir)],
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
        )
    if restore.returncode != 0:
        add(checks, "migration", "restore dry-run", "FAIL", restore.stdout + restore.stderr)
    else:
        try:
            payload = json.loads(restore.stdout)
        except json.JSONDecodeError as exc:
            add(checks, "migration", "restore dry-run", "FAIL", f"invalid JSON: {exc}")
        else:
            if payload.get("restore") is True and payload.get("dry_run") is True and payload.get("files") == 1:
                add(checks, "migration", "restore dry-run", "PASS", "manifest hash and Codex-owned path validation passed")
            else:
                add(checks, "migration", "restore dry-run", "FAIL", restore.stdout)

    if not workspace_only:
        inventory = subprocess.run(
            [sys.executable, str(WORKSPACE / "tools" / "codex_harness_inventory.py")],
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
        )
        if inventory.returncode != 0:
            add(checks, "migration", "inventory generation", "FAIL", inventory.stdout + inventory.stderr)
        elif "ready | 49" in inventory.stdout and "| normalize | 0" in inventory.stdout:
            add(checks, "migration", "inventory generation", "PASS", "ready 49, normalize 0")
        else:
            add(checks, "migration", "inventory generation", "WARN", "inventory generated but expected readiness summary was not found")

        validator = run_codex_validator()
        add(checks, "migration", "Codex validator", validator[0], validator[1])


def check_github_preflight(checks: list[Check]) -> None:
    if not (WORKSPACE / ".git").exists():
        add(checks, "github", "Git repository initialized", "WARN", "workspace is not a Git repo yet; GitHub stage starts with git init")
        return
    status = subprocess.run(["git", "status", "--short"], cwd=WORKSPACE, text=True, capture_output=True)
    if status.returncode != 0:
        add(checks, "github", "Git status", "FAIL", status.stdout + status.stderr)
    else:
        detail = status.stdout.strip() or "clean worktree"
        add(checks, "github", "Git status", "PASS", detail)


def run_codex_validator() -> tuple[str, str]:
    py = HOME / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "bin" / "python3"
    migrator = CODEX / "vendor_imports" / "skills" / "skills" / ".curated" / "migrate-to-codex" / "scripts" / "migrate-to-codex.py"
    if not py.exists() or not migrator.exists():
        return "WARN", "bundled Python or migrate-to-codex validator not found"
    result = subprocess.run([str(py), str(migrator), "--validate-target", str(CODEX)], text=True, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return "FAIL", result.stdout + result.stderr
    warnings = [line for line in result.stdout.splitlines() if line.strip().startswith("warning:")]
    if warnings:
        return "WARN", f"validator passed with {len(warnings)} warnings"
    return "PASS", "validator passed without warnings"


def build_markdown(checks: list[Check]) -> str:
    counts = {status: sum(1 for check in checks if check.status == status) for status in ("PASS", "WARN", "FAIL")}
    overall = "PASS" if counts["FAIL"] == 0 else "FAIL"
    lines = [
        "# Harness Verification Report",
        "",
        "## Summary",
        "",
        f"- Overall: `{overall}`",
        f"- PASS: {counts['PASS']}",
        f"- WARN: {counts['WARN']}",
        f"- FAIL: {counts['FAIL']}",
        "",
        "## Checks",
        "",
        "| Area | Check | Status | Detail |",
        "|---|---|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("\n", "<br>")
        if len(detail) > 700:
            detail = detail[:700] + "..."
        lines.append(f"| {check.area} | {check.name} | {check.status} | {detail} |")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "GitHub 후보 하네스 검토는 `FAIL`이 0개일 때만 진행한다. `WARN`은 원인과 허용 범위를 문서화한 경우 pass로 본다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--workspace-only", action="store_true", help="Run checks that are safe on a fresh GitHub runner without local Codex home config.")
    args = parser.parse_args()

    checks: list[Check] = []
    check_workspace_files(checks)
    check_documentation_sync(checks)
    check_ai_bootstrap_contract(checks)
    check_secret_preflight(checks)
    check_harness_boundary_classification(checks)
    if not args.workspace_only:
        check_target_encoding(checks)
        check_active_residue(checks)
        check_skills(checks)
        check_config_and_hooks(checks)
    check_scripts(checks)
    if not args.workspace_only:
        check_hook_simulation(checks)
    check_migration_tools(checks, workspace_only=args.workspace_only)
    check_github_preflight(checks)

    data = {
        "summary": {
            "pass": sum(1 for check in checks if check.status == "PASS"),
            "warn": sum(1 for check in checks if check.status == "WARN"),
            "fail": sum(1 for check in checks if check.status == "FAIL"),
        },
        "checks": [check.__dict__ for check in checks],
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = build_markdown(checks)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 1 if data["summary"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
