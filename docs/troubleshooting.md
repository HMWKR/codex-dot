# Codex Harness Troubleshooting

이 문서는 Codex 하네스가 예상대로 동작하지 않을 때 AI와 사람이 같은 순서로 진단하기 위한 운영 가이드다.
기본 원칙은 Codex 환경만 확인하고, Claude 환경은 읽기 전용 reference로만 다루는 것이다.

## Quick Triage

```bash
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
python3 tools/codex_skill_index.py
python3 tools/codex_native_harness_migrate.py
git status --short
```

판단 기준:

- `FAIL: 0`이면 운영상 적용 가능 상태다.
- `WARN`은 문서화된 허용 범위인지 확인한다.
- `git status --short`에 변경 파일이 있으면 문서/인덱스가 최신인지 먼저 확인한다.

## UserPromptSubmit Hook Error

증상:

```text
UserPromptSubmit hook (failed)
error: hook returned invalid user prompt submit JSON output
```

원인:

- `UserPromptSubmit` 훅이 plain text를 출력하면 Codex가 JSON-safe 출력으로 해석하지 못할 수 있다.
- 이 하네스에서는 checkpoint 알림을 위해 쓰던 `UserPromptSubmit` plain-text 훅을 비활성화한다.

확인:

```bash
python3 -m json.tool ~/.codex/hooks.json
rg '"UserPromptSubmit"|SessionStart|PreToolUse|PostToolUse|Stop' ~/.codex/hooks.json
```

정상 상태:

- 활성 훅은 `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`만 사용한다.
- `UserPromptSubmit`은 `codex-harness.manifest.json`의 `disabled_hook_events`에만 문서화한다.

복구:

```bash
python3 tools/codex_native_harness_migrate.py --apply
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

## Skills Not Loading

증상:

- 사용자가 `$what`, `$architect` 같은 스킬을 불렀는데 세션에서 인식하지 못한다.
- 스킬 목록에 개인 스킬이 보이지 않는다.

확인:

```bash
find ~/.agents/skills -maxdepth 2 -name SKILL.md -print | sort | wc -l
python3 tools/codex_skill_index.py
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

정상 상태:

- 개인 스킬 경로는 `$HOME/.agents/skills`.
- 각 스킬은 `SKILL.md`, `name`, `description` frontmatter를 가진다.
- `docs/skills-index.md`와 `docs/skills-index.json`이 활성 스킬 root와 hash 기준으로 일치한다.

복구:

- 스킬 파일을 수정했다면 `python3 tools/codex_skill_index.py`를 다시 실행한다.
- Codex 세션의 스킬 목록은 세션 시작 시점에 로드될 수 있으므로, 파일은 맞는데 세션에서 안 보이면 새 세션에서 재확인한다.
- Claude 전용 `skill.md`, `allowed-tools`, `CLAUDE.md` marker가 남아 있으면 Codex-native `SKILL.md`로 정규화한다.

## MCP Or Plugin Missing

증상:

- `github`, `playwright`, `vercel`, `supabase` 같은 MCP/plugin 기능이 보이지 않는다.
- CLI에서는 설치된 것처럼 보이는데 Codex 세션에서 호출되지 않는다.

확인:

```bash
codex mcp list
command -v node
command -v npx
command -v uvx
command -v gh
gh auth status
```

운영 기준:

- MCP server 자체는 공통 프로그램일 수 있지만, Claude와 Codex의 클라이언트 등록은 별개다.
- 이 저장소는 Codex 설정만 다루며 `~/.claude` MCP 설정은 수정하지 않는다.
- provider 인증은 GitHub, Slack, Vercel, Supabase 등 서비스별로 분리된다.

복구:

- Codex에서 필요한 MCP만 Codex 설정에 등록한다.
- 외부 하네스의 install script를 그대로 실행하지 않는다.
- 후보 판단은 `docs/codex-only-mcp-plugin-catalog.md`와 `docs/domain-profiles/`를 기준으로 한다.

## Terminal Codex Command Broken

증상:

- 터미널에서 `codex`를 실행할 수 없다.
- `command -v codex`가 AppTranslocation 경로를 가리킨다.

확인:

```bash
command -v codex
codex --version
codex login status
```

복구:

- macOS에서는 `/Applications/Codex.app`에 앱을 고정하고 `/opt/homebrew/bin/codex` symlink를 사용한다.
- 자세한 절차는 `docs/macos-terminal-codex-setup.md`를 따른다.

## UTF-8 Or Replacement Character Failure

증상:

- verifier에서 UTF-8 strict 또는 `U+FFFD` replacement character 실패가 난다.
- 한글이 깨진 문서나 스킬이 보인다.

확인:

```bash
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
python3 -c 'from pathlib import Path; roots=[Path.home()/".codex", Path.home()/".agents"/"skills"]; [print(path) for root in roots for path in root.rglob("*") if path.is_file() and path.suffix in {".md",".json",".toml",".py",".sh",".yaml",".yml",".txt"} and "\ufffd" in path.read_text(encoding="utf-8", errors="ignore")]'
```

운영 기준:

- active Codex target에 `U+FFFD`가 있으면 실패한다.
- Claude reference 경로의 알려진 깨짐은 allowlist로만 관리하고, Codex 적용 대상에는 가져오지 않는다.

복구:

- 원본이 깨진 경우 그대로 복사하지 말고 의도만 다시 작성한다.
- 모든 Python 파일 I/O는 `encoding="utf-8"`, JSON 출력은 `ensure_ascii=False`를 사용한다.

## Dangerous Command Denied

증상:

- `rm -rf`, `git reset --hard`, `DROP TABLE`류 명령이 hook에서 거부된다.

원인:

- `PreToolUse`의 anti-loop/anti-destructive guard가 의도적으로 막은 것이다.

확인:

```bash
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

복구:

- 정말 필요한 파괴적 작업이면 사용자가 명시적으로 요청하고, 작업 범위와 백업을 먼저 확인한다.
- 일반 하네스 업데이트 과정에서는 guard를 끄지 않는다.

## GitHub Push Or Actions Failure

증상:

- `git push`가 실패한다.
- GitHub Actions에서 workspace-only verifier가 실패한다.

확인:

```bash
git remote -v
git status --short
gh auth status
gh run list --repo HMWKR/codex-dot --limit 5
```

복구:

- 로컬 전체 검증은 홈 Codex 설정을 본다.
- GitHub Actions는 공개 runner에서 `--workspace-only`만 실행한다.
- Actions 실패가 workspace 문서 sync라면 README, `AI_BOOTSTRAP.md`, manifest, verifier required list를 같이 업데이트한다.

## Windows Apply Caveat

증상:

- Windows에서 dry-run은 되지만 hook command 적용이 불확실하다.

운영 기준:

- 현재 하네스는 macOS-first이며 Windows는 기본적으로 dry-run/validation 경로가 안전하다.
- native Windows apply 전에는 hook command의 PowerShell/Git Bash/WSL 실행 방식을 먼저 정해야 한다.

복구:

- Windows에서 실제 적용이 필요하면 `hooks.powershell.json` 또는 OS별 hook 렌더링 분기를 별도 batch로 만든다.
- 그 전까지는 `py -3 tools/codex_harness_verify.py --workspace-only ...` 검증 중심으로 운용한다.
