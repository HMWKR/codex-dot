# Rebuild 3-Pass Review

## 목적

이 문서는 Claude-native 하네스의 의도를 Codex-native 하네스로 별도 구현하기 전에 수행한 3회 검토 결과다. 이후 HTML 설명서와 실제 스킬 재작성은 이 검토 결과를 기준으로 진행한다.

## Pass 1: 원본 의도 추출

Claude-native 하네스의 핵심 의도는 단순한 도구 모음이 아니라, 개인 작업 방식 전체를 안정적으로 반복하기 위한 하네스다.

| 영역 | 원본 의도 | 확인한 위치 |
|------|----------|------------|
| 글로벌 지침 | CE 원칙, 한국어 출력, 세션 연속성, 검증 중심 문제 해결, 4섹션 커밋 메시지 | `~/.claude/CLAUDE.md` |
| commands | 분석, 사고여정, 오케스트레이션, PDCA gap 검증, 규칙 참조를 빠르게 활성화 | `~/.claude/commands/*.md` |
| agents | CE 리뷰, 코드베이스 탐색, 하네스 평가, 인프라 감사, 사고여정 생성 | `~/.claude/agents/*.md` |
| skills | reasoning, agent teams, QA, 보안, 문서/오피스, 배포, 웹 디자인 보조 | `~/.claude/skills/*` |
| hooks/scripts | 파괴적 명령 방지, 루프 방지, 체크포인트 저장, insight 수집 | `~/.claude/settings.local.json`, `~/.claude/scripts/*` |
| rules | 환각 방지, 안전, 루프 방지, insight 분산, skill-notion-sync | `~/.claude/rules/*` |

핵심 자산은 스킬 본문만이 아니다. 각 스킬이 기대하는 사용자 확인, 위임 방식, 검증 마커, 산출물 형식까지 함께 보존해야 한다.

## Pass 2: Codex 매핑

원본 의도는 유지하되 실행 문법은 Codex primitives로 바꿔야 한다.

| Claude 개념 | Codex-native 매핑 | 이유 |
|-------------|------------------|------|
| `CLAUDE.md` | `AGENTS.md` | Codex 프로젝트/글로벌 지침 파일명 |
| `~/.claude/skills` | `~/.agents/skills` | Codex 사용자 스킬 공식 위치 |
| `skill.md` | `SKILL.md` | Codex skill entrypoint 인덱싱 안정화 |
| slash command `/pdca` | `source-command-pdca` skill + 자연어 트리거 | Claude slash command 런타임은 Codex skill 호출과 다름 |
| `$ARGUMENTS` | 일반 prompt 문맥 또는 명시 질문 | Codex에서 자동 치환되지 않음 |
| `AskUserQuestion` | 필요한 경우 짧은 사용자 질문 | 현재 Codex 세션의 대화 모델에 맞게 조정 필요 |
| `TodoWrite` | `update_plan` | Codex의 계획/진행 상태 도구 |
| `Task tool`, `Agent tool` | `spawn_agent` 정책 또는 순차 fallback | Codex subagent는 사용 조건과 권한 정책이 다름 |
| `tools` allowlist | agent developer instruction의 행동 가이드 | Codex 권한 경계가 아님 |
| `PreCompact` prompt hook | 수동 점검/Stop checkpoint/문서화 | Codex hook lifecycle과 1:1 대응하지 않음 |

현재 Codex active harness는 큰 구조는 잡혀 있다.

- `~/.codex/AGENTS.md`: Claude 전역 지침을 Codex 경로와 용어로 변환함.
- `~/.codex/config.toml`: `features.codex_hooks = true`가 설정됨.
- `~/.codex/hooks.json`: command hook 중심으로 정리됨.
- `~/.codex/agents/*.toml`: 5개 agent가 Codex custom agent 형식으로 정리됨.
- `~/.agents/skills`: Claude 스킬 자산과 Codex-only 스킬이 공존함.

## Pass 3: 누락/오해/충돌 검토

3차 검토에서 확인한 위험은 다음과 같다.

