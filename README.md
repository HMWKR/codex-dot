# codex-dot

Codex-native harness control-plane repository.

이 저장소는 Codex 환경에만 하네스를 설정하기 위한 제어 저장소다. Claude 하네스와 Codex 하네스는 서로 독립된 active harness로 분류하고, 실제 홈 디렉터리 설정(`~/.codex`, `~/.agents/skills`)은 Git에 직접 넣지 않고 재현 가능한 도구와 운영 문서로 관리한다.

현재 방향은 단순 복사가 아니라, Claude-native 하네스의 의도와 워크플로우를 읽어 Codex-native 구현으로 별도 설계하는 것이다. Claude 환경은 수정하지 않고, Codex 적용은 명시적 `--apply`가 있을 때만 수행한다. 경계 기준은 `docs/harness-boundary-classification.md`가 우선한다.

## AI-first 사용법

AI 에이전트에게 이 저장소 URL만 주고 하네스를 맞추게 하려면 다음처럼 요청한다.

```text
https://github.com/HMWKR/codex-dot 를 기준으로 내 Codex 하네스를 맞춰줘.
먼저 AI_BOOTSTRAP.md와 codex-harness.manifest.json을 읽고,
clone → dry-run → validate → explicit apply 순서로 진행해.
```

AI가 가장 먼저 읽어야 할 파일:

- `AI_BOOTSTRAP.md`: AI 실행 계약, macOS/Windows 분기, 금지 경계, 적용 순서.
- `codex-harness.manifest.json`: 스킬/훅/에이전트/MCP/검증 기준의 machine-readable SSoT.
- `docs/harness-boundary-classification.md`: Claude와 Codex를 섞지 않는 경계 기준.
- `docs/skills-index.md`: 활성 개인 스킬 59개의 라우팅용 인덱스.
- `docs/skill-behavior-contract-tests.md`: 스킬 트리거/확인 질문/중단 조건 행동 계약 테스트.
- `docs/troubleshooting.md`: 훅, 스킬, MCP, 터미널 문제의 진단/복구 경로.

OS별 기본 흐름:

```bash
# macOS
git clone https://github.com/HMWKR/codex-dot.git
cd codex-dot
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

```powershell
# Windows PowerShell
git clone https://github.com/HMWKR/codex-dot.git
Set-Location codex-dot
py -3 tools/codex_native_harness_migrate.py
py -3 tools/codex_harness_verify.py --workspace-only --markdown-output .\docs\harness-verification-report.md --json-output .\docs\harness-verification-report.json
```

실제 적용은 두 OS 모두 사용자가 명시적으로 승인한 뒤에만 실행한다. Windows native 적용은 hook command의 shell 호환성을 먼저 확인한다.

## 핵심 원칙

- Claude-native active harness와 Codex-native active harness를 분리한다.
- 이 저장소가 설정하는 대상은 Codex 환경(`~/.codex`, `~/.agents/skills`)뿐이다.
- GitHub에서 clone하거나 기본 명령을 실행하는 것만으로 사용자의 홈 환경을 수정하지 않는다.
- Claude 스킬은 개인 자산으로 취급하되 Claude 환경은 그대로 유지한다.
- Codex 실사용본은 Claude의 의도, 트리거, 워크플로우를 분석해 Codex-native 형식으로 별도 구현한다.
- Codex 설정은 `~/.codex`, 사용자 스킬은 `~/.agents/skills`를 기준으로 한다.
- Custom agent 정의는 현재 5개를 유지하되, 운영 한도는 `agents.max_threads = 128`로 확장한다.
- `goal` 기능은 로컬 Codex CLI에서 `goals` feature flag가 `under development` 상태임을 명시하고 실험 기능으로 활성화한다.
- 한글/인코딩 깨짐 방지를 위해 UTF-8 strict 검증과 `U+FFFD` 검사에 실패하면 적용을 중단한다.
- 실제 적용은 `--apply`를 명시했을 때만 수행하고, 실행 전 백업과 SHA-256 manifest를 남긴다.
- 인증, 세션, 플러그인 캐시, 런타임 상태 파일은 Git에 올리지 않는다.
- 하네스 변경은 관련 문서 업데이트와 같은 작업 단위로 처리한다.

## 구성

```text
AI_BOOTSTRAP.md                    # AI 에이전트가 가장 먼저 읽을 실행 계약
codex-harness.manifest.json         # 하네스 대상/검증/OS 분기 machine-readable manifest
tools/
  codex_native_harness_migrate.py   # Codex 환경 적용 도구, 기본 dry-run
  codex_curated_skill_sync.py        # codex/skills curated 스킬을 ~/.agents/skills로 명시적 동기화
  codex_normalize_active_skill_agents.py # 활성 스킬의 oversized AGENTS.md 참조를 references/로 정규화
  codex_skill_index.py               # 활성 개인 스킬의 Markdown/JSON 라우팅 인덱스 생성
  codex_skill_contract_verify.py      # 스킬 행동 계약 테스트: 질문/확인/도구 우선순위/중단 조건
  codex_harness_inventory.py        # Claude/Codex 자산 인벤토리와 재구축 baseline 리포트
  codex_harness_verify.py           # 상세 검증 게이트: 인코딩, hooks, skills, scripts, GitHub preflight
codex/
  skills/                           # Codex-native curated 스킬 원본, 명시적 sync 후 활성화
