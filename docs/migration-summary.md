# Codex-native 하네스 이전 요약

## 목표

Codex 환경에서 사용할 개인 하네스와 스킬 자산을 안전하게 정리하고, 이후 Codex-native 재구축을 위한 bootstrap 상태를 만들었다.

이 작업의 최종 목표는 단순 복사가 아니다. Claude와 Codex는 서로 독립된 active harness로 유지하고, Claude의 각 스킬과 설정 Markdown에서 얻은 의도는 Codex의 skill, subagent, hook, AGENTS 체계에 맞게 별도 구현한다. 이 저장소가 실제로 설정하는 범위는 Codex 환경뿐이다.

## 적용 범위

- 글로벌 Codex 설정: `~/.codex`
- 사용자 스킬: `~/.agents/skills`
- 현재 프로젝트 소스: `tools/codex_native_harness_migrate.py`, `docs/*`

## 주요 변경

- `~/.codex/AGENTS.md`를 Codex 경로 기준으로 재작성했다.
- 개인 스킬을 `~/.agents/skills`에 삭제 없이 병합했다.
- Claude command 5개를 `source-command-*` Codex skill로 변환했다.
- 누락됐던 `source-command-pdca`를 추가했다.
- Codex hooks는 command hook만 남겼다.
- `PreToolUse`, `PostToolUse`, `SessionStart`, `UserPromptSubmit`, `Stop` 훅을 Codex 경로로 연결했다.
- `~/.codex/scripts`에 Codex-native helper script를 생성했다.
- `~/.codex/agents/*.toml` 5개를 Codex custom agent 형식으로 정리했다.

## 스킬 자산

- Claude skill 파일 동기화: 371개 copied, 0 skipped
- 최상위 skill 엔트리: 49개
- 중첩 skill 포함 audit 기준: 63개
- `_core` 공유 리소스 유지

## 인코딩 처리

- 대상 텍스트 파일 340개 UTF-8 strict 검증 통과
- `U+FFFD` replacement 문자 0개
- `think-teams/skill.md`는 Claude-native 파일에 이미 있던 깨짐 문자를 Codex 대상에서 문맥 복구했다.
- Claude 환경은 변경하지 않았다.

## 검증 결과

- Codex validator: config, skills, agents 통과
- `infra-audit.sh --quick`: 16 PASS / 0 WARN / 0 FAIL / score 100
- `tools/codex_harness_verify.py`: 상세 검증 게이트 추가
- 안전 훅 시뮬레이션:
  - 안전 명령 통과
  - `rm -rf` 차단 확인
- TOML/JSON/Python/Shell 문법 검증 통과

## 백업

최신 백업:

```text
/Users/leesungmin/Desktop/codex-dot/codex-harness-backups/20260504-141259
```

백업 manifest:

- 백업 항목: 394개
- SHA-256 포함

`codex-harness-backups/`는 Git에 올리지 않는다. 필요 시 로컬 복구용으로만 보관한다.

## 남겨둔 항목

- `claude-plugins-official`은 Codex plugin marketplace 이름이므로 유지한다.
- `superpowers` 내부 release note/test 문서의 `.claude` 표기는 원본 자산의 역사적 문맥이라 실행 경로로 사용하지 않는다.

## 발견된 한계

- 현재 세션에서 보이는 skill 목록은 세션 시작 시점의 인덱스에 가까워, 새로 추가되거나 수정된 skill이 즉시 트리거되지 않을 수 있다.
- Claude에서 가져온 많은 스킬이 `skill.md` 소문자 entrypoint를 사용한다. Codex 실사용본은 `SKILL.md` 대문자로 정규화해야 한다.
- 일부 스킬은 `AskUserQuestion`, `Task tool`, `Agent tool`, `TodoWrite`, slash command 호출 같은 Claude 런타임 표현을 포함한다.
- `allowed-tools`, `argument-hint`, `user_invocable` 같은 Claude frontmatter는 Codex에서 동일한 권한 또는 호출 의미를 갖지 않는다.

## 다음 방향

다음 단계는 `docs/codex-native-rebuild-plan.md` 기준으로 진행한다.

- Claude-native active harness와 Codex-native active harness를 분리 유지한다.
- 스킬별 의도, 트리거, 워크플로우, 산출물을 추출한다.
- Codex-native `SKILL.md`, agent TOML, hook script, AGENTS 지침으로 재작성한다.
- 적용 도구는 기본 dry-run으로 두고, Codex 환경 적용은 `--apply`를 명시할 때만 수행한다.
- 변경할 때마다 관련 문서를 함께 업데이트한다.

현재 재구축 기준 문서:

