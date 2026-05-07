---
name: grill-me
description: Relentless but concise planning interview for resolving a plan, design, product idea, architecture choice, or ambiguous implementation request before execution. Use when the user says "grill me", "그릴미", "계획 검증", "질문하면서 다듬어줘", "stress-test this plan", "interview me about this", or when a plan has unresolved branches that would make implementation risky.
---

# Grill Me

## Overview

Use this skill to turn a fuzzy plan into explicit decisions. Ask one high-leverage question at a time, provide your recommended answer, and use repo exploration instead of user questions whenever the answer is discoverable from files.

## Operating Rules

- Ask exactly one question per turn unless the user asks for a batch.
- Include a recommended answer with each question.
- Prefer concrete alternatives over open-ended questions.
- If a question can be answered by reading the codebase, inspect the files first.
- Do not proceed to implementation until the critical decision tree is resolved or the user explicitly says to stop grilling.
- Keep the tone direct and useful. The goal is alignment, not interrogation theater.

## Workflow

1. Restate the plan in one sentence.
2. Identify the most load-bearing unresolved decision.
3. If local context can answer it, inspect files with `rg`, `rg --files`, `sed`, or equivalent before asking.
4. Ask one question in this format:

```text
Question: ...
Recommended answer: ...
Why it matters: ...
Options: A / B / C
```

5. After the user answers, update the decision state in a short note:

```text
Resolved: ...
Still open: ...
Next question: ...
```

6. Repeat until the next implementation step is obvious.
7. Finish with a decision brief:

```text
Goal:
Confirmed decisions:
Constraints:
Risks:
First implementation move:
```

## Question Selection

Prioritize questions in this order:

1. Success criteria and non-goals.
2. User or stakeholder behavior.
3. Data model, domain vocabulary, and invariants.
4. External dependencies and constraints.
5. Error handling, fallback, and rollback.
6. Testability and verification signal.
7. Scope splits and sequencing.

When the user asks for implementation after grilling, convert the final decision brief into `update_plan` items if there are three or more execution steps.

## Codex Fit

Use the current Codex environment rules:

- Use `rg` first for repository discovery.
- Ask concise plain-text questions in Default mode when the answer cannot be inferred safely.
- Respect user-owned dirty worktree changes.
- Do not spawn subagents unless the user explicitly requested delegation or parallel agent work.
- Do not write new files until the plan's first implementation move is clear.
