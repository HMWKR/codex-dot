# Architecture Language

Use these terms when discussing `improve-codebase-architecture` findings.

## Module

Anything with an interface and an implementation: function, class, package, vertical slice, command, component, or subsystem.

## Interface

Everything a caller must know to use a module:

- type shape
- invariants
- error modes
- ordering rules
- configuration
- side effects
- performance expectations

## Implementation

The hidden work behind the interface.

## Depth

The amount of useful behavior behind a small interface. A deep module gives callers leverage. A shallow module forces callers to understand nearly as much as the implementation.

## Seam

A place where behavior can vary without editing callers in place.

## Adapter

A concrete implementation that sits at a seam.

## Leverage

What callers gain when a module is deep: fewer details, fewer decisions, and a more stable way to express intent.

## Locality

What maintainers gain when a module is deep: bugs, changes, and domain knowledge stay concentrated.

## Deletion Test

Imagine deleting the module:

- If complexity vanishes, it was likely a pass-through.
- If complexity reappears across many callers, the module was probably earning its keep.

## Real Seam Test

One adapter may be hypothetical. Two adapters usually prove a seam is real.
