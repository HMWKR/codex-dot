# 스킬 자산 관리 원칙

## 원칙

Claude 스킬은 개인 자산으로 취급한다. 다만 Claude 하네스는 Codex의 보관소나 하위 개념이 아니라 Claude-native active harness로 계속 유지한다. 이 저장소는 Claude 환경을 수정하지 않고, Codex 환경에 필요한 구현만 Codex-native active harness로 별도 작성한다.

## 하네스 분류

```text
Claude-native active harness:
  ~/.claude/skills

Codex-native active harness:
  ~/.agents/skills
```

`~/.claude/skills`는 Claude에서 계속 사용하는 실사용 환경이다. `~/.agents/skills`는 Codex에서 사용하는 실사용 환경이다. 두 환경은 서로 덮어쓰지 않고, 같은 작업 철학이 필요할 때도 각 런타임에 맞는 별도 `SKILL.md`로 구현한다.

## 동기화 정책

- 삭제 없는 병합을 기본값으로 한다.
- `__pycache__`, `.git`, `.DS_Store`만 제외한다.
- 텍스트 파일은 UTF-8로 읽고 쓴다.
- `CLAUDE.md`, `.claude`, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 같은 Claude 전용 실행 문맥은 Codex active harness에 실행 지시로 남기지 않는다.
- 변환 후 대상에 `U+FFFD`가 남아 있으면 실패로 본다.
- 이 저장소의 적용 도구는 Claude 경로에는 쓰지 않고 Codex 경로에만 쓴다.
- `python3 tools/codex_native_harness_migrate.py`는 기본 dry-run이며, 실제 적용은 `--apply`가 있을 때만 수행한다.

## Codex-native 재작성 정책

- Codex skill entrypoint는 `SKILL.md` 대문자로 고정한다.
- frontmatter에는 `name`, `description`을 반드시 둔다.
- description은 자연어 호출이 가능하도록 한국어와 영어 트리거를 함께 포함한다.
- Claude slash command는 Codex skill name과 자연어 트리거로 바꾼다.
- Claude 전용 도구명은 Codex 실제 기능에 맞게 바꾼다.
  - `AskUserQuestion`: 필요한 경우 짧은 사용자 질문.
  - `Task tool`, `Agent tool`: Codex subagent 정책.
  - `TodoWrite`: `update_plan`.
  - `allowed-tools`: 권한 경계가 아닌 행동 가이드.
- 원본의 철학과 판단 기준은 보존하되, Codex에서 실행 불가능한 절차는 그대로 남기지 않는다.

## 3회 검토 원칙

스킬 하나를 변환할 때도 최소 3번 검토한다.

1. 원본 의도 검토: Claude Markdown의 목적, 트리거, 흐름, 산출물을 그대로 요약한다.
2. Codex 매핑 검토: Codex skill, subagent, hook, script, plan 도구로 옮길 수 있는 부분과 없는 부분을 나눈다.
3. 누락/충돌 검토: 빠진 규칙, 잘못 해석한 표현, 시스템 지침과 충돌하는 행동을 다시 확인한다.

3회 검토 결과가 불명확하면 Codex active harness를 수정하지 않고 문서에 미확정 항목으로 남긴다.

## 스킬 수정 절차

1. Claude-native 스킬 또는 기존 Codex 실사용본을 읽고 의도를 정리한다.
2. 3회 검토 게이트를 통과한다.
3. Codex-native `SKILL.md`를 수정한다.
4. 관련 문서를 업데이트한다.
5. dry-run을 실행한다.

```bash
python3 tools/codex_harness_inventory.py --output docs/claude-corpus-inventory.md
```

```bash
python3 tools/codex_native_harness_migrate.py
```

6. 문제가 없으면 적용한다.

```bash
python3 tools/codex_native_harness_migrate.py --apply
```

7. 검증한다.

```bash
bash ~/.agents/skills/infra-audit/scripts/infra-audit.sh --quick
```

## 주의

- `~/.agents/skills`에서 직접 수정한 Codex-only 스킬은 삭제하지 않는다.
- Claude 경로는 이 저장소가 수정하지 않는다.
- Claude 파일에 이미 깨진 문자가 있으면 Claude 환경은 그대로 두고 Codex 대상에서만 문맥 복구한다.
- 인증 정보, 세션 기록, 플러그인 캐시는 스킬 자산이 아니므로 이 저장소에 올리지 않는다.
