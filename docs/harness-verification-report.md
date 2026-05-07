# Harness Verification Report

## Summary

- Overall: `PASS`
- PASS: 31
- WARN: 0
- FAIL: 0

## Checks

| Area | Check | Status | Detail |
|---|---|---|---|
| workspace | UTF-8 and replacement characters | PASS | 76 files checked |
| workspace | HTML smoke parse | PASS | 3 html files parsed |
| workspace | documentation sync | PASS | verification tool, report, and GitHub gate are documented |
| workspace | AI bootstrap contract | PASS | AI entrypoint, manifest, macOS/Windows split, and safety gates are machine-checkable |
| workspace | Secret/PII preflight | PASS | 74 workspace text files scanned |
| skills | AI skill index | PASS | 59 indexed skills matched active skill root |
| skills | Skill behavior contracts | PASS | 11 contracts, 35 scenarios, fail 0, warn 0 |
| boundary | Claude/Codex harness classification | PASS | Claude and Codex are separate active harnesses; repo defaults are non-mutating |
| encoding | Codex active harness UTF-8 strict | PASS | 370 active Codex text files checked |
| encoding | Claude reference replacement allowlist | PASS | no Claude reference replacement characters |
| encoding | Codex active harness Claude-residue boundary | PASS | no active residue outside allowlist; 9 historical/plugin references allowed |
| skills | unique skill names | PASS | 59 unique names |
| skills | Codex skill entrypoints | PASS | 59 skills have SKILL.md, frontmatter, and no runtime markers |
| config | hooks.json parse | PASS | PostToolUse, PreToolUse, SessionStart, Stop |
| config | config.toml parse | PASS | /Users/leesungmin/.codex/config.toml |
| config | codex_hooks enabled | PASS | /Users/leesungmin/.codex/config.toml |
| config | agent thread cap | PASS | agents.max_threads = 128 |
| config | goals feature enabled | PASS | [features].goals = true |
| config | hook event policy | PASS | only supported command hooks with explicit timeouts |
| config | hook command paths | PASS | 4 referenced absolute paths exist |
| config | custom agents | PASS | 5 expected agents with expected sandbox modes |
| config | local goals feature flag | PASS | goals under development true |
| scripts | Python compile | PASS | 11 files |
| scripts | Shell syntax | PASS | 2 files |
| hooks | hook simulations | PASS | safe allow, dangerous deny, checkpoint write in temp dir |
| migration | dry-run | PASS | {<br>  "dry_run": true,<br>  "preflight_files": 700,<br>  "reference_replacement_characters": [],<br>  "note": "Claude reference U+FFFD characters are allowed in dry-run; Codex active harness validation still fails if any remain after apply."<br>} |
| migration | dry-run idempotency | PASS | two default dry-runs returned the same JSON payload |
| migration | restore dry-run | PASS | manifest hash and Codex-owned path validation passed |
| migration | inventory generation | PASS | ready 59, normalize 0 |
| migration | Codex validator | PASS | validator passed; 22 cache/reference warnings ignored |
| github | Git status | PASS | clean worktree |

## Gate

GitHub 후보 하네스 검토는 `FAIL`이 0개일 때만 진행한다. `WARN`은 원인과 허용 범위를 문서화한 경우 pass로 본다.
`github / Git status`의 dirty worktree `WARN`은 개발 중 진단용으로만 허용하며, release 전에는 반드시 clean 상태로 정리한다.
