#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable


DEFAULT_BASE_URL = "http://192.168.20.9/pro/"
SUCCESS_MARKER = "保存成功"
HOUR_PATTERN = re.compile(r"^(?P<title>.+?)(?:\t+|\s+)(?P<hours>\d+(?:\.\d+)?)$")


@dataclass
class WorkItem:
    title: str
    estimate: float


@dataclass
class ScheduledItem:
    title: str
    estimate: float
    start: dt.date
    deadline: dt.date


class ZenTaoClient:
    def __init__(self, base_url: str, account: str, password: str) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.account = account
        self.password = password
        self.session_id: str | None = None
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    def _open(self, url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> str:
        request = urllib.request.Request(url, data=data, headers=headers or {})
        with self.opener.open(request) as response:
            return response.read().decode("utf-8", errors="replace")

    def login(self) -> None:
        session_response = self._open(urllib.parse.urljoin(self.base_url, "api-getsessionid.json"))
        payload = json.loads(session_response)
        session_data = json.loads(payload["data"])
        self.session_id = session_data["sessionID"]

        login_url = urllib.parse.urljoin(
            self.base_url,
            f"user-login.json?zentaosid={urllib.parse.quote(self.session_id)}",
        )
        form = urllib.parse.urlencode(
            {
                "account": self.account,
                "password": self.password,
                "keepLogin": "0",
                "referer": "",
            }
        ).encode("utf-8")
        login_response = self._open(
            login_url,
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        payload = json.loads(login_response)
        if payload.get("status") != "success":
            raise RuntimeError(f"ZenTao login failed: {payload}")

    def create_task(
        self,
        *,
        project_id: int,
        parent_task_id: int | None,
        assigned_to: str,
        task_type: str,
        pri: int,
        item: ScheduledItem,
    ) -> None:
        if not self.session_id:
            raise RuntimeError("Not logged in")

        if parent_task_id is not None:
            url = urllib.parse.urljoin(
                self.base_url,
                f"task-batchCreate-{project_id}-0-0-{parent_task_id}-0.html?zentaosid={urllib.parse.quote(self.session_id)}",
            )
            form = {
                "module[0]": "0",
                "parent[0]": str(parent_task_id),
                "story[0]": "",
                "name[0]": item.title,
                "type[0]": task_type,
                "assignedTo[0]": assigned_to,
                "estimate[0]": format_number(item.estimate),
                "estStarted[0]": item.start.isoformat(),
                "deadline[0]": item.deadline.isoformat(),
                "desc[0]": "",
                "pri[0]": str(pri),
            }
        else:
            url = urllib.parse.urljoin(
                self.base_url,
                f"task-create-{project_id}--0.html?zentaosid={urllib.parse.quote(self.session_id)}",
            )
            form = {
                "project": str(project_id),
                "module": "0",
                "story": "",
                "name": item.title,
                "type": task_type,
                "assignedTo[]": assigned_to,
                "estimate": format_number(item.estimate),
                "estStarted": item.start.isoformat(),
                "deadline": item.deadline.isoformat(),
                "desc": "",
                "pri": str(pri),
            }

        encoded = urllib.parse.urlencode(form, doseq=True).encode("utf-8")
        response = self._open(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if SUCCESS_MARKER not in response:
            raise RuntimeError(f"ZenTao create failed for '{item.title}': {response[:400]}")

    def update_task(
        self,
        *,
        task_id: int,
        parent_task_id: int | None,
        assigned_to: str,
        task_type: str,
        pri: int,
        item: ScheduledItem,
        comment: str,
    ) -> None:
        if not self.session_id:
            raise RuntimeError("Not logged in")

        url = urllib.parse.urljoin(
            self.base_url,
            f"task-edit-{task_id}.html?zentaosid={urllib.parse.quote(self.session_id)}",
        )
        form = {
            "module": "0",
            "story": "",
            "parent": "" if parent_task_id is None else str(parent_task_id),
            "assignedTo": assigned_to,
            "type": task_type,
            "status": "wait",
            "pri": str(pri),
            "name": item.title,
            "desc": "",
            "comment": comment,
            "estStarted": item.start.isoformat(),
            "deadline": item.deadline.isoformat(),
            "estimate": format_number(item.estimate),
            "left": format_number(item.estimate),
            "consumed": "0",
            "lastEditedDate": "",
        }
        encoded = urllib.parse.urlencode(form, doseq=True).encode("utf-8")
        response = self._open(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if f"task-view-{task_id}.html" not in response:
            raise RuntimeError(f"ZenTao update failed for #{task_id} '{item.title}': {response[:400]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create ZenTao tasks from a work-item list.")
    parser.add_argument("--project-id", type=int, required=True, help="ZenTao iteration/project ID")
    parser.add_argument("--parent-task-id", type=int, help="Create child tasks under this parent task")
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
    parser.add_argument("--base-url", default=os.environ.get("ZENTAO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--input-file", help="Read work items from this file instead of stdin")
    parser.add_argument(
        "--include-weekends",
        action="store_true",
        help="Schedule on calendar days instead of working days",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print schedule without creating tasks")
    return parser.parse_args()


def load_input(path: str | None) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def parse_work_items(raw_text: str) -> list[WorkItem]:
    items: list[WorkItem] = []
    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = HOUR_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number} must end with estimate hours: {raw_line!r}")
        title = match.group("title").strip()
        estimate = float(match.group("hours"))
        if estimate <= 0:
            raise ValueError(f"Line {line_number} estimate must be positive: {raw_line!r}")
        items.append(WorkItem(title=title, estimate=estimate))
    if not items:
        raise ValueError("No work items found in input")
    return items


def date_from_offset(start_date: dt.date, offset: int, include_weekends: bool) -> dt.date:
    if include_weekends:
        return start_date + dt.timedelta(days=offset)

    current = start_date
    counted = 0
    while counted < offset:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:
            counted += 1
    return current


def schedule_items(
    items: Iterable[WorkItem],
    start_date: dt.date,
    hours_per_day: float,
    include_weekends: bool = False,
) -> list[ScheduledItem]:
    if hours_per_day <= 0:
        raise ValueError("hours_per_day must be positive")

    scheduled: list[ScheduledItem] = []
    used_hours = 0.0
    epsilon = 1e-9

    for item in items:
        start_day_offset = int(used_hours // hours_per_day)
        end_hour = used_hours + item.estimate
        end_day_offset = int((end_hour - epsilon) // hours_per_day)
        scheduled.append(
            ScheduledItem(
                title=item.title,
                estimate=item.estimate,
                start=date_from_offset(start_date, start_day_offset, include_weekends),
                deadline=date_from_offset(start_date, end_day_offset, include_weekends),
            )
        )
        used_hours = end_hour

    return scheduled


def shift_workdays(date_value: dt.date, days: int) -> dt.date:
    shifted = date_value
    for _ in range(days):
        shifted += dt.timedelta(days=1)
        while shifted.weekday() >= 5:
            shifted += dt.timedelta(days=1)
    return shifted


def apply_workday_shift(items: Iterable[ScheduledItem], days: int) -> list[ScheduledItem]:
    if days < 0:
        raise ValueError("shift_workdays must be zero or positive")
    if days == 0:
        return list(items)

    return [
        ScheduledItem(
            title=item.title,
            estimate=item.estimate,
            start=shift_workdays(item.start, days),
            deadline=shift_workdays(item.deadline, days),
        )
        for item in items
    ]


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def print_schedule(items: Iterable[ScheduledItem]) -> None:
    for item in items:
        print(
            "\t".join(
                [
                    item.title,
                    format_number(item.estimate),
                    item.start.isoformat(),
                    item.deadline.isoformat(),
                ]
            )
        )


def main() -> int:
    args = parse_args()
    start_date = dt.date.fromisoformat(args.start_date)
    raw_text = load_input(args.input_file)
    work_items = parse_work_items(raw_text)
    scheduled_items = schedule_items(
        work_items,
        start_date,
        args.hours_per_day,
        include_weekends=args.include_weekends,
    )
    scheduled_items = apply_workday_shift(scheduled_items, args.shift_workdays)

    print_schedule(scheduled_items)
    if args.dry_run:
        return 0

    account = os.environ.get("ZENTAO_ACCOUNT")
    password = os.environ.get("ZENTAO_PASSWORD")
    if not account or not password:
        raise SystemExit("ZENTAO_ACCOUNT and ZENTAO_PASSWORD must be set")

    assigned_to = args.assigned_to or account
    client = ZenTaoClient(args.base_url, account, password)
    client.login()

    for item in scheduled_items:
        client.create_task(
            project_id=args.project_id,
            parent_task_id=args.parent_task_id,
            assigned_to=assigned_to,
            task_type=args.type,
            pri=args.pri,
            item=item,
        )
        print(f"CREATED\t{item.title}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
