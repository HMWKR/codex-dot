# Video / Media Tool Domain Profile

## 적용 대상

- Video editor, audio editor, timeline tool.
- Transcoding/export tool.
- Media asset manager.
- Motion graphics or template editor.

## 핵심 품질 기준

- Timeline model and non-destructive edit graph.
- Proxy/cache strategy for large media.
- Import/export format matrix.
- Long-running render cancellation and resume.
- Preview/render parity.
- Undo/redo and autosave.
- Large file and generated output Git policy.

## Codex Skill / Agent Mapping

| 필요 | Codex 후보 |
|---|---|
| 도메인 분석 | `domain-expert-analysis`, `source-command-analyze` |
| 구조 설계 | `architect`, `pipeline-orchestrator` |
| UI/UX | `frontend-design`, `playwright-design-audit` |
| QA | `continuous-qa-loop`, `webapp-testing` |
| 문서화 | `docx`, `pdf`, `presentations` when outputs need reports |

## Codex-only MCP / Plugin 후보

- `ffmpeg/media MCP`: P2 후보. 로컬 바이너리, 라이선스, 파일 크기 정책이 필요하다.
- `playwright`: web-based media editor UI 검증.
- `github`: large file policy, CI artifacts, release workflow.

## 검증 체크리스트

- [ ] Timeline edit graph가 destructive 원본 변경을 하지 않는다.
- [ ] Import format과 export format이 표로 정의됐다.
- [ ] Proxy/cache 파일 경로가 Git에서 제외된다.
- [ ] 긴 render를 취소/재개할 수 있다.
- [ ] Preview 결과와 final export 차이를 확인한다.
- [ ] Undo/redo stack이 복합 편집에서 깨지지 않는다.
- [ ] 대용량 샘플 파일은 repo에 직접 커밋하지 않는다.

## 보류 항목

- ffmpeg wrapper 자동 설치.
- codec/license 자동 판단.
- media binary test fixture 대량 커밋.
