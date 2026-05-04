# Harness Boundary Classification

## 목적

이 저장소는 Claude와 Codex를 섞지 않기 위한 제어 저장소다. Claude는 Claude 환경에서 계속 쓰는 독립 하네스이고, Codex는 Codex 환경에서 쓰는 독립 하네스다. 이 프로젝트가 실제로 설정하는 범위는 Codex 환경만이다.

## 분류

| 구분 | 경로 | 권한 | 설명 |
|---|---|---|---|
| Claude-native active harness | `~/.claude` | 읽기 가능, 쓰기 금지 | Claude에서 계속 사용하는 독립 환경이다. Codex 설정 적용 대상이 아니다. |
| Codex-native active harness | `~/.codex`, `~/.agents/skills` | 명시적 적용 시 쓰기 가능 | Codex가 실제로 읽고 실행하는 하네스다. 이 저장소의 적용 범위는 여기까지다. |
| Project control plane | 이 저장소의 `tools/`, `docs/` | Git 추적 | 분류, 검증, 문서화, 재현 절차를 관리한다. 홈 런타임 파일을 직접 커밋하지 않는다. |
| Local recovery backups | `codex-harness-backups/` | 로컬 전용 | 적용 전 복구용 백업이다. GitHub에 올리지 않는다. |
| Vendor/plugin/runtime cache | `~/.codex/plugins/cache`, 세션/인증/로그 | 제외 | 사용자의 로컬 상태이므로 이 저장소가 소유하지 않는다. |

## Codex-only apply policy

- 이 저장소가 설정하는 대상은 Codex 환경만이다.
- 적용 스크립트는 Claude 경로에는 쓰지 않는다.
- 적용 스크립트는 Codex 경로에만 쓴다.
- GitHub에서 clone만으로 홈 디렉터리를 수정하지 않는다.
- `python3 tools/codex_native_harness_migrate.py`의 기본 동작은 dry-run이다.
- 실제 적용은 사용자가 `--apply`를 명시했을 때만 수행한다.
- 적용 전에는 Codex 대상 백업과 SHA-256 manifest를 만든다.

## 변환의 의미

Claude 내용을 참고할 수는 있지만, 그것은 Claude 하네스를 Codex로 흡수한다는 뜻이 아니다. 필요한 경우 같은 작업 철학을 각 런타임에 맞게 별도 구현한다.

```text
Claude-native active harness
  ~/.claude/*
  Claude 고유의 command, hook, agent, settings 체계

Codex-native active harness
  ~/.codex/*
  ~/.agents/skills/*
  Codex 고유의 AGENTS.md, skill, subagent, hook, config 체계

Project control plane
  tools/*
  docs/*
  검증 보고서와 GitHub 운영 절차
```

## GitHub 배포 원칙

다른 사용자가 이 저장소를 clone해도 그 사용자의 Claude, Codex, 기타 홈 환경은 자동으로 변경되지 않아야 한다.

허용되는 기본 동작:

- 문서 읽기.
- inventory와 verifier의 읽기 전용 검사.
- migration dry-run.
- workspace 안의 보고서 생성.

명시적 동의가 필요한 동작:

- `~/.codex` 수정.
- `~/.agents/skills` 수정.
- Codex hook/script/agent 설정 적용.

금지되는 동작:

- `~/.claude` 수정.
- 인증 파일, 세션 기록, 플러그인 캐시, 로그 복사.
- 외부 하네스 install script를 그대로 실행해 홈 디렉터리를 덮어쓰기.
- clone, import, verify 과정에서 사용자의 기존 환경을 자동 변경하기.

## MCP와 Plugin 분리 원칙

MCP server 자체는 Claude 전용이 아니라 여러 클라이언트가 붙을 수 있는 외부 서버다. Claude와 Codex가 같은 MCP server를 사용할 수는 있지만, 설정은 각 클라이언트의 런타임에 따로 등록된다.

이 저장소의 기준:

- Codex에서 쓸 MCP나 plugin만 Codex 설정 후보로 다룬다.
- Claude MCP 설정은 이 저장소가 수정하지 않는다.
- 외부 MCP install script가 `~/.claude`, `~/.codex`, provider 설정을 함께 바꿀 수 있으므로 그대로 실행하지 않는다.
- 외부 MCP는 설치 단위가 아니라 `server 목적`, `필요 권한`, `Codex 설정 위치`, `검증 방법`으로 분해해 검토한다.
- 같은 MCP server를 Claude와 Codex가 모두 쓰고 싶다면, 각 환경에서 별도 등록한다. 한쪽 설정이 다른 쪽에 자동으로 전파된다고 가정하지 않는다.

## 검증 기준

`tools/codex_harness_verify.py`는 이 경계를 다음 기준으로 검사한다.

- `.gitignore`가 `.claude/`, `.codex/`, `checkpoint.md`, `session-handoff.md`, `codex-harness-backups/`를 제외한다.
- migration 도구의 기본 실행 결과가 `dry_run: true`다.
- 문서가 Claude-native active harness, Codex-native active harness, Project control plane을 분리해 설명한다.
- Codex active harness 안에 의도치 않은 Claude 실행 잔재가 남지 않는다.
- GitHub workflow가 clone만으로 홈 디렉터리를 수정하지 않는다고 명시한다.
