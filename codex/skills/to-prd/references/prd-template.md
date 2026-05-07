# PRD Template

Use this template when `to-prd` needs a durable product requirements document.

## Problem Statement

Describe the user's problem from the user's perspective. Avoid implementation details unless they are necessary to understand the problem.

## Solution

Describe the intended user-facing solution. Name the core experience, workflow, or capability.

## User Stories

Write an extensive numbered list. Prefer this shape:

```text
1. As a <user or actor>, I want <capability>, so that <outcome>.
```

Cover primary, edge, permission, failure, and recovery scenarios.

## Implementation Decisions

List confirmed technical decisions without brittle code snippets. Include:

- modules or areas that will be built or changed
- interface-level decisions
- schema or API contract decisions
- architectural constraints
- explicit tradeoffs

## Testing Decisions

List how behavior will be verified. Include:

- public interfaces or user flows to test
- critical paths
- edge cases
- existing test patterns to follow
- what should not be mocked

## Out of Scope

List the boundaries that prevent the PRD from becoming a catch-all.

## Further Notes

Record assumptions, unresolved risks, follow-up questions, and links to related issues or docs.
