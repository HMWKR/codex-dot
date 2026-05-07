#!/usr/bin/env python3
"""
Verify behavior contracts for Codex skills.

This is a deterministic contract test, not a live model evaluation. It checks
that each skill contains the trigger, question, confirmation, tool-order, and
stop-condition language needed for the model to follow the intended behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


HOME = Path.home()
WORKSPACE = Path(__file__).resolve().parents[1]
CURATED = WORKSPACE / "codex" / "skills"
ACTIVE = HOME / ".agents" / "skills"


FORBIDDEN_RUNTIME_MARKERS = [
    "AskUserQuestion",
    "TodoWrite",
    "Task tool",
    "Agent tool",
    "allowed-tools",
    "CLAUDE_CODE",
    "CLAUDE.md",
    "~/.claude",
    "/home/claude",
]


@dataclass(frozen=True)
class Scenario:
    name: str
    prompt: str
    expected_first_move: str
    must_ask_or_confirm: str
    must_not: str


@dataclass(frozen=True)
class Contract:
    skill: str
    source: str
    purpose: str
    required_terms: dict[str, list[str]]
    ordered_terms: list[str]
    scenarios: list[Scenario]
    min_scenarios: int = 3
    compare_active_sync: bool = True


@dataclass
class AssertionResult:
    name: str
    status: str
    detail: str


@dataclass
class ContractResult:
    skill: str
    source: str
    status: str
    assertions: list[AssertionResult]
    scenario_count: int
    scenarios: list[Scenario]


def scenario(name: str, prompt: str, expected_first_move: str, must_ask_or_confirm: str, must_not: str) -> Scenario:
    return Scenario(
        name=name,
        prompt=prompt,
        expected_first_move=expected_first_move,
        must_ask_or_confirm=must_ask_or_confirm,
        must_not=must_not,
    )


CONTRACTS: list[Contract] = [
    Contract(
        skill="what",
        source="active",
        compare_active_sync=False,
        purpose="Golden reference for staged confirmation-loop behavior.",
        required_terms={
            "trigger_boundary": ["/what", "트리거", "비트리거", "NOT for"],
            "iron_law": ["Iron Law", "사용자의 Yes 없이는 절대 다음 STEP으로 넘어가지 않는다"],
            "announce": ["구조화된 사고 프레임워크를 사용하여 요청의 근본 목적을 정립합니다", "Why → What → How → So What"],
            "step_contract": ["STEP 1: Why", "STEP 2: What", "STEP 3: How", "STEP 4: So What"],
            "confirmation": ["Confirmation Loop", "Progressive Table + 자연어 요약", "이 방향이 맞나요"],
            "repair": ["Backtrack Protocol", "다시 제시", "수정이 필요합니다"],
            "execution_choice": ["실행 방식 선택", "update_plan로 단계별 추적하며 실행", "바로 실행"],
        },
        ordered_terms=["Announce", "STEP 1: Why", "STEP 2: What", "STEP 3: How", "STEP 4: So What", "실행 방식 선택"],
        scenarios=[
            scenario("/what trigger", "/what 이 기능의 목적을 정리해줘", "Announce then STEP 1 table only.", "Ask whether the Why direction is right.", "Do not jump to What before user confirmation."),
            scenario("yes advances one step", "맞아", "Advance only to the next pending step.", "Ask for confirmation again at the new step.", "Do not collapse multiple steps into one response."),
            scenario("modify branch", "수정이 필요해", "Offer concrete modification choices for the current step.", "Ask which correction to apply.", "Do not repeat the same table unchanged."),
            scenario("backtrack", "이전 Why가 틀렸어", "Announce that a prior step needs correction.", "Ask whether to return to the earlier step or continue.", "Do not keep later steps as confirmed after backtracking."),
            scenario("skip framework", "그냥 해줘", "Stop the framework and summarize confirmed context.", "Confirm direct execution path if needed.", "Do not continue the four-step loop."),
        ],
        min_scenarios=5,
    ),
    Contract(
        skill="grill-me",
        source="curated",
        purpose="One-question-at-a-time planning interview.",
        required_terms={
            "trigger": ["grill me", "그릴미", "stress-test this plan"],
            "question_contract": ["Ask exactly one question per turn", "Include a recommended answer", "Options: A / B / C"],
            "context_first": ["If a question can be answered by reading the codebase", "inspect files with `rg`"],
            "stop_guard": ["Do not proceed to implementation", "critical decision tree is resolved"],
            "finish": ["Goal:", "Confirmed decisions:", "First implementation move:"],
        },
        ordered_terms=["Restate the plan", "Identify the most load-bearing", "Ask one question", "After the user answers", "Finish with a decision brief"],
        scenarios=[
            scenario("fuzzy plan", "그릴미. 결제 기능 만들 계획 검증해줘", "Restate plan and ask exactly one load-bearing question.", "Include recommended answer and options.", "Do not implement payment code."),
            scenario("repo-answerable", "이 구조에서 인증 방식을 질문하면서 정리해줘", "Inspect repo first when files can answer.", "Ask only the unresolved decision.", "Do not ask questions already answerable from files."),
            scenario("implementation handoff", "이제 구현해줘", "Convert final decision brief to plan when enough decisions exist.", "Ask remaining critical question if still unresolved.", "Do not proceed while critical branches remain open."),
        ],
    ),
    Contract(
        skill="to-prd",
        source="curated",
        purpose="Convert known context into a product requirements document without needless interviewing.",
        required_terms={
            "trigger": ["to PRD", "PRD로 만들어줘", "제품 요구사항 문서"],
            "repo_context": ["Read existing context", "Inspect repository signals"],
            "ask_guard": ["Do not interview by default", "ask only when a missing decision would materially change the PRD", "ask one focused question before publishing"],
            "publishing": ["Confirm the target repository/project", "Do not include secrets", "Report the created issue URL"],
            "quality": ["confirmed decisions", "inferred decisions", "out-of-scope"],
        },
        ordered_terms=["Read existing context", "Inspect repository signals", "Decide output target", "Apply a triage label"],
        scenarios=[
            scenario("known context", "지금 대화를 PRD로 만들어줘", "Synthesize the PRD from available context.", "Ask only if a missing decision changes the PRD materially.", "Do not start a broad interview."),
            scenario("issue publishing", "이걸 GitHub issue용 PRD로 만들어줘", "Prepare issue-shaped PRD and check target repo if ambiguous.", "Confirm target when multiple repos/projects are plausible.", "Do not publish to the wrong tracker."),
            scenario("local draft", "docs에 PRD 파일로 남겨줘", "Use existing docs/prd or product-docs location.", "Ask if output path materially changes project convention.", "Do not use brittle source file promises."),
        ],
    ),
    Contract(
        skill="tdd",
        source="curated",
        purpose="One observable behavior at a time red-green-refactor loop.",
        required_terms={
            "trigger": ["TDD", "red-green-refactor", "TDD + 피드백 루프"],
            "loop": ["RED: one behavior test fails", "GREEN: minimal code makes it pass", "REFACTOR"],
            "ask_guard": ["Clarify the public interface", "if they are ambiguous", "Stop and ask before proceeding"],
            "planning": ["Create an `update_plan`", "three or more behavior slices"],
            "test_standard": ["public interfaces", "Fails for one clear reason", "Avoids mocking internal collaborators"],
        },
        ordered_terms=["Discover the existing test runner", "Write the first failing test", "Run the narrowest relevant test", "Implement the smallest change", "Finish with the broader relevant test"],
        scenarios=[
            scenario("feature request", "TDD로 검색 필터 추가해줘", "Discover test runner and pick the first observable behavior.", "Clarify public interface if ambiguous.", "Do not write all tests before implementation."),
            scenario("bug regression", "이 버그를 regression-first로 고쳐줘", "Create a failing regression test first.", "Ask if a stable behavior interface cannot be identified.", "Do not patch without watching the test fail."),
            scenario("no tests wanted", "그냥 구현만 해", "Stop TDD path when user explicitly rejects tests.", "Confirm direct implementation implications if needed.", "Do not force TDD against explicit user direction."),
        ],
    ),
    Contract(
        skill="diagnose",
        source="curated",
        purpose="Feedback-loop-first debugging and performance diagnosis.",
        required_terms={
            "trigger": ["diagnose", "debug this", "버그 진단", "performance regression"],
            "loop_first": ["Do not fix by staring", "Feedback Loop", "pass/fail loop"],
            "ask_guard": ["If no loop can be built", "stop and ask for a captured artifact"],
            "hypotheses": ["Generate 3-5 ranked hypotheses", "Each hypothesis must predict"],
            "cleanup": ["All `[DEBUG-...]` instrumentation is removed", "confirmed cause", "prevention opportunity"],
        },
        ordered_terms=["Feedback Loop", "Reproduce", "Hypothesize", "Instrument", "Fix and Regression Test", "Cleanup and Report"],
        scenarios=[
            scenario("hard failure", "diagnose. 로그인 후 깨져", "Build or find a deterministic repro loop first.", "Ask for artifact if no loop can be built.", "Do not jump straight to code changes."),
            scenario("intermittent bug", "가끔 실패해", "Choose repeated-run, stress, bisection, or differential loop.", "Ask for reproduction artifacts if needed.", "Do not claim fixed without rerunning the original loop."),
            scenario("performance regression", "최근 느려졌어", "Measure a baseline and map probes to hypotheses.", "Report ranked hypotheses before or after probing.", "Do not compare multiple changes at once."),
        ],
    ),
    Contract(
        skill="improve-codebase-architecture",
        source="curated",
        purpose="Architecture friction discovery before proposing refactors.",
        required_terms={
            "trigger": ["improve-codebase", "아키텍처 개선", "make this more testable"],
            "context_first": ["Read project context before judging architecture", "Explore the codebase with `rg`"],
            "candidate_first": ["Present candidates before proposing interfaces", "Ask which candidate the user wants to explore"],
            "decision_guards": ["Do not treat every abstraction as good", "Do not fight ADRs", "offer to record an ADR"],
            "format": ["Candidate name", "Files/modules:", "Testability impact:"],
        },
        ordered_terms=["Read project context", "Explore the codebase", "Notice friction", "Apply the deletion test", "Present candidates"],
        scenarios=[
            scenario("scan architecture", "improve-codebase 해줘", "Read context and surface candidates first.", "Ask which candidate to explore.", "Do not propose full interfaces immediately."),
            scenario("testability focus", "이걸 더 테스트 가능하게 만들어줘", "Find seams and test surface problems.", "Ask before deep-diving into a candidate.", "Do not refactor without user selecting scope."),
            scenario("ADR conflict", "기존 결정이 이상해 보여", "Check ADR/context conflicts.", "Ask whether to reopen or record an ADR when justified.", "Do not fight stable ADRs casually."),
        ],
    ),
    Contract(
        skill="live-verify-loop",
        source="curated",
        purpose="Repeated live browser verification until declared criteria pass.",
        required_terms={
            "trigger": ["live verification", "100% until browser passes", "multi-round live audit"],
            "setup_questions": ["Target scope", "Verification mode", "Termination criteria", "Tool plan", "Round limits"],
            "ask_guard": ["If any item is ambiguous, ask before starting the loop"],
            "tool_priority": ["Terminal:", "Browser Use:", "Computer Use:", "Playwright or scripts:", "Do not require Playwright MCP"],
            "browser_proof": ["Capture screenshots only as evidence", "not as the sole pass condition", "cannot satisfy Layer 2"],
        },
        ordered_terms=["Terminal:", "Browser Use:", "Computer Use:", "Playwright or scripts:"],
        scenarios=[
            scenario("ambiguous target", "100% 브라우저 통과할 때까지 봐줘", "Ask for missing target scope, mode, criteria, tool plan, and round limits.", "Confirm ambiguous setup before loop.", "Do not start clicking with undefined scope."),
            scenario("browser default", "localhost UI live verify 해줘", "Use terminal for server/checks and Browser Use for proof.", "Ask for credentials/destructive boundary if needed.", "Do not require Playwright MCP when Browser Use can prove it."),
            scenario("desktop state", "다운로드와 파일 피커까지 검증해줘", "Escalate to Computer Use for OS/browser-profile state.", "Confirm safe boundaries around files/accounts.", "Do not treat terminal-only checks as live proof."),
        ],
    ),
    Contract(
        skill="harness-loop",
        source="curated",
        purpose="Codex-native orchestration with explicit subagent authorization and quality gates.",
        required_terms={
            "trigger": ["harness loop", "agent orchestration", "agents plus verification"],
            "delegation_guard": ["Only spawn subagents when the user explicitly asked", "Otherwise, run the work locally"],
            "routing": ["Classify the task", "build", "fix", "audit", "analyze", "cleanup"],
            "quality_gates": ["Browser Use first", "Computer Use", "Playwright/scripts", "Static analysis alone is not a final UI proof"],
            "stop_guard": ["Stop and ask before continuing", "destructive access", "overlapping write scopes"],
        },
        ordered_terms=["Phase 0: Discover", "Phase 1: Route", "Phase 2: Execute Rounds", "Phase 3: Quality Gates", "Phase 4: Record"],
        scenarios=[
            scenario("no delegation", "이 버그 고쳐줘", "Run locally with quality gates unless delegation was authorized.", "Ask before spawning if task truly needs agents.", "Do not spawn subagents by default."),
            scenario("explicit agents", "agents plus verification로 개선해줘", "Route mode and assign disjoint ownership when delegating.", "Clarify overlapping write scopes if needed.", "Do not let workers revert unrelated changes."),
            scenario("UI changed", "UI 고치고 검증까지", "Use Browser Use first and scripts for deterministic checks as needed.", "Ask for credentials or destructive boundaries.", "Do not accept static analysis as final UI proof."),
        ],
    ),
    Contract(
        skill="cantos-write",
        source="curated",
        purpose="Cantos MCP-first durable project records with honest local fallback.",
        required_terms={
            "trigger": ["Cantos MCP", "ADR", "DDR", "journal"],
            "tool_selection": ["Check whether Cantos MCP tools are available", "If unavailable", "Never pretend a remote Cantos write happened"],
            "approval": ["ask for explicit approval", "registering a project"],
            "visual_order": ["Browser Use by default", "Computer Use", "Playwright/scripts"],
            "safety": ["Do not write secrets", "Do not use Cantos as a substitute for tests"],
        },
        ordered_terms=["Check whether Cantos MCP tools are available", "If available", "If unavailable", "Never pretend"],
        scenarios=[
            scenario("mcp connected", "Cantos에 ADR 써줘", "Use connected Cantos tool when available.", "Ask approval before first remote registration/write if required.", "Do not create only local markdown while claiming remote write."),
            scenario("mcp missing", "Cantos DDR 준비해줘", "Say Cantos MCP is not connected and offer local draft.", "Ask whether to create local fallback.", "Do not pretend remote Cantos exists."),
            scenario("visual record", "브라우저 증거 붙여서 DDR", "Capture Browser Use evidence by default, Computer Use if OS state matters.", "Confirm missing visual evidence.", "Do not substitute Cantos record for verification."),
        ],
    ),
    Contract(
        skill="ultradetail-walk",
        source="curated",
        purpose="One exhaustive persona walk-through with explicit scope and category/persona choices.",
        required_terms={
            "trigger": ["ultradetail walk", "click everything", "all interactions checked once"],
            "preflight": ["Confirm target routes", "Confirm browser proof tooling", "Create an `update_plan`"],
            "choice_points": ["For Step 3 and Step 4", "propose 2-4 options", "let the user adjust"],
            "tool_priority": ["Browser Use by default", "Computer Use", "Playwright or scripts", "not a Playwright MCP dependency"],
            "clean_claim_guard": ["Do not claim a clean result unless every selected persona", "explicitly scoped out"],
        },
        ordered_terms=["Preflight", "Seven-Step Walk", "Discovery", "Browser Walk", "Adversarial Pass", "Report"],
        scenarios=[
            scenario("broad walk", "ultradetail로 버튼 전부 봐줘", "Confirm scope, roles, tooling, and create plan.", "Offer category/persona options when broad.", "Do not start without browser-capable tooling."),
            scenario("small scope", "이 한 페이지 클릭 전부 확인", "Make conservative category/persona recommendation and proceed if risk is small.", "Ask only when scope/risk needs adjustment.", "Do not remove selected personas silently."),
            scenario("no credentials", "관리자 플로우도 봐줘", "Stop if login/test data is missing and cannot be safely created.", "Ask for test data or scope narrowing.", "Do not use destructive flows."),
        ],
    ),
    Contract(
        skill="ultradetail-loop",
        source="curated",
        purpose="Repeated exhaustive walk-fix-walk convergence loop for release gates.",
        required_terms={
            "trigger": ["ultradetail loop", "exhaustive QA until zero new defects", "walk fix re-walk"],
            "setup": ["Confirm target scope", "Set hard limits", "stagnation limit", "per-round evidence expectations"],
            "tool_priority": ["Browser Use as the default", "Computer Use", "Playwright or scripts", "Do not block the loop merely because Playwright MCP is unavailable"],
            "round_cycle": ["Walk all selected normal personas", "Walk all selected adversarial personas", "Record round evidence"],
            "stop": ["same defect survives three fix attempts", "maximum rounds are reached", "required tooling, credentials, or test data is missing"],
        },
        ordered_terms=["Initial Setup", "Tool Priority", "Round Cycle", "Stop Conditions", "Evidence", "Cantos"],
        scenarios=[
            scenario("release gate", "ultradetail-loop로 출시 전까지 반복해줘", "Confirm scope, roles, browser tooling, hard limits, and evidence expectations.", "Ask for destructive-flow boundaries.", "Do not run an unbounded loop."),
            scenario("playwright missing", "Playwright 없이 브라우저 루프", "Use Browser Use or Computer Use if they can provide evidence.", "Ask only if no browser-capable tool exists.", "Do not block merely because Playwright MCP is unavailable."),
            scenario("stagnation", "계속 같은 문제가 남아", "Stop or reassess after repeated failed fix attempts.", "Ask whether to narrow, redesign, or stop.", "Do not keep fixing symptoms forever."),
        ],
    ),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_home(path: Path) -> str:
    try:
        return "$HOME/" + str(path.relative_to(HOME))
    except ValueError:
        try:
            return str(path.relative_to(WORKSPACE))
        except ValueError:
            return str(path)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.DOTALL)
    if not match:
        return {}
    values: dict[str, str] = {}
    current_key: str | None = None
    block_lines: list[str] = []
    for line in match.group(1).splitlines():
        if current_key and (line.startswith(" ") or line.startswith("\t")):
            block_lines.append(line.strip())
            continue
        if current_key:
            values[current_key] = " ".join(block_lines).strip()
            current_key = None
            block_lines = []
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            current_key = key
            block_lines = []
        else:
            values[key] = value.strip("'\"")
    if current_key:
        values[current_key] = " ".join(block_lines).strip()
    return values


def contains_term(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def terms_in_order(text: str, terms: list[str]) -> tuple[bool, str]:
    cursor = 0
    lower = text.lower()
    for term in terms:
        index = lower.find(term.lower(), cursor)
        if index < 0:
            return False, f"missing or out of order: {term!r}"
        cursor = index + len(term)
    return True, "terms appear in expected order"


def selected_skill_path(contract: Contract) -> Path:
    if contract.source == "curated":
        return CURATED / contract.skill / "SKILL.md"
    if contract.source == "active":
        return ACTIVE / contract.skill / "SKILL.md"
    raise ValueError(f"unknown source {contract.source!r}")


def compare_source_to_active(skill: str) -> AssertionResult:
    source_dir = CURATED / skill
    active_dir = ACTIVE / skill
    if not active_dir.exists():
        return AssertionResult("active sync", "FAIL", f"missing active skill {rel_home(active_dir)}")
    mismatches: list[str] = []
    for source_file in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        if source_file.name == ".DS_Store" or "__pycache__" in source_file.parts:
            continue
        relative = source_file.relative_to(source_dir)
        active_file = active_dir / relative
        if not active_file.exists():
            mismatches.append(f"missing {relative}")
        elif sha256(source_file) != sha256(active_file):
            mismatches.append(f"hash mismatch {relative}")
    if mismatches:
        return AssertionResult("active sync", "FAIL", "; ".join(mismatches[:20]))
    return AssertionResult("active sync", "PASS", "curated source files match active skill root")


def verify_contract(contract: Contract, *, workspace_only: bool) -> ContractResult:
    assertions: list[AssertionResult] = []
    path = selected_skill_path(contract)

    if workspace_only and contract.source == "active":
        assertions.append(AssertionResult("workspace-only skip", "PASS", "active-only contract skipped by workspace-only policy"))
        return ContractResult(contract.skill, contract.source, "PASS", assertions, len(contract.scenarios), contract.scenarios)

    if not path.exists():
        assertions.append(AssertionResult("entrypoint", "FAIL", f"missing {rel_home(path)}"))
        return ContractResult(contract.skill, contract.source, "FAIL", assertions, len(contract.scenarios), contract.scenarios)

    try:
        text = read_text(path)
    except UnicodeDecodeError as exc:
        assertions.append(AssertionResult("utf8", "FAIL", str(exc)))
        return ContractResult(contract.skill, contract.source, "FAIL", assertions, len(contract.scenarios), contract.scenarios)

    frontmatter = parse_frontmatter(text)
    if frontmatter.get("name") == contract.skill and frontmatter.get("description"):
        assertions.append(AssertionResult("frontmatter", "PASS", "name and description present"))
    else:
        assertions.append(AssertionResult("frontmatter", "FAIL", "frontmatter must include matching name and description"))

    for group, terms in contract.required_terms.items():
        missing = [term for term in terms if not contains_term(text, term)]
        if missing:
            assertions.append(AssertionResult(group, "FAIL", "missing: " + ", ".join(repr(term) for term in missing)))
        else:
            assertions.append(AssertionResult(group, "PASS", f"{len(terms)} required terms found"))

    if contract.ordered_terms:
        ok, detail = terms_in_order(text, contract.ordered_terms)
        assertions.append(AssertionResult("ordered flow", "PASS" if ok else "FAIL", detail))

    forbidden = [term for term in FORBIDDEN_RUNTIME_MARKERS if contains_term(text, term)]
    if forbidden:
        assertions.append(AssertionResult("runtime residue", "FAIL", "forbidden markers: " + ", ".join(forbidden)))
    else:
        assertions.append(AssertionResult("runtime residue", "PASS", "no forbidden runtime markers"))

    if len(contract.scenarios) >= contract.min_scenarios:
        assertions.append(AssertionResult("scenario matrix", "PASS", f"{len(contract.scenarios)} scenarios defined"))
    else:
        assertions.append(AssertionResult("scenario matrix", "FAIL", f"expected at least {contract.min_scenarios}, got {len(contract.scenarios)}"))

    if contract.compare_active_sync:
        if workspace_only:
            assertions.append(AssertionResult("active sync", "PASS", "skipped by workspace-only policy"))
        else:
            assertions.append(compare_source_to_active(contract.skill))

    statuses = {assertion.status for assertion in assertions}
    status = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"
    return ContractResult(contract.skill, contract.source, status, assertions, len(contract.scenarios), contract.scenarios)


def build_payload(results: list[ContractResult], *, workspace_only: bool) -> dict[str, object]:
    summary = {
        "pass": sum(1 for result in results if result.status == "PASS"),
        "warn": sum(1 for result in results if result.status == "WARN"),
        "fail": sum(1 for result in results if result.status == "FAIL"),
        "contracts": len(results),
        "scenarios": sum(result.scenario_count for result in results),
        "workspace_only": workspace_only,
    }
    return {
        "schema_version": "1.0.0",
        "generated_by": "tools/codex_skill_contract_verify.py",
        "summary": summary,
        "results": [
            {
                "skill": result.skill,
                "source": result.source,
                "status": result.status,
                "assertions": [asdict(assertion) for assertion in result.assertions],
                "scenario_count": result.scenario_count,
                "scenarios": [asdict(item) for item in result.scenarios],
            }
            for result in results
        ],
    }


def build_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]  # type: ignore[index]
    assert isinstance(summary, dict)
    lines = [
        "# Skill Behavior Contract Tests",
        "",
        "이 문서는 스킬이 실제 대화에서 지켜야 할 행동 계약을 deterministic하게 검증하기 위한 테스트 매트릭스다.",
        "실제 모델 호출 결과를 채점하는 테스트가 아니라, `SKILL.md`가 트리거, 확인 질문, 중단 조건, 도구 우선순위, 금지 런타임 문구를 충분히 명시하는지 확인한다.",
        "",
        "## Summary",
        "",
        f"- Contracts: {summary['contracts']}",
        f"- Scenarios: {summary['scenarios']}",
        f"- PASS: {summary['pass']}",
        f"- WARN: {summary['warn']}",
        f"- FAIL: {summary['fail']}",
        f"- Workspace-only: `{str(summary['workspace_only']).lower()}`",
        "",
        "## Command",
        "",
        "```bash",
        "python3 tools/codex_skill_contract_verify.py --markdown-output docs/skill-behavior-contract-tests.md --json-output docs/skill-behavior-contract-tests.json",
        "```",
        "",
        "## Interpretation",
        "",
        "- `what`은 활성 스킬 루트의 골든 레퍼런스로 검사한다.",
        "- `codex/skills`의 curated 스킬은 원본과 `$HOME/.agents/skills` 활성 사본의 해시 일치까지 검사한다.",
        "- `PASS`는 문서 계약이 충분하다는 뜻이다. 실제 모델 회귀 테스트는 같은 시나리오를 headless Codex runner에 연결하면 확장할 수 있다.",
        "- `WARN`은 workspace-only 환경에서 active root 검증을 건너뛴 경우처럼 의도적으로 약화된 검사다.",
        "",
        "## Contract Results",
        "",
        "| Skill | Source | Status | Scenarios | Key assertion summary |",
        "|---|---|---|---:|---|",
    ]
    for result in payload["results"]:  # type: ignore[index]
        assert isinstance(result, dict)
        assertions = result["assertions"]
        assert isinstance(assertions, list)
        failed = [item for item in assertions if isinstance(item, dict) and item.get("status") == "FAIL"]
        warned = [item for item in assertions if isinstance(item, dict) and item.get("status") == "WARN"]
        if failed:
            summary_text = "FAIL: " + "; ".join(str(item.get("name")) for item in failed[:4])
        elif warned:
            summary_text = "WARN: " + "; ".join(str(item.get("name")) for item in warned[:4])
        else:
            summary_text = "all assertions passed"
        lines.append(f"| `{result['skill']}` | {result['source']} | {result['status']} | {result['scenario_count']} | {summary_text} |")

    lines.extend(["", "## Scenario Matrix", ""])
    for result in payload["results"]:  # type: ignore[index]
        assert isinstance(result, dict)
        lines.extend([f"### {result['skill']}", "", "| Scenario | Prompt | Expected first move | Must ask/confirm | Must not |", "|---|---|---|---|---|"])
        for item in result["scenarios"]:  # type: ignore[index]
            assert isinstance(item, dict)
            values = [str(item["name"]), str(item["prompt"]), str(item["expected_first_move"]), str(item["must_ask_or_confirm"]), str(item["must_not"])]
            escaped = [value.replace("|", "\\|").replace("\n", " ") for value in values]
            lines.append("| " + " | ".join(escaped) + " |")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-only", action="store_true", help="Skip active-root-only checks for GitHub runners.")
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    results = [verify_contract(contract, workspace_only=args.workspace_only) for contract in CONTRACTS]
    payload = build_payload(results, workspace_only=args.workspace_only)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(build_markdown(payload), encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    summary = payload["summary"]
    assert isinstance(summary, dict)
    return 1 if int(summary["fail"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
