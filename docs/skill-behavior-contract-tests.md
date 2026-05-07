# Skill Behavior Contract Tests

이 문서는 스킬이 실제 대화에서 지켜야 할 행동 계약을 deterministic하게 검증하기 위한 테스트 매트릭스다.
실제 모델 호출 결과를 채점하는 테스트가 아니라, `SKILL.md`가 트리거, 확인 질문, 중단 조건, 도구 우선순위, 금지 런타임 문구를 충분히 명시하는지 확인한다.

## Summary

- Contracts: 11
- Scenarios: 35
- PASS: 11
- WARN: 0
- FAIL: 0
- Workspace-only: `false`

## Command

```bash
python3 tools/codex_skill_contract_verify.py --markdown-output docs/skill-behavior-contract-tests.md --json-output docs/skill-behavior-contract-tests.json
```

## Interpretation

- `what`은 활성 스킬 루트의 골든 레퍼런스로 검사한다.
- `codex/skills`의 curated 스킬은 원본과 `$HOME/.agents/skills` 활성 사본의 해시 일치까지 검사한다.
- `PASS`는 문서 계약이 충분하다는 뜻이다. 실제 모델 회귀 테스트는 같은 시나리오를 headless Codex runner에 연결하면 확장할 수 있다.
- `WARN`은 workspace-only 환경에서 active root 검증을 건너뛴 경우처럼 의도적으로 약화된 검사다.

## Contract Results

| Skill | Source | Status | Scenarios | Key assertion summary |
|---|---|---|---:|---|
| `what` | active | PASS | 5 | all assertions passed |
| `grill-me` | curated | PASS | 3 | all assertions passed |
| `to-prd` | curated | PASS | 3 | all assertions passed |
| `tdd` | curated | PASS | 3 | all assertions passed |
| `diagnose` | curated | PASS | 3 | all assertions passed |
| `improve-codebase-architecture` | curated | PASS | 3 | all assertions passed |
| `live-verify-loop` | curated | PASS | 3 | all assertions passed |
| `harness-loop` | curated | PASS | 3 | all assertions passed |
| `cantos-write` | curated | PASS | 3 | all assertions passed |
| `ultradetail-walk` | curated | PASS | 3 | all assertions passed |
| `ultradetail-loop` | curated | PASS | 3 | all assertions passed |

## Scenario Matrix

### what

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| /what trigger | /what 이 기능의 목적을 정리해줘 | Announce then STEP 1 table only. | Ask whether the Why direction is right. | Do not jump to What before user confirmation. |
| yes advances one step | 맞아 | Advance only to the next pending step. | Ask for confirmation again at the new step. | Do not collapse multiple steps into one response. |
| modify branch | 수정이 필요해 | Offer concrete modification choices for the current step. | Ask which correction to apply. | Do not repeat the same table unchanged. |
| backtrack | 이전 Why가 틀렸어 | Announce that a prior step needs correction. | Ask whether to return to the earlier step or continue. | Do not keep later steps as confirmed after backtracking. |
| skip framework | 그냥 해줘 | Stop the framework and summarize confirmed context. | Confirm direct execution path if needed. | Do not continue the four-step loop. |

### grill-me

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| fuzzy plan | 그릴미. 결제 기능 만들 계획 검증해줘 | Restate plan and ask exactly one load-bearing question. | Include recommended answer and options. | Do not implement payment code. |
| repo-answerable | 이 구조에서 인증 방식을 질문하면서 정리해줘 | Inspect repo first when files can answer. | Ask only the unresolved decision. | Do not ask questions already answerable from files. |
| implementation handoff | 이제 구현해줘 | Convert final decision brief to plan when enough decisions exist. | Ask remaining critical question if still unresolved. | Do not proceed while critical branches remain open. |

### to-prd

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| known context | 지금 대화를 PRD로 만들어줘 | Synthesize the PRD from available context. | Ask only if a missing decision changes the PRD materially. | Do not start a broad interview. |
| issue publishing | 이걸 GitHub issue용 PRD로 만들어줘 | Prepare issue-shaped PRD and check target repo if ambiguous. | Confirm target when multiple repos/projects are plausible. | Do not publish to the wrong tracker. |
| local draft | docs에 PRD 파일로 남겨줘 | Use existing docs/prd or product-docs location. | Ask if output path materially changes project convention. | Do not use brittle source file promises. |

