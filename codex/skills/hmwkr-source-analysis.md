# HMWKR Source Analysis

Sources:

- Initial import: `HMWKR/claude-code-skills` at `f9c4824a0de1f0a3c7d5b38511d7b90611dd40aa`.
- Update pass: `HMWKR/claude-code-skills` at `bcef14069d1714060d5f455f84c925c1bf378d07`.

## Missing Before Import

Compared with active `~/.agents/skills`, these repository skills were absent:

- `live-verify-loop`
- `harness-loop`
- `cantos-write`

## Import Decisions

`live-verify-loop` was rewritten as a Codex-native live browser verification loop. Source-specific runtime hooks, legacy paths, and recursive loop commands were replaced with Codex planning, Browser Use/Playwright proof, optional heartbeat follow-up, and explicit evidence recording.

`harness-loop` was rewritten as a Codex-native orchestration loop. Legacy agent folder discovery was replaced with current-session subagent policy and project custom agents under the Codex configuration.

`cantos-write` was treated as MCP-ready, not as a dead shim. The new skill prefers future Cantos MCP tools when connected and uses local Markdown only as an explicit fallback.

## 2026-05-07 Update

The upstream update generalized `live-verify-loop` by removing project-specific origin language and added two sibling skills:

- `ultradetail-walk`: one-shot exhaustive persona walk-through for discovery.
- `ultradetail-loop`: high-cost walk, fix, and re-walk convergence loop.

Codex adaptation:

- `live-verify-loop` now documents the three-skill live verification system.
- `ultradetail-walk` is a concise Codex skill with detailed matrices in `references/walk-matrices.md`.
- `ultradetail-loop` is a concise Codex skill with round and guardrail details in `references/loop-matrices.md`.
- Legacy runtime markers and legacy paths were not copied into active skill entrypoints.
