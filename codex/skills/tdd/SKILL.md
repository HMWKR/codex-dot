---
name: tdd
description: Test-driven development loop for implementing features or fixing bugs one observable behavior at a time. Use when the user asks for TDD, "red-green-refactor", "test first", "TDD + 피드백 루프", integration-test-first development, regression-first bug fixes, or wants a disciplined feedback loop while coding.
---

# TDD

## Overview

Use one test, one minimal implementation, one refactor at a time. Tests should verify behavior through public interfaces, not internal structure.

## Core Rule

Do not write all tests first and then all implementation. That creates imagined tests. Work in vertical slices:

```text
RED: one behavior test fails
GREEN: minimal code makes it pass
REFACTOR: improve structure while tests stay green
repeat
```

## Workflow

1. Discover the existing test runner and nearby test style.
2. Clarify the public interface and highest-value behaviors if they are ambiguous.
3. Create an `update_plan` when there are three or more behavior slices.
4. Write the first failing test for one observable behavior.
5. Run the narrowest relevant test command and confirm it fails for the expected reason.
6. Implement the smallest change that passes that test.
7. Run the narrow test again.
8. Repeat for the next behavior.
9. Refactor only while all touched tests are green.
10. Finish with the broader relevant test command.

## Good Test Standard

- Describes what the system does.
- Uses public interfaces or user-facing flows.
- Would survive a refactor that preserves behavior.
- Fails for one clear reason.
- Avoids mocking internal collaborators unless the external dependency is slow, flaky, expensive, or impossible to run locally.

See [references/test-quality.md](references/test-quality.md) for the checklist.

## Refactor Gate

Refactor after green, not before. Look for:

- duplicated behavior setup
- shallow pass-through modules
- unclear interface boundaries
- complex logic hidden behind UI or I/O code
- names that drift from domain vocabulary

When refactoring reveals an architectural testing problem, hand off to `improve-codebase-architecture`.

## Stop Conditions

Stop and ask before proceeding if:

- the behavior cannot be expressed through a stable interface
- the test runner cannot be identified
- writing a meaningful test requires production credentials or live destructive data
- the user explicitly wants implementation without tests