docs/
  migration-summary.md              # 최근 이전 결과와 검증 요약
  skills-index.md                    # 개인 스킬 라우팅 인덱스
  skills-index.json                  # AI-readable 스킬 인덱스(raw)
  skill-behavior-contract-tests.md    # 스킬별 행동 계약 테스트 매트릭스
  skill-behavior-contract-tests.json  # 스킬별 행동 계약 테스트 결과(raw)
  troubleshooting.md                 # 운영 중 문제 진단/복구 가이드
  codex-native-rebuild-plan.md       # Claude 자산 분석 기반 재구축 전략
  codex-native-rebuild-guide.html    # 3-pass 재구축 방식 상세 HTML 설명서
  github-harness-candidate-analysis.html # 외부 GitHub 하네스 후보 판단용 HTML
  external-harness-import-notes.md   # 외부 후보를 우리 하네스로 흡수하기 위한 3-pass notes
  harness-boundary-classification.md # Claude/Codex 독립 분류와 Codex-only 적용 원칙
  developer-domain-extension-review.md # IDE/앱/게임/영상 툴 개발 후보 검토
  codex-only-mcp-plugin-catalog.md  # Codex-only MCP/plugin 후보 카탈로그
  domain-profiles/                  # IDE/app/game/media 개발 도메인 프로파일
  templates/                         # spec/design/tasks/PDCA 상태 템플릿
  rebuild-3pass-review.md            # HTML 작성 전 수행한 3-pass 검토 기록
  claude-corpus-inventory.md         # 현재 Claude/Codex 자산 인벤토리 리포트
  harness-verification-report.md     # 최신 상세 검증 결과
  harness-verification-report.json   # 최신 상세 검증 결과(raw)
  release-checklist.md               # GitHub 배포 전 Secret/Restore/Idempotency 게이트
  skill-asset-policy.md             # 스킬 자산 관리 원칙
  github-workflow.md                # GitHub 푸시/운영 절차
  macos-terminal-codex-setup.md      # macOS 터미널 codex 명령 고정 설치 절차
.gitignore                          # 런타임 상태와 백업 제외
.github/workflows/verify.yml         # GitHub runner용 workspace-only 검증
```

## 빠른 실행

```bash
python3 tools/codex_harness_inventory.py --output docs/claude-corpus-inventory.md
python3 tools/codex_curated_skill_sync.py
python3 tools/codex_skill_index.py
python3 tools/codex_skill_contract_verify.py --markdown-output docs/skill-behavior-contract-tests.md --json-output docs/skill-behavior-contract-tests.json
python3 tools/codex_domain_profile.py --query "browser game with level editor"
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
python3 tools/codex_curated_skill_sync.py --apply
python3 tools/codex_native_harness_migrate.py --apply
```

적용 대상:

- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- `~/.codex/hooks.json`
- `~/.codex/agents/*.toml`
- `~/.codex/rules/*`
- `~/.codex/scripts/*`
- `~/.agents/skills/*`

Curated Codex-native skills are versioned under `codex/skills/*` and copied into
`~/.agents/skills/*` only through explicit sync or apply actions.

## 최신 상태

2026-05-04 기준으로 개인 스킬 371개 파일을 Codex 스킬 위치에 반영했고, Codex validator와 UTF-8 검증을 통과했다. 이후 Batch 2에서 최상위 49개 스킬은 모두 `SKILL.md`, `name`, `description`, Claude runtime marker 제거 기준을 만족한다. Batch 4에서는 `agents.max_threads = 128`과 `[features].goals = true`를 하네스 정책으로 추가했다. Batch 5부터는 Claude와 Codex를 독립 active harness로 분류하고, 이 저장소의 적용 범위를 Codex 환경으로만 제한한다. Batch 9에서는 `docs/skills-index.md`와 `docs/skills-index.json`으로 개인 스킬을 AI-first 라우팅 가능한 인덱스로 만들고, `docs/troubleshooting.md`로 훅/스킬/MCP/터미널 문제의 복구 경로를 문서화했다. Batch 10에서는 Codex-native curated 스킬 원본을 `codex/skills`에 버전관리하고 명시적 sync를 통해 활성 스킬 root에 반영하는 흐름을 추가했다.

상세 흐름은 `docs/codex-native-rebuild-guide.html`에서 보고, 실제 baseline 수치는 `docs/claude-corpus-inventory.md`를 본다. GitHub 후보 하네스 검토와 저장소 푸시는 `docs/harness-verification-report.md`에서 `FAIL: 0`을 확인한 뒤 진행한다.

외부 GitHub 하네스 후보 판단용 문서는 `docs/github-harness-candidate-analysis.html`이다. 실제 선별 흡수 기준과 batch 제안은 `docs/external-harness-import-notes.md`에 기록한다. 두 문서는 설치 지침이 아니라, 우리 하네스 기준으로 가져올 패턴과 버릴 런타임을 분리하기 위한 평가 자료다.

GitHub 배포 전 최종 확인은 `docs/release-checklist.md`를 따른다. 이 체크리스트는 Secret/PII preflight, restore dry-run, migration idempotency, MCP 분리 원칙을 포함한다.

개발 도메인별 시작점은 `docs/domain-profiles/`와 `docs/codex-only-mcp-plugin-catalog.md`에 둔다. `tools/codex_domain_profile.py`는 프로젝트 설명을 받아 IDE/app/game/media 프로파일과 Codex-only MCP/plugin 후보를 추천하는 읽기 전용 도구다.

macOS 터미널에서 `codex` 명령을 안정적으로 쓰는 방법은 `docs/macos-terminal-codex-setup.md`에 기록한다. 현재 Mac은 `/Applications/Codex.app`과 `/opt/homebrew/bin/codex` symlink 기준으로 검증했다.

운영 중 문제가 생기면 `docs/troubleshooting.md`를 먼저 본다. 특히 `UserPromptSubmit` JSON 오류, 스킬 미로딩, MCP 인증/등록 분리, `AppTranslocation`, `U+FFFD` 인코딩 문제를 같은 순서로 진단한다.