| 위험 | 내용 | 조치 |
|------|------|------|
| 대소문자 착시 | macOS 파일시스템에서는 `SKILL.md` 조회가 실제 `skill.md`를 읽을 수 있다. | 디렉터리 엔트리 이름을 직접 검사한다. |
| 스킬 미인식 | 많은 Claude 스킬이 실제 파일명 `skill.md`라 Codex 인덱싱에서 빠질 수 있다. | target entrypoint를 `SKILL.md`로 재생성한다. |
| frontmatter 누락 | `agent-architect`는 YAML frontmatter가 없어 자동 트리거 품질이 낮다. | `name`, `description`을 추가한다. |
| Claude 도구명 잔재 | `AskUserQuestion`, `Task tool`, `Agent tool`, `TodoWrite`가 실행 지시처럼 남아 있다. | Codex-native 도구/대화 규칙으로 재작성한다. |
| slash command 기대 | `/think-teams`, `/pdca` 같은 호출을 사용자가 기대할 수 있다. | skill name과 자연어 트리거를 HTML/문서에 명확히 설명한다. |
| 세션 인덱스 | 현재 세션은 이전 후 추가된 skill을 즉시 재인덱싱하지 않을 수 있다. | 새 세션/재시작 필요성을 문서화한다. |
| 하네스 혼입 위험 | Codex active harness를 고치다 Claude-native 의미와 Codex-native 실행 의미가 섞일 수 있다. | Claude와 Codex를 독립 active harness로 분류한다. |
| 과도한 자동화 | 한 번의 스크립트 변환으로 의미를 다 살릴 수 없다. | 각 배치를 3-pass 검토 후 재작성한다. |

## 인벤토리 기준 수치

`tools/codex_harness_inventory.py` 실행 기준:

- Claude text files scanned: 336
- Codex text files scanned: 116
- Claude skill directories: 45
- Codex active skill directories: 50
- Claude command files: 5
- Claude agent files: 5
- UTF-8 failures: 0
- Files containing `U+FFFD`: 1
- Codex active `skill.md` entrypoints: 35
- Codex active Claude runtime marker skills: 21

`U+FFFD`는 Claude-native `~/.claude/skills/think-teams/skill.md`에 존재한다. Codex active harness는 이전 단계에서 문맥 복구되어 replacement 문자가 남지 않았다.

## HTML 작성 기준

HTML 설명서는 이 검토 결과를 반영해야 한다.

- “왜 단순 복사가 아닌 재구축인가”를 먼저 설명한다.
- Claude-native active harness와 Codex-native active harness를 분리해 보여준다.
- 3-pass 검토 게이트를 핵심 운영 방식으로 설명한다.
- Claude 개념과 Codex 매핑을 표로 보여준다.
- 사용자가 스킬을 어떻게 호출해야 하는지 설명한다.
- 인코딩, 백업, manifest, 검증이 왜 필요한지 설명한다.
- 현재 알려진 한계와 다음 작업 순서를 숨기지 않는다.

## Batch 1: source-command 재구축

### Pass 1: 원본 의도

Claude command 5개는 빠른 모드 전환용 자산이다.

| Command | 원본 의도 |
|---------|----------|
| `analyze` | 현재 작업을 심층 분석 모드로 다루고 검증 마커를 사용한다. |
| `journal` | CE 사고 여정을 `.thoughts/`에 기록한다. |
| `orchestrate` | Agent Teams 오케스트레이션 흐름을 활성화한다. |
| `pdca` | 설계와 구현의 gap을 비교하고 반복 개선한다. |
| `rules` | 하네스 규칙 계층과 참조 위치를 보여준다. |

### Pass 2: Codex 매핑

각 command는 `source-command-*` skill로 유지하되, Claude command template을 그대로 감싸는 방식은 중단했다.

- slash command는 자연어 호출과 skill name 호출로 전환했다.
- `$ARGUMENTS`는 Codex에서 자동 치환되지 않으므로 현재 요청에서 추론하거나 짧게 질문하도록 바꿨다.
- `orchestrate`는 Codex subagent 정책에 맞춰 “사용자가 명시적으로 위임/병렬 에이전트를 요청한 경우”에만 subagent를 사용하도록 바꿨다.
- `journal`은 사용자가 명시적으로 기록을 요청했을 때 `.thoughts/`에 작성하도록 조정했다.
- `rules`는 active Codex 경로를 기준으로 설명하도록 바꿨다.

### Pass 3: 누락/충돌 검토

- active `source-command-*` skill에서 `.claude`, `CLAUDE.md`, `Shift+Tab`, `Delegate Mode`, `$ARGUMENTS`, `Task tool`, `Agent tool`, `TodoWrite` 문자열이 남지 않도록 정리했다.
- Claude 참조 출처는 `~/.claude/...` 실행 경로가 아니라 `commands/*.md` reference entry로 표현했다.
- Codex validator 통과를 확인했다.

