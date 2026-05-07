---
name: ultradetail-walk
description: Exhaustive one-shot persona walk-through for web apps after implementation. Use when the user asks for ultradetail walk, exhaustive QA, persona walk, click everything, every button/form/menu, adversarial browser inspection, implementation-ready live audit, or "all interactions checked once". Skip for ongoing fix loops, simple page checks, or when the user wants repeated convergence.
---

# Ultradetail Walk

## Overview

Use this skill for one deep discovery pass. The goal is to find defects that normal route loads, tests, screenshots, and happy-path checks miss.

Core rule:

```text
rendered once != walked by real personas
```

The walk combines normal personas, adversarial personas, interactive element enumeration, and explicit defect categories. It reports findings; it does not automatically run a fix loop.

## Boundaries

- Use `live-verify-loop` after this skill when discovered defects need repeated fixes and verification.
- Use `ultradetail-loop` when every round must repeat the full walk after fixes.
- Use `playwright-qa-expert` for a narrower expert QA pass.
- Use `harness-loop` when this walk is one stage inside a broader orchestration.

## Preflight

Before walking:

1. Confirm target routes, environment, user roles, and whether test accounts exist.
2. Confirm browser proof tooling. Prefer Browser Use, add Computer Use for desktop/browser-profile setup, and reserve Playwright or scripts for deterministic automation. Without any browser-capable tool, stop; exhaustive walk cannot be completed.
3. Discover project shape from package/config files and source routes.
4. Decide whether Cantos evidence should be written through `cantos-write` when the MCP is connected.
5. Create an `update_plan` for the seven-step walk.

## Tool Priority

Use terminal commands for setup and static checks, then walk the product through Browser Use by default. Reach for Computer Use when the walk depends on OS-level browser state, profiles, downloads, file pickers, native dialogs, or installed-app behavior. Use Playwright or scripts when the same interaction must be repeated across routes, viewports, or regression runs.

Playwright-specific QA skills remain valid for scripted audits, but this skill's default proof path is the Codex desktop browser surface, not a Playwright MCP dependency.

## Seven-Step Walk

1. Preflight and project shape.
2. Discovery through six signal channels.
3. Defect category selection.
4. Persona selection.
5. Normal persona walk.
6. Adversarial persona walk.
7. Findings report and optional handoff to `live-verify-loop`.

For Step 3 and Step 4, propose 2-4 options and let the user adjust when the scope is broad or high-stakes. For small scopes, make a conservative recommendation and proceed unless it changes risk.

## Discovery

Use these signal channels:

| Channel | Look for |
|---|---|
| routes | protected areas, checkout, admin, account, onboarding |
| inputs | forms, filters, uploads, date fields, rich text, comboboxes |
| libraries | auth, payments, data fetching, forms, drag/drop, tables |
| components | modals, tabs, menus, tables, pagination, toast, tooltips |
| standards | accessibility, security, performance, SEO where relevant |
| prior pitfalls | live/browser mismatch, render-only checks, role isolation failures |

See [references/walk-matrices.md](references/walk-matrices.md) for defect and persona templates.

## Browser Walk

For each persona:

1. Establish auth/session state safely.
2. Navigate each selected route.
3. Enumerate interactive elements from the accessibility tree and DOM.
4. Interact with every relevant button, link, input, select, tab, menu item, switch, slider, dialog, and upload control.
5. Re-enumerate after each state change.
6. Capture console errors, page errors, failed requests, visual anomalies, and state mismatches.
7. Record the exact reproduction path.

Do not remove a persona, route, or defect category merely because it "seems unrealistic" after discovery. If it was selected, complete it or ask to narrow scope.

## Adversarial Pass

Apply adversarial checks based on risk:

- empty, max-length, special character, malformed, and hostile inputs
- unexpected order of operations
- rapid repeated clicks and interrupted flows
- direct navigation to restricted routes
- stale/loading/error states
- small and large viewport changes
- permission and data isolation attempts
- browser back/forward/reload behavior

## Report

Return:

- target and environment
- personas walked
- route and element coverage
- findings table with severity, reproduction, evidence, and suggested owner
- defects suitable for `live-verify-loop`
- Cantos record status when relevant

Do not claim a clean result unless every selected persona, route, and relevant interactive element was walked or explicitly scoped out.

## Stop Conditions

Stop if:

- browser tooling is unavailable
- login/test data is missing and cannot be safely created
- destructive flows would be required
- the target is too large for one pass and needs user narrowing
- the same element repeatedly destabilizes the app and blocks safe exploration
