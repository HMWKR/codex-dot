---
name: live-verify-loop
description: Live browser verification loop for closing the gap between code passing and real user flows passing. Use when the user asks for live verification, "100% until browser passes", repeated Browser Use or Computer Use-assisted validation with fixes, console-clean verification, critical user journey proof, production-readiness QA, or multi-round live audit. Skip for one-shot tests, single bug fixes, or code-only generation.
---

# Live Verify Loop

## Overview

Use this skill when static checks are not enough. The core rule is:

```text
code green != live green
```

A round only passes when the agreed live behavior is verified through the browser, the relevant data/API layer is checked, and code quality gates are clean.

## Use Boundaries

- Use `playwright-qa-expert` for one deep QA pass.
- Use `continuous-qa-loop` for a lighter fix-test loop.
- Use `harness-loop` when the user wants broader multi-agent orchestration.
- Use `ultradetail-walk` for one exhaustive discovery pass across personas and interactive elements.
- Use `ultradetail-loop` for high-cost release gates where every round must do exhaustive walk, fix, and re-walk.
- Use this skill when the user wants repeated live verification until explicit pass conditions are met.

Do not claim success from `curl`, unit tests, typecheck, or screenshot-only checks. They are useful signals, not live proof.

## Setup

Before the first round, establish five items:

1. Target scope: routes, pages, APIs, user roles, devices, and environments.
2. Verification mode: UI/UX, data, code quality, API, accessibility, performance, SEO, security, or integrated.
3. Termination criteria: the exact checks that must pass before stopping.
4. Tool plan: terminal for server/build/test work, Browser Use for normal browser proof, Computer Use for desktop/browser-profile setup, Playwright or scripts only for deterministic automation, and MCP tools only when actually available.
5. Round limits: maximum rounds, stagnation limit, and whether follow-up wakeups are allowed.

If any item is ambiguous, ask before starting the loop. For three or more steps, create an `update_plan`.

## Tool Priority

Use tools in this order unless the user explicitly asks for a different route:

1. Terminal: start dev servers, run builds/tests/lint/typecheck, inspect logs, and manage local files.
2. Browser Use: default live-browser proof for localhost, staging, forms, navigation, console inspection, visual state, and screenshots.
3. Computer Use: use when the proof depends on OS-level browser state, desktop windows, installed browsers, profiles, login dialogs, file pickers, downloads, or system prompts.
4. Playwright or scripts: use for deterministic repeatability, selector-level checks, console/network capture, regression automation, or CI-ready evidence.

Do not require Playwright MCP when Browser Use can produce the live browser evidence. Do not replace real browser proof with terminal-only checks.

## Modes

Use `lite` for a focused PR or a small flow:

1. Confirm target and termination criteria.
2. Confirm browser/data/code tools.
3. Run the round loop.

Use `full` for launch readiness or a new product area:

1. Confirm verification mode.
2. Build a critical user journey matrix.
3. Map user roles and data isolation cases.
4. Define browser, API/data, and code quality checks.
5. Load the pitfall reference if relevant.
6. Decide how to record round evidence.
7. Run the round loop.

See [references/live-verification-matrix.md](references/live-verification-matrix.md) for check matrices and pitfall summaries.

If the user asks to "click everything", perform a persona walk, or discover every interactive defect, route to `ultradetail-walk` first. If the user asks to keep doing that exhaustive walk after every fix until no new defects remain, route to `ultradetail-loop`.

## Round Loop

Each round has five stages:

1. Map the current target and declared checks for this round.
2. Verify Layer 1 to Layer 4.
3. Fix the smallest set of defects that block the declared checks.
4. Re-run the failed checks and inspect for regressions.
5. Record evidence, remaining gaps, and whether another round is needed.

Use this pass matrix:

| Layer | Purpose | Pass standard |
|---|---|---|
| 1 health | Server and route reachability | target services respond as expected |
| 2 live browser | Render, console, interaction, and state | critical journeys pass in the browser with no unexplained console/page failures |
| 3 data/API | Data consistency, permissions, migrations, API behavior | expected schema/response/authorization behavior is verified without destructive access |
| 4 code quality | Typecheck, lint, tests, build | relevant commands pass or known existing failures are documented |

Layer 2 must include interaction proof when the user flow has buttons, forms, menus, auth state, role switching, uploads, or navigation. A clean page load alone is not enough.

## Browser Proof

For each critical journey:

1. Navigate to the start route.
2. Inspect console messages, page errors, failed requests, and visible error boundaries.
3. Click or fill every declared user action.
4. Assert the resulting DOM, URL, network response, storage/cookie state, or visible UI state.
5. Capture screenshots only as evidence, not as the sole pass condition.

If Browser Use, Computer Use, and Playwright/scripted browser automation are all unavailable, stop and report that live verification cannot be completed. A degraded non-browser check may be useful, but it cannot satisfy Layer 2.

## Data And Safety

For data or DB checks:

- Prefer read-only inspection first.
- Never run destructive migrations, deletes, or production writes without explicit approval.
- For multi-role products, verify both route authorization and data isolation.
- Treat "admin can see seller data" or "seller A can access seller B data" as a cross-cutting matrix, not a single route check.

## Loop Control

Continue rounds until one of these happens:

- all declared termination criteria pass
- the user stops the loop
- the same defect fails three rounds in a row
- the configured round limit is reached
- a required tool, credential, or environment cannot be safely accessed

For unattended follow-up, use Codex heartbeat automation only when the user explicitly asks the thread to wake up and continue. Keep the prompt self-contained and include the next round number, target, and remaining gaps.

## Evidence

At the end of each round, report:

- checks run
- defects fixed
- evidence captured
- criteria still failing
- next action

For long loops, write a concise round note under `.thoughts/live-verify-rounds/` or update `session-handoff.md` when the project already uses those files. Do not create commits unless the user asked for commits.

## Red Flags

Stop and explain the risk if you catch yourself saying:

- a route loaded, so the feature works
- tests passed, so the live app works
- a screenshot looks fine, so interactions work
- a previous round checked this, so this round can skip it
- speed matters more than the declared verification layers
- an exhaustive walk is needed, but a light live loop is "probably enough"
