# IDE / Developer Tool Domain Profile

## 적용 대상

- IDE, code editor, extension host, language tooling.
- Code intelligence, refactoring tool, test runner, debugging UI.
- Internal developer platform or command palette driven tool.

## 핵심 품질 기준

- Symbol graph, dependency trace, rename/refactor safety.
- Diagnostics latency and incremental analysis.
- Large workspace performance.
- Crash-safe project state.
- Keyboard-first UX and command palette ergonomics.
- Extension/plugin packaging and update path.

## Codex Skill / Agent Mapping

| 필요 | Codex 후보 |
|---|---|
| 구조 분석 | `architect`, `codebase-explorer` |
| 심층 코드 탐색 | `source-command-analyze`, `deep-analysis-mode` |
| LSP/symbol 분석 | `Serena` plugin 후보, 직접 설치는 보류 |
| QA | `continuous-qa-loop`, `security-audit`, `infra-audit` |
| UI 검증 | `playwright-qa-expert`, `playwright-design-audit` |

## Codex-only MCP / Plugin 후보

- `serena`: symbol-aware code navigation. 프로젝트 언어가 정해진 뒤 Codex-only로 검토.
- `github`: issue, PR, CI triage.
- `playwright`: editor UI, command palette, web IDE 검증.
- `context7`: language/framework API 문서 조회.

## 검증 체크리스트

- [ ] Rename/refactor가 import/export와 references를 깨지 않는다.
- [ ] Diagnostics가 대형 workspace에서 점진적으로 갱신된다.
- [ ] 명령 팔레트, 단축키, 메뉴가 같은 action model을 공유한다.
- [ ] Extension/plugin failure가 IDE 전체를 죽이지 않는다.
- [ ] 프로젝트 상태 파일은 Git 추적/비추적 기준이 명확하다.
- [ ] UI가 키보드만으로 주요 작업을 수행할 수 있다.

## 보류 항목

- LSP/MCP 자동 설치.
- 사용자 editor 설정 자동 rewrite.
- 모든 언어 서버 기본 활성화.
