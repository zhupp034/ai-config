# Doc Baseline

Use this baseline when bootstrapping AI project docs.

## Core
- AGENTS.md
- README.md docs navigation section

## Recommended
- TESTING.md
- docs/AI_COLLAB_WORKFLOW.md
- docs/TASK_RECORD_TEMPLATE.md
- docs/TEST_CASE_MATRIX.md
- docs/DELIVERY_REPORT_TEMPLATE.md
- docs/GIT_COMMIT_GUIDE.md
- docs/LINT_AND_BUILD_KNOWN_ISSUES.md
- skills/md-doc-sync/SKILL.md

## Conditional
- docs/BUSINESS_SCENARIO_MAP.md
- docs/ROUTES_AND_ACCESS.md
- docs/SOCKET_PROTOCOL_MAP.md
- docs/SDK_USAGE.md

## Language
- Governance docs default to Chinese.
- Commands, code, paths, environment variables, and Conventional Commit types stay in English.
- Single-repo commit guidance should prefer Chinese subjects and descriptions, while keeping the Conventional Commit `type(scope)` prefix in English.
- Commit message examples and templates should prefer detailed wording over short generic summaries.
- External-facing API content may keep existing English style.

## Generation Principles
- Generate only missing files.
- Keep existing content unless user asks to refactor.
- Use real project facts: stack, route map, role model, test commands.
- Prefer auditability: the repository should show plan, review, testing, retest, and delivery evidence.
- Prefer docs that help explain meaningful git output, not just AI usage.
- Enforce markdown sync: when key files change, update docs; if no docs exist, create new markdown first.
