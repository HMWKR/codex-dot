# Codex Orchestration Reference

## Agent Role Mapping

| Need | Preferred role |
|---|---|
| source structure, symbol tracing, dependency reading | explorer or codebase-explorer |
| bounded implementation | worker |
| CE/code review | ce-reviewer |
| infra and harness checks | infra-auditor |
| scoring harness quality | harness-evaluator |
| thinking/session record after significant work | thoughts-writer |

Use only roles that are available in the current session.

## Worker Prompt Template

```text
You are responsible for: <files/modules>.
You are not alone in the codebase. Do not revert edits made by others.
Keep changes inside your ownership scope.
Implement <specific outcome>.
Run or name the narrow checks you used.
Final response: changed files, verification, remaining risks.
```

## Reviewer Prompt Template

```text
Review <files/behavior> for correctness, regressions, missing tests, security, and maintainability.
Do not edit files.
Return findings first with file/line references, then residual risk.
```

## Quality Gate Template

```markdown
## Gate

- Scope:
- Commands:
- Browser proof:
- Data/API proof:
- PASS:
- WARN:
- FAIL:
```

## Parallelism Rules

- Parallelize independent reading and non-overlapping implementation.
- Keep immediate blockers local.
- Do not ask two workers to edit the same files.
- Wait for agents only when their output is needed for the next local step.
