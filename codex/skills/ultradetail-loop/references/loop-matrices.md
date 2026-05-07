# Ultradetail Loop Matrices

## Round Template

```markdown
## Ultradetail Loop Round N

- Target:
- Stable categories:
- Stable personas:
- Normal walk coverage:
- Adversarial walk coverage:
- New findings:
- Reopened findings:
- Fixes:
- Verification:
- Cost/risk note:
- Continue decision:
```

## Round Table

| Round | New defects | Fixed | Reopened | Remaining critical/high | Decision |
|---|---:|---:|---:|---:|---|
| 1 |  |  |  |  | continue |
| 2 |  |  |  |  | continue/stop |

## Guardrails

| Guardrail | Default |
|---|---|
| maximum rounds | 5 unless user asks for more |
| stagnation | stop after same defect survives 3 attempts |
| destructive flows | always require explicit approval |
| category/persona drift | requires user approval |
| browser tool unavailable | stop |

## Finding Lifecycle

| State | Meaning |
|---|---|
| new | first discovered this round |
| accepted | agreed valid defect |
| fixed | code/config/data changed |
| verified | re-walk proves behavior fixed |
| reopened | returned after fix |
| deferred | user accepted residual risk |

## Recommended Flow

1. Start with `ultradetail-walk` when the defect universe is unknown.
2. Use this loop when the user wants convergence, not just discovery.
3. Switch to `live-verify-loop` if the remaining defects are narrow and exhaustive re-walk is no longer worth the cost.
