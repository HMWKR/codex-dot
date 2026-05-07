---
name: to-prd
description: Convert the current conversation, repo context, or feature discussion into a PRD suitable for a project issue tracker or local docs. Use when the user says "to PRD", "to-prd", "PRD로 만들어줘", "제품 요구사항 문서", "turn this into a PRD", or asks to publish a feature spec as an issue. Do not use for lightweight implementation plans unless the user wants a product-facing spec.
---

# To PRD

## Overview

Synthesize what is already known into a product requirements document. Do not interview by default; explore the repo if needed, infer carefully, and ask only when a missing decision would materially change the PRD.

## Workflow

1. Read existing context from the conversation.
2. Inspect repository signals if relevant:
   - `README.md`
   - `docs/`
   - `CONTEXT.md`
   - `docs/adr/`
   - related source files found with `rg`
3. Identify modules or areas likely to change, but avoid brittle file-path promises in the PRD.
4. Decide output target:
   - If the user asked for an issue and GitHub/Linear tooling is available, prepare or create the issue.
   - If no issue tracker is configured, write a local PRD draft only when the user asked for a file; otherwise provide the PRD in the response.
5. Apply a triage label such as `needs-triage` only when the project uses that vocabulary and the issue tracker supports it.

## PRD Template

Use the template in [references/prd-template.md](references/prd-template.md). Keep it product-facing:

- Problem Statement
- Solution
- User Stories
- Implementation Decisions
- Testing Decisions
- Out of Scope
- Further Notes

## Quality Rules

- Use the project's domain language when it exists.
- Express user stories as externally observable outcomes.
- Document implementation decisions at the module/interface level, not as volatile code snippets.
- Separate confirmed decisions from inferred decisions.
- Include testing decisions that verify behavior through public interfaces.
- State out-of-scope items explicitly to prevent scope drift.
- If the PRD would be misleading because core context is missing, ask one focused question before publishing.

## Publishing Rules

When creating an issue:

- Use the available GitHub, Linear, or other tracker connector if present.
- Confirm the target repository/project when more than one is plausible.
- Do not include secrets, private transcripts, or unstable file paths.
- Report the created issue URL in the final answer.

When writing a local draft, prefer `docs/prd/` or an existing product-docs location if the repo already has one. Use `apply_patch` for manual file creation.
