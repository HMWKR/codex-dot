---
name: diagnose
description: Disciplined bug and performance diagnosis loop - feedback loop first, reproduce, hypothesize, instrument, fix, regression-test, and clean up. Use when the user says "diagnose", "debug this", "원인 진단", "버그 진단", "깨졌어", "failing", "throwing", "performance regression", or reports a hard-to-explain failure.
---

# Diagnose

## Overview

Do not fix by staring. Build a fast, deterministic pass/fail loop first, then let hypotheses compete against that loop.

## Phase 1: Feedback Loop

Spend disproportionate effort here. A weak loop creates weak debugging.

Try these in order:

1. Failing unit, integration, or end-to-end test.
2. HTTP or CLI reproduction script with fixture input.
3. Headless browser check for UI bugs.
4. Captured trace or payload replay.
5. Small throwaway harness around the suspected module.
6. Property, fuzz, stress, or repeated-run loop for intermittent bugs.
7. Bisection or differential loop for regressions.
8. Human-in-the-loop script as a last resort. See [scripts/hitl-loop.template.sh](scripts/hitl-loop.template.sh).

If no loop can be built, stop and ask for a captured artifact: logs, HAR, screen recording, input fixture, core dump, or access to the environment that reproduces it.

## Phase 2: Reproduce

Run the loop until the reported failure appears. Confirm:

- the symptom matches the user's report
- the failure repeats or has a high enough reproduction rate
- the exact error, wrong output, or slow timing is captured

## Phase 3: Hypothesize

Generate 3-5 ranked hypotheses before changing code. Each hypothesis must predict what would make the bug disappear, move, or worsen.

Format:

```text
1. If ... is the cause, then ... should happen when we ...
```

Show the ranked list briefly before testing when the user is active. If the user is AFK, proceed with the best-ranked probe and report the list later.

## Phase 4: Instrument

Map each probe to one hypothesis. Change one variable at a time.

- Prefer debugger or REPL inspection when available.
- Use targeted logs at decision points.
- Prefix temporary logs with a unique tag like `[DEBUG-a4f2]`.
- Never leave untagged debug noise behind.
- For performance, measure a baseline first and compare one change at a time.

## Phase 5: Fix and Regression Test

When there is a correct seam, turn the minimized repro into a failing test before the fix. Then:

1. Watch the regression test fail.
2. Apply the smallest fix.
3. Watch the regression test pass.
4. Re-run the original broader loop.

If no correct seam exists, document that as an architecture finding and recommend `improve-codebase-architecture` after the bug is fixed.

## Phase 6: Cleanup and Report

Before declaring done:

- Original repro no longer fails.
- Regression test passes, or absence of a correct seam is documented.
- All `[DEBUG-...]` instrumentation is removed.
- Throwaway harnesses are deleted or clearly marked.
- The final report states the confirmed cause and the prevention opportunity.

For detailed loop patterns, read [references/feedback-loop-patterns.md](references/feedback-loop-patterns.md).
