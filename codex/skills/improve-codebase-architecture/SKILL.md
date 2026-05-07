---
name: improve-codebase-architecture
description: Architecture improvement skill for finding deepening opportunities, testability gaps, shallow modules, tangled seams, and AI-navigability problems in a codebase. Use when the user says "improve-codebase", "improve-codebase-architecture", "아키텍처 개선", "코드베이스 개선", "리팩터링 기회 찾아줘", "make this more testable", or asks for architecture-level refactoring candidates.
---

# Improve Codebase Architecture

## Overview

Surface architecture friction and propose deepening opportunities: changes that move complexity behind smaller, more stable interfaces.

## Vocabulary

Use these words consistently. Read [references/architecture-language.md](references/architecture-language.md) when the discussion becomes detailed.

- Module: anything with an interface and an implementation.
- Interface: what callers must know to use the module, including types, invariants, errors, ordering, and configuration.
- Implementation: the code behind the interface.
- Depth: how much useful behavior sits behind a small interface.
- Seam: a place behavior can change without editing callers in place.
- Adapter: a concrete implementation at a seam.
- Leverage: what callers gain from the module.
- Locality: how much change, bugs, and knowledge stay concentrated.

## Workflow

1. Read project context before judging architecture:
   - `CONTEXT.md` if present
   - `docs/adr/` if present
   - README and nearby docs
2. Explore the codebase with `rg`, `rg --files`, and focused file reads.
3. Notice friction while navigating:
   - understanding one concept requires many tiny files
   - modules pass data through without concentrating complexity
   - tests depend on internals or cannot reach real behavior
   - callers know too much about ordering, flags, or state
   - two or more adapters are trying to exist without a real seam
4. Apply the deletion test: if deleting the module makes complexity vanish, it was probably pass-through; if complexity reappears across callers, the module may be earning its keep.
5. Present candidates before proposing interfaces.

## Candidate Format

Use a numbered list:

```text
1. Candidate name
   Files/modules:
   Problem:
   Solution direction:
   Benefits:
   Testability impact:
   ADR/context conflicts:
```

Do not propose full interfaces in the first pass. Ask which candidate the user wants to explore.

## Exploration Rules

- Do not treat every abstraction as good. A pass-through wrapper is a shallow module.
- Do not fight ADRs unless real friction justifies reopening one.
- Prefer candidates that improve locality and test surface.
- Use project domain words from `CONTEXT.md` when available.
- If the user asks to proceed on one candidate, use `grill-me` style questioning to resolve the design tree.
- If a new domain term becomes load-bearing, offer to add it to `CONTEXT.md`.
- If the user rejects a candidate for a stable architectural reason, offer to record an ADR.

## Codex Subagent Policy

The original inspiration assumes an agent exploration tool. In this Codex harness, do not spawn subagents merely because the codebase is large. Use subagents only when the user explicitly asks for parallel agent work or delegation. Otherwise explore locally and keep findings grounded in file paths.
