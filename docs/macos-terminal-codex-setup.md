# macOS Terminal Codex Setup

## 목적

macOS 터미널에서 어느 디렉터리든 `codex`를 입력하면 Codex CLI/TUI가 바로 실행되도록 안정 경로를 만든다.

## 문제 상황

Codex Desktop을 다운로드 후 바로 실행하면 macOS가 앱을 `AppTranslocation` 임시 경로에서 실행할 수 있다. 이 경우 `command -v codex`가 다음처럼 일시적인 경로를 가리킬 수 있다.

```text
/private/var/folders/.../AppTranslocation/.../Codex.app/Contents/Resources/codex
```

이 경로는 터미널 워크플로우의 기준으로 쓰기 어렵다. 하네스 검증, MCP 관리, `codex app`, `codex exec`, `codex mcp list`를 안정적으로 쓰려면 `/Applications/Codex.app`과 PATH에 잡힌 `codex` 명령이 필요하다.

## 적용 절차

현재 실행 중인 Codex 앱 번들을 안정 위치로 복사한다.

```bash
ditto /path/to/AppTranslocation/.../Codex.app /Applications/Codex.app
```

Gatekeeper quarantine 속성이 남아 있으면 제거한다.

```bash
xattr -dr com.apple.quarantine /Applications/Codex.app
```

Homebrew PATH에 CLI symlink를 만든다.

```bash
ln -s /Applications/Codex.app/Contents/Resources/codex /opt/homebrew/bin/codex
```

이미 symlink가 있으면 기존 대상이 올바른지 먼저 확인한다.

```bash
ls -l /opt/homebrew/bin/codex
```

## 검증

새 셸에서 확인한다.

```bash
zsh -lc 'command -v codex'
zsh -lc 'codex --version'
zsh -lc 'codex login status'
zsh -lc 'codex mcp list'
```

통과 기준:

- `command -v codex`가 `/opt/homebrew/bin/codex`를 반환한다.
- `codex --version`이 Codex CLI 버전을 출력한다.
- `codex login status`가 현재 로그인 상태를 출력한다.
- `codex mcp list`가 Codex MCP 목록을 출력한다.

## 현재 Mac 검증값

2026-05-04 기준 이 Mac은 다음 상태를 확인했다.

| 항목 | 값 |
|---|---|
| 안정 앱 경로 | `/Applications/Codex.app` |
| 터미널 명령 | `/opt/homebrew/bin/codex` |
| CLI version | `codex-cli 0.128.0-alpha.1` |
| Login | `Logged in using ChatGPT` |
| MCP | `codex mcp list` 정상 출력 |

## 주의

- 이 절차는 macOS 전용이다.
- `/Applications`와 `/opt/homebrew/bin` 쓰기는 사용자 승인 또는 관리자 권한이 필요할 수 있다.
- 임시 AppTranslocation 경로를 symlink 대상으로 쓰지 않는다.
- Codex 업데이트 후 `/Applications/Codex.app/Contents/Resources/codex`가 유지되는지 다시 확인한다.

