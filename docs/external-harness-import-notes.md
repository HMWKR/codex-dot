# External Harness Import Notes

## 목표

외부 GitHub 하네스를 그대로 설치하지 않고, 우리 Codex-native 하네스의 빈틈을 보강하는 패턴만 선별한다.

기준은 다음 순서다.

1. 개인 스킬 자산과 현재 Codex active harness를 우선한다.
2. Codex active harness의 `SKILL.md`, `AGENTS.md`, hooks, scripts, agents 정책을 깨지 않는다.
3. 외부 후보는 workflow, template, quality gate, state model 단위로만 흡수한다.
4. install script, provider 설정, 홈 디렉터리 overwrite, 인증/세션/캐시는 가져오지 않는다.
5. 반영 전후 `tools/codex_harness_verify.py`에서 `FAIL: 0`을 유지한다.

MCP server는 Claude 전용이 아니라 여러 클라이언트가 붙을 수 있는 서버다. 하지만 Claude와 Codex의 client 설정은 분리되어 있으므로, 외부 MCP를 검토할 때도 Codex 설정 후보만 다루고 Claude 설정은 수정하지 않는다.

## 2026-05-04 검토 기준

상세 검증 게이트:

- `FAIL: 0`
- Codex active harness UTF-8 strict 통과
- Codex active harness Claude-residue boundary 통과
- 49개 최상위 skill entrypoint 통과
- hooks/config/agents/scripts/hook simulation 통과

따라서 외부 후보 검토는 진행 가능하지만, 아직 외부 코드를 가져와 설치하는 단계는 아니다.

## 후보별 3-Pass 판단

### 1. bkit-codex

Source:

- <https://github.com/popup-studio-ai/bkit-codex>
- README 기준: PDCA methodology, Context Engineering, 27 Agent Skills, 16 MCP tools, 9-stage pipeline, 3 project levels, multilingual trigger, status/memory files.

Pass 1: 원본 의도

- PDCA를 개발 lifecycle의 중심으로 둔다.
- Plan → Design → Do → Check → Act → Report를 문서 산출물과 상태 파일로 관리한다.
- Context Engineering을 AGENTS.md, SKILL.md, references, MCP/state 계층으로 분리한다.
- 90% match threshold, max iteration, post-write gap analysis 같은 evaluator-optimizer 루프를 가진다.

Pass 2: 우리 하네스 매핑

| bkit 개념 | 우리 target |
|-----------|-------------|
| `$pdca plan/design/analyze` | `source-command-pdca` 자연어 trigger |
| `docs/.pdca-status.json` | 프로젝트별 `docs/.codex-pdca-status.json` 후보 |
| 9-stage pipeline | `pipeline-orchestrator`, `project-bootstrapper`, `project-kickstart` |
| 3 project levels | `project-bootstrapper`의 project classification 보강 |
| evaluator-optimizer loop | `source-command-pdca` match rate loop, `continuous-qa-loop` |
| MCP pre/post-write check | Codex hook + skill instruction + verification script |

Pass 3: 누락/충돌

- bkit MCP server를 바로 추가하면 우리 `.codex/config.toml`과 충돌할 수 있다.
- bkit install 방식은 `AGENTS.md`와 `.codex/config.toml`을 생성/수정하므로 그대로 실행하지 않는다.
- `$pdca` syntax는 Codex skill 호출 습관과 다르다. 우리 문서에서는 `source-command-pdca 실행`으로 유지한다.
- 상태 파일은 숨김 파일을 무분별하게 늘리지 말고 프로젝트 문서 구조 안에 둔다.

판정:

- P0 흡수 후보.
- 첫 반영은 코드 import가 아니라 `source-command-pdca`, `pipeline-orchestrator`, `project-bootstrapper`의 문서/워크플로우 보강이다.

## 2. addyosmani/agent-skills

Source:

- <https://github.com/addyosmani/agent-skills>
- README 기준: production-grade engineering skills, DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP lifecycle, 7 slash commands, skill auto-activation.

Pass 1: 원본 의도

