# Doc Baseline

Use this baseline when bootstrapping AI collaboration docs for a single repository.

## Core

- `AGENTS.md`
- `README.md` docs navigation section

## Recommended

- `TESTING.md`
- `docs/AI_COLLAB_WORKFLOW.md`
- `docs/TASK_RECORD_TEMPLATE.md`
- `docs/TEST_CASE_MATRIX.md`
- `docs/DELIVERY_REPORT_TEMPLATE.md`
- `docs/GIT_COMMIT_GUIDE.md`
- `docs/LINT_AND_BUILD_KNOWN_ISSUES.md`
- `skills/md-doc-sync/SKILL.md`

## Conditional

- `docs/DOMAIN_CONTEXT.md`
- `docs/ROUTES_AND_ACCESS.md`
- `docs/EVENT_AND_MESSAGE_FLOW.md`
- `docs/INTEGRATION_DEPENDENCIES.md`

Legacy equivalents accepted by the checker:
- `docs/BUSINESS_SCENARIO_MAP.md`
- `docs/SOCKET_PROTOCOL_MAP.md`
- `docs/SDK_USAGE.md`

## Language

- Preserve the repository's existing dominant documentation language when it is obvious.
- If the repository has no strong language signal, governance docs default to Chinese.
- Commands, code, file paths, environment variables, API names, and Conventional Commit `type(scope)` stay in English.
- Commit guidance should follow repository rules first. Without a stronger local rule, still prefer Chinese-first summary/body even in English-first repositories, while keeping the Conventional Commits `type(scope)` prefix in English. Guidance should require a body after the summary and clearly cover changed object, intent, impact, risks, and validation.

## Generation Principles

- Generate only missing files.
- Keep existing content unless the user explicitly asks to refactor it.
- Use real repository facts: stack, commands, directories, domain terms, and known risks.
- Prefer auditability: the repository should preserve plan, review, testing, retest, and delivery evidence.
- Prefer neutral templates that can be refined for frontend, backend, SDK, CLI, library, or mixed repositories.
- Enforce Markdown sync: when key files change, update docs; if no matching docs exist, create Markdown first.
