---
name: ultradetail-loop
description: High-cost exhaustive walk-fix-walk convergence loop for release gates. Use when the user asks for ultradetail loop, exhaustive QA until zero new defects, repeated click-everything rounds, walk fix re-walk, 100% defect removal, or launch readiness with adversarial personas every round. Skip for one-shot discovery, small fixes, or token-saving loops.
---

# Ultradetail Loop

## Overview

Use this skill when the user needs both depth and persistence:

```text
ultradetail-walk depth + live-verify-loop persistence
```

Every round repeats an exhaustive persona walk, fixes the highest-value defects, then walks again. This is intentionally expensive and should be reserved for release gates, critical flows, and high-risk multi-role systems.

## Boundaries

- Use `ultradetail-walk` for one discovery pass.
- Use `live-verify-loop` for lighter repeated fixes without walking every element every round.
- Use `harness-loop` when broader subagent orchestration is the main request.

Do not run this skill when a simple failing test, one broken page, or a small PR check is enough.

## Initial Setup

Before Round 1:

1. Confirm target scope, environment, roles, and destructive-flow boundaries.
2. Confirm browser proof tooling. Prefer Browser Use, add Computer Use for desktop/browser-profile setup, and reserve Playwright or scripts for deterministic automation. Without any browser-capable tool, stop.
3. Discover routes, inputs, libraries, components, standards, and prior pitfalls.
4. Select defect categories and personas. Keep these stable across rounds unless the user changes scope.
5. Set hard limits: maximum rounds, stagnation limit, per-round evidence expectations, and whether follow-up wakeups are allowed.
6. Decide whether Cantos records should be written through `cantos-write` when connected.

See [references/loop-matrices.md](references/loop-matrices.md) for round templates and guardrails.

## Tool Priority

Run each round with a terminal-first harness for setup and code gates, then use Browser Use as the default live-browser walker. Use Computer Use when a round depends on OS-level browser state, profiles, downloads, file pickers, native dialogs, or installed-app behavior. Use Playwright or scripts for repeatable selector, console, network, viewport, or CI-style checks.

Do not block the loop merely because Playwright MCP is unavailable when Browser Use or Computer Use can provide the required live evidence.

## Round Cycle

Each round:

1. Walk all selected normal personas.
2. Walk all selected adversarial personas.
3. Classify findings against the fixed defect categories.
4. Fix critical and high-confidence defects within the approved write scope.
5. Run relevant code, data, and browser checks.
6. Record round evidence and compare against prior rounds.
7. Decide whether to stop or continue.

If fixes require risky data writes, destructive actions, or overlapping file ownership, pause for approval or switch to a narrower plan.

## Stop Conditions

Stop when any condition is met:

- no new defects are found and all prior critical/high defects are verified fixed
- the user stops the loop
- maximum rounds are reached
- the same defect survives three fix attempts
- required tooling, credentials, or test data is missing
- the loop cost is no longer justified by the remaining risk

For unattended continuation, use Codex heartbeat automation only when the user explicitly asks this thread to wake up and continue. The wakeup prompt must include target scope, round number, remaining defects, and guardrails.

## Evidence

For every round, keep:

- personas walked
- routes and element coverage
- normal and adversarial findings
- fixes applied
- checks rerun
- remaining defects
- stop/continue decision

For long runs, write `.thoughts/ultradetail-loop/round-N.md` or update an existing project handoff. Do not commit or tag unless requested.

## Cantos

When Cantos MCP is connected and the user wants records:

- use `cantos-write` for ADR/DDR/journal creation
- create DDR candidates for critical visual or interaction defects
- include route, persona, viewport, screenshot/evidence path, decision, and impact

When Cantos is unavailable, explicitly report that records are local drafts only.

## Red Flags

Stop and reassess if:

- the selected categories or personas drift without user approval
- a render-only pass is treated as equivalent to a persona walk
- a round skips adversarial checks to save time
- the loop keeps fixing symptoms without reducing findings
- the user actually needs a one-shot `ultradetail-walk` instead
