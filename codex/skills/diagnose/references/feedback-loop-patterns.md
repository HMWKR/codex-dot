# Feedback Loop Patterns

Use this reference when `diagnose` needs a reproduction strategy.

## Fastest Useful Loop

Choose the smallest loop that reproduces the user's symptom:

1. Unit or integration test when the behavior has a stable seam.
2. CLI command with fixture input when the bug is command-driven.
3. HTTP request script when the bug is API-driven.
4. Playwright or browser automation when the bug is UI-driven.
5. Captured payload replay when production-only input causes the bug.
6. Repeated stress loop when the bug is intermittent.
7. `git bisect run` when a regression range is known.

## Loop Quality

Improve the loop before fixing:

- Faster: cache setup and narrow initialization.
- Sharper: assert on the exact symptom.
- More deterministic: pin time, seed randomness, isolate filesystem and network.
- Safer: avoid production mutation and external side effects.

## Intermittent Bugs

Do not wait for a perfect repro. Increase reproduction rate:

- run the trigger many times
- parallelize isolated attempts
- add stress or timing pressure
- capture failure artifacts automatically
- reduce the scenario after a failure appears

## Performance Regressions

Measure before changing code:

- establish baseline timing
- run the same input repeatedly
- isolate warm-up and cache effects
- compare old vs new when possible
- prefer profiler, query plan, or flamegraph over broad logging

## No Loop

If no loop is possible, stop and ask for one of:

- a log dump
- HAR or network capture
- screen recording with timestamps
- fixture input
- failing environment access
- permission to add temporary instrumentation
