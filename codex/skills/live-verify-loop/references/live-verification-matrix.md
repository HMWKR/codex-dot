# Live Verification Matrix

## Verification Modes

| Mode | Primary focus | Typical tools |
|---|---|---|
| UI/UX | layout, responsive behavior, flows | browser navigation, screenshots, interaction assertions |
| Data | schema, migrations, integrity | read-only DB/MCP queries, app-visible state checks |
| Code quality | type safety, lint, tests | project test commands |
| API | status codes, payloads, auth | API client, browser network observations |
| Accessibility | keyboard, labels, contrast, focus | browser checks, axe when present |
| Performance | LCP/INP/CLS, waterfalls, bundle | trace, Lighthouse when present |
| SEO | metadata, sitemap, structured data | rendered DOM and route inspection |
| Security | auth, isolation, injection, secrets | safe scans and manual abuse cases |
| Integrated | cross-mode release check | selected checks from all relevant modes |

## Critical Journey Template

```yaml
journeys:
  - name: "new user completes core task"
    actor: "guest/user/admin/etc"
    start_route: "/"
    steps:
      - navigate: "/signup"
      - fill: "email/password/name"
      - click: "Create account"
      - assert: "dashboard visible and no console/page errors"
    data_expectation:
      - "created user belongs only to this account"
```

## Cross-Cutting Matrix

For multi-role applications, verify route and data access as a matrix:

| Actor | Own data | Other actor data | Admin area | Expected |
|---|---|---|---|---|
| guest | no | no | no | redirect or 401 |
| regular user | yes | no | no | 200 for own, 403/404 otherwise |
| admin | policy-defined | policy-defined | yes | explicit product policy |

## Pitfalls

- R45: HTTP 200 is not browser behavior.
- R54: green code checks do not prove live behavior.
- R55: automated test runner success is not the same as an observed browser flow.
- R75: type inference can regress through apparently local pagination or cursor changes.
- R76: skipping a declared verification layer is a self-violation unless the user approved the skip and the reason is recorded.
- R77: render-only checks miss broken buttons, forms, permissions, and state transitions.

## Basic Defect Casebook

Use this as a starter set before adding domain-specific defects:

| Defect | Signal | Fix direction |
|---|---|---|
| hydration mismatch | console/page error after route load | isolate client-only state behind mounted guards or server-safe defaults |
| duplicate API prefix | requests like `/api/api/...` | make one base URL source of truth |
| enum mismatch | UI state differs from API/domain enum | add explicit mapping at the boundary |
| undefined data | render crash from missing array/object | normalize query results and validate shape |
| cross-cutting exposure | shared header/menu leaks into restricted area | route-aware boundary or explicit permission branch |
| migration drift | UI/API assumes missing table/column/index | verify schema and migration state before live pass |

## Three-Skill Live Verification System

| Skill | Purpose | Cost | Stop condition |
|---|---|---|---|
| `ultradetail-walk` | one exhaustive discovery pass | high once | report complete |
| `live-verify-loop` | repeated focused fixes and live checks | medium per round | declared layers pass |
| `ultradetail-loop` | exhaustive walk, fix, and re-walk each round | very high | no new defects and all fixes verified |

## Round Evidence Template

```markdown
## Live Verify Round N

- Target:
- Mode:
- Checks run:
- Browser evidence:
- Data/API evidence:
- Code quality evidence:
- Fixes:
- Remaining gaps:
- Next round:
```
