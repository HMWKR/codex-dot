# Release Checklist

## 목적

이 체크리스트는 GitHub에 올리기 전, 이 저장소가 다른 사용자의 Claude/Codex/기타 홈 환경을 자동으로 건드리지 않는지 확인하기 위한 최종 게이트다.

## Required Gate

```bash
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_harness_inventory.py --output docs/claude-corpus-inventory.md
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
git status --short
```

통과 기준:

- `docs/harness-verification-report.md`의 `FAIL`이 0개다.
- 기본 migration 결과가 `dry_run: true`다.
- Secret/PII preflight가 `PASS`다.
- Restore dry-run이 `PASS`다.
- Idempotency 검사가 `PASS`다.
- `.claude/`, `.codex/`, `codex-harness-backups/`, checkpoint 파일이 Git 추적 대상에 없다.
- GitHub Actions workflow는 `--workspace-only` 검증을 사용한다.

## Secret/PII Preflight

GitHub에 올릴 파일에는 다음이 들어가면 안 된다.

- API key, provider token, GitHub token, Slack token, Stripe live key.
- private key block.
- 세션 transcript, 인증 cache, plugin runtime cache.
- 사용자의 개인 홈 런타임 전체 복사본.

검사는 `tools/codex_harness_verify.py`의 `Secret/PII preflight` 항목에서 수행한다.

## Restore Dry-Run

백업은 생성만으로 충분하지 않다. 복원 경로도 검증되어야 한다.

```bash
python3 tools/codex_native_harness_migrate.py --restore codex-harness-backups/<timestamp>
```

기본은 dry-run이다. 실제 복원은 다음처럼 명시한다.

```bash
python3 tools/codex_native_harness_migrate.py --restore codex-harness-backups/<timestamp> --apply
```

복원 정책:

- manifest에 기록된 SHA-256을 검증한다.
- Codex-owned path만 복원한다.
- `~/.claude`는 복원 대상이 아니다.
- manifest에 기록된 파일만 복원하고, 새로 생긴 파일을 자동 삭제하지 않는다.

## Idempotency

기본 migration dry-run은 여러 번 실행해도 같은 결과를 내야 한다. verifier는 기본 실행을 두 번 수행해 JSON payload가 같은지 확인한다.

실제 `--apply`는 홈 디렉터리를 쓰므로 release 전 자동으로 반복 실행하지 않는다. apply idempotency는 별도 로컬 검증 배치에서만 다룬다.

## MCP

외부 MCP server는 Claude나 Codex 중 어느 한쪽에 자동으로 같이 설치되는 것이 아니다. MCP server는 공통으로 쓸 수 있지만, Claude와 Codex의 클라이언트 설정은 별개다.

release 기준:

- 외부 MCP install script를 그대로 실행하지 않는다.
- Codex에서 쓸 MCP만 Codex 설정 후보로 문서화한다.
- Claude MCP 설정은 이 저장소가 수정하지 않는다.
- 같은 MCP를 양쪽에서 쓰려면 각 환경에서 별도 등록해야 한다.
- 후보 선택은 `docs/codex-only-mcp-plugin-catalog.md`를 기준으로 한다.
- 도메인별 필요성은 `docs/domain-profiles/`를 먼저 확인한다.

## GitHub Metadata

첫 push 전 남은 값:

- Git remote URL.
- Git author `user.name`.
- Git author `user.email`.

이 값은 사용자 로컬 Git 설정이므로 이 저장소가 자동으로 정하지 않는다.

## GitHub Actions

`.github/workflows/verify.yml`은 공개 runner에서 홈 Codex 설정을 요구하지 않는 `--workspace-only` 모드를 사용한다.

로컬 전체 검증:

```bash
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
```

GitHub runner 검증:

```bash
python3 tools/codex_harness_verify.py --workspace-only --markdown-output /tmp/harness-verification-report.md --json-output /tmp/harness-verification-report.json
```
