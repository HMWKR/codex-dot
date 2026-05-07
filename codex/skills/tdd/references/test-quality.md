# Test Quality Checklist

Use this reference when `tdd` needs to decide whether a test is worth keeping.

## Good Tests

- Verify observable behavior.
- Use the same public interface a caller, user, CLI, API client, or integration would use.
- Fail for a specific reason.
- Keep setup realistic but focused.
- Avoid asserting private function calls, internal names, or incidental data shapes.
- Survive a behavior-preserving refactor.

## Mocking

Mock only at true external seams:

- network services
- time
- random number generation
- slow storage or queue infrastructure
- paid APIs
- non-deterministic platform behavior

Avoid mocking internal collaborators just because it is convenient. If internals must be mocked to test behavior, the interface may be too shallow or the module may lack a useful seam.

## Vertical Slice Loop

```text
1. Pick one behavior.
2. Write one failing test.
3. Implement only enough code to pass.
4. Run the narrow test.
5. Refactor while green.
6. Run the broader relevant suite.
```

## Red Flags

- Tests pass while the user-facing behavior is broken.
- Tests fail after renaming internals while behavior is unchanged.
- Test setup is more complex than the behavior being tested.
- Assertions check implementation ordering with no user-visible effect.
- Multiple new tests fail for unrelated reasons in the same cycle.
