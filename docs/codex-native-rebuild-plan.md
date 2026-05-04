# Codex-native 하네스 재구축 계획

## 결정

Claude 하네스와 Codex 하네스는 서로 독립된 active harness로 분류한다. 이 저장소가 설정하는 범위는 Codex 환경뿐이며, Claude 환경은 계속 Claude-native 방식으로 유지한다.

1차 마이그레이션은 백업, 인코딩 검증, 안전한 병합, Codex 경로 정리를 위한 bootstrap 단계였다. 이후 작업은 Claude의 각 스킬과 설정 Markdown을 심층 분석해 의도, 트리거, 워크플로우, 산출물을 추출하되, Codex에서 사용할 구현은 Codex-native 형식으로 별도 작성한다.

## 이유

- Claude slash command는 Codex skill 호출 방식과 다르다.
- Claude의 `AskUserQuestion`, `Task tool`, `TodoWrite`, `allowed-tools`, `argument-hint`는 Codex에서 같은 런타임 의미를 갖지 않는다.
- 일부 Claude 스킬은 `skill.md` 소문자 파일명, 약한 frontmatter, Claude 전용 환경 변수에 의존한다.
- 개인 스킬은 자산급이므로 손실 없는 보존과 재설계가 모두 필요하다.

## 하네스 경계

```text
Claude-native active harness:
  ~/.claude/skills
  ~/.claude/commands
  ~/.claude/agents
  ~/.claude/hooks
  ~/.claude/scripts
  ~/.claude/settings*

Codex-native active harness:
  ~/.agents/skills
  ~/.codex/AGENTS.md
  ~/.codex/agents
  ~/.codex/hooks.json
  ~/.codex/config.toml
  ~/.codex/scripts

Project control plane:
  tools/*
  docs/*
```

Claude-native active harness는 이 저장소가 수정하지 않는다. Codex-native active harness만 이 저장소의 적용 대상이며, 적용은 `--apply`를 명시했을 때만 수행한다. 상세 기준은 `docs/harness-boundary-classification.md`를 따른다.

## 재구축 워크플로우

1. Claude-native active harness와 Codex-native active harness를 분류한다.
2. 각 Markdown을 3-pass로 검토한다.
3. Codex 대응 가능성과 재설계 필요 지점을 분류한다.
4. Codex-native `SKILL.md`, agent TOML, hook script, AGENTS 지침으로 재작성한다.
5. UTF-8 strict, `U+FFFD`, JSON/TOML/Python/Shell, skill frontmatter 검증을 실행한다.
6. 검증 결과와 설계 결정을 `docs/`에 업데이트한다.

## 검증 게이트

GitHub 후보 하네스 검토나 저장소 push는 Codex-native active harness 검증이 먼저 통과해야 한다.

```bash
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

통과 기준:

- `docs/harness-verification-report.md`의 `FAIL`이 0개다.
- Codex active harness UTF-8 strict와 `U+FFFD` 검사가 통과한다.
- 모든 최상위 skill은 `SKILL.md`, `name`, `description`을 가진다.
- active Codex harness에는 의도된 역사적 언급을 제외한 `.claude`, `CLAUDE.md`, `~/.Codex/skills` 잔재가 없다.
- `docs/harness-boundary-classification.md` 기준으로 clone/default-run이 홈 환경을 수정하지 않는다.
- Codex hooks는 지원 이벤트의 command hook만 사용한다.
- `agents.max_threads = 128`로 agent thread 운영 한도가 설정되어 있다.
- `[features].goals = true`가 설정되어 있고, `goal`은 stable이 아니라 under-development 기능으로 문서화되어 있다.
- `WARN`은 원인과 허용 범위가 문서에 기록되어 있다.

## Agent 운영 한도와 Goal 기능

현재 custom agent 정의는 5개다.

- `ce-reviewer`
- `codebase-explorer`
- `harness-evaluator`
- `infra-auditor`
- `thoughts-writer`

이 숫자는 역할 정의 개수이며, 동시 운영 한도와 다르다. Codex 공식 config 기준으로 `agents.max_threads`는 동시에 열 수 있는 agent thread 최대 수다. 하네스는 대규모 orchestration 실험을 위해 이 값을 128로 설정한다.

`goal` 기능은 로컬 Codex CLI `0.128.0-alpha.1`에서 `goals` feature flag로 확인된다. 현재 stage는 `under development`이므로 안정 기능으로 단정하지 않고 실험 기능으로 활성화한다.

설정 기준:

```toml
[agents]
max_threads = 128

