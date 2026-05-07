---
name: cantos-write
description: Cantos MCP writing workflow for ADR, DDR, journal, and visual verification records. Use when the user asks to write to Cantos, create ADR/DDR/journal entries, register a project in Cantos, attach visual verification evidence, or prepare records for a Cantos MCP connection. Prefer live Cantos MCP tools when connected; otherwise use an explicit local fallback.
---

# Cantos Write

## Overview

Use this skill to write durable project knowledge into Cantos. The intended path is MCP-first: when Cantos tools are available in the session, use them directly. Local Markdown is only a fallback when the MCP is not connected or the user asks for an offline draft.

## Tool Selection

1. Check whether Cantos MCP tools are available in the current tool list.
2. If available, use the matching MCP tool:
   - `mcp__cantos__create_adr`
   - `mcp__cantos__create_ddr`
   - `mcp__cantos__create_journal`
   - `mcp__cantos__register_project`
   - `mcp__cantos__list_projects`
   - `mcp__cantos__capture_visual`
3. If unavailable, say Cantos MCP is not connected in this session and offer a local draft under `docs/cantos/`.
4. Never pretend a remote Cantos write happened when only a local fallback was created.

## Record Types

| Type | Use when | Minimum content |
|---|---|---|
| ADR | architecture, tool, protocol, or policy decision | context, drivers, options, decision, consequences |
| DDR | UI/UX, design system, visual proof, product behavior decision | context, before/after, visual evidence, decision, impact |
| Journal | work log, learning, investigation, session note | summary, evidence, links, next action |

See [references/cantos-records.md](references/cantos-records.md) for schemas and local fallback paths.

## Workflow

1. Identify project, record type, title, and source evidence.
2. Build a slug from the title unless the user provides one.
3. Gather provenance: current repo, branch if relevant, files, commands, screenshots, issues, PRs, and user quotes when useful.
4. If registering a project or writing remotely for the first time, ask for explicit approval.
5. Call the Cantos MCP tool when available.
6. If MCP is unavailable and the user wants a draft, write local Markdown under `docs/cantos/<type>/`.
7. Report the destination and any missing evidence.

## Visual Verification Records

For visual or UI records:

1. Capture browser evidence with Browser Use by default, Computer Use when OS/browser-profile or desktop state matters, and Playwright/scripts when deterministic capture is useful.
2. Use `mcp__cantos__capture_visual` if connected.
3. Attach viewport, route, theme, timestamp, and pass/fail context to the DDR.
4. If only local fallback is available, place screenshots in the project’s normal screenshot directory or link existing evidence.

## Safety

- Do not register a project without explicit approval.
- Do not write secrets, access tokens, private customer data, or production credentials.
- Do not use Cantos as a substitute for tests or live verification evidence.
- Keep records factual: decision, reason, evidence, impact, and follow-up.
