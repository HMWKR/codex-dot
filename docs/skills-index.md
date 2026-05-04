# Codex Skill Index

이 문서는 활성 Codex 사용자 스킬을 AI가 빠르게 라우팅할 수 있도록 만든 인덱스다.
원본 스킬 본문은 Git에 복사하지 않고, `$HOME/.agents/skills/*/SKILL.md`의 frontmatter와 해시만 기록한다.

## Summary

- Skills: 49
- Source root: `$HOME/.agents/skills`
- Machine-readable index: `docs/skills-index.json`
- Regenerate: `python3 tools/codex_skill_index.py`

## Category Map

| Category | Count | Primary use |
|---|---:|---|
| command-bridge | 5 | Claude command 의도를 Codex skill로 호출하는 bridge |
| core | 1 | 공통 SSoT와 하네스 핵심 규칙 |
| documents | 4 | 문서, PDF, PPT, 스프레드시트 작업 |
| engineering | 6 | 아키텍처, 리팩터링, 도메인 리서치 |
| orchestration | 11 | 멀티 에이전트, 프로젝트 부트스트랩, QA 루프 |
| reasoning | 11 | 문제 정의, 사고 프레임, 의사결정 |
| support | 1 | 특수 보조 작업 |
| validation | 8 | 테스트, 보안, 인프라, UI/UX 검증 |
| web-platform | 2 | Vercel, React, Next.js, 웹 배포 |

## Routing Rules

- 사용자가 `$skill` 또는 명시적 스킬명을 말하면 해당 `SKILL.md`를 먼저 연다.
- 여러 스킬이 맞으면 `reasoning → orchestration → validation → implementation` 순서로 최소 조합만 사용한다.
- 스킬 본문 전체를 한꺼번에 복사하지 말고, frontmatter와 직접 참조된 파일만 progressive disclosure로 읽는다.
- Claude 전용 런타임 표현은 Codex 행동 지침으로 해석하고, Claude 경로에는 쓰지 않는다.
- 스킬 변경 후에는 `python3 tools/codex_skill_index.py`와 verifier를 같이 실행한다.

## Skills

### command-bridge

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P0 | `source-command-analyze` | source-command-analyze | 심층 분석 모드 활성화 및 현재 작업 분석 Use when the user asks for deep analysis, 심층 분석, careful review, root-cause analysis, or a more rigorous current-task analysis. | 42 |
| P0 | `source-command-journal` | source-command-journal | 현재 작업에 대한 CE 사고 여정 생성 Use when the user asks to write a CE journey, 사고 여정, thinking log, 작업 기록, or post-work context-engineering record. | 53 |
| P0 | `source-command-orchestrate` | source-command-orchestrate | Agent Teams 오케스트레이션 모드 활성화 Use when the user explicitly asks for Agent Teams, orchestration, parallel agents, subagents, 팀 구성, or multi-agent delegation. | 52 |
| P0 | `source-command-pdca` | source-command-pdca | PDCA Gap 검증 및 반복 개선 (설계 vs 구현 비교) Use when the user asks for PDCA, gap analysis, 설계 vs 구현 비교, implementation drift, match rate, or iterative improvement. | 64 |
| P0 | `source-command-rules` | source-command-rules | 전체 하니스 규칙 참조 가이드 Use when the user asks for harness rules, rule references, 하니스 규칙, Codex environment structure, or where instructions live. | 58 |

### core

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P0 | `_core` | _core | Shared SSoT (Single Source of Truth) resources referenced by multiple skills. Contains expert role definitions, problem-solving protocols, team orchestration patterns, and QA checklists. This skill should NOT be invoked directly — it provides foundational references for other skills via file paths. | 46 |

### documents

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P2 | `docx` | docx | Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when working with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks | 227 |
| P2 | `pdf` | pdf | Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. Use when filling in PDF forms or programmatically processing, generating, or analyzing PDF documents at scale. | 563 |
| P2 | `ppt-study` | ppt-study | PPT 학습자료 자동 생성 스킬. PPT 파일을 분석하여 PDF 학습 정리 + PDF 시험문제 + Notion 페이지 2종을 자동 생성. Use when "/ppt-study", "PPT 정리", "PPT 분석해서 정리", "시험자료 만들어줘", "수업자료 정리", or user provides a .pptx file for study material generation. NOT for: simple PPT file reading, PPT template creation, or slide design tasks. | 377 |
| P2 | `xlsx` | xlsx | Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. Use when working with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating new spreadsheets with formulas and formatting, (2) Reading or analyzing data, (3) Modifying existing spreadsheets while preserving formulas, (4) Data analysis and visualization in spreadsheets, or (5) Recalculating formulas | 322 |

