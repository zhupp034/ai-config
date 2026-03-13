---
name: project-ai-init
description: Initialize a single repository for AI-assisted development with a reusable, project-agnostic documentation baseline. Use when a repository is missing AGENTS.md, testing guidance, collaboration workflow docs, or delivery templates, and the goal is to create only missing artifacts.
---

# Project AI Init

Use this skill for one repository at a time.

## When To Use

- The repository is missing baseline collaboration docs and needs a lightweight bootstrap.
- The goal is to add missing files only, not to rewrite an already-initialized repository.
- The repository may use any stack. Detect real signals first instead of assuming frontend, Node.js, or a specific business domain.

If the repository already has the documents but their quality is weak, hand off to `$project-ai-audit` instead of forcing another initialization pass.

## Workflow

1. Read minimal repo context.
- Open top-level `README.md`, existing `AGENTS.md`, and the primary build file (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle*`, etc.).
- Detect stack, test entrypoints, documentation layout, and domain signals from actual files.

2. Run the baseline check.
- Execute `scripts/check_ai_init.sh <repo-root>`.
- Treat the script output as the source of truth for which artifacts are missing or still incomplete.

3. Preview before writing.
- Execute `scripts/auto_init_docs.sh <repo-root> dry-run`.
- Review the proposed files and README navigation change.

4. Create only missing docs.
- Execute `scripts/auto_init_docs.sh <repo-root> apply`.
- Never overwrite existing docs by default.

5. Refine generated placeholders.
- Replace placeholders with real commands, directories, module names, and risks from the repository.
- Keep the wording project-agnostic unless the repository itself uses domain-specific language.
- Preserve the repository's dominant documentation language when it is obvious; otherwise default governance docs to Chinese.

6. Re-check and summarize.
- Re-run `scripts/check_ai_init.sh <repo-root>`.
- Report which files were created, which were skipped, and which placeholders still need manual follow-up.

## Artifacts

Core:
- `AGENTS.md`
- `README.md` docs navigation section

Recommended:
- `TESTING.md`
- `docs/AI_COLLAB_WORKFLOW.md`
- `docs/TASK_RECORD_TEMPLATE.md`
- `docs/TEST_CASE_MATRIX.md`
- `docs/DELIVERY_REPORT_TEMPLATE.md`
- `docs/GIT_COMMIT_GUIDE.md`
- `docs/LINT_AND_BUILD_KNOWN_ISSUES.md`
- `skills/md-doc-sync/SKILL.md`

Conditional when matching signals are detected:
- `docs/DOMAIN_CONTEXT.md`
- `docs/ROUTES_AND_ACCESS.md`
- `docs/EVENT_AND_MESSAGE_FLOW.md`
- `docs/INTEGRATION_DEPENDENCIES.md`

Legacy compatibility accepted during checks:
- `docs/BUSINESS_SCENARIO_MAP.md`
- `docs/SOCKET_PROTOCOL_MAP.md`
- `docs/SDK_USAGE.md`

## Rules

- Prefer minimal diff.
- Do not delete or rewrite existing docs unless explicitly requested.
- Focus on baseline AI collaboration setup, not audit scoring or organization-wide governance.
- Generated commit guidance must follow the active repository rules. If no project rule exists, still prefer Chinese-first summary/body even for English-first repositories, while keeping the Conventional Commits `type(scope)` prefix in English. The generated guidance should require a body after the summary and explain change object, intent, impact, risks, and validation.
- Generated testing guidance must use discovered commands when available and clearly mark placeholders when not.
- Generated workflow docs must keep the Markdown sync rule: key file changes require Markdown updates, and missing docs should be created before commit.

## Resources

- `scripts/check_ai_init.sh`
- `scripts/auto_init_docs.sh`
- `references/doc-baseline.md`
