# AI Bootstrap Contract

## Purpose

This file is the first entrypoint for an AI agent that receives only this GitHub repository URL and the request:

```text
Make my current Codex harness match HMWKR/codex-dot.
```

The agent must treat this repository as a Codex harness control plane, not as a raw home-directory backup. The repo describes how to validate and apply a Codex-native harness while preserving the user's existing environment until explicit apply approval.

## Read Order

Read these files in order before editing or applying anything:

1. `AI_BOOTSTRAP.md`
2. `codex-harness.manifest.json`
3. `README.md`
4. `docs/harness-boundary-classification.md`
5. `docs/skill-asset-policy.md`
6. `docs/codex-only-mcp-plugin-catalog.md`
7. `docs/release-checklist.md`
8. `tools/codex_native_harness_migrate.py`
9. `tools/codex_harness_verify.py`

## Non-Negotiable Safety Rules

- Do not modify `~/.claude`.
- Do not copy authentication files, session logs, plugin caches, or transcripts.
- Do not apply changes during clone or first inspection.
- Do not run external install scripts from other harness repositories.
- Run dry-run and verification before any real apply.
- Apply only after the user explicitly approves `python3 tools/codex_native_harness_migrate.py --apply`.
- Stop if UTF-8 strict validation fails or any file contains `U+FFFD` in the active Codex target.

## Harness Targets

| Target | macOS / Linux | Windows |
|---|---|---|
| Codex config | `$HOME/.codex` | `%USERPROFILE%\.codex` |
| User skills | `$HOME/.agents/skills` | `%USERPROFILE%\.agents\skills` |
| Claude config | read-only reference only | read-only reference only |
| Repository | project control plane | project control plane |

The active Codex harness consists of:

- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- `~/.codex/hooks.json`
- `~/.codex/agents/*.toml`
- `~/.codex/rules/*`
- `~/.codex/scripts/*`
- `~/.agents/skills/*/SKILL.md`

## macOS Path

Use this path when Codex is running on macOS.

```bash
git clone https://github.com/HMWKR/codex-dot.git
cd codex-dot
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

If the user approves real application:

```bash
python3 tools/codex_native_harness_migrate.py --apply
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

Optional local runtime support for enabled MCP servers:

```bash
brew install gh node uv php
```

Use `gh auth login --web` for GitHub operations. Service-specific MCP authentication is separate and must be confirmed per provider.

## Windows Path

Use this path when Codex is running on Windows PowerShell.

```powershell
git clone https://github.com/HMWKR/codex-dot.git
Set-Location codex-dot
py -3 tools/codex_native_harness_migrate.py
py -3 tools/codex_harness_verify.py --workspace-only --markdown-output .\docs\harness-verification-report.md --json-output .\docs\harness-verification-report.json
```

If Python is exposed as `python`, use `python` instead of `py -3`.

Before real application on Windows, the agent must inspect `tools/codex_native_harness_migrate.py` and the generated hook commands for shell compatibility. The current harness is macOS-first and Codex-path portable, but some generated hook commands use POSIX shell idioms. If native Windows hook execution is required, prefer one of these explicit choices:

- Use WSL/Git Bash for Codex hook execution.
- Add a Windows-specific hook command port before applying.
- Keep Windows in dry-run/validation mode until the user approves a porting batch.

Recommended Windows local runtime support:

```powershell
winget install Git.Git
winget install GitHub.cli
winget install OpenJS.NodeJS
winget install astral-sh.uv
```

PHP is only needed for Laravel Boost MCP:

```powershell
winget install PHP.PHP
```

## AI Execution Protocol

1. Identify OS and shell.
2. Read `codex-harness.manifest.json`.
3. Explain the target paths and safety boundary to the user.
4. Run migration dry-run.
5. Run verifier.
6. Report PASS/WARN/FAIL and any Windows/macOS-specific caveat.
7. Ask for explicit approval before `--apply`.
8. Apply only to Codex-owned paths.
9. Re-run verifier.
10. If this repo is under Git control, commit documentation or harness-control-plane changes separately from home runtime changes.

## Success Criteria

An AI agent has followed this contract when:

- It can name the Codex-owned target paths.
- It can name the paths that must not be modified.
- It runs dry-run before apply.
- It runs verifier before and after apply.
- It preserves UTF-8 and rejects replacement characters in active Codex targets.
- It does not install or authenticate third-party MCP providers without user approval.
- It distinguishes macOS commands from Windows commands.