### engineering

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P0 | `architect` | architect | Architecture scaffolding and project structure design skill. This skill should be used when the user asks to "design architecture", "scaffold project", "아키텍처 설계", "프로젝트 구조 잡아줘", "파이프라인 설계", "팀 구성 설계", "에이전트 팀 편성", or "프로젝트 초기 설정". NOT for: "architect" as person/role reference, code containing "architect" as variable name. 7-step execution flow with expert role-playing system and built-in improvement proposals. | 359 |
| P2 | `domain-expert-analysis` | domain-expert-analysis | Autonomously adopt domain-appropriate expert perspectives for analysis tasks. This skill activates for research, analysis, investigation, evaluation, assessment, review, audit, diagnosis, consultation, and expert opinion tasks. Provides dynamic expert role generation and strict anti-hallucination protocol. Use when deep domain expertise and verified information are critical. Agent-Teams 모드: Codex subagents=1 시 다중 전문가 병렬 분석. Fallback: agent-teams 미활성 시 단일 에이전트 순차 분석. | 629 |
| P2 | `domain-researcher` | domain-researcher | 프로젝트 시작 전 도메인 날리지를 웹 검색으로 체계적으로 수집하는 리서치 스킬. 5개 모듈(시장 분석, 경쟁사 분석, 기술 스택 리서치, 도메인 데이터, 규제/법률)을 자동 실행하여 검증된 도메인 날리지 파일을 생성한다. 트리거: "시장 조사해줘", "경쟁사 분석", "도메인 리서치", "자료 조사", "시장 규모 알아봐줘", "기술 스택 조사", "관련 법률 확인", "도메인 날리지", "/research", "프로젝트 시작 전에 조사부터", "이 분야 현황 파악" 같은 표현. 또한 project-bootstrapper나 project-kickstart가 실행될 때 도메인 날리지가 부족하다고 판단되면 이 스킬을 선행 호출할 수 있다. 단순 지식 질문("GDP가 뭐야?")에는 트리거하지 않는다 — 프로젝트/서비스 구축을 위한 체계적 리서치 의도가 있을 때만 작동. | 240 |
| P2 | `js-refactor-cleanup-skill` | js-refactor-cleanup-skill | Use when cleaning up, renaming, or refactoring JavaScript/TypeScript code. JavaScript-focused refactor and cleanup Skill with example JS files illustrating common refactor cases; the Skill's instructions reference these examples for guidance and tests. | 320 |
| P2 | `unused-code-refactor-suggester` | unused-code-refactor-suggester | Scans project source files to identify functions and classes that are not referenced elsewhere within the same file (file-scoped unused code). For each finding, generates a concise refactoring_report.md entry recommending deletion or preservation with a short reason and risk summary. Common triggers: "find unused in file", "identify dead code per-file", "generate refactoring report". | 294 |
| P2 | `ux-pattern-researcher` | ux-pattern-researcher | 도메인별 UI/UX 패턴, 유저 플로우, 전환율 가이드라인, UI 컴포넌트 맵을 웹 검색으로 수집하는 UX 리서치 스킬. 사용자가 "UX 리서치", "UI 패턴 조사", "화면 설계 전에 조사", "UX 가이드라인", "경쟁사 UI 분석", "전환율 최적화 조사", "도메인 UX", "/ux-research" 같은 표현을 쓰면 트리거한다. 또한 project-bootstrapper의 STAGE 4(와이어프레임) 실행 전에 자동 호출되어 도메인 특화 UX 날리지를 사전 구축할 수 있다. 단순 "예쁘게 만들어줘" 같은 비주얼 디자인 요청에는 트리거하지 않는다 — 정보 설계, 유저 플로우, 전환율 최적화 등 구조적 UX 리서치 의도가 있을 때만 작동. | 249 |