### tdd

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| feature request | TDD로 검색 필터 추가해줘 | Discover test runner and pick the first observable behavior. | Clarify public interface if ambiguous. | Do not write all tests before implementation. |
| bug regression | 이 버그를 regression-first로 고쳐줘 | Create a failing regression test first. | Ask if a stable behavior interface cannot be identified. | Do not patch without watching the test fail. |
| no tests wanted | 그냥 구현만 해 | Stop TDD path when user explicitly rejects tests. | Confirm direct implementation implications if needed. | Do not force TDD against explicit user direction. |

### diagnose

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| hard failure | diagnose. 로그인 후 깨져 | Build or find a deterministic repro loop first. | Ask for artifact if no loop can be built. | Do not jump straight to code changes. |
| intermittent bug | 가끔 실패해 | Choose repeated-run, stress, bisection, or differential loop. | Ask for reproduction artifacts if needed. | Do not claim fixed without rerunning the original loop. |
| performance regression | 최근 느려졌어 | Measure a baseline and map probes to hypotheses. | Report ranked hypotheses before or after probing. | Do not compare multiple changes at once. |

### improve-codebase-architecture

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| scan architecture | improve-codebase 해줘 | Read context and surface candidates first. | Ask which candidate to explore. | Do not propose full interfaces immediately. |
| testability focus | 이걸 더 테스트 가능하게 만들어줘 | Find seams and test surface problems. | Ask before deep-diving into a candidate. | Do not refactor without user selecting scope. |
| ADR conflict | 기존 결정이 이상해 보여 | Check ADR/context conflicts. | Ask whether to reopen or record an ADR when justified. | Do not fight stable ADRs casually. |

### live-verify-loop

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| ambiguous target | 100% 브라우저 통과할 때까지 봐줘 | Ask for missing target scope, mode, criteria, tool plan, and round limits. | Confirm ambiguous setup before loop. | Do not start clicking with undefined scope. |
| browser default | localhost UI live verify 해줘 | Use terminal for server/checks and Browser Use for proof. | Ask for credentials/destructive boundary if needed. | Do not require Playwright MCP when Browser Use can prove it. |
| desktop state | 다운로드와 파일 피커까지 검증해줘 | Escalate to Computer Use for OS/browser-profile state. | Confirm safe boundaries around files/accounts. | Do not treat terminal-only checks as live proof. |

### harness-loop

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| no delegation | 이 버그 고쳐줘 | Run locally with quality gates unless delegation was authorized. | Ask before spawning if task truly needs agents. | Do not spawn subagents by default. |
| explicit agents | agents plus verification로 개선해줘 | Route mode and assign disjoint ownership when delegating. | Clarify overlapping write scopes if needed. | Do not let workers revert unrelated changes. |
| UI changed | UI 고치고 검증까지 | Use Browser Use first and scripts for deterministic checks as needed. | Ask for credentials or destructive boundaries. | Do not accept static analysis as final UI proof. |

### cantos-write

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| mcp connected | Cantos에 ADR 써줘 | Use connected Cantos tool when available. | Ask approval before first remote registration/write if required. | Do not create only local markdown while claiming remote write. |
| mcp missing | Cantos DDR 준비해줘 | Say Cantos MCP is not connected and offer local draft. | Ask whether to create local fallback. | Do not pretend remote Cantos exists. |
| visual record | 브라우저 증거 붙여서 DDR | Capture Browser Use evidence by default, Computer Use if OS state matters. | Confirm missing visual evidence. | Do not substitute Cantos record for verification. |

### ultradetail-walk

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| broad walk | ultradetail로 버튼 전부 봐줘 | Confirm scope, roles, tooling, and create plan. | Offer category/persona options when broad. | Do not start without browser-capable tooling. |
| small scope | 이 한 페이지 클릭 전부 확인 | Make conservative category/persona recommendation and proceed if risk is small. | Ask only when scope/risk needs adjustment. | Do not remove selected personas silently. |
| no credentials | 관리자 플로우도 봐줘 | Stop if login/test data is missing and cannot be safely created. | Ask for test data or scope narrowing. | Do not use destructive flows. |

### ultradetail-loop

| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |
|---|---|---|---|---|
| release gate | ultradetail-loop로 출시 전까지 반복해줘 | Confirm scope, roles, browser tooling, hard limits, and evidence expectations. | Ask for destructive-flow boundaries. | Do not run an unbounded loop. |
| playwright missing | Playwright 없이 브라우저 루프 | Use Browser Use or Computer Use if they can provide evidence. | Ask only if no browser-capable tool exists. | Do not block merely because Playwright MCP is unavailable. |
| stagnation | 계속 같은 문제가 남아 | Stop or reassess after repeated failed fix attempts. | Ask whether to narrow, redesign, or stop. | Do not keep fixing symptoms forever. |
