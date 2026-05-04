# Codex-only MCP / Plugin Catalog

## 목적

이 문서는 개발자 작업을 위해 검토할 MCP와 plugin 후보를 Codex-only 기준으로 분류한다. 여기 있는 항목은 설치 목록이 아니라 선택 카탈로그다.

## 원칙

- Claude MCP/plugin 설정은 수정하지 않는다.
- Codex에서 쓸 후보만 Codex 설정 후보로 검토한다.
- 외부 install script는 그대로 실행하지 않는다.
- 같은 MCP server를 Claude와 Codex가 모두 쓰려면 각 클라이언트에 별도 등록한다.
- provider token, OAuth, local binary가 필요한 항목은 프로젝트별 승인 후 설정한다.

## P1 후보

| 후보 | 용도 | 적용 조건 | 검증 |
|---|---|---|---|
| GitHub | issue, PR, CI, release triage | GitHub remote가 정해진 뒤 | read-only query부터 시작 |
| Playwright / browser | web app, IDE UI, game playtest | local web UI가 있을 때 | screenshot, interaction, console error |
| Context7/docs lookup | version-specific docs | framework/API 판단이 필요할 때 | primary docs 링크 기록 |
| Serena / LSP | large codebase symbol analysis | 언어와 project root가 명확할 때 | symbol query, references check |
| Game Studio | browser game | 게임 프로젝트일 때 | playtest + canvas verification |
| Build iOS/macOS | Apple app/tool | Xcode/Swift 프로젝트일 때 | build/run/debug command |

## 현재 로컬 Codex 상태

2026-05-04 기준 이 Mac의 Codex 설정에는 다음 MCP가 `enabled` 상태다.

| 구분 | 항목 |
|---|---|
| Local stdio MCP | `computer-use`, `context7`, `firebase`, `laravel-boost`, `playwright`, `serena`, `xcodebuildmcp` |
| Remote MCP | `asana`, `github`, `gitlab`, `greptile`, `linear`, `slack`, `stripe`, `supabase`, `vercel` |
| Local runtime | `node`, `npm`, `npx`, `uvx`, `php` |

로컬 실행 기반은 Homebrew로 보강했다.

| Runtime | Version | 필요한 MCP |
|---|---:|---|
| Node.js | 25.9.0 | `context7`, `firebase`, `playwright`, `xcodebuildmcp` |
| npm/npx | 11.12.1 | `npx` 기반 MCP |
| uvx | 0.11.8 | `serena` |
| PHP | 8.5.5 | `laravel-boost` |

주의: 설치/활성화와 서비스별 로그인은 별개다. GitHub는 `gh auth login`과 `workflow` scope까지 확인했다. Asana, GitLab, Linear, Slack, Stripe, Supabase, Vercel 등은 각 서비스 작업을 시작할 때 해당 workspace 권한을 별도로 확인한다.

## P2 후보

| 후보 | 용도 | 보류 이유 |
|---|---|---|
| ffmpeg/media MCP | video/audio pipeline | 로컬 바이너리, codec/license, 대용량 파일 정책 필요 |
| Supabase/Firebase | backend app platform | 프로젝트가 해당 플랫폼을 선택한 뒤 |
| Vercel | deploy/preview | web deployment target이 Vercel일 때 |
| Linear/Notion/Slack | product/project workflow | 사용자의 workspace 연결과 권한 확인 필요 |

## Reject

| 후보 | 이유 |
|---|---|
| 외부 install script 일괄 실행 | Claude/Codex/provider 설정을 동시에 변경할 수 있음 |
| provider routing config import | 기존 Codex model/config를 덮을 위험 |
| 모든 plugin 기본 활성화 | 도구 검색 품질과 권한 경계를 흐림 |
| MCP server 자동 background 실행 | 사용자가 의도하지 않은 장기 프로세스가 생길 수 있음 |

## 도입 절차

1. 도메인 프로파일을 고른다.
2. 필요한 MCP/plugin 후보를 하나만 고른다.
3. 권한, token, local binary, 네트워크 필요성을 확인한다.
4. Codex 설정 후보를 문서로 먼저 작성한다.
5. 사용자가 명시적으로 승인한 뒤 Codex 환경에만 적용한다.
6. `tools/codex_harness_verify.py`를 실행한다.