### orchestration

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P1 | `agent-architect` | agent-architect | Agent Architect (대화형) — 계층형 에이전트 조직 자동 구축. Codex-native skill migrated from Claude source. Use when the user asks for agent-architect, Agent Architect (대화형) — 계층형 에이전트 조직 자동 구축, or the matching workflow. | 230 |
| P1 | `agent-teams-code-review` | agent-teams-code-review | Parallel code review with 4 specialists (Security, Architecture, Performance, Testing). Use when asked to "review code", "code review", "review PR", "check code quality", "코드 리뷰", "리뷰해줘", or "PR 리뷰". Requires Codex subagents=1. | 740 |
| P1 | `agent-teams-deep-analysis` | agent-teams-deep-analysis | Deep codebase analysis with 3 parallel specialists (Structure, Patterns, Dependencies). Use when asked to "analyze codebase", "analyze architecture", "analyze project structure", "dependency analysis", "코드 분석", "아키텍처 분석", or "구조 분석". Requires Codex subagents=1. | 734 |
| P1 | `agent-teams-feature-dev` | agent-teams-feature-dev | Full-stack feature development with Pipeline+Parallel pattern (Design, Implement, Test, Review). Use when asked to "build feature", "implement feature", "develop new functionality", "기능 개발", "기능 구현", or "풀스택 개발". Requires Codex subagents=1. | 673 |
| P1 | `agent-teams-orchestrator` | agent-teams-orchestrator | Auto-select optimal team composition and orchestration pattern for complex tasks. Use when asked to "orchestrate", "organize team", "팀 구성", "오케스트레이션", or for complex multi-step tasks requiring multiple agents. Requires Codex subagents=1. | 911 |
| P1 | `agent-teams-reactive-dev` | agent-teams-reactive-dev | Reactive Observer-Worker: Playwright Observer가 상주하며 Worker 코드 변경을 즉시 검증하고, 설계 불일치 시 즉각 피드백하는 폐쇄 루프(Closed-Loop) 개발 스킬. Use when asked to "reactive dev", "reactive build", "build with live feedback", "실시간 검증 개발", "리액티브 개발", "Observer-Worker 개발", or when feature implementation requires continuous Playwright verification. Requires Codex subagents=1. | 672 |
| P1 | `continuous-qa-loop` | continuous-qa-loop | Continuous QA Loop: 이슈 발견 → 전문가 분석 → 코드 수정 → 재검증 자동 반복. N-Agent Hybrid: Lead(Playwright) + 동적 전문가(2~6명 병렬) + Fixer(직렬). 모드: --custom "항목" (경량) / Comprehensive (전체 Tier). 옵션: --dry-run, --resume, --max-iter N, --full, --all. Use when asked to "continuous QA", "반복 QA", "QA 루프", "자동 수정 반복", "이슈 자동 수정", or when iterative fix-and-verify workflow is needed. Requires Codex subagents=1. | 360 |
| P1 | `insight-sentinel` | insight-sentinel | 인사이트 감시 에이전트. 작업 중 발생한 인사이트가 제대로 기록되고 있는지 감시하고, 미기록 인사이트를 식별하여 사용자에게 기록을 제안한다. 트리거: "/insight-check", "인사이트 체크", "인사이트 확인", "인사이트 기록했어?", 또는 Stop 훅에서 자동 호출. | 98 |
| P1 | `pipeline-orchestrator` | pipeline-orchestrator | 프로젝트 파이프라인의 지능적 오케스트레이터. 4개 스킬(domain-researcher, ux-pattern-researcher, project-bootstrapper, project-kickstart)을 도메인에 맞게 분석/선택/실행/검증/연결하는 제어 계층. 트리거: "/orchestrate", "/파이프라인", "완벽하게 설계해줘", "제대로 된 프로젝트", "검증까지 포함해서", "빠짐없이 만들어줘", "최적화된 프로젝트", "프로 수준으로", "도메인에 맞게 설계". 또한 사용자가 프로젝트 구축을 요청하면서 품질/완전성/검증을 강조하는 표현을 쓸 때 트리거한다. 단순 "만들어줘"(→ kickstart)와 다르게, "제대로/완벽하게/검증해서/빠짐없이" 같은 품질 강조 키워드가 있을 때 이 스킬이 우선한다. | 240 |
| P1 | `project-bootstrapper` | project-bootstrapper | 웹사이트/앱 프로젝트의 전체 부트스트래핑을 자동화하는 스킬. 사용자가 "~~ 사이트 만들어줘", "~~ 앱 개발해줘", "~~ 플랫폼 구축" 같은 요청을 하면 7단계 파이프라인을 실행하여 에이전트 팀 구성부터 프로토타입 코드까지 전체 산출물을 파일로 제공한다. 반드시 이 스킬을 사용해야 하는 트리거: 사용자가 웹사이트, 앱, 쇼핑몰, 대시보드, SaaS, 플랫폼, 커뮤니티, 마켓플레이스, 서비스 등을 "만들고 싶다", "개발하고 싶다", "구축하고 싶다"고 말할 때. 단순 코드 스니펫이나 컴포넌트 하나를 요청하는 경우에는 트리거하지 않는다 — "프로젝트 전체"를 만드는 의도가 있을 때만 작동. 또한 사용자가 "프로젝트 부트스트래핑", "전체 설계", "풀스택 프로젝트", "MVP 만들어줘", "서비스 기획부터 개발까지" 같은 표현을 쓸 때도 반드시 트리거한다. | 235 |
| P1 | `project-kickstart` | project-kickstart | 프로젝트 부트스트래핑을 한 번에 자동 실행하는 원클릭 트리거 스킬. 사용자가 "/kickstart", "/bootstrap", "/프로젝트시작", "전체 프로젝트 한번에 만들어줘", "처음부터 끝까지 다 해줘", "풀 패키지로 줘", "한방에 다 만들어줘" 같은 표현을 쓰면 트리거한다. 이 스킬은 project-bootstrapper 스킬의 7단계 파이프라인을 확인 없이 자동으로 전부 실행하고, 최종 ZIP 하나로 모든 산출물을 한꺼번에 제공한다. 단순 질문이나 코드 수정 요청에는 트리거하지 않는다. 반드시 트리거해야 하는 상황: 사용자가 웹/앱 프로젝트의 전체 설계를 한 번에 원하는 경우, "에이전트부터 코드까지", "설계부터 개발까지", "기획부터 프로토타입까지" 같은 표현을 쓸 때. | 192 |