[features]
codex_hooks = true
goals = true
```

운영 원칙:

- custom agent 파일을 128개 생성하지 않는다.
- subagent spawn은 사용자가 명시적으로 위임/병렬 에이전트 작업을 요청한 경우에만 사용한다.
- 128은 상한(cap)이지 기본 fan-out 수가 아니다.
- `goal` 기능은 장기 목표/재개 흐름 검증용으로 사용하고, 실패 시 기존 checkpoint/session-handoff 흐름으로 fallback한다.

## 3-Pass 검토 게이트

한 번의 읽기만으로 변환하지 않는다. 각 스킬 또는 설정 묶음은 최소 3회 관점 검토 후 Codex active harness에 반영한다.

| Pass | 목적 | 확인 항목 |
|------|------|----------|
| Pass 1: Claude 의도 추출 | Claude Markdown을 그대로 읽고 원래 의도를 이해한다. | 트리거, 목적, 워크플로우, 도구, 확인 지점, 산출물 |
| Pass 2: Codex 매핑 | 원본 의도를 Codex 기능으로 옮길 수 있는지 판단한다. | `SKILL.md`, subagent 정책, hooks, scripts, AGENTS 지침, 미지원 의미 |
| Pass 3: 누락/오해/충돌 검토 | 앞선 두 검토에서 빠진 부분과 잘못 이해한 부분을 찾는다. | Claude 전용 잔재, 과도한 변환, 손실된 자산, 시스템 지침 충돌 |

Pass 3에서 문제가 발견되면 바로 작성하지 않고 Pass 1 또는 Pass 2로 되돌아간다.

## 변환 규칙

- 모든 Codex skill entrypoint는 `SKILL.md` 대문자를 사용한다.
- frontmatter는 최소 `name`, `description`을 포함한다.
- description에는 한국어와 영어 트리거를 함께 둔다.
- `/pdca`, `/think-teams` 같은 Claude command 호출은 자연어 트리거와 skill name 호출로 변환한다.
- `AskUserQuestion`은 Codex 대화 흐름에 맞춘 짧은 사용자 확인 규칙으로 바꾼다.
- `Task tool`, `Agent tool`은 Codex subagent 정책에 맞게 재작성한다.
- `TodoWrite`는 `update_plan` 사용 지침으로 바꾼다.
- Claude tool allowlist는 권한 경계가 아니라 행동 가이드로만 보존한다.

## 우선순위

1. `source-command-*`: Claude command의 의도를 Codex skill로 안정화한다. Batch 1에서 1차 재작성 완료.
2. `think-*`: 사고 체인 스킬을 Codex 질문/계획 흐름에 맞춘다.
3. `agent-teams-*`: Codex subagent 정책과 충돌하지 않게 재작성한다.
4. `infra-audit`, `security-audit`, QA 계열: 검증 하네스의 기준점으로 정리한다.
5. 문서/오피스/배포 보조 스킬: 트리거와 산출물 중심으로 정규화한다.

## 외부 GitHub 하네스 후보

Codex-native active harness가 `tools/codex_harness_verify.py`에서 `FAIL: 0`을 통과한 뒤에만 외부 GitHub 후보를 검토한다. 판단용 HTML은 `docs/github-harness-candidate-analysis.html`, 상세 import notes는 `docs/external-harness-import-notes.md`다.

외부 후보는 다음 순서로 다룬다.

1. `bkit-codex`: PDCA, Context Engineering, status model을 우리 `source-command-pdca`와 pipeline 계열에 매핑한다.
2. `addyosmani/agent-skills`: skill anatomy, verification gate, review/test/security 기준을 선별한다.
3. `github/spec-kit`, `cc-sdd`: SDD requirements/design/tasks 흐름을 project-bootstrap 계열과 연결한다.
4. `ok-skills`: 우리에게 없는 소형 skill만 선별한다.
5. `oh-my-codex`, `codex-settings`: runtime/config overwrite는 보류하고 운영 UX와 설정 예시만 참고한다.

외부 install script, provider 설정, 홈 디렉터리 overwrite는 실행하지 않는다. 모든 반영은 3-pass 검토와 상세 검증 게이트를 통과해야 하며, 이 저장소가 설정하는 범위는 Codex 환경만이다.

현재 import batch 제안:

1. Batch 4A: bkit-codex의 PDCA/CE phase gate를 `source-command-pdca`, `pipeline-orchestrator`에 매핑한다.
2. Batch 4B: agent-skills의 engineering quality gate를 GitHub/QA/review 문서에 반영한다.
3. Batch 4C: spec-kit/cc-sdd의 SDD 표준을 project bootstrap과 architecture 흐름에 연결한다.
4. Batch 4D: ok-skills의 GitHub CI triage 패턴을 push 이후 운영 문서로 확장한다.

## 진행 중 문서화 규칙

앞으로 하네스를 바꿀 때는 코드나 설정만 수정하지 않는다. 같은 작업에서 다음 문서 중 필요한 항목을 함께 업데이트한다.

- `README.md`: 저장소 목적, 현재 운영 모델, 빠른 실행.
- `docs/migration-summary.md`: 실제 적용 결과, 검증 결과, 발견된 한계.
- `docs/skill-asset-policy.md`: 스킬 자산 보존/수정/생성 정책.
- `docs/codex-native-rebuild-plan.md`: 재구축 전략, 변환 규칙, 우선순위.
- `docs/rebuild-3pass-review.md`: 배치별 3-pass 검토 결과.
- `docs/claude-corpus-inventory.md`: 인벤토리 도구로 생성한 현재 baseline.
- `docs/codex-native-rebuild-guide.html`: 사용자와 사람이 읽는 상세 재구축 설명서.
- `docs/github-harness-candidate-analysis.html`: 외부 GitHub 하네스 후보의 선별 흡수 판단 자료.
- `docs/external-harness-import-notes.md`: 외부 후보의 3-pass 검토와 batch별 import 기준.
- `docs/harness-boundary-classification.md`: Claude/Codex 독립 분류와 Codex-only 적용 원칙.
- `docs/developer-domain-extension-review.md`: IDE, 앱, 게임, 영상 편집 도구 개발 관점의 확장 후보.
- `docs/codex-only-mcp-plugin-catalog.md`: Codex-only MCP/plugin 후보와 reject 기준.
- `docs/domain-profiles/`: IDE, app, game, media tool 도메인별 개발 프로파일.
- `docs/templates/`: spec, design, tasks, PDCA 상태 모델 템플릿.
- `docs/harness-verification-report.md`: GitHub 작업 전 상세 검증 결과.
- `docs/harness-verification-report.json`: 자동화가 읽을 수 있는 상세 검증 결과.
- `docs/release-checklist.md`: Secret/PII, restore dry-run, idempotency, MCP 분리 기준.
- `docs/github-workflow.md`: GitHub에 올리기 전 확인 절차.

문서와 구현이 어긋나면 문서를 먼저 의심하지 않는다. 현재 코드, 실제 홈 디렉터리 상태, 검증 로그를 확인한 뒤 문서나 구현 중 틀린 쪽을 바로잡는다.

## 완료 기준

- Claude-native active harness는 이 저장소에 의해 수정되지 않는다.
- Codex active harness는 `SKILL.md` 대문자, frontmatter, Codex 경로 기준을 만족한다.
- Claude 전용 런타임 용어가 실행 지시로 남지 않는다.
- 새 Codex 세션에서 주요 스킬이 목록에 잡히고 자연어로 트리거된다.
- 모든 텍스트 파일이 UTF-8 strict로 읽히고 `U+FFFD`가 없다.
- 검증 명령이 통과하고 결과가 문서에 기록된다.

## 현재 산출물

- `tools/codex_harness_inventory.py`: Claude/Codex harness readiness를 읽기 전용으로 검사한다.
- `tools/codex_harness_verify.py`: agent thread cap, goals feature, hooks, skills, scripts, 인코딩, secret preflight, restore dry-run, dry-run idempotency를 상세 검증한다.
- `docs/harness-boundary-classification.md`: Claude-native active harness, Codex-native active harness, Project control plane 경계를 정의한다.
- `docs/release-checklist.md`: GitHub 배포 전 최종 안전 게이트를 정의한다.
- `.github/workflows/verify.yml`: GitHub runner에서 workspace-only verifier를 실행한다.
- `docs/developer-domain-extension-review.md`: 개발자 도메인별 MCP/plugin/skill 추가 후보를 Codex-only 기준으로 분류한다.
- `tools/codex_domain_profile.py`: 프로젝트 설명에 맞는 개발 도메인 프로파일과 Codex-only 후보를 추천한다.
- `docs/claude-corpus-inventory.md`: 첫 baseline 리포트.
- `docs/rebuild-3pass-review.md`: HTML 작성 전 3-pass 검토 기록.
- `docs/codex-native-rebuild-guide.html`: 재구축 방식의 상세 설명서.
