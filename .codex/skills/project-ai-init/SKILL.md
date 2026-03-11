---
name: project-ai-init
description: Initialize a single repository for AI-assisted development. Use when a repository is missing AGENTS.md, testing guidance, AI collaboration workflow docs, or task/report templates, and the goal is to create only the missing baseline artifacts.
---

# Project AI Init

Use this skill for one repository at a time.

## Workflow

1. Confirm the repository root and read minimal context.
- Read `package.json` or equivalent build files.
- Read top-level `README.md` and existing `AGENTS.md` if present.
- Detect project signals from real files instead of assumptions.

2. Run the initialization check.
- Execute `scripts/check_ai_init.sh <repo-root>`.
- Treat the script output as the source of truth for missing baseline artifacts.

3. Preview and create only missing docs.
- Execute `scripts/auto_init_docs.sh <repo-root> dry-run` first.
- Execute `scripts/auto_init_docs.sh <repo-root> apply` only after reviewing the preview.
- Never overwrite existing project docs by default.

4. Refine generated placeholders only where needed.
- Replace generic commands or workflow text with project-real commands, directories, and risks.
- Keep edits minimal and repository-specific.
- Ensure generated rules include:
  - Key-file changes must sync Markdown docs.
  - If no corresponding Markdown exists, create one first.
  - Run local `skills/md-doc-sync/SKILL.md` check before commit.

5. Re-check and summarize.
- Re-run `scripts/check_ai_init.sh <repo-root>`.
- Report which files were created, which were skipped, and what still needs manual refinement.

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

Conditional when the repository contains matching signals:
- `docs/BUSINESS_SCENARIO_MAP.md`
- `docs/ROUTES_AND_ACCESS.md`
- `docs/SOCKET_PROTOCOL_MAP.md`
- `docs/SDK_USAGE.md`

## Language

- Governance and collaboration Markdown should default to Chinese.
- Keep code symbols, commands, file paths, environment variables, API names, and Conventional Commit types in English.
- For single-repo commit guidance, prefer Chinese commit subjects and descriptions while keeping the Conventional Commit `type(scope)` prefix in English.
- Commit guidance should encourage detailed messages that explain change intent, affected scope, and key context instead of overly short summaries.
- If a repository already has a clearly external or English-first technical README, preserve that style for API-facing sections and keep governance additions in Chinese when practical.

## Rules

- Prefer minimal diff.
- Do not delete or rewrite existing docs unless explicitly requested.
- Focus on baseline AI collaboration setup, not audit scoring or multi-repo governance.
- If the repository already looks initialized but low quality, hand off to `$project-ai-audit` instead of forcing more initialization.

## Resources

- `scripts/check_ai_init.sh`
- `scripts/auto_init_docs.sh`
- `references/doc-baseline.md`
