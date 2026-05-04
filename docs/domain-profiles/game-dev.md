# Game Development Domain Profile

## 적용 대상

- Browser game, 2D/3D game, simulation, interactive visual tool.
- Game editor, level editor, asset pipeline.
- WebGL, Canvas, Three.js, Phaser, React Three Fiber.

## 핵심 품질 기준

- Input loop, render loop, update loop 분리.
- Asset loading, fallback, license tracking.
- Frame stability and performance budget.
- Save/load state.
- Responsive viewport and device controls.
- Playtest checklist and regression capture.

## Codex Skill / Agent Mapping

| 필요 | Codex 후보 |
|---|---|
| 게임 구조 | `game-studio:web-game-foundations` |
| 2D 구현 | `game-studio:phaser-2d-game` |
| 3D 구현 | `game-studio:three-webgl-game`, `game-studio:react-three-fiber-game` |
| UI | `game-studio:game-ui-frontend`, `frontend-design` |
| 검증 | `game-studio:game-playtest`, `playwright-qa-expert` |
| asset | `game-studio:sprite-pipeline`, `game-studio:web-3d-asset-pipeline` |

## Codex-only MCP / Plugin 후보

- `Playwright`: browser playtest automation.
- `Game Studio`: game-specific skills and asset workflows.
- `browser-use`: in-app browser exploration for local builds.

## 검증 체크리스트

- [ ] 첫 화면이 실제 플레이 화면이다.
- [ ] 렌더 루프가 nonblank canvas를 만든다.
- [ ] desktop/mobile viewport에서 framing이 맞다.
- [ ] keyboard/mouse/touch 입력이 검증됐다.
- [ ] frame drop, asset load failure, restart flow가 확인됐다.
- [ ] asset license/source가 기록됐다.
- [ ] 대용량 generated asset은 Git 정책을 따른다.

## 보류 항목

- asset generation 자동화.
- 대용량 asset 자동 커밋.
- 128 agent fan-out 기반 playtest.