- senior engineer의 반복 가능한 품질 습관을 skills로 포장한다.
- spec before code, small atomic tasks, tests as proof, review before merge를 강조한다.
- 개발 lifecycle을 command/skill 조합으로 단순하게 기억하게 만든다.

Pass 2: 우리 하네스 매핑

| agent-skills 개념 | 우리 target |
|-------------------|-------------|
| `/spec` | `what`, `what-ce`, `project-bootstrapper` |
| `/plan` | `source-command-pdca`, `pipeline-orchestrator` |
| `/build` | 기본 Codex coding workflow + `project-kickstart` |
| `/test` | `continuous-qa-loop`, `playwright-qa-expert`, `webapp-testing` |
| `/review` | `security-audit`, `infra-audit`, review stance |
| `/ship` | `vercel-deploy`, `github-workflow.md` |

Pass 3: 누락/충돌

- Claude slash command 중심 표현은 우리 skill trigger로 번역해야 한다.
- 이미 보유한 QA/보안/배포 스킬과 중복이 크다.
- 가져올 핵심은 새 skill 수가 아니라 quality gate 표현이다.

판정:

- P0/P1 품질 게이트 참고.
- `docs/github-workflow.md`, `docs/codex-native-rebuild-plan.md`, `infra-audit` 기준에 반영하기 좋다.

## 3. github/spec-kit

Source:

- <https://github.com/github/spec-kit>
- README 기준: Spec-Driven Development, constitution/specify/plan/tasks/implement 흐름, presets/extensions, Codex integration with skills option.

Pass 1: 원본 의도

- 구현 전에 specification과 governing principles를 먼저 세운다.
- specification, technical plan, task breakdown을 분리한다.
- preset으로 조직/도메인별 형식과 gate를 강제한다.

Pass 2: 우리 하네스 매핑

| spec-kit 개념 | 우리 target |
|---------------|-------------|
| constitution | `AGENTS.md`, `docs/codex-native-rebuild-plan.md` |
| specify | `what`, `what-ce`, `project-bootstrapper` |
| clarify | `source-command-analyze`, 짧은 사용자 확인 규칙 |
| plan | `source-command-pdca`, `pipeline-orchestrator` |
| tasks | `project-kickstart`, `session-handoff.md` |
| analyze | `source-command-pdca`, `infra-audit`, `security-audit` |
| implement | Codex normal implementation workflow |

Pass 3: 누락/충돌

- spec-kit CLI 초기화는 프로젝트 파일을 생성/수정하므로 우리 repo에 바로 실행하지 않는다.
- slash command 이름은 우리 skill name과 충돌하지 않게 문서 레벨에서만 참고한다.
- `.specify/` 구조는 도입 전 `.codex`/`docs` 상태 모델과 비교해야 한다.

판정:

- P1 표준 참조.
- 외부 표준명으로 문서화할 가치가 높지만, 첫 import 대상은 아니다.

## 4. cc-sdd

Source:

- <https://github.com/gotalab/cc-sdd>
- README 기준: Kiro-inspired SDLC, discovery/requirements/design/tasks/autonomous implementation, 17 skills, Codex stable support, boundary-first spec discipline.

Pass 1: 원본 의도

- spec을 code의 master command가 아니라 시스템 경계 계약으로 다룬다.
- discovery가 작업을 분류하고, requirements/design/tasks/impl로 이어진다.
- task마다 independent review와 auto-debug를 수행한다.
- design의 file structure plan과 task boundary를 강하게 본다.

Pass 2: 우리 하네스 매핑

| cc-sdd 개념 | 우리 target |
|-------------|-------------|
| discovery | `cynefin`, `what`, `source-command-analyze` |
| requirements | `what-ce`, `project-bootstrapper` |
| design | `architect`, `project-bootstrapper` |
| tasks | `pipeline-orchestrator`, `project-kickstart` |
| per-task review | `agent-teams-code-review`, review stance |
| auto-debug | `continuous-qa-loop`, `playwright-qa-agent-teams` |
| boundary-first | `architect`, `infra-audit`, CE review 기준 |

Pass 3: 누락/충돌

