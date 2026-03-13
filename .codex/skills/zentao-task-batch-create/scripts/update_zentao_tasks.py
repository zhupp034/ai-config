#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

from create_zentao_tasks import (
    DEFAULT_BASE_URL,
    ZenTaoClient,
    apply_workday_shift,
    format_number,
    parse_work_items,
    schedule_items,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update existing ZenTao tasks from a work-item list.")
    parser.add_argument("--project-id", type=int, required=True, help="ZenTao iteration/project ID")
    parser.add_argument("--parent-task-id", type=int, help="Parent task ID if the tasks are child tasks")
    parser.add_argument("--task-ids", required=True, help="Comma-separated task IDs in the same order as the input lines")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--assigned-to", help="ZenTao account to assign tasks to")
    parser.add_argument("--hours-per-day", type=float, default=8.0, help="Scheduling capacity per day")
    parser.add_argument(
        "--shift-workdays",
        type=int,
        default=0,
        help="Shift both start and deadline forward by this many working days, skipping weekends",
    )
    parser.add_argument("--type", default="devel", help="ZenTao task type, default: devel")
    parser.add_argument("--pri", type=int, default=3, help="ZenTao task priority, default: 3")
    parser.add_argument("--comment", default="按最新工时版本更新预计并重新排期", help="Edit comment to write into ZenTao")
    parser.add_argument("--base-url", default=os.environ.get("ZENTAO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--input-file", help="Read work items from this file instead of stdin")
    parser.add_argument(
        "--include-weekends",
        action="store_true",
        help="Schedule on calendar days instead of working days",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print update plan without submitting")
    return parser.parse_args()


def load_input(path: str | None) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def main() -> int:
    args = parse_args()
    task_ids = [int(part.strip()) for part in args.task_ids.split(",") if part.strip()]
    start_date = dt.date.fromisoformat(args.start_date)
    raw_text = load_input(args.input_file)
    work_items = parse_work_items(raw_text)
    if len(task_ids) != len(work_items):
        raise SystemExit(f"task_ids count {len(task_ids)} does not match work item count {len(work_items)}")

    scheduled_items = schedule_items(
        work_items,
        start_date,
        args.hours_per_day,
        include_weekends=args.include_weekends,
    )
    scheduled_items = apply_workday_shift(scheduled_items, args.shift_workdays)

    for task_id, item in zip(task_ids, scheduled_items):
        print(
            "\t".join(
                [
                    str(task_id),
                    item.title,
                    format_number(item.estimate),
                    item.start.isoformat(),
                    item.deadline.isoformat(),
                ]
            )
        )

    if args.dry_run:
        return 0

    account = os.environ.get("ZENTAO_ACCOUNT")
    password = os.environ.get("ZENTAO_PASSWORD")
    if not account or not password:
        raise SystemExit("ZENTAO_ACCOUNT and ZENTAO_PASSWORD must be set")

    assigned_to = args.assigned_to or account
    client = ZenTaoClient(args.base_url, account, password)
    client.login()

    for task_id, item in zip(task_ids, scheduled_items):
        client.update_task(
            task_id=task_id,
            parent_task_id=args.parent_task_id,
            assigned_to=assigned_to,
            task_type=args.type,
            pri=args.pri,
            item=item,
            comment=args.comment,
        )
        print(f"UPDATED\t{task_id}\t{item.title}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