- `docs/rebuild-3pass-review.md`: 원본 의도, Codex 매핑, 누락/충돌 3-pass 검토 결과.
- `docs/claude-corpus-inventory.md`: Claude/Codex 자산 baseline.
- `docs/codex-native-rebuild-guide.html`: 재구축 방식 상세 설명서.
- `docs/harness-boundary-classification.md`: Claude/Codex 독립 분류와 Codex-only 적용 원칙.

## 2026-05-04 Batch 1

P0 command bridge인 `source-command-*` 5개를 Codex-native skill로 재작성했다.

- `source-command-analyze`: 심층 분석 workflow를 Codex current-turn skill로 정리.
- `source-command-journal`: 명시 요청 시 `.thoughts/` CE 사고여정 작성 흐름으로 정리.
- `source-command-orchestrate`: Codex subagent 정책에 맞춰 명시적 위임 요청이 있을 때만 orchestration 사용.
- `source-command-pdca`: `$ARGUMENTS` 의존 제거, 현재 요청/짧은 질문 기반 target 탐지로 변경.
- `source-command-rules`: active Codex 경로 기준 rule hierarchy로 변경.

검증:

- Codex validator 통과.
- Codex active harness UTF-8 검증 통과.
- active `source-command-*`에서 Claude runtime marker 잔재 없음.
- 인벤토리 ready skill: 12 → 13.
- Claude runtime marker 포함 target skill: 21 → 20.

## 2026-05-04 Batch 2

Claude에서 온 최상위 스킬들을 Codex가 안정적으로 인식하도록 구조 정규화했다.

- 모든 최상위 `skill.md`를 실제 디렉터리 엔트리 기준 `SKILL.md`로 변경.
- 모든 최상위 skill frontmatter를 `name`, `description` 중심으로 정리.
- `agent-architect`처럼 frontmatter가 없던 스킬에 Codex metadata 추가.
- Claude 런타임 표기가 active entrypoint 실행 지시로 남지 않도록 변환.
- `_shared`는 공유 리소스로 취급하여 skill readiness count에서 제외.
- `think-teams/SKILL.md`의 `U+FFFD` 복구 경로를 보강.

검증:

- Codex validator에서 49개 target skill frontmatter 통과.
- Codex active harness UTF-8 검증 통과.
- inventory ready skill: 49 / 49.
- lowercase `skill.md`: 0.
- entrypoint runtime marker skills: 0.

## 2026-05-04 Batch 3

GitHub 작업 전 상세 검증 게이트와 외부 후보 판단 문서를 프로젝트에 추가했다.

- `tools/codex_harness_verify.py`가 workspace 문서, Codex active harness 인코딩, Claude reference allowlist, active 잔재, skill entrypoint, hooks/config, agent TOML, script syntax, hook simulation, migration dry-run, inventory, Codex validator, GitHub preflight를 검사한다.
- 결과는 `docs/harness-verification-report.md`와 `docs/harness-verification-report.json`에 기록한다.
- GitHub 후보 하네스 검토와 push는 `Harness Verification Report`에서 `FAIL: 0`을 확인한 뒤 진행한다.
- 로컬 Git 저장소를 초기화하고 기본 브랜치를 `main`으로 설정했다.
- `docs/github-harness-candidate-analysis.html`에 bkit-codex, agent-skills, spec-kit, cc-sdd, oh-my-codex, ok-skills, codex-settings 판단 기준을 정리했다.
- `docs/external-harness-import-notes.md`에 외부 후보별 3-pass 검토와 Batch 4A-4D import 제안을 기록했다.

허용된 warning:

- Claude-native `think-teams/skill.md`의 reference-only `U+FFFD`. Codex active harness는 복구되어 깨짐 문자가 없다.
- Codex validator의 크기 관련 warning. 활성 Codex harness 실패가 아니라 큰 `AGENTS.md` 계열 문서에 대한 경고다.
- 현재 프로젝트가 아직 Git 저장소가 아닌 경우 GitHub preflight warning이 발생한다. GitHub 단계에서 `git init`으로 처리한다.

## 2026-05-04 Batch 4

Agent 운영 한도와 `goal` 기능을 Codex-native 설정으로 반영했다.

- custom agent 정의 5개는 유지한다.
- agent thread 운영 한도는 `agents.max_threads = 128`로 설정한다.
- `goal` 기능은 `[features].goals = true`로 활성화한다.
- 로컬 Codex CLI는 `0.128.0-alpha.1`이며, `goals` feature flag는 `under development` stage로 확인됐다.
- `goal`은 안정 기능이 아니라 장기 목표/재개 흐름 실험 기능으로 문서화한다.

검증 강화:

- `tools/codex_harness_verify.py`가 `agents.max_threads == 128`을 검사한다.
- `tools/codex_harness_verify.py`가 `[features].goals == true`를 검사한다.
- `codex features list`에서 `goals under development true`가 되는지 확인한다.

