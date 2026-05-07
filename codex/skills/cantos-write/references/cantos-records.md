# Cantos Record Reference

## ADR Shape

```yaml
type: adr
title:
slug:
status: proposed | accepted | superseded
context:
decision_drivers:
considered_options:
decision:
consequences:
provenance:
  repo:
  files:
  commands:
  links:
```

## DDR Shape

```yaml
type: ddr
title:
slug:
status: proposed | accepted | superseded
context:
visual_evidence:
  routes:
  viewports:
  screenshots:
decision:
impact:
follow_up:
```

## Journal Shape

```yaml
type: journal
title:
slug:
summary:
evidence:
next_action:
```

## Local Fallback Paths

Use these only when Cantos MCP is unavailable or the user asks for an offline draft:

```text
docs/cantos/adr/<slug>.md
docs/cantos/ddr/<slug>.md
docs/cantos/journal/<slug>.md
```

Each local fallback should include a note:

```text
Status: local draft, not yet synced to Cantos MCP.
```
