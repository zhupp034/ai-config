---
name: monthly-performance-from-git
description: Use when the user wants to summarize monthly personal git work into a performance draft, aligned to Notion scoring pages they provide, and directly create or update the monthly page under a parent page they provide.
---

# Monthly Performance from Git

## Overview

Generate a monthly绩效草稿 from personal git commits, align it to the Notion `打分标准` and `示例` pages provided for the current run, then directly create or update the same-month page under the provided parent page.

Default behavior:
- Read the scoring standard and sample from Notion.
- Generate `简洁版`、`稳妥打分版`、`积极打分版`.
- Update the existing same-month page if it already exists.
- Otherwise create a new child page under the provided parent page.

## When to Use

- User asks for 月报绩效、绩效举证、git 月度总结、按打分标准整理 git 工作内容
- User wants the output written back to Notion directly
- User wants the same month to reuse the same Notion page instead of creating duplicates

Do not use this skill for weekly reports or for free-form prose summaries that do not need the Notion scoring structure.

## Inputs

- Git root: default `/Users/zpp/Desktop`
- Author scope: default current global git identity (`--mine`)
- Time range:
  - default current month
  - support `--month YYYY-MM` when user specifies a different month
  - support `--since YYYY-MM-DD[ HH:mm:ss] --until YYYY-MM-DD[ HH:mm:ss]` when the user wants a custom date range
- Notion parent page: required at runtime
- Notion standard page: optional but recommended at runtime
- Notion sample page: optional but recommended at runtime

## Workflow

1. Read shared terminology from `/Users/zpp/.codex/memories/term-glossary.json`.
2. Fetch the fixed Notion `打分标准` and `示例` pages for wording alignment.
3. Run:

```bash
python3 /Users/zpp/.codex/skills/monthly-performance-from-git/scripts/generate_monthly_performance_from_git.py --root /Users/zpp/Desktop --mine --format json
```

Required runtime flags:

```bash
--parent-page-id <page-id>
```

Optional runtime flags:

```bash
--standard-page-url <notion-url>
--sample-page-url <notion-url>
--month YYYY-MM
--since YYYY-MM-DD[ HH:mm:ss]
--until YYYY-MM-DD[ HH:mm:ss]
```

If `--since` and `--until` are both provided, they take precedence over `--month`.

4. Parse the JSON output:
   - `title`
   - `content`
   - `parent_page_id`
5. Fetch the provided parent page and inspect its child pages.
6. If a child page title exactly matches `title`, update that page with `replace_content`.
7. If no matching child page exists, create a new page under `parent_page_id`.
8. Return the Notion page URL to the user.

## Update Rule

- Same month: always update the existing page with the same title.
- Different month: create a new page.
- Do not create duplicate pages for the same month under the same parent page.

## Noise Filtering

The bundled script already filters common noise:
- `codex-config`
- `git-weekly-report`
- `chore: sync codex config`
- weekly-report artifact commits
- dist-only commits

The goal is to keep business delivery, problem fixing, testing, engineering baseline work, and cross-project support, while suppressing report artifacts and config sync noise.

## Output Shape

The generated page contains:
- `简洁版`
- `稳妥打分版`
- `积极打分版`
- `备注`

It is git-evidence-first: do not invent non-git contributions. If the user wants training, on-call,联调, or offline support added, append them explicitly after generation.
