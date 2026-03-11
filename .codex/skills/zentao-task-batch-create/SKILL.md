---
name: zentao-task-batch-create
description: Log in to the local ZenTao web app with account/password, optionally open a specific target page, and create ZenTao tasks from a pasted work-item list. Use when the user wants to log into ZenTao or bulk-create tasks in a specific iteration, optionally under a parent task if a parent task ID is provided.
---

# ZenTao Task Batch Create

Use this skill when the user wants Codex to:

- log into the local ZenTao site with account/password
- open a specific ZenTao page after login
- create ZenTao tasks from a text list such as `任务名 工时` or `任务名<TAB>工时`

## Login Only

Run `python3 scripts/login_zentao.py` when the user only needs a verified ZenTao login or wants to confirm that a target page is reachable after authentication.

Common arguments:

- optional `--base-url`
- optional `--target-path` such as `task-batchCreate-1205-0-0-138596-0.html`
- optional `--target-url` such as `http://192.168.20.9/pro/task-view-138596.html`

The script prints:

- `session_name`
- `session_id`
- `login_url`
- `target_url` if one was requested

## Required Inputs

Ask for these values before running:

- Iteration ID (`project_id`)
- Start date (`YYYY-MM-DD`)
- Whether the tasks should be created under a parent task

If the user provides a parent task ID, create child tasks under that parent task. If no parent task ID is provided, create normal tasks directly in the iteration.

## Workflow

1. Set environment variables:
   - `ZENTAO_BASE_URL`
   - `ZENTAO_ACCOUNT`
   - `ZENTAO_PASSWORD`
2. If needed, verify login and target page access first with `python3 scripts/login_zentao.py`.
3. Put the work items into a text file or pass them on stdin. Each non-empty line should end with the estimate hours.
4. Run `python3 scripts/create_zentao_tasks.py` with:
   - `--project-id`
   - `--start-date`
   - optional `--parent-task-id`
   - optional `--assigned-to`
   - optional `--hours-per-day` (default `8`)
   - optional `--shift-workdays` (default `0`, shift both start and deadline forward by working days and skip weekends)
   - optional `--type` (default `devel`)
   - optional `--pri` (default `3`)
   - optional `--dry-run`
5. Review the printed schedule and creation results.

## Accepted Input Format

Examples:

```text
资源库新增学科网tab-校本资源库 1
点击自动打开选择资源的弹窗 2
弹窗内点击上传课件、微课、备课包打开响应弹窗	4
```

The parser treats the trailing number as estimate hours and the leading text as the task title.

## Defaults

- Default base URL: `http://192.168.20.9/pro/`
- Default assignee: same as `ZENTAO_ACCOUNT` unless `--assigned-to` is provided
- Default task type: `devel`
- Default priority: `3`
- Default hours per day: `8`
- Default workday shift: `0`

## Quick Start

```bash
export ZENTAO_BASE_URL="http://192.168.20.9/pro/"
export ZENTAO_ACCOUNT="zhupengpeng"
export ZENTAO_PASSWORD="your-password"

python3 scripts/login_zentao.py \
  --target-path task-batchCreate-1205-0-0-138596-0.html

python3 scripts/create_zentao_tasks.py \
  --project-id 1205 \
  --parent-task-id 138596 \
  --start-date 2026-03-12 \
  --shift-workdays 1 \
  --assigned-to zhupengpeng \
  <<'EOF'
资源库新增学科网tab-校本资源库 1
点击自动打开选择资源的弹窗 2
EOF
```

## Resources

- `scripts/login_zentao.py`: Log in to ZenTao with account/password and optionally open a target page.
- `scripts/create_zentao_tasks.py`: Log in to ZenTao, compute task dates from the input list, and create either normal iteration tasks or child tasks under a parent task.