### reasoning

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P0 | `what` | what | 구조화된 사고 프레임워크. Why-What-How-So What 4단계로 근본 목적을 역추적·정립. Use when "what 분석", "what 정리", "what 파악", "목적 정리", "왜 하는 건지 정리", "의도 분석", "기획 의도", or user prefixes request with "what" in structured thinking context. NOT for: "what is X?" simple knowledge questions, "what does X do?" explanations. | 341 |
| P1 | `ce-advisor` | ce-advisor | This skill provides CE+PE hybrid prompt optimization with 3+1 suggestions. Use when asked to "optimize prompt", "ce advice", "improve my prompt", "제안해줘", "제안 해줘", "suggest", "advise", or at the start of complex tasks requiring context optimization. Based on CE v2.0 principles (Right Altitude, Token Position, 4 Failure Modes). | 350 |
| P1 | `cynefin` | cynefin | Cynefin Framework 기반 문제 분류 + 스킬 라우터. 문제를 Clear/Complicated/Complex/Chaotic/Confusion 5개 영역으로 분류하고, 각 영역에 맞는 전략과 스킬을 자동 라우팅한다. Use when "/cynefin", "문제 분류", "어떤 접근이 맞을까", "이거 복잡한 문제야?", "어떻게 접근해야 해", "분류해줘", or when facing an ambiguous problem. NOT for: simple knowledge questions, already-clear tasks, direct skill invocations. | 192 |
| P1 | `deep-analysis-mode` | deep-analysis-mode | Use when the user requests deep analysis for complex tasks such as bug fixing, feature implementation, refactoring, code review, optimization, troubleshooting, or debugging. NOT for: simple questions, explanations, single-file edits, plan mode, or internal operations. NOT for: domain research/analysis tasks (use domain-expert-analysis instead). Core features: Role-playing as domain experts, anti-hallucination protocol, 5-stage metacognitive prompts, and systematic 8-step workflow. | 382 |
| P1 | `first-principles` | first-principles | First Principles Thinking 기반 전제 해체 + 재구성 스킬. 기존 가정을 체계적으로 분해하여 기본 진실에 도달하고, 그 위에서 새롭게 재구성한다. Use when "/first-principles", "근본부터 다시 생각해", "왜 이렇게 하는 건지", "전제를 의심해봐", "기존 방식 말고", "처음부터 다시", "관행이 아닌 다른 방법", or when assumptions behind a decision need to be challenged. NOT for: simple tasks with clear solutions, emergency situations (use Cynefin Chaotic), initial purpose clarification (use /what). | 240 |
| P1 | `ooda` | ooda | OODA Loop 기반 적응적 실행 스킬. Observe-Orient-Decide-Act 순환으로 실행 중 환경 변화에 적응한다. Use when "/ooda", "적응적으로 진행해", "상황 변했어", "계획 수정 필요", "중간 점검", "방향 재설정", or during long tasks (5+ turns) as checkpoint. NOT for: simple one-shot tasks, initial planning (use /what), problem classification (use /cynefin). | 212 |
| P1 | `think-deep` | think-deep | 3단계 압축 사고 체인. 6개 스킬을 3 Stage로 융합하여 균형 잡힌 깊이와 효율 제공. Stage 1(분류+목적) → Stage 2(전제해체+최적화) → Stage 3(심층분석+적응실행). Use when "/think-deep", "깊이 분석해줘", "제대로 생각해보자", "심층적으로 접근", "중요한 설계니까 꼼꼼하게", or for important design decisions and architecture. NOT for: everyday tasks (use /think-lite), maximum depth (use /think-full). think- 패밀리 중 균형형. 토큰 25-35K. | 233 |
| P1 | `think-full` | think-full | 최대 깊이 사고 체인. 6개 스킬을 항상 전부 순서대로 실행. Cynefin → What → First Principles → CE Advisor → Deep Analysis → OODA. 각 Stage 사이 Handoff Object로 누적 전달. 어떤 문제든 6단계 전체를 돌림. Use when "/think-full", "전체 사고 체인", "최대 깊이로 분석", "완벽하게 생각해줘", "대형 프로젝트 설계", "전략적으로 접근", or for major architecture/strategy decisions. NOT for: everyday tasks (use /think-lite), standard design (use /think-deep). think- 패밀리 중 최대 깊이. 토큰 50K+. | 282 |
| P1 | `think-lite` | think-lite | 적응형 사고 체인. Cynefin이 문제를 분류한 후 영역별로 필요한 스킬만 선택 실행. Clear는 3단계, Complex는 6단계 — 문제 복잡도에 비례한 사고 깊이. Use when "/think-lite", "가볍게 분석", "스마트하게 접근", "빠르게 생각 정리", "이거 어떻게 접근하지", or for everyday coding/analysis tasks. NOT for: maximum depth analysis (use /think-full), important design decisions (use /think-deep). think- 패밀리 중 가장 일상적. 토큰 3-20K. | 245 |
| P1 | `think-teams` | think-teams | 전문가 팀 사고 체인. 질문의 도메인을 분석하여 3-6명의 전문가 Agent Teams를 동적 생성하고, 6단계 파이프라인을 병렬 분석 + 확인 루프와 함께 실행. think-full의 6단계 깊이 + Agent Teams 다관점 병렬 = 최대 품질. Requires Codex subagents=1 (미지원 시 순차 Fallback). | 854 |
| P1 | `what-ce` | what-ce | 2단계 파이프라인: What 목적 정립 → CE 프롬프트 최적화. Stage 1이 Why-What-How-So What 4단계로 진짜 목적을 정립하고, 그 결과가 자동으로 Stage 2 CE+PE 최적화의 입력이 된다. Use when "what-ce", "목적 정립 후 최적화", "what then ce", "what ce", "프롬프트 최적화 전에 목적부터", or when user wants to clarify purpose before optimizing execution. Fast mode: add "--fast" to compress Stage 1 confirmation. NOT for: "what is X?" knowledge questions, standalone CE advice (use ce-advisor), standalone purpose analysis (use what). | 501 |

