# GitHub 운영 절차

## 초기화

현재 디렉터리가 Git 저장소가 아니라면 한 번만 실행한다.

```bash
git init
git branch -M main
```

## 배포 안전 원칙

이 저장소를 GitHub에서 clone하는 것만으로 홈 디렉터리를 수정하지 않는다. 기본 명령은 읽기 전용 검증과 dry-run이어야 하며, 실제 설정 적용은 사용자가 명시적으로 `--apply`를 실행할 때만 가능하다.

- 이 저장소가 설정하는 범위는 Codex 환경만이다.
- Claude 환경은 별도 active harness로 유지하며, 이 저장소의 도구가 `~/.claude`에 쓰지 않는다.
- Codex 적용 대상은 `~/.codex`와 `~/.agents/skills`다.
- 인증, 세션, 로그, 플러그인 캐시, 다른 사용자의 기존 환경은 GitHub 배포 대상이 아니다.

## 커밋 전 확인

```bash
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_harness_inventory.py --output docs/claude-corpus-inventory.md
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
bash ~/.agents/skills/infra-audit/scripts/infra-audit.sh --quick
git status --short
```

`docs/harness-verification-report.md`의 `FAIL`이 0개가 아니면 GitHub 후보 하네스 검토, commit, push를 진행하지 않는다. `WARN`은 원인과 허용 범위가 문서화된 경우에만 통과로 본다.

최종 push 전에는 `docs/release-checklist.md`의 Secret/PII preflight, Restore dry-run, Idempotency, MCP 분리 원칙도 확인한다.

GitHub Actions에서는 홈 Codex 설정이 없을 수 있으므로 `.github/workflows/verify.yml`은 `--workspace-only` 검증만 수행한다. 로컬 전체 검증은 위 명령처럼 홈 Codex active harness까지 포함한다.

하네스 동작, 스킬 변환 규칙, 검증 기준이 바뀌었다면 같은 커밋에서 관련 문서도 함께 갱신한다.

- `README.md`
- `docs/migration-summary.md`
- `docs/codex-native-rebuild-plan.md`
- `docs/rebuild-3pass-review.md`
- `docs/claude-corpus-inventory.md`
- `docs/codex-native-rebuild-guide.html`
- `docs/github-harness-candidate-analysis.html`
- `docs/external-harness-import-notes.md`
- `docs/harness-boundary-classification.md`
- `docs/developer-domain-extension-review.md`
- `docs/codex-only-mcp-plugin-catalog.md`
- `docs/domain-profiles/`
- `docs/templates/`
- `docs/harness-verification-report.md`
- `docs/harness-verification-report.json`
- `docs/release-checklist.md`
- `docs/skill-asset-policy.md`
- `docs/github-workflow.md`

추적 대상에 다음이 들어가면 안 된다.

- `.claude/`
- `.codex/`
- `checkpoint.md`
- `codex-harness-backups/`
- 인증 파일, 세션 로그, 플러그인 캐시

## 커밋 메시지 형식

```text
## What
- 변경 요약

## Why
- 변경 이유

## Impact
- 영향 범위와 검증 결과

Co-Authored-By: Codex <codex@openai.com>
```

## GitHub 연결

현재 프로젝트는 로컬 Git 저장소로 초기화되어 있고 기본 브랜치는 `main`이다. 원격 저장소 URL이 정해지면 아래 절차를 이어간다.

현재 남은 값:

- Git remote URL
- Git author `user.name`
- Git author `user.email`

```bash
git config user.name "<YOUR_NAME>"
git config user.email "<YOUR_EMAIL>"
git remote add origin <GITHUB_REPO_URL>
git add README.md docs tools .github .gitignore
git commit -m "$(cat <<'MSG'
## What
- Document Codex-native harness bootstrap and rebuild workflow
- Add migration, inventory, verification tools, and GitHub workflow docs
- Add external harness candidate analysis for future imports

## Why
- Preserve Claude skill assets while rebuilding them for Codex
- Prepare this project as the source repository for Codex environment setup
- Gate external GitHub harness imports behind detailed verification

## Impact
- Runtime state and backups are excluded from Git
- Migration remains reproducible through tools/codex_native_harness_migrate.py
- Detailed verification is reproducible through tools/codex_harness_verify.py
- Future harness changes are tracked with matching documentation updates

Co-Authored-By: Codex <codex@openai.com>
MSG
)"
git push -u origin main
```

## 새 머신에서 복원

1. 저장소를 clone한다.
2. clone만으로 홈 디렉터리를 수정하지 않는다.
3. Claude를 쓰는 사용자는 Claude 환경을 별도로 유지한다. 이 저장소는 Claude 환경을 수정하지 않는다.
4. Codex 환경만 설정하려는 경우 migration을 dry-run 후 명시적으로 적용한다.

```bash
python3 tools/codex_native_harness_migrate.py
python3 tools/codex_native_harness_migrate.py --apply
```

5. 검증한다.

```bash
python3 tools/codex_harness_verify.py --markdown-output docs/harness-verification-report.md --json-output docs/harness-verification-report.json
bash ~/.agents/skills/infra-audit/scripts/infra-audit.sh --quick
```
