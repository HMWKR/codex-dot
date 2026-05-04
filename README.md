# codex-dot

Codex-native harness control-plane repository.

이 저장소는 Codex 환경에만 하네스를 설정하기 위한 제어 저장소다. Claude 하네스와 Codex 하네스는 서로 독립된 active harness로 분류하고, 실제 홈 디렉터리 설정(`~/.codex`, `~/.agents/skills`)은 Git에 직접 넣지 않고 재현 가능한 도구와 운영 문서로 관리한다.

현재 방향은 단순 복사가 아니라, Claude-native 하네스의 의도와 워크플로우를 읽어 Codex-native 구현으로 별도 설계하는 것이다. Claude 환경은 수정하지 않고, Codex 적용은 명시적 `--apply`가 있을 때만 수행한다. 경계 기준은 `docs/harness-boundary-classification.md`가 우선한다.

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
tools/
  codex_native_harness_migrate.py   # Codex 환경 적용 도구, 기본 dry-run
  codex_harness_inventory.py        # Claude/Codex 자산 인벤토리와 재구축 baseline 리포트
  codex_harness_verify.py           # 상세 검증 게이트: 인코딩, hooks, skills, scripts, GitHub preflight
docs/
  migration-summary.md              # 최근 이전 결과와 검증 요약
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
.gitignore                          # 런타임 상태와 백업 제외
.github/workflows/verify.yml         # GitHub runner용 workspace-only 검증
```

## 빠른 실행

```bash
python3 tools/codex_harness_inventory.py --output docs/claude-corpus-inventory.md
python3 tools/codex_domain_profile.py --query "browser game with level editor"
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
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

## 최신 상태

2026-05-04 기준으로 개인 스킬 371개 파일을 Codex 스킬 위치에 반영했고, Codex validator와 UTF-8 검증을 통과했다. 이후 Batch 2에서 최상위 49개 스킬은 모두 `SKILL.md`, `name`, `description`, Claude runtime marker 제거 기준을 만족한다. Batch 4에서는 `agents.max_threads = 128`과 `[features].goals = true`를 하네스 정책으로 추가했다. Batch 5부터는 Claude와 Codex를 독립 active harness로 분류하고, 이 저장소의 적용 범위를 Codex 환경으로만 제한한다.

상세 흐름은 `docs/codex-native-rebuild-guide.html`에서 보고, 실제 baseline 수치는 `docs/claude-corpus-inventory.md`를 본다. GitHub 후보 하네스 검토와 저장소 푸시는 `docs/harness-verification-report.md`에서 `FAIL: 0`을 확인한 뒤 진행한다.

외부 GitHub 하네스 후보 판단용 문서는 `docs/github-harness-candidate-analysis.html`이다. 실제 선별 흡수 기준과 batch 제안은 `docs/external-harness-import-notes.md`에 기록한다. 두 문서는 설치 지침이 아니라, 우리 하네스 기준으로 가져올 패턴과 버릴 런타임을 분리하기 위한 평가 자료다.

GitHub 배포 전 최종 확인은 `docs/release-checklist.md`를 따른다. 이 체크리스트는 Secret/PII preflight, restore dry-run, migration idempotency, MCP 분리 원칙을 포함한다.

개발 도메인별 시작점은 `docs/domain-profiles/`와 `docs/codex-only-mcp-plugin-catalog.md`에 둔다. `tools/codex_domain_profile.py`는 프로젝트 설명을 받아 IDE/app/game/media 프로파일과 Codex-only MCP/plugin 후보를 추천하는 읽기 전용 도구다.