- autonomous implementation은 Codex subagent 정책상 사용자가 명시적으로 위임/병렬 작업을 요청한 경우에만 사용한다.
- 우리는 subagent를 자동으로 spawn하지 않는다.
- boundary annotations는 좋지만, 기존 문서 포맷과 충돌하지 않게 선택적으로 도입한다.

판정:

- P1/P2 후보.
- `architect`, `project-bootstrapper`, `agent-teams-*` 재구축 시 강하게 참고한다.

## 5. oh-my-codex / OMX

Source:

- <https://github.com/Yeachan-Heo/oh-my-codex>
- README 기준: Codex CLI workflow layer, `$deep-interview`, `$ralplan`, `$team`, `$ralph`, `.omx/` state, tmux runtime, Codex App is not default experience.

Pass 1: 원본 의도

- Codex 위에 stronger workflow/runtime layer를 얹는다.
- clarification → approved plan → team/persistent completion loop를 제공한다.
- runtime state와 HUD/team execution을 `.omx/`와 tmux로 관리한다.

Pass 2: 우리 하네스 매핑

| OMX 개념 | 우리 target |
|----------|-------------|
| `$deep-interview` | `source-command-analyze`, `think-teams`, `what-ce` |
| `$ralplan` | `source-command-pdca`, `architect`, `pipeline-orchestrator` |
| `$team` | `agent-teams-orchestrator`, explicit subagent delegation only |
| `$ralph` | `continuous-qa-loop`, session-handoff/checkpoint |
| `.omx/` state | 보류. 우리 상태 모델은 `docs/`와 Codex hooks 기준 |

Pass 3: 누락/충돌

- Codex App은 OMX의 default experience가 아니다.
- tmux/HUD/runtime hooks를 우리 Codex App 하네스에 바로 이식하면 안정성이 떨어질 수 있다.
- `omx setup`은 prompts, skills, AGENTS, config, hooks를 건드릴 수 있으므로 실행하지 않는다.

판정:

- 운영 UX와 role keyword만 참고.
- runtime import는 보류.

## 6. ok-skills

Source:

- <https://github.com/mxyhi/ok-skills>
- README 기준: 36 reusable skills, Codex/Claude/Cursor/OpenClaw 호환, docs lookup, browser automation, GitHub Actions debugging, planning, frontend, PDF/Office.

Pass 1: 원본 의도

- portable `SKILL.md` 예제와 범용 playbook을 제공한다.
- 몇 개만 골라 설치해도 가치가 나도록 작게 쪼개져 있다.

Pass 2: 우리 하네스 매핑

| ok-skills 후보 | 우리 상태 |
|----------------|-----------|
| planning-with-files | `session-handoff.md`, `checkpoint.md`, `pipeline-orchestrator`와 중복 |
| find-docs/get-api-docs | `domain-researcher`, `openai-docs`, Context7 plugin과 일부 중복 |
| gh-fix-ci | 현재 비어 있는 GitHub CI 운영 영역 보강 가능 |
| systematic-debugging | `continuous-qa-loop`, `source-command-analyze` 보강 가능 |
| test-driven-development | QA 계열 스킬의 TDD gate 강화 가능 |

Pass 3: 누락/충돌

- 문서/오피스/브라우저 계열은 이미 우리 하네스와 Codex plugins에 상당히 있다.
- top-level clone 방식은 스킬 root를 중첩시켜 검색 품질을 떨어뜨릴 수 있다.
- 실제 흡수는 개별 `SKILL.md` 단위로만 판단한다.

판정:

- P2 개별 선별.
- 첫 후보는 `gh-fix-ci`, `systematic-debugging`, `test-driven-development`.

## 7. codex-settings

Source:

- <https://github.com/feiskyer/codex-settings>
- README 기준: Codex CLI config, providers, prompts, experimental skills, quick start가 `~/.codex` 백업 후 clone 방식.

Pass 1: 원본 의도

- Codex CLI 설정 예시와 provider routing, prompts, experimental skills를 제공한다.
- LiteLLM/OpenRouter/Azure/ChatGPT 등 다양한 model provider 구성을 보여준다.

Pass 2: 우리 하네스 매핑

