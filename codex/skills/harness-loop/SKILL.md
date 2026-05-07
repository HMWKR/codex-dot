---
name: harness-loop
description: Codex-native quality gate orchestration loop for work that explicitly needs subagents, repeated review, implementation, verification, and final reporting. Use when the user asks for a harness loop, agent orchestration, quality gate loop, multi-agent improvement loop, mega loop, task router, or "agents plus verification". Skip for simple questions, single-file edits, or requests that do not authorize delegation.
---

# Harness Loop

## Overview

Use this skill to coordinate a bounded improvement loop with explicit quality gates. It routes work across the current Codex environment, keeps write ownership clear, verifies results, and reports remaining risk.

Only spawn subagents when the user explicitly asked for agents, delegation, parallel work, a harness loop, or an equivalent orchestration workflow. Otherwise, run the work locally and use the same quality gates.

## Modes

Choose one mode from the user request:

| Mode | Use when | Shape |
|---|---|---|
| status | user asks to inspect harness readiness | discover agents/tools and report only |
| task router | one bounded task with validation | classify, execute, verify, report |
| mega loop | repeated improvement rounds | round plan, worker/reviewer split, gates, next round |
| audit | security, infra, UX, code, or process audit | read-only specialists first, fixes only if requested |

## Phase 0: Discover

Gather only what is needed:

1. Read project instructions and relevant metadata files.
2. Inspect current `spawn_agent` roles available in this session and project custom agents under `~/.codex/agents` when needed.
3. Identify test/build/browser commands from package or config files.
4. Find any existing `session-handoff.md`, `checkpoint.md`, or project-specific insight docs.

Do not require a legacy agent folder. Codex agents and the currently available tools are the source of truth.

## Phase 1: Route

Classify the task:

| Category | Signals | Execution pattern |
|---|---|---|
| build | create, implement, migrate, scaffold | worker/direct local implementation then review |
| fix | bug, failing test, regression | diagnose, patch, rerun failing checks |
| audit | review, inspect, score, evaluate | read-only review first, fixes after confirmation if scope changes |
| analyze | investigate, trace, compare | explorer/read-only pass, synthesize findings |
| cleanup | organize, dedupe, simplify | narrow write scope and regression checks |

When delegating implementation, assign disjoint ownership. Tell workers they are not alone in the codebase, must avoid reverting others, and must list changed files.

## Phase 2: Execute Rounds

Each round:

1. Restate the round goal and exit criteria.
2. Decide what work stays local and what can run in parallel.
3. Delegate only independent sidecar work; keep blocking work local.
4. Integrate returned changes or findings.
5. Run the narrowest meaningful checks.
6. Update the plan with pass/fail and remaining gaps.

Use [references/codex-orchestration.md](references/codex-orchestration.md) for delegation prompts and quality gate templates.

## Phase 3: Quality Gates

Use gates that match the work:

- Code: tests, typecheck, lint, build, smoke command.
- Web/UI: Browser Use first for live proof, Computer Use for OS/browser-profile or desktop-dependent proof, and Playwright/scripts for deterministic regression checks when a UI changed.
- Data: safe read-only checks first; destructive operations require approval.
- Security: secret scan, auth/permission abuse cases, dependency warnings when relevant.
- Documentation: examples, links, commands, and generated reports stay in sync.

For web apps, the final gate should include a real browser check when feasible. Static analysis alone is not a final UI proof.

## Phase 4: Record

Report:

- selected mode
- agents or local roles used
- files changed
- checks run
- unresolved issues
- next recommended round, if any

Persist a handoff only for multi-session loops or when the project already uses one. Do not create commits unless requested.

## Stop Conditions

Stop and ask before continuing if:

- the next round needs destructive access
- delegation would require overlapping write scopes
- required credentials or services are missing
- the same issue survives three rounds
- the user did not authorize subagent work but the task now truly needs it
