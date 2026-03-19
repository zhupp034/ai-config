---
name: git-weekly-summary
description: Summarize git commits across one or more local repositories for a weekly report. Use when Codex needs to scan a directory that contains multiple projects, collect this week's commit history, and produce a concise human-readable summary with repo-level highlights, commit themes, and notable changes.
---

# Git Weekly Summary

## Overview

Scan the current directory for git repositories, collect commits for a target week, and emit a structured weekly dataset for downstream consumers. Use the bundled script to gather deterministic commit data before writing the final summary or saving it into a weekly markdown file. When the root directory is `gitlab`, the script also scans the sibling `github` directory automatically if it exists.

## Workflow

1. Confirm the reporting window.
   Default to the current week from Monday 00:00 to now unless the user gives a different range.
2. Confirm the author scope.
   When the user asks for "my commits", run with `--mine` so the script resolves the current global git `user.name` and `user.email`.
3. Run `scripts/collect_weekly_commits.py` against the parent directory that contains the repos.
3. Prefer the generated JSON as the source of truth for downstream weekly-report generation.
   The JSON now carries:
   - stable top-level metadata: `report_type`, `schema_version`, `analysis_mode`
   - raw commit records
   - per-commit file and diff content
   - repo-level `themes` for downstream grouping
   - `themes.analysis` as the weekly-report consumer layer
   - optional per-commit AI analysis results when `--analysis-mode ai` is enabled
4. When the user wants a saved report, run with `--write-report`.
   The script writes to `/Users/zpp/Desktop/workspace/git-weekly-report/<generated-date>.md` by default, using the report generation date as the filename and overwriting that day's file on repeated runs. When the output directory is a git repo with a configured remote, it also auto-commits and pushes the updated report.
   The default path can be overridden by `WORKSPACE_ROOT`, `DESKTOP_ROOT`, or an explicit `--report-dir`.
5. For human-readable output, prefer file-content-aware summaries over raw commit subject restatement.
6. When AI analysis is available, keep the output detailed and preserve commit/theme structure for downstream consumers instead of over-compressing it.
7. Before generating the final wording, read the shared glossary at `/Users/zpp/.codex/memories/term-glossary.json` first, then fall back to `term-glossary.json` in the skill root for skill-specific terms.

## Quick Start

Run from the directory that contains multiple project folders:

```bash
python3 scripts/collect_weekly_commits.py --root /path/to/projects --mine
```

Use explicit dates when the user asks for "last week" or a custom period:

```bash
python3 scripts/collect_weekly_commits.py \
  --root /path/to/projects \
  --since 2026-03-02 \
  --until 2026-03-08 \
  --format markdown
```

Use `--json` output only when another script needs to post-process the commit data.
Use `--analysis-mode rule` as the default stable workflow when the current environment does not provide OpenAI credentials.
Use `--analysis-mode ai` when OpenAI credentials are configured and the downstream consumer needs file-content-aware AI analysis.
Use `--include-inactive` when the report must list repositories with no commits.
Use `--include-merges` only when merge commits themselves are meaningful to the report.
Use `--current-branch-only` only when the user explicitly wants to ignore commits from other branches.
Use `--write-report` to write the generated summary into a markdown file.
Use `--report-dir /custom/path` when the weekly files should be stored somewhere other than `/Users/zpp/Desktop/workspace/git-weekly-report`.
Use `--extra-root /another/path` when an extra directory outside the default sibling scan should also be included.
Use environment variables such as `DESKTOP_ROOT`, `WORKSPACE_ROOT`, and `CODEX_SHARED_GLOSSARY` when the script runs outside the default local directory layout.

Example:

```bash
python3 scripts/collect_weekly_commits.py \
  --root /path/to/projects \
  --mine \
  --write-report
```

## Reporting Guidance

- Group the final summary by repository when there are multiple active repos.
- Prefer the JSON `themes` layer for downstream report generation instead of rebuilding topics from raw commits again.
- Prefer `themes.analysis` over `themes.summaries` when the downstream consumer needs weekly-report-ready sections.
- Merge similar commits into themes such as dependency updates, bug fixes, feature delivery, build changes, or code cleanup.
- Prefer impact-oriented phrasing over raw git subjects.
- Mention the absence of activity when that matters to the user's report.
- Do not invent intent that is not supported by commit messages, touched files, diff content, or branch names.

## Repository Discovery Rules

- Include the root directory itself if it is a git repo.
- Include direct child directories that contain a `.git` directory.
- Skip common non-project folders such as `node_modules`, `.git`, and hidden directories unless the user explicitly asks for recursive scanning.
- If nested repos deeper than one level are relevant, rerun the script with `--recursive`.

## Resources

- `scripts/collect_weekly_commits.py`: Gather weekly commit history from multiple local repos, emit raw or summarized output, and optionally write the weekly markdown file.
- `references/structured-report-schema.md`: Formal JSON schema notes for the report that downstream weekly-report generation consumes.
- `/Users/zpp/.codex/memories/term-glossary.json`: Shared terminology dictionary for reusable project and module explanations across skills.
- `term-glossary.json`: Skill-local fallback terminology dictionary for overrides or skill-specific additions.
- `references/report-template.md`: Suggested structure for the final weekly summary.
