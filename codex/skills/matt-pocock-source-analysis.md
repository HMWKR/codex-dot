# Matt Pocock Skills Source Analysis

This document records the 3-pass import review for the Codex-native versions in this directory.

## Sources

- `grill-me`: https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me
- `to-prd`: https://github.com/mattpocock/skills/tree/main/skills/engineering/to-prd
- `tdd`: https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd
- `diagnose`: https://github.com/mattpocock/skills/tree/main/skills/engineering/diagnose
- `improve-codebase-architecture`: https://github.com/mattpocock/skills/tree/main/skills/engineering/improve-codebase-architecture

## Pass 1: Original Intent

| Skill | Original intent |
|---|---|
| `grill-me` | Interview the user about a plan until decisions and dependencies are explicit. |
| `to-prd` | Convert current context into a product requirements document and publish it to an issue tracker. |
| `tdd` | Build or fix behavior through a red-green-refactor loop, one vertical slice at a time. |
| `diagnose` | Debug hard bugs by building a feedback loop before hypothesizing or fixing. |
| `improve-codebase-architecture` | Find module-deepening opportunities that improve locality, leverage, and testability. |

## Pass 2: Codex Mapping

| Original concept | Codex-native mapping |
|---|---|
| Slash commands | Skill names and natural language triggers in frontmatter. |
| Agent exploration tool | Local `rg`/file reads by default; subagents only when the user explicitly asks for delegation. |
| Issue tracker publishing | Use available GitHub/Linear tools when present, otherwise return or write a local PRD draft. |
| Todo state | `update_plan` when the task has three or more execution steps. |
| Human questioning | Short plain-text questions in Default mode, one question at a time for `grill-me`. |
| Claude-specific runtime wording | Removed or rewritten as Codex behavior. |

## Pass 3: Conflict and Omission Review

- No copied Claude runtime markers are required.
- No skill writes to `~/.claude`.
- No skill requires a plugin cache path.
- No skill assumes subagents are available without explicit user request.
- `improve-codebase` is represented by the actual upstream folder name `improve-codebase-architecture`.
- Detailed checklists are split into one-level `references/` files to preserve progressive disclosure.
