# App / Program Domain Profile

## 적용 대상

- 일반 웹앱, 데스크톱 앱, 모바일 앱, CLI/TUI 프로그램.
- 내부 업무 도구, SaaS, admin dashboard.
- 배포와 rollback이 필요한 사용자-facing 프로그램.

## 핵심 품질 기준

- Spec, design, tasks 분리.
- Config/secrets boundary.
- Error handling and observability.
- Data migration and rollback.
- Cross-platform packaging when needed.
- Accessibility and responsive UX for frontend apps.

## Codex Skill / Agent Mapping

| 필요 | Codex 후보 |
|---|---|
| 요구사항 정리 | `what`, `what-ce`, `project-bootstrapper` |
| 설계 | `architect`, `pipeline-orchestrator` |
| 구현 | 기본 Codex coding workflow, `project-kickstart` |
| 테스트 | `continuous-qa-loop`, `webapp-testing`, `playwright-qa-expert` |
| 배포 | `vercel-deploy`, platform plugin 후보 |
| 리뷰 | `security-audit`, `infra-audit`, `ce-reviewer` |

## Codex-only MCP / Plugin 후보

- `github`: PR/issue/release workflow.
- `vercel`: web deployment when project chooses Vercel.
- `supabase` or `firebase`: backend platform only when chosen by project.
- `playwright`: browser app verification.

## 검증 체크리스트

- [ ] `docs/templates/spec.md`가 작성됐다.
- [ ] `docs/templates/design.md`가 작성됐다.
- [ ] `docs/templates/tasks.md`가 작업 단위로 쪼개졌다.
- [ ] Secret이 repo에 들어가지 않는다.
- [ ] Rollback 또는 restore path가 있다.
- [ ] 에러 상태와 빈 상태가 UI에 존재한다.
- [ ] 배포 전 verifier가 `FAIL: 0`이다.

## 보류 항목

- provider config 자동 import.
- 인증/세션 cache 복사.
- 프로젝트별 hook 자동 rewrite.
