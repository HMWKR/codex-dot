# Developer Domain Extension Review

## 목적

이 문서는 개발자가 만들 법한 IDE, 앱, 게임, 영상 편집 도구, 내부 개발자 플랫폼을 기준으로 현재 Codex 하네스에 추가하면 좋은 후보를 분류한다. MCP와 plugin은 Codex-only 원칙을 따른다.

## 기준

- Codex 환경에만 적용한다.
- Claude MCP, Claude plugin, Claude settings는 수정하지 않는다.
- 외부 install script는 실행하지 않는다.
- 개발 workflow를 실제로 줄여주는 항목만 P1로 둔다.
- 특정 제품이나 provider 설정을 강제하지 않는다.

## P1 추천

| 영역 | 추가 후보 | 이유 | 현재 매핑 |
|---|---|---|---|
| IDE / 개발 도구 | Language-server aware analysis profile | IDE, editor, code intelligence 제품은 symbol graph와 dependency trace가 중요하다. | `codebase-explorer`, `architect`, `serena` plugin 후보 |
| 앱 / 프로그램 | Spec → Design → Tasks 템플릿 | 일반 앱 개발은 요구사항과 설계/작업 분리가 품질을 크게 올린다. | `docs/templates/spec.md`, `design.md`, `tasks.md` |
| 게임 | Game loop verification checklist | 게임은 렌더링, 입력, asset, frame loop 검증이 일반 앱과 다르다. | `game-studio:*`, Playwright visual check |
| 영상 편집 / 미디어 툴 | Media pipeline checklist | timeline, codec, preview, export, undo/redo, asset cache가 핵심이다. | 향후 `media-tooling` skill 후보 |
| DevOps / GitHub | CI triage workflow | GitHub push 이후 실패 원인을 빠르게 좁히는 운영 루프가 필요하다. | `.github/workflows/verify.yml`, `github-workflow.md` |
| 품질 / 리뷰 | Skill quality score | 스킬이 많아질수록 entrypoint 통과만으로는 부족하다. | `codex_harness_inventory.py` quality signals |

## P2 실험

| 영역 | 후보 | 보류 이유 |
|---|---|---|
| IDE | LSP/MCP 자동 설치 | 사용자 언어와 editor가 다양하고 홈 설정 변경 위험이 있다. |
| 게임 | asset generation pipeline 자동화 | 비용, 저작권, asset 품질 검증 문제가 있다. |
| 영상 | ffmpeg/codec wrapper MCP | 매우 유용하지만 로컬 바이너리, 라이선스, 대용량 파일 정책이 필요하다. |
| 데스크톱 앱 | OS별 build runner | macOS/iOS/Windows/Linux별 runner와 인증 요구가 다르다. |
| 대규모 agent team | 자동 128 fan-out | `agents.max_threads`는 상한이지 기본 전략이 아니다. |

## Reject

| 후보 | 이유 |
|---|---|
| 외부 MCP install script 그대로 실행 | `~/.claude`, `~/.codex`, provider config를 동시에 바꿀 수 있다. |
| 모든 plugin 기본 활성화 | 도구 검색 품질과 권한 경계가 흐려진다. |
| 프로젝트마다 자동 hook rewrite | 사용자의 repo 정책과 충돌할 수 있다. |
| media/game 대용량 asset 자동 커밋 | GitHub 저장소 품질과 라이선스 검증을 해친다. |

## Codex-only MCP / Plugin 후보

| 후보 | 용도 | 판정 |
|---|---|---|
| GitHub plugin/MCP | 이슈, PR, CI triage | P1. GitHub push 이후 필요 |
| Playwright/browser plugin | 웹앱, IDE UI, 게임 UI 검증 | P1. UI 도구 제작에 강함 |
| Context7/docs lookup | 프레임워크/API 문서 조회 | P1. 버전별 문서 확인에 유용 |
| Serena/LSP 계열 | 대형 코드베이스 symbol analysis | P1/P2. 프로젝트 언어별 검토 필요 |
| Vercel/Supabase/Firebase | 웹앱/백엔드 배포와 운영 | P2. 프로젝트가 해당 플랫폼일 때만 |
| Game Studio | 브라우저 게임 제작 | P1. 게임 도메인에서만 |
| Build iOS/macOS Apps | Apple 앱 제작 | P1. Apple 플랫폼 프로젝트에서만 |
| ffmpeg/media MCP | 영상 편집 도구와 media pipeline | P2. 설치/라이선스/대용량 정책 필요 |

## 도메인별 체크리스트

### IDE / Editor / Developer Tool

- Symbol navigation, rename/refactor, diagnostics, formatter, test runner.
- Extension/plugin packaging.
- Keyboard shortcuts and command palette.
- Large workspace performance.
- Crash-safe project state.

### General App / Program

- Requirements, design, tasks 분리.
- Config and secrets boundary.
- Error reporting.
- Update/rollback.
- Cross-platform packaging.

### Game

- Input loop, render loop, asset loading, save state.
- Performance budget and frame stability.
- Browser/mobile viewport checks when web game.
- Asset license and generated asset manifest.

### Video Editing / Media Tool

- Timeline model.
- Non-destructive edit graph.
- Preview proxy/cache.
- Import/export formats.
- Long-running render cancellation and resume.
- Large file policy and Git exclusion.

## 다음 반영 순서

1. Spec/Design/Tasks 템플릿을 project-bootstrap 계열 문서와 연결한다.
2. Skill quality score를 inventory report에 유지한다.
3. GitHub CI workspace-only verifier를 첫 push 전에 확인한다.
4. `docs/domain-profiles/`에서 실제 프로젝트 도메인을 고른다.
5. `docs/codex-only-mcp-plugin-catalog.md`에서 Codex-only MCP/plugin 후보를 하나씩 검토한다.
6. Media/game/IDE 특화 skill은 실제 프로젝트가 생길 때 도메인별로 추가한다.

## Profile Selector

읽기 전용 도구:

```bash
python3 tools/codex_domain_profile.py --query "video editor with timeline and export"
```

이 도구는 문서 후보를 추천할 뿐 MCP/plugin을 설치하지 않는다.
