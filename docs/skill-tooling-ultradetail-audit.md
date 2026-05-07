# Skill Tooling Ultradetail Audit

Date: 2026-05-07
Scope: active user skills in `/Users/leesungmin/.agents/skills` plus curated harness assets in `codex/skills`.

## Decision

For Codex Desktop and terminal-first harness work, browser verification should prefer this order:

1. Terminal for servers, builds, tests, lint, typecheck, logs, and local files.
2. Browser Use for normal live-browser proof on localhost, staging, forms, navigation, console state, visible UI, and screenshots.
3. Computer Use when proof depends on OS-level browser state, installed apps, browser profiles, login dialogs, downloads, file pickers, or native system prompts.
4. Playwright or scripts when deterministic selector, console, network, viewport, regression, or CI evidence is required.

Playwright MCP remains useful, but it should not be the default dependency for general Codex live verification when Browser Use or Computer Use can prove the behavior.

## Applied Changes

| Skill | Change |
|---|---|
| `live-verify-loop` | Replaced the generic Browser Use/Playwright wording with terminal-first, Browser Use default, Computer Use assisted, Playwright/scripted deterministic policy. |
| `ultradetail-walk` | Added Browser Use default walk policy and Computer Use escalation for desktop/browser-profile state. |
| `ultradetail-loop` | Added Browser Use default round policy and clarified that missing Playwright MCP alone should not stop the loop. |
| `harness-loop` | Updated the Web/UI quality gate to use Browser Use first, Computer Use second, Playwright/scripts for deterministic regression. |
| `cantos-write` | Updated visual evidence capture order to Browser Use, Computer Use, then Playwright/scripts. |

## Full Active Skill Scan

The active root contains 59 `SKILL.md` entrypoints.

| Area | Signal | Risk | Disposition |
|---|---|---|---|
| Newly curated live verification family | `Browser Use or Playwright` phrasing treated Playwright as equal/default | Medium: may route terminal Codex sessions into Playwright MCP unnecessarily | Fixed in curated source and synced into active root. |
| `playwright-qa-expert`, `playwright-qa-agent-teams`, `playwright-design-audit`, `playwright-uiux-audit` | Explicit Playwright MCP skills | Low when invoked by name, medium if used as generic live proof | Keep as specialized scripted-audit assets. Prefer `live-verify-loop` or `ultradetail-*` for default Codex browser proof. |
| `agent-teams-reactive-dev`, `continuous-qa-loop` | Observer/lead model is Playwright MCP-centered | Medium: useful legacy workflow, but tool selection is too narrow for Codex Desktop | Report-only in this pass. Candidate for a later Browser Use/Computer Use-first rewrite or companion skill. |
| `webapp-testing` | Playwright Python examples and selector reference | Low: intentionally a scripting toolkit | Keep. Use when deterministic local automation is desired, not as the default browser-proof route. |
| `superpowers` package | Claude, `.claude`, `CLAUDE_PLUGIN_ROOT`, `allowed-tools`, and Playwright references | Low in current verifier because it is a vendor/reference bundle; high if treated as active Codex runtime policy | Report-only. Do not mass rewrite vendor corpus without a dedicated migration. |
| `docx` and `pdf` | `Claude` appears as document author/comment metadata and OOXML validation marker | Low: content metadata, not active runtime instruction | Keep. This should remain an allowlisted reference/metadata signal. |
| `source-command-*` | Claude command origin notes | Low: historical bridge docs already say rebuilt as Codex-native skills | Keep. |
| `project-kickstart` | `/home/claude/{project-name}` and `claudemd-template.md` examples | Medium: path/runtime residue can mislead Codex users | Report-only for this pass. Recommended follow-up: migrate examples to workspace-relative paths and AGENTS.md naming. |
| `vercel-deploy` | `claude.ai` capability wording and Claude deploy endpoint | Medium: may be stale or environment-specific | Report-only. Needs a separate Vercel deploy policy review before editing. |
| `ppt-study`, `what`, `what-ce`, `ce-advisor`, `infra-audit` | MCP mentions are generic or tool-specific | Low: MCP availability checks are valid in Codex | Keep. |

## Routing Rule

When a user asks for real UI proof in this harness:

- use `live-verify-loop` for repeated browser-fix-browser convergence
- use `ultradetail-walk` for one exhaustive click/persona discovery pass
- use `ultradetail-loop` for repeated exhaustive walk-fix-walk release gates
- use Playwright-named skills only when the user explicitly wants Playwright/scripted QA or deterministic automation
- use Computer Use only when the proof depends on desktop/browser state that Browser Use cannot express cleanly

## Recommended Follow-Up Batches

1. Rewrite `agent-teams-reactive-dev` and `continuous-qa-loop` as Codex-native observer loops with Browser Use default and Playwright/scripted evidence optional.
2. Normalize `project-kickstart` away from `/home/claude` and Claude naming in generated templates.
3. Review `vercel-deploy` against the current Codex/Vercel plugin path before changing deployment behavior.
4. Decide whether `superpowers` should remain a reference/vendor corpus or be migrated into smaller Codex-native skills.

## Verification Expectations

After sync, the active root should show the updated policy in:

- `/Users/leesungmin/.agents/skills/live-verify-loop/SKILL.md`
- `/Users/leesungmin/.agents/skills/ultradetail-walk/SKILL.md`
- `/Users/leesungmin/.agents/skills/ultradetail-loop/SKILL.md`
- `/Users/leesungmin/.agents/skills/harness-loop/SKILL.md`
- `/Users/leesungmin/.agents/skills/cantos-write/SKILL.md`

The remaining broad Playwright references are intentional specialized skills or report-only legacy/vendor assets.

## Post-Sync Scan Snapshot

After sync, the 59 active `SKILL.md` entrypoints show:

- 5 skills mention Browser Use.
- 5 skills mention Computer Use.
- 17 skills mention Playwright.
- 9 skills mention Playwright MCP, including the newly fixed skills where the mention is a non-dependency warning.
- 1 active entrypoint still contains Claude runtime path wording: `project-kickstart`.

This is acceptable for the current pass because the active live-verification path now has Browser Use and Computer Use priority, while broader legacy rewrites are separated into follow-up batches.
