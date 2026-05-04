# Claude/Codex Harness Inventory

## Summary

This report is generated from local Claude/Codex files and is used as the rebuild baseline without modifying either harness.

| Area | Count |
|---|---:|
| Claude text files scanned | 336 |
| Codex text files scanned | 117 |
| Claude skill directories | 44 |
| Codex active skill directories | 49 |
| Claude command files | 5 |
| Claude agent files | 5 |
| UTF-8 failures | 0 |
| Files containing `U+FFFD` | 1 |

## Claude Corpus Shape

| Category | Files |
|---|---:|
| agents | 5 |
| commands | 5 |
| global-instructions | 1 |
| other | 10 |
| rules | 5 |
| scripts | 6 |
| settings | 4 |
| skills | 300 |

## Codex Active Skill Readiness

| Status | Count | Meaning |
|---|---:|---|
| ready | 49 | Codex entrypoint/frontmatter are clean and no Claude runtime markers were found in entrypoint |
| normalize | 0 | File case or Claude runtime language needs Codex-native rewrite |
| frontmatter | 0 | Missing or incomplete Codex skill metadata |
| missing | 0 | No `SKILL.md` or `skill.md` entrypoint |

## Main Findings

- Codex active harness has 0 skill entrypoints named `skill.md`; these should be renamed or regenerated as `SKILL.md`.
- Codex active harness has 0 skills with missing or incomplete frontmatter.
- Codex active harness has 0 skills whose entrypoint still contains Claude runtime markers.
- Codex-only skills: source-command-analyze, source-command-journal, source-command-orchestrate, source-command-pdca, source-command-rules
- Claude-only skills: -
- `~/.claude/settings.json`: valid
- `~/.claude/settings.local.json`: valid
- `~/.codex/hooks.json`: valid

## Codex Skill Quality Signals

- Average quality score: 95.1 / 100
- Skills below A grade: 0

| Skill | Grade | Score | Signals |
|---|---:|---:|---|
| `agent-teams-code-review` | A | 92 | large entrypoint |
| `agent-teams-deep-analysis` | A | 92 | large entrypoint |
| `agent-teams-feature-dev` | A | 92 | large entrypoint |
| `agent-teams-orchestrator` | A | 92 | large entrypoint |
| `agent-teams-reactive-dev` | A | 92 | large entrypoint |
| `architect` | A | 92 | large entrypoint |
| `ce-advisor` | A | 92 | large entrypoint |
| `continuous-qa-loop` | A | 92 | large entrypoint |
| `deep-analysis-mode` | A | 92 | large entrypoint |
| `domain-expert-analysis` | A | 92 | large entrypoint |
| `infra-audit` | A | 92 | large entrypoint |
| `js-refactor-cleanup-skill` | A | 92 | large entrypoint |

## Claude Runtime Marker Totals

| Marker | Count | Codex rewrite |
|---|---:|---|
| - | 0 | - |

## Normalization Queue

| Priority | Skill | Status | Entrypoint | Runtime markers | Notes |
|---|---|---|---|---|---|

## Claude Commands

| Command file | Codex skill |
|---|---|
| `commands/analyze.md` | `source-command-analyze` |
| `commands/journal.md` | `source-command-journal` |
| `commands/orchestrate.md` | `source-command-orchestrate` |
| `commands/pdca.md` | `source-command-pdca` |
| `commands/rules.md` | `source-command-rules` |

## Claude Agents

| Agent file | Codex agent |
|---|---|
| `agents/ce-reviewer.md` | `~/.codex/agents/ce-reviewer.toml` |
| `agents/codebase-explorer.md` | `~/.codex/agents/codebase-explorer.toml` |
| `agents/harness-evaluator.md` | `~/.codex/agents/harness-evaluator.toml` |
| `agents/infra-auditor.md` | `~/.codex/agents/infra-auditor.toml` |
| `agents/thoughts-writer.md` | `~/.codex/agents/thoughts-writer.toml` |

## Encoding Exceptions

| File | Issue |
|---|---|
| `/Users/leesungmin/.claude/skills/think-teams/skill.md` | contains U+FFFD x52 |

## Next Actions

1. Treat the structural Codex skill migration as complete.
2. Continue semantic 3-pass reviews for high-value skills before changing behavior.
3. Keep Claude-native and Codex-native active harnesses separate.
4. Defer external GitHub harness imports until the Codex active harness is judged stable.
5. Re-run this inventory and update this report after each rebuild batch.

## 3-Pass Review Gate

| Pass | Purpose | Output |
|---|---|---|
| Pass 1 | Extract original intent from Claude Markdown without rewriting it. | Trigger, workflow, tools, outputs, confirmation points. |
| Pass 2 | Map the extracted intent to Codex-native primitives. | Skill metadata, subagent policy, hook/script behavior, unsupported semantics. |
| Pass 3 | Check omissions, misunderstandings, and conflicts. | Final rewrite checklist and residual risks. |
