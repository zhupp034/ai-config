---
name: weekly-report-summary
description: Generate a weekly report draft by first running the git-weekly-summary workflow to refresh the current week's markdown in `/Users/zpp/Desktop/workspace/git-weekly-report`, then reading the generated markdown files and condensing them into a structured weekly-report draft. Use when the user asks for a weekly report draft, a weekly summary source, or wants to summarize the git-weekly-report markdown files before polishing.
---

# Weekly Report Summary

## Overview

Use `scripts/generate_weekly_report_summary.py` to first refresh this week's ZenTao note when credentials are available, then refresh this week's source JSON/markdown and build a structured weekly report draft written into `/Users/zpp/Desktop/workspace/weekly-report`.
If there is a matching notes file under `/Users/zpp/Desktop/workspace/weekly-report-notes`, merge it into an `其他工作` section.

## Standard Flow

1. Use `$weekly-report-summary` to generate the weekly Markdown draft.
2. Prefer consuming the upstream `git-weekly-summary` JSON `themes` layer.
   When `themes.analysis` exists, the weekly report should use it before falling back to raw commit summarization.
3. Review the draft for missing scope or obviously wrong grouping.
4. When the user wants a cleaner final version, pass the draft to `$report-polisher` in `weekly_frontend` mode.
5. Treat these as two separate stages: draft generation first, semantic polishing second.

## Workflow

1. Run `python3 scripts/generate_weekly_report_summary.py`.
2. Let the script invoke the ZenTao refresh step first; pass `--zentao-account` / `--zentao-password` explicitly, provide `ZENTAO_ACCOUNT` / `ZENTAO_PASSWORD` in the environment, or store them in `~/.codex/secrets/common.env`.
3. Let the script invoke the existing `git-weekly-summary` generator with `--write-report --write-json-report` before doing any summarization.
4. Build the weekly report from upstream repo `themes`; if `themes.analysis` exists, use `completed_sections` / `project_summary` / `risks` / `next_steps` / `reflections` first.
5. Review the resulting weekly report draft on stdout.
6. When the user wants smoother wording, pass the draft to `$report-polisher` in `weekly_frontend` mode for semantic polishing.
7. If needed, use `--write-output` to also save the draft into a markdown file.
8. If the upstream refresh steps fail on network restrictions, rerun with the required permission so the refresh can finish.

## Defaults

- Git root: `/Users/zpp/Desktop/gitlab`
- Source markdown directory: `/Users/zpp/Desktop/workspace/git-weekly-report`
- Final weekly report directory: `/Users/zpp/Desktop/workspace/weekly-report`
- Extra notes directory: `/Users/zpp/Desktop/workspace/weekly-report-notes`
- 这些默认目录可通过 `DESKTOP_ROOT`、`WORKSPACE_ROOT`、`GITLAB_ROOT`、`GIT_WEEKLY_REPORT_DIR`、`WEEKLY_REPORT_OUTPUT_DIR`、`WEEKLY_REPORT_NOTES_DIR` 等环境变量覆写
- Current week window: Monday 00:00 to now
- Author filter: `--mine`

## Quick Start

```bash
python3 scripts/generate_weekly_report_summary.py --zentao-account "$ZENTAO_ACCOUNT" --zentao-password "$ZENTAO_PASSWORD"
```

Write the final report to the dedicated weekly report folder as well:

```bash
python3 scripts/generate_weekly_report_summary.py --write-output --zentao-account "$ZENTAO_ACCOUNT" --zentao-password "$ZENTAO_PASSWORD"
```

Then polish the saved draft with `$report-polisher` when needed.

## Hand-off Prompt

Use this prompt when passing the generated draft to `$report-polisher`:

```text
Use $report-polisher in weekly_frontend mode to polish this weekly report draft.
Keep the Markdown structure unchanged.
Preserve all supported facts, project names, versions, and technical identifiers.
Rewrite it into natural Chinese that reads like it was written by an experienced frontend developer.
```

## Output Shape

- `# 本周周报`
- `统计周期`
- `## 一、本周完成`
- `### 需求开发`
- `### 问题修复`
- `### 技术优化`
- `## 二、项目维度汇总`
- `## 三、问题与风险`
- `## 四、心得体会`
- `## 五、下周计划`

## Resources

- `scripts/generate_weekly_report_summary.py`: Refresh this week's `git-weekly-report` data via the existing git summary workflow, then prefer upstream `themes` / `themes.analysis` to rewrite it into a cleaner weekly report format under `weekly-report`.
- `/Users/zpp/.codex/skills/report-polisher/SKILL.md`: Dedicated AI polishing skill used after the weekly draft is assembled.
- `/Users/zpp/.codex/memories/report-polish-rules.md`: Shared semantic report polishing rules for AI rewriting.