| codex-settings 개념 | 우리 target |
|---------------------|-------------|
| provider config examples | 참고만. 현재 config 보존 |
| prompts | Codex prompt 기능 도입 여부 검토 |
| autonomous-skill | `continuous-qa-loop`, explicit automation policy와 비교 |
| kiro/spec-kit skills | spec-kit/cc-sdd 판단과 통합 |
| `/skills` discovery note | 사용자 호출 문서 보강 |

Pass 3: 누락/충돌

- `mv ~/.codex ~/.codex.bak` 후 clone은 우리 보존 정책과 정면 충돌한다.
- provider 설정은 인증/과금/라우팅에 영향을 주므로 가져오지 않는다.
- Claude Code 연동 skill은 우리 현재 목표와 다르다.

판정:

- reference only.
- config overwrite 금지.

## Import Batch 제안

### Batch 4A: PDCA/CE 보강

목표:

- bkit의 PDCA status, phase gate, evaluator-optimizer 표현을 우리 `source-command-pdca`와 docs에 반영한다.

대상:

- `docs/rebuild-3pass-review.md`
- `docs/codex-native-rebuild-plan.md`
- 추후 승인 시 `~/.agents/skills/source-command-pdca/SKILL.md`
- 추후 승인 시 `~/.agents/skills/pipeline-orchestrator/SKILL.md`

도입:

- Plan/Design/Do/Check/Act/Report 산출물 표준
- match rate 90% 기준
- max iteration 정책
- design missing 시 구현 중단
- post-write gap analysis 권장

제외:

- bkit MCP server 설치
- `.codex/config.toml` 자동 수정
- `$pdca` 호출 문법

### Batch 4B: 품질 게이트 보강

목표:

- agent-skills의 DEFINE/PLAN/BUILD/VERIFY/REVIEW/SHIP 흐름을 우리 GitHub/QA/review 문서에 반영한다.

대상:

- `docs/github-workflow.md`
- `docs/codex-native-rebuild-guide.html`
- 추후 승인 시 `infra-audit`, `security-audit`, `continuous-qa-loop`

도입:

- tests are proof
- review before merge
- small atomic tasks
- ship gate checklist

제외:

- Claude slash commands
- marketplace/plugin install

### Batch 4C: SDD 표준 참조

목표:

- spec-kit과 cc-sdd의 constitution/spec/requirements/design/tasks/boundary-first 개념을 우리 project bootstrap 흐름과 연결한다.

대상:

- `project-bootstrapper`
- `architect`
- `what-ce`
- `agent-teams-*`

도입:

- constitution/guiding principles
- requirements/design/tasks 분리
- file structure plan
- task boundary/dependency annotation
- independent review loop

제외:

- `specify init` 실행
- `npx cc-sdd` 실행
- autonomous subagent auto-spawn

### Batch 4D: GitHub 운영 보강

목표:

- ok-skills의 `gh-fix-ci` 성격을 참고해 GitHub push 이후 CI 대응 문서를 만든다.

대상:

- `docs/github-workflow.md`
- 신규 후보: `docs/github-ci-triage.md`

도입:

- failing checks 수집
- 로그 요약
- root cause / fix plan / verification 분리

제외:

- `yeet`류 일괄 stage/commit/push 자동화
- remote가 정해지지 않은 상태의 push

## 즉시 결정

- 지금 가져올 것: 문서화된 판단 기준, PDCA/quality gate/SDD mapping.
- 지금 가져오지 않을 것: 외부 repo 설치, MCP server, runtime hooks, provider config, 홈 디렉터리 overwrite.
- 다음 실제 반영 우선순위: Batch 4A → Batch 4B → Batch 4C → Batch 4D.

## 출처

- bkit-codex: <https://github.com/popup-studio-ai/bkit-codex>
- agent-skills: <https://github.com/addyosmani/agent-skills>
- spec-kit: <https://github.com/github/spec-kit>
- cc-sdd: <https://github.com/gotalab/cc-sdd>
- oh-my-codex: <https://github.com/Yeachan-Heo/oh-my-codex>
- ok-skills: <https://github.com/mxyhi/ok-skills>
- codex-settings: <https://github.com/feiskyer/codex-settings>