### 결과

- 최신 적용 백업: `/Users/leesungmin/Desktop/codex-dot/codex-harness-backups/20260504-140836`
- `source-command-*` 5개는 Codex-native 설명, 호출법, 제약, 출력 규칙을 갖는 `SKILL.md`로 재작성됐다.
- 인벤토리 기준 ready skill 수는 12개에서 13개로 증가했다.
- Claude runtime marker가 남은 target skill 수는 21개에서 20개로 감소했다.

## Batch 2: 최상위 스킬 구조 정규화

### Pass 1: 원본 의도

Claude-native 스킬은 대부분 `skill.md` 소문자 entrypoint와 Claude 전용 frontmatter를 사용했다. 보존할 것은 각 스킬의 workflow와 판단 기준이며, 파일명이나 Claude frontmatter 자체가 Codex 자산은 아니다.

### Pass 2: Codex 매핑

- 모든 최상위 스킬 entrypoint를 `SKILL.md` 대문자로 정규화했다.
- 최상위 스킬 frontmatter는 Codex 인덱싱에 필요한 `name`, `description` 중심으로 정리했다.
- `AskUserQuestion`, `Task tool`, `Agent tool`, `TodoWrite`, `Delegate Mode`, `Shift+Tab`, `argument-hint`, `user_invocable`, `CLAUDE_CODE` 같은 Claude 런타임 표기는 Codex active harness에서 실행 지시로 남지 않도록 변환했다.
- `_shared`는 skill entrypoint가 아니라 공유 리소스이므로 인벤토리 skill count에서 제외했다.

### Pass 3: 누락/충돌 검토

- macOS case-insensitive 파일시스템에서 `skill.md` → `SKILL.md` 변경이 실제 디렉터리 엔트리에 반영되도록 임시 파일을 거치는 rename을 적용했다.
- `think-teams`의 기존 `U+FFFD` 복구 로직이 `SKILL.md`에도 작동하도록 수정했다.
- postflight UTF-8 검증이 실패를 잡았고, 복구 후 재적용해 target replacement 문자를 0개로 만들었다.

### 결과

- 최신 적용 백업: `/Users/leesungmin/Desktop/codex-dot/codex-harness-backups/20260504-141259`
- Codex active skill directories: 49
- `SKILL.md` entrypoint: 49
- lowercase `skill.md` entrypoint: 0
- missing/incomplete frontmatter: 0
- entrypoint runtime marker skills: 0
- inventory 기준 ready skill: 49 / 49

## Batch 3: 상세 검증 게이트와 외부 후보 진입

### Pass 1: 원본 의도

외부 GitHub 후보는 우리 하네스를 대체하려는 대상이 아니라, 이미 정리한 Codex active harness를 보강할 reference 자료다.

| 후보 | 원본 의도 |
|------|----------|
| `bkit-codex` | PDCA와 Context Engineering을 Codex CLI workflow로 구현 |
| `agent-skills` | senior engineering lifecycle과 quality gate를 skill로 패키징 |
| `spec-kit` | constitution/spec/plan/tasks 중심의 spec-driven development 표준화 |
| `cc-sdd` | Kiro식 requirements/design/tasks와 boundary-first autonomous implementation |
| `oh-my-codex` | Codex CLI 위에 workflow/runtime/team layer 제공 |
| `ok-skills` | portable `SKILL.md` 예제와 범용 playbook 제공 |
| `codex-settings` | Codex CLI config, provider, prompt, experimental skill 예시 제공 |

### Pass 2: Codex 매핑

- `bkit-codex`는 `source-command-pdca`, `pipeline-orchestrator`, `project-bootstrapper`에 매핑한다.
- `agent-skills`는 `infra-audit`, `security-audit`, `continuous-qa-loop`, `github-workflow.md` 품질 게이트에 매핑한다.
- `spec-kit`과 `cc-sdd`는 `what-ce`, `architect`, `project-bootstrapper`, `agent-teams-*` 재구축 시 참조한다.
- `ok-skills`는 `gh-fix-ci`, `systematic-debugging`, `test-driven-development` 성격만 개별 선별한다.
- `oh-my-codex`와 `codex-settings`는 런타임/설정 설치가 아니라 운영 UX와 config 예시만 참고한다.