## 2026-05-04 Batch 5

Claude와 Codex의 하네스 경계를 다시 정리했다.

- Claude는 Claude-native active harness로 계속 유지한다.
- Codex는 Codex-native active harness로 별도 유지한다.
- 이 저장소는 Project control plane이며, GitHub 배포본이 다른 사용자의 홈 환경을 자동으로 수정하지 않도록 한다.
- `tools/codex_native_harness_migrate.py`의 기본 실행을 dry-run으로 변경했다.
- 실제 Codex 적용은 `python3 tools/codex_native_harness_migrate.py --apply`가 있을 때만 수행한다.
- `docs/harness-boundary-classification.md`를 추가해 Claude-native active harness, Codex-native active harness, Project control plane, Codex-only apply policy를 문서화했다.

검증 강화:

- `tools/codex_harness_verify.py`가 migration 기본 실행이 `dry_run: true`인지 검사한다.
- `tools/codex_harness_verify.py`가 `.gitignore`의 홈 런타임 제외 목록을 검사한다.
- `tools/codex_harness_verify.py`가 GitHub workflow에 clone만으로 홈 디렉터리를 수정하지 않는 원칙이 있는지 검사한다.

## 2026-05-04 Batch 6

GitHub 배포 전 P0 안전장치를 보강했다.

- `tools/codex_native_harness_migrate.py`에 `--restore <backup_dir>` 경로를 추가했다.
- restore는 기본 dry-run이며, 실제 복원은 `--apply`가 있을 때만 수행한다.
- restore는 manifest SHA-256을 검증하고 Codex-owned path만 대상으로 삼는다.
- `tools/codex_harness_verify.py`에 Secret/PII preflight를 추가했다.
- `tools/codex_harness_verify.py`에 restore dry-run 검증을 추가했다.
- `tools/codex_harness_verify.py`에 기본 migration dry-run idempotency 검사를 추가했다.
- `docs/release-checklist.md`를 추가했다.
- `docs/harness-boundary-classification.md`에 MCP와 plugin 분리 원칙을 추가했다.

MCP 판단:

- MCP server 자체는 Claude 전용이 아니다.
- Claude와 Codex의 MCP client 설정은 별개다.
- 외부 MCP install script가 양쪽 설정을 함께 건드릴 수 있으므로 그대로 실행하지 않는다.
- 이 저장소는 Codex에서 쓸 MCP/plugin만 Codex 설정 후보로 다루며 Claude MCP 설정은 수정하지 않는다.

## 2026-05-04 Batch 7

P1 운영 보강을 추가했다.

- `tools/codex_harness_inventory.py`에 Codex skill quality score를 추가했다.
- `docs/templates/spec.md`, `docs/templates/design.md`, `docs/templates/tasks.md`를 추가했다.
- `docs/templates/pdca-status.schema.json`을 추가해 PDCA 상태 모델 후보를 문서화했다.
- `.github/workflows/verify.yml`을 추가했다.
- `tools/codex_harness_verify.py`에 `--workspace-only` 모드를 추가해 GitHub runner에서 홈 Codex 설정 없이도 안전하게 검증할 수 있게 했다.
- `docs/developer-domain-extension-review.md`를 추가해 IDE, 앱, 게임, 영상 편집 도구, 개발자 플랫폼 관점의 추가 후보를 분류했다.

도메인 판단:

- IDE/개발 도구: LSP/symbol analysis, diagnostics, refactor workflow가 중요하다.
- 앱/프로그램: spec/design/tasks 분리와 rollback/release gate가 우선이다.
- 게임: render loop, input, asset, viewport/performance 검증이 중요하다.
- 영상 편집/미디어 도구: timeline, non-destructive edit graph, proxy/cache, export 검증이 중요하다.
- MCP/plugin은 Codex-only 후보로만 다루고, 실제 프로젝트가 해당 도메인을 요구할 때만 선택 적용한다.

## 2026-05-04 Batch 8

보류했던 개발자 도메인 후보를 실제 설치 없이 repo 관리 자산으로 구체화했다.

- `docs/domain-profiles/ide-devtool.md` 추가.
- `docs/domain-profiles/app-program.md` 추가.
- `docs/domain-profiles/game-dev.md` 추가.
- `docs/domain-profiles/media-tool.md` 추가.
- `docs/codex-only-mcp-plugin-catalog.md` 추가.
- `tools/codex_domain_profile.py` 추가.

반영 기준:

- IDE/LSP, 게임, 영상 편집, 앱 개발 후보를 도메인 프로파일로 정리했다.
- MCP/plugin은 설치 목록이 아니라 Codex-only 선택 카탈로그로 유지한다.
- 외부 MCP 자동 설치, provider config import, Claude 설정 수정은 계속 금지한다.
