# Ultradetail Walk Matrices

## Defect Category Options

| Option | Bias | Use when |
|---|---|---|
| Balanced | routes, inputs, libraries, standards equally | general release-readiness |
| Security and permission | auth, role, IDOR, private data | multi-role or sensitive data apps |
| UX and micro-interaction | modals, focus, a11y, edge UI | rich interfaces and dashboards |
| Reliability and performance | loading, retry, cache, heavy pages | data-heavy or high-traffic apps |

## Defect Table Template

| Category | Signal source | Walk action | Impact | Rationale |
|---|---|---|---|---|
| permission bypass | protected routes and auth library | direct URL and role-switch checks | critical | role matrix can pass route load but fail data isolation |
| broken form state | forms and validation library | invalid/empty/max input attempts | high | user flow depends on valid feedback and submit state |
| modal focus trap | modal component detected | keyboard tab/escape/click outside | medium | accessibility and navigation can break despite visual pass |
| stale async state | query/cache library detected | navigate, mutate, back, reload | high | render can pass while data refresh fails |

## Persona Options

| Option | Persona shape |
|---|---|
| Realistic | likely production user distribution |
| Coverage | every role and permission level |
| Adversarial-heavy | fewer happy paths, more abuse paths |
| Custom | domain-specific actors from the user |

## Interactive Element Query Targets

Inspect at least:

```text
button
a[href]
input
select
textarea
[role=button]
[role=link]
[role=tab]
[role=menuitem]
[role=switch]
[role=slider]
[role=combobox]
[role=checkbox]
[role=radio]
[onclick]
[contenteditable]
```

## Finding Template

```markdown
| Severity | Persona | Route | Element | Repro | Evidence | Suggested fix |
|---|---|---|---|---|---|---|
```