### Pass 3: 누락/충돌 검토

- 외부 install script는 `~/.codex`, `AGENTS.md`, hooks, provider config를 바꿀 수 있어 실행하지 않는다.
- MCP server, tmux runtime, provider routing은 현재 Codex App 하네스에 바로 넣지 않는다.
- slash command와 `$command` syntax는 우리 skill name과 자연어 trigger로 번역한다.
- 모든 반영은 `tools/codex_harness_verify.py`에서 `FAIL: 0`을 유지해야 한다.

### 결과

- `docs/github-harness-candidate-analysis.html` 작성.
- `docs/external-harness-import-notes.md` 작성.
- Batch 4A-4D import 순서 정의.

## Batch 4: Agent 운영 한도 128과 Goal 기능

### Pass 1: 원본 의도

사용자의 의도는 custom agent TOML 파일을 128개 생성하는 것이 아니라, Codex에서 agent 호출/운영 한도를 128 수준으로 확장하는 것이다.

확인된 현재 상태:

- custom agent 정의: 5개
- 공식 config key: `agents.max_threads`
- 기본값: unset일 때 6
- 로컬 CLI: `codex-cli 0.128.0-alpha.1`
- 로컬 feature flag: `goals under development false`

### Pass 2: Codex 매핑

| 요구 | Codex-native 매핑 |
|------|------------------|
| agent 운영 한도 128 | `~/.codex/config.toml`의 `[agents].max_threads = 128` |
| goal 기능 추가 | `~/.codex/config.toml`의 `[features].goals = true` |
| 5개 agent 유지 | `~/.codex/agents/*.toml` 5개 역할 정의는 그대로 유지 |
| 안정 검증 | `tools/codex_harness_verify.py`에 config/feature 검증 추가 |

### Pass 3: 누락/충돌 검토

- `agents.max_threads`는 상한(cap)이지 기본 fan-out 수가 아니다.
- 128개 agent 파일을 만들지 않는다.
- `goals`는 stable이 아니라 `under development` 기능이므로 문서에 실험 기능으로 기록한다.
- `multi_agent_v2`가 활성화된 상태에서는 `agents.max_threads`와 충돌할 수 있으므로 현재 `multi_agent_v2 = false` 상태에서만 운영한다.
- subagent spawn은 기존 정책처럼 사용자가 명시적으로 위임/병렬 에이전트 작업을 요청한 경우에만 사용한다.

### 결과

- `tools/codex_native_harness_migrate.py`가 `agents.max_threads = 128`과 `features.goals = true`를 유지하도록 수정.
- `tools/codex_harness_verify.py`가 agent thread cap과 local goals feature flag를 검사하도록 수정.
- 관련 문서에 custom agent 정의 개수와 agent thread 운영 한도의 차이를 기록.

## Batch 5: Claude/Codex 하네스 경계 분류

### Pass 1: 원본 의도

사용자의 의도는 Claude 하네스를 Codex의 보관소나 source layer로 낮추는 것이 아니다. Claude도 계속 사용하므로 Claude는 Claude-native active harness로 유지하고, Codex는 Codex-native active harness로 별도 운영한다.

추가 제약:

- 이 저장소가 설정하는 범위는 Codex 환경만이다.
- GitHub에서 clone한 다른 사용자의 Claude, Codex, 기타 홈 환경은 자동으로 수정되면 안 된다.
- 외부 하네스나 Claude 설정을 참고할 수는 있지만, 적용은 Codex 환경에 맞춘 별도 구현이어야 한다.

### Pass 2: Codex 매핑

| 요구 | Codex-native 매핑 |
|------|------------------|
| Claude/Codex 분리 | `docs/harness-boundary-classification.md`에 독립 active harness로 분류 |
| Codex만 설정 | 적용 대상은 `~/.codex`, `~/.agents/skills`로 제한 |
| clone 안전성 | migration 기본 실행을 dry-run으로 변경 |
| 명시 적용 | 실제 쓰기는 `python3 tools/codex_native_harness_migrate.py --apply`에서만 수행 |
| 검증 | `tools/codex_harness_verify.py`에 boundary classification 검사 추가 |

### Pass 3: 누락/충돌 검토

