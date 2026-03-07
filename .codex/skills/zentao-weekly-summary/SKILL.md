---
name: zentao-weekly-summary
description: Log in to the local ZenTao instance, collect this week's personal activity from the dynamic timeline, and write a weekly markdown note that can be merged into the final weekly report. Use when the user wants ZenTao tasks, bugs, stories, todos, or effort logs included in the weekly report.
---

# ZenTao Weekly Summary

## Overview

Use `scripts/fetch_zentao_weekly.py` to log in to ZenTao, collect this week's personal activity, summarize the notable work items, and write them into the weekly notes directory for later merging.

## Workflow

1. Set environment variables before running:
   - `ZENTAO_BASE_URL`
   - `ZENTAO_ACCOUNT`
   - `ZENTAO_PASSWORD`
2. Run `python3 scripts/fetch_zentao_weekly.py`.
3. Let the script log in through the verified web login endpoint, then fetch `my-dynamic`.
4. Review the generated note under `/Users/zpp/Desktop/workspace/weekly-report-notes/`.
5. Run `$weekly-report-summary` after this if the ZenTao content should be merged into the final weekly report.

## Defaults

- Default base URL: `http://192.168.20.9/pro/`
- Notes directory: `/Users/zpp/Desktop/workspace/weekly-report-notes`
- Week window: Monday 00:00 to now

## Quick Start

```bash
export ZENTAO_BASE_URL="http://192.168.20.9/pro/"
export ZENTAO_ACCOUNT="your-account"
export ZENTAO_PASSWORD="your-password"
python3 scripts/fetch_zentao_weekly.py
```

## Output

The script writes a weekly note file named like:

`/Users/zpp/Desktop/workspace/weekly-report-notes/2026-03-02-zentao.md`

## Resources

- `scripts/fetch_zentao_weekly.py`: Log in to ZenTao, fetch this week's dynamic activity, and write a markdown note for weekly report merging.