### support

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P3 | `superpowers` | superpowers | Codex Superpowers 플러그인. Agent Teams, 커스텀 스킬, 훅, 커맨드를 제공하는 확장 패키지. This skill should be used when the plugin's sub-skills or commands are invoked via their respective triggers. | 458 |

### validation

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P1 | `infra-audit` | infra-audit | This skill should be used when the user asks to "audit infra", "infra audit", "인프라 감사", "인프라 검사", "check infrastructure", "health check", "infra health", "설정 검사", or "인프라 건강도". Codex 인프라(AGENTS.md, hooks, skills, rules, scripts, agents, MCP)의 종합 건강도를 점수(0-100) + 등급(S/A/B/C/F)으로 진단하고, 하니스 5축(CE/AC/GC/EL/SI) 기여도를 매핑한다. | 302 |
| P1 | `playwright-design-audit` | playwright-design-audit | Unified UI/UX + Design Quality audit with 19 Agent-Teams specialists, ~450 checklist items. Use when asked to "design audit", "디자인 감사", "통합 감사", "design quality check", "UI/UX + design audit", or "playwright-design-audit". UX Score (0-100, 18 dimensions). Modes: basic/--pro/--expert/--focus=<cat>. Requires Codex subagents=1. | 603 |
| P1 | `playwright-qa-agent-teams` | playwright-qa-agent-teams | This skill performs parallel QA testing with Agent Teams using Playwright MCP tools. Use when AGENT_TEAMS=1 and asked to "QA test with team", or routed from playwright-qa-expert. Hybrid Pattern: Lead collects data via Playwright, 4-8 Teammates analyze in parallel. Supports 3 tiers: basic (~35 items), --full (~120 items), --all (175 items). Fallback: single agent mode when agent-teams is disabled. Requires Codex subagents=1. | 956 |
| P1 | `playwright-qa-expert` | playwright-qa-expert | QA testing using Playwright MCP tools with multi-expert panel analysis. Use when asked to "test this page", "QA test", "check UI bugs", "test website", "run QA checks", "QA 테스트", "버그 확인", or "웹 테스트". Supports 3 tiers: basic (~30), --full (~80), --all (175 items). Routes to agent-teams when AGENT_TEAMS=1, to uiux-audit with --audit flag. | 527 |
| P1 | `playwright-uiux-audit` | playwright-uiux-audit | Comprehensive UI/UX audit with 18 Agent-Teams specialists, 360 checklist items. Use when asked to "audit UI/UX", "UX review", "accessibility check", "UI audit", "check design quality", "UX 감사", "UI 감사", "접근성 검사", or "디자인 검토". UX Score (0-100). Modes: basic/--pro/--expert/--focus=<cat>. Requires Codex subagents=1. | 381 |
| P1 | `security-audit` | security-audit | OWASP-based security audit with 3 parallel specialists (App, Infra, Dependencies). Use when asked to "security audit", "check vulnerabilities", "OWASP scan", "check security", "보안 감사", "취약점 검사", or "보안 검토". Modes: full/--scope/--deps-only/--quick. Agent-Teams with AGENT_TEAMS=1. | 483 |
| P1 | `web-design-guidelines` | web-design-guidelines | Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices". | 445 |
| P1 | `webapp-testing` | webapp-testing | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs. Use when asked to \"test my app\", \"check the page\", \"take a screenshot\", \"브라우저 테스트\", \"앱 테스트\", \"스크린샷\", or when verifying local web app behavior. | 607 |

### web-platform

| Priority | Directory | Skill name | Description | Lines |
|---|---|---|---|---:|
| P2 | `vercel-deploy` | vercel-deploy | Deploy applications and websites to Vercel. Use this skill when the user requests deployment actions such as "Deploy my app", "Deploy this to production", "Create a preview deployment", "Deploy and give me the link", or "Push this live". No authentication required - returns preview URL and claimable deployment link. | 510 |
| P2 | `vercel-react-best-practices` | vercel-react-best-practices | React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React components, Next.js pages, data fetching, bundle optimization, or performance improvements. | 483 |

## Maintenance

스킬은 개인 자산이므로 Git에는 본문 전체를 복사하지 않는다. 이 저장소에는 검색, 라우팅, stale 감지를 위한 인덱스만 둔다.
인덱스의 `sha256`은 로컬 활성 스킬과 문서가 맞는지 검증하기 위한 값이며 인증 정보나 세션 정보가 아니다.