- `source corpus`/`target` 표현은 Claude를 하위 재료처럼 오해시킬 수 있어 핵심 정책 문서에서는 `Claude-native active harness`, `Codex-native active harness`, `Project control plane`로 바꾼다.
- `tools/codex_native_harness_migrate.py`는 Claude 경로를 읽을 수는 있지만 쓰면 안 된다.
- `.claude/`, `.codex/`, `checkpoint.md`, `session-handoff.md`, `codex-harness-backups/`는 Git에 올라가면 안 된다.
- verifier와 inventory는 읽기 전용이어야 하며, hook simulation은 임시 디렉터리에서만 부작용을 만든다.

### 결과

- `docs/harness-boundary-classification.md` 추가.
- migration 도구 기본 실행을 non-mutating dry-run으로 변경.
- GitHub workflow에 clone/default-run 안전 원칙과 `--apply` 명시 적용 원칙을 추가.
- verifier가 경계 문서, `.gitignore`, migration 기본 dry-run, GitHub workflow 안전 문구를 검사한다.

## Batch 6-7: Release Safety와 Developer Domain 확장

### Pass 1: 원본 의도

사용자의 의도는 하네스를 무작정 키우는 것이 아니라, GitHub에 공개했을 때 안전하게 재현되고 개발자 작업 범위를 잘 지원하는 구조를 만드는 것이다. 개발 대상은 IDE, 일반 앱, 게임, 영상 편집 도구처럼 폭이 넓으므로 공통 개발 절차와 도메인별 검증 포인트를 분리해야 한다.

### Pass 2: Codex 매핑

| 요구 | Codex-native 매핑 |
|------|------------------|
| rollback 가능성 | `--restore <backup_dir>` dry-run/apply 경로 |
| secret 유출 방지 | verifier `Secret/PII preflight` |
| 반복 실행 안정성 | migration dry-run idempotency 검사 |
| GitHub CI | `.github/workflows/verify.yml` + `--workspace-only` |
| spec/design/tasks | `docs/templates/*.md` |
| PDCA 상태 모델 | `docs/templates/pdca-status.schema.json` |
| 개발 도메인 확장 | `docs/developer-domain-extension-review.md` |

### Pass 3: 누락/충돌 검토

- GitHub runner에는 `~/.codex`가 없을 수 있으므로 전체 verifier를 그대로 돌리지 않는다.
- MCP server는 공용일 수 있지만 Claude와 Codex client 설정은 분리한다.
- 외부 MCP/plugin install script는 Codex-only 원칙을 깨뜨릴 수 있으므로 그대로 실행하지 않는다.
- IDE/게임/영상 도구 전용 skill은 실제 프로젝트가 생길 때 도메인별로 추가한다.

### 결과

- P1 보강은 repo 파일과 문서에만 반영했다.
- 홈 Codex/Claude 환경에는 적용 변경을 하지 않았다.
- GitHub 공개 runner용 workspace-only 검증 경로를 추가했다.

## Batch 8: Domain Profiles와 Codex-only Catalog

### Pass 1: 원본 의도

사용자가 추가로 요구한 범위는 IDE, 프로그램, 게임, 영상 편집 도구처럼 개발자가 만들 수 있는 제품군까지 하네스가 판단할 수 있게 하는 것이다. 단, MCP/plugin은 Codex-only 원칙을 유지해야 한다.

### Pass 2: Codex 매핑

| 요구 | Codex-native 매핑 |
|------|------------------|
| IDE/LSP 후보 | `docs/domain-profiles/ide-devtool.md` |
| 일반 앱/프로그램 | `docs/domain-profiles/app-program.md` |
| 게임 | `docs/domain-profiles/game-dev.md` |
| 영상/미디어 툴 | `docs/domain-profiles/media-tool.md` |
| MCP/plugin 후보 | `docs/codex-only-mcp-plugin-catalog.md` |
| 선택 보조 | `tools/codex_domain_profile.py` |

### Pass 3: 누락/충돌 검토

- 도메인 프로파일은 설치가 아니라 판단 자료다.
- Codex-only 카탈로그는 Claude 설정을 수정하지 않는다.
- 실제 MCP/plugin 적용은 프로젝트 도메인과 권한이 확인된 뒤 하나씩 진행한다.

### 결과

- 개발 도메인별 체크리스트, 후보 plugin/MCP, reject 기준을 문서화했다.
- 선택 보조 CLI를 추가했다.
- verifier가 새 문서들을 documentation sync 대상으로 검사한다.
