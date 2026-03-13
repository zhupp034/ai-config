#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import math
import os
import re
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

from create_zentao_tasks import DEFAULT_BASE_URL, ZenTaoClient

DEFAULT_GIT_ROOT = Path("/Users/zpp/Desktop/gitlab")
DEFAULT_TASK_PAGE = "my-task-assignedTo.html"
DEFAULT_MAX_PAGES = 3
DEFAULT_MIN_SCORE = 7.5
DEFAULT_DIFF_CHAR_LIMIT = 20000
PENDING_STATUSES = {"wait", "doing", "pause"}
SKILLS_ROOT = Path(__file__).resolve().parents[2]
GIT_WEEKLY_SCRIPT = SKILLS_ROOT / "git-weekly-summary" / "scripts" / "collect_weekly_commits.py"
NON_WORD_PATTERN = re.compile(r"[^0-9a-z\u4e00-\u9fff]+", re.IGNORECASE)
ROW_PATTERN = re.compile(r"<tr\b.*?>.*?</tr>", re.S | re.I)
TAG_PATTERN = re.compile(r"<[^>]+>")
ATTR_PATTERN = re.compile(r"([:\w-]+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\")", re.S)
PAGER_PATTERN = re.compile(
    r"data-rec-total='(?P<total>\d+)'.*?data-rec-per-page='(?P<per_page>\d+)'.*?data-page='(?P<page>\d+)'.*?data-link-creator='(?P<link>[^']+)'",
    re.S,
)


@dataclass(frozen=True)
class ZenTaoTask:
    task_id: int
    project_name: str
    title: str
    status_key: str
    status_label: str
    assigned_to_label: str
    consumed: str
    left: str
    finish_path: str | None


@dataclass(frozen=True)
class CommitRecord:
    repo_name: str
    repo_path: str
    sha: str
    short_sha: str
    date: str
    subject: str
    body: str
    files: tuple[str, ...]
    diff_excerpt: str
    search_lines: tuple[str, ...]
    normalized_search_text: str


@dataclass(frozen=True)
class CommitEvidence:
    commit: CommitRecord
    score: float
    reasons: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare ZenTao pending tasks with real git commits and optionally finish matched tasks."
    )
    parser.add_argument("--root", default=str(DEFAULT_GIT_ROOT), help="Git repository root, default: /Users/zpp/Desktop/gitlab")
    parser.add_argument("--since", help="Start date for git scan, default: current week Monday")
    parser.add_argument("--until", help="End date for git scan, default: today")
    parser.add_argument("--base-url", default=os.environ.get("ZENTAO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--page-path", default=DEFAULT_TASK_PAGE, help="ZenTao task list path to scan")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES, help="Maximum ZenTao task pages to scan")
    parser.add_argument("--task-ids", help="Optional comma-separated task IDs to limit the sync scope")
    parser.add_argument(
        "--project-keyword",
        action="append",
        default=[],
        help="Only consider ZenTao tasks whose project name contains this keyword. Repeatable.",
    )
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE, help="Minimum match score to treat a task as completed")
    parser.add_argument("--match-limit", type=int, default=3, help="Maximum supporting commits to display per matched task")
    parser.add_argument("--diff-char-limit", type=int, default=DEFAULT_DIFF_CHAR_LIMIT, help="Maximum diff characters to keep per commit")
    parser.add_argument("--skip-diff", action="store_true", help="Skip commit diff excerpts and only use subject/body/files for matching")
    parser.add_argument("--assigned-to", help="Override assignedTo when finishing a task")
    parser.add_argument("--current-consumed", help="Override currentConsumed when finishing tasks")
    parser.add_argument(
        "--comment-template",
        default="根据 git 实际提交确认任务已完成，自动同步完成时间为 {date}。关联提交：{commits}",
        help="Comment written into ZenTao when --apply is used. Supported placeholders: {date}, {commits}",
    )
    parser.add_argument("--apply", action="store_true", help="Finish matched tasks in ZenTao. Default is dry-run only.")
    return parser.parse_args()


def week_start(today: date | None = None) -> date:
    current = today or date.today()
    return current - timedelta(days=current.weekday())


def normalize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = html.unescape(text)
    cleaned = cleaned.replace("\u3000", " ")
    cleaned = cleaned.lower()
    cleaned = NON_WORD_PATTERN.sub(" ", cleaned)
    return " ".join(cleaned.split())


def strip_html(text: str) -> str:
    return " ".join(TAG_PATTERN.sub(" ", html.unescape(text)).split())


def parse_attrs(fragment: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in ATTR_PATTERN.finditer(fragment):
        attrs[match.group(1)] = html.unescape(match.group(2) or match.group(3) or "")
    return attrs


def extract_cell(row_html: str, marker: str) -> str:
    pattern = re.compile(rf"<td\b[^>]*class=['\"][^'\"]*{re.escape(marker)}[^'\"]*['\"][^>]*>(.*?)</td>", re.S | re.I)
    match = pattern.search(row_html)
    return match.group(1) if match else ""


def parse_task_rows(page_html: str) -> list[ZenTaoTask]:
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", page_html, re.S | re.I)
    if not tbody_match:
        return []

    tasks: list[ZenTaoTask] = []
    for row_html in ROW_PATTERN.findall(tbody_match.group(1)):
        checkbox_match = re.search(r"name='taskIDList\[\]'\s+value='(\d+)'", row_html)
        if not checkbox_match:
            continue

        task_id = int(checkbox_match.group(1))
        project_cell = extract_cell(row_html, "c-project")
        name_cell = extract_cell(row_html, "c-name")
        assigned_cell = extract_cell(row_html, "c-assignedTo")
        status_cell = extract_cell(row_html, "c-status")
        actions_cell = extract_cell(row_html, "c-actions")
        hour_cells = re.findall(r"<td\b[^>]*class=['\"][^'\"]*c-hours[^'\"]*['\"][^>]*>(.*?)</td>", row_html, re.S | re.I)

        project_name = strip_html(project_cell)
        title_attr = re.search(r"<td\b[^>]*class=['\"][^'\"]*c-name[^'\"]*['\"][^>]*title=['\"]([^'\"]+)['\"]", row_html, re.I)
        title = html.unescape(title_attr.group(1)) if title_attr else strip_html(name_cell)
        assigned_title = re.search(r"<span\b[^>]*title=['\"]([^'\"]+)['\"]", assigned_cell, re.I)
        assigned_to_label = html.unescape(assigned_title.group(1)) if assigned_title else strip_html(assigned_cell)

        status_match = re.search(r"status-task\s+status-([a-z]+)[^>]*>\s*([^<]+)", status_cell, re.I)
        status_key = status_match.group(1).lower() if status_match else ""
        status_label = status_match.group(2).strip() if status_match else strip_html(status_cell)

        finish_match = re.search(r"href=['\"]([^'\"]*task-finish-\d+\.html[^'\"]*)['\"]", actions_cell, re.I)
        finish_path = html.unescape(finish_match.group(1)) if finish_match else None

        estimate, consumed, left = "", "", ""
        if len(hour_cells) >= 3:
            estimate = strip_html(hour_cells[0])
            consumed = strip_html(hour_cells[1])
            left = strip_html(hour_cells[2])
        elif len(hour_cells) == 2:
            consumed = strip_html(hour_cells[0])
            left = strip_html(hour_cells[1])

        if not title:
            continue

        tasks.append(
            ZenTaoTask(
                task_id=task_id,
                project_name=project_name,
                title=title,
                status_key=status_key,
                status_label=status_label,
                assigned_to_label=assigned_to_label,
                consumed=consumed,
                left=left,
                finish_path=finish_path,
            )
        )
    return tasks


def parse_pager_config(page_html: str) -> tuple[int, int, int, str] | None:
    match = PAGER_PATTERN.search(page_html)
    if not match:
        return None
    return (
        int(match.group("total")),
        int(match.group("per_page")),
        int(match.group("page")),
        html.unescape(match.group("link")),
    )


def build_page_path(link_template: str, per_page: int, page: int) -> str:
    return link_template.replace("{recPerPage}", str(per_page)).replace("{page}", str(page))


def add_session_id(url: str, session_id: str | None) -> str:
    if not session_id:
        return url
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    if not any(key == "zentaosid" for key, _ in query):
        query.append(("zentaosid", session_id))
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))


def page_url(client: ZenTaoClient, path: str) -> str:
    return add_session_id(urllib.parse.urljoin(client.base_url, path.lstrip("/")), client.session_id)


def fetch_pending_tasks(
    client: ZenTaoClient,
    page_path: str,
    max_pages: int,
    allowed_task_ids: set[int] | None,
    project_keywords: list[str],
) -> list[ZenTaoTask]:
    initial_html = client._open(page_url(client, page_path))
    tasks = collect_tasks_from_page(initial_html, allowed_task_ids, project_keywords)

    pager_config = parse_pager_config(initial_html)
    if not pager_config or max_pages <= 1:
        return tasks

    total, per_page, _, link_template = pager_config
    total_pages = max(1, math.ceil(total / per_page))
    last_page = min(total_pages, max_pages)

    seen_ids = {task.task_id for task in tasks}
    for page_number in range(2, last_page + 1):
        next_path = build_page_path(link_template, per_page, page_number)
        page_html = client._open(page_url(client, next_path))
        for task in collect_tasks_from_page(page_html, allowed_task_ids, project_keywords):
            if task.task_id not in seen_ids:
                tasks.append(task)
                seen_ids.add(task.task_id)
    return tasks


def collect_tasks_from_page(
    page_html: str, allowed_task_ids: set[int] | None, project_keywords: list[str]
) -> list[ZenTaoTask]:
    tasks = []
    normalized_keywords = [keyword.strip() for keyword in project_keywords if keyword.strip()]
    for task in parse_task_rows(page_html):
        if task.status_key not in PENDING_STATUSES:
            continue
        if not task.finish_path:
            continue
        if allowed_task_ids and task.task_id not in allowed_task_ids:
            continue
        if normalized_keywords and not any(keyword in task.project_name for keyword in normalized_keywords):
            continue
        tasks.append(task)
    return tasks


def parse_finish_form_defaults(page_html: str) -> dict[str, str]:
    defaults: dict[str, str] = {}

    for match in re.finditer(r"<input\b([^>]+)>", page_html, re.S | re.I):
        attrs = parse_attrs(match.group(1))
        name = attrs.get("name")
        if not name or name.endswith("[]"):
            continue
        input_type = attrs.get("type", "text").lower()
        if input_type in {"file", "submit", "button", "image"}:
            continue
        if input_type in {"checkbox", "radio"} and "checked" not in match.group(1).lower():
            continue
        defaults[name] = attrs.get("value", "")

    for match in re.finditer(r"<textarea\b([^>]*)>(.*?)</textarea>", page_html, re.S | re.I):
        attrs = parse_attrs(match.group(1))
        name = attrs.get("name")
        if not name or name.endswith("[]"):
            continue
        defaults[name] = strip_html(match.group(2))

    for match in re.finditer(r"<select\b([^>]*)>(.*?)</select>", page_html, re.S | re.I):
        attrs = parse_attrs(match.group(1))
        name = attrs.get("name")
        if not name or name.endswith("[]"):
            continue
        selected_value = ""
        for option in re.finditer(r"<option\b([^>]*)>(.*?)</option>", match.group(2), re.S | re.I):
            option_attrs = parse_attrs(option.group(1))
            option_value = option_attrs.get("value", "")
            selected = "selected" in option.group(1).lower()
            if selected:
                selected_value = option_value
                break
            if selected_value == "":
                selected_value = option_value
        defaults[name] = selected_value

    return defaults


def load_git_report(root: str, since: str, until: str) -> dict:
    if not GIT_WEEKLY_SCRIPT.exists():
        raise RuntimeError(f"Missing git weekly summary script: {GIT_WEEKLY_SCRIPT}")
    command = [
        "python3",
        str(GIT_WEEKLY_SCRIPT),
        "--root",
        root,
        "--since",
        since,
        "--until",
        until,
        "--mine",
        "--format",
        "json",
    ]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "git weekly summary failed")
    try:
        return __import__("json").loads(completed.stdout)
    except Exception as error:  # pragma: no cover - defensive parse guard
        raise RuntimeError(f"Unable to parse git report JSON: {error}") from error


def diff_excerpt(repo_path: str, sha: str, char_limit: int) -> str:
    command = ["git", "-C", repo_path, "show", "--format=", "--unified=0", "--no-color", sha]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""

    excerpt_lines: list[str] = []
    current_length = 0
    current_file = ""
    for line in completed.stdout.splitlines():
        if line.startswith("diff --git "):
            diff_match = re.search(r" b/(.+)$", line)
            current_file = diff_match.group(1) if diff_match else ""
            continue
        if line.startswith(("+++", "---", "@@")):
            continue
        if not line.startswith(("+", "-")):
            continue
        if current_file.startswith(("dist/", "build/", "coverage/")):
            continue
        if current_file.endswith((".map", ".min.js", "yarn.lock", "package-lock.json")):
            continue
        cleaned = line[1:].strip()
        if not cleaned:
            continue
        if len(cleaned) > 300:
            continue
        excerpt_lines.append(cleaned)
        current_length += len(cleaned)
        if current_length >= char_limit:
            break
    return "\n".join(excerpt_lines)


def build_commit_records(report: dict, char_limit: int, skip_diff: bool) -> list[CommitRecord]:
    records: list[CommitRecord] = []
    seen: set[str] = set()
    for repo in report.get("repositories", []):
        repo_name = repo.get("name", "")
        repo_path = repo.get("path", "")
        for commit in repo.get("commits", []):
            sha = commit.get("sha", "")
            if not sha or sha in seen:
                continue
            seen.add(sha)
            subject = commit.get("subject", "").strip()
            body = commit.get("body", "").strip()
            files = tuple(commit.get("files", []))
            excerpt = "" if skip_diff else diff_excerpt(repo_path, sha, char_limit)
            search_lines = [repo_name, subject]
            search_lines.extend(line.strip() for line in body.splitlines() if line.strip())
            search_lines.extend(files)
            if excerpt:
                search_lines.extend(line.strip() for line in excerpt.splitlines() if line.strip())
            combined_text = "\n".join(part for part in search_lines if part)
            records.append(
                CommitRecord(
                    repo_name=repo_name,
                    repo_path=repo_path,
                    sha=sha,
                    short_sha=commit.get("short_sha", sha[:8]),
                    date=commit.get("date", ""),
                    subject=subject,
                    body=body,
                    files=files,
                    diff_excerpt=excerpt,
                    search_lines=tuple(search_lines),
                    normalized_search_text=normalize_text(combined_text),
                )
            )
    return records


def is_cjk_token(token: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in token)


def task_fragments(title: str) -> list[str]:
    parts = re.split(r"[\s/_\-（）()【】\[\]、，,：:]+", title)
    fragments: list[str] = []
    seen: set[str] = set()
    for part in parts:
        normalized = normalize_text(part)
        if len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        fragments.append(normalized)
    return fragments


def task_tokens(title: str) -> list[str]:
    normalized = normalize_text(title)
    tokens: list[str] = []
    seen: set[str] = set()
    for token in normalized.split():
        if is_cjk_token(token):
            if len(token) < 2:
                continue
        else:
            if len(token) < 3:
                continue
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def best_similarity(title: str, search_lines: tuple[str, ...]) -> tuple[str, float]:
    normalized_title = normalize_text(title)
    best_line = ""
    best_ratio = 0.0
    for line in search_lines:
        normalized_line = normalize_text(line)
        if len(normalized_line) < 2:
            continue
        ratio = SequenceMatcher(None, normalized_title, normalized_line).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_line = line.strip()
    return best_line, best_ratio


def normalized_line_core(line: str) -> str:
    normalized = normalize_text(line)
    normalized = re.sub(r"^(?:#+\s+|\d+\s+)", "", normalized)
    return normalized


def exact_title_line(title: str, search_lines: tuple[str, ...]) -> str:
    normalized_title = normalize_text(title)
    if not normalized_title:
        return ""
    for line in search_lines:
        if normalized_line_core(line) == normalized_title:
            return line.strip()
    return ""


def cjk_ngrams(text: str, size: int = 2) -> set[str]:
    normalized = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalize_text(text))
    if not normalized:
        return set()
    if len(normalized) <= size:
        return {normalized}
    return {normalized[index : index + size] for index in range(len(normalized) - size + 1)}


def best_ngram_overlap(title: str, search_lines: tuple[str, ...]) -> tuple[str, float]:
    title_ngrams = cjk_ngrams(title)
    if not title_ngrams:
        return "", 0.0
    best_line = ""
    best_ratio = 0.0
    for line in search_lines:
        line_ngrams = cjk_ngrams(line)
        if not line_ngrams:
            continue
        ratio = len(title_ngrams & line_ngrams) / len(title_ngrams)
        if ratio > best_ratio:
            best_ratio = ratio
            best_line = line.strip()
    return best_line, best_ratio


def is_ambiguous_short_title(title: str) -> bool:
    normalized = re.sub(r"\s+", "", normalize_text(title))
    return bool(normalized) and len(normalized) <= 4 and is_cjk_token(normalized)


def score_task_against_commit(task: ZenTaoTask, commit: CommitRecord) -> CommitEvidence | None:
    normalized_title = normalize_text(task.title)
    if not normalized_title:
        return None

    score = 0.0
    reasons: list[str] = []
    short_title = is_ambiguous_short_title(task.title)
    exact_line = exact_title_line(task.title, commit.search_lines)
    if normalized_title in commit.normalized_search_text and (not short_title or exact_line):
        score += 12.0
        reasons.append("任务标题完整命中提交内容")

    matched_fragments: list[str] = []
    for fragment in task_fragments(task.title):
        if short_title and not exact_line:
            break
        if fragment and fragment in commit.normalized_search_text:
            matched_fragments.append(fragment)
            score += 3.0 if len(fragment) >= 4 else 1.5
    if matched_fragments:
        reasons.append(f"命中标题片段: {', '.join(matched_fragments[:3])}")

    token_hits: list[str] = []
    for token in task_tokens(task.title):
        if short_title and not exact_line:
            break
        if token in commit.normalized_search_text:
            token_hits.append(token)
            score += 0.8 if is_cjk_token(token) else 0.5
    if token_hits:
        score += min(len(token_hits), 5) * 0.4

    project_name = normalize_text(task.project_name)
    project_hit = bool(project_name and project_name in commit.normalized_search_text)
    if project_hit:
        score += 1.0
        reasons.append("命中迭代名称")

    similar_line, ratio = best_similarity(task.title, commit.search_lines)
    if ratio >= 0.72 and (not short_title or exact_line or project_hit):
        score += ratio * 4
        reasons.append(f"与提交内容高相似: {similar_line[:80]}")
    elif ratio >= 0.58 and (not short_title or exact_line or project_hit):
        score += ratio * 2
        reasons.append(f"与提交内容部分相似: {similar_line[:80]}")

    overlap_line, overlap_ratio = best_ngram_overlap(task.title, commit.search_lines)
    if overlap_ratio >= 0.45 and (not short_title or exact_line or project_hit):
        score += overlap_ratio * 16
        reasons.append(f"命中标题高重叠片段: {overlap_line[:80]}")
    elif overlap_ratio >= 0.3 and (not short_title or exact_line or project_hit):
        score += overlap_ratio * 10
        reasons.append(f"命中标题重叠片段: {overlap_line[:80]}")

    if score <= 0:
        return None

    return CommitEvidence(commit=commit, score=round(score, 2), reasons=tuple(reasons))


def supporting_evidence(evidence_list: list[CommitEvidence], min_score: float, match_limit: int) -> list[CommitEvidence]:
    if not evidence_list:
        return []
    ordered = sorted(evidence_list, key=lambda item: (-item.score, item.commit.date, item.commit.short_sha))
    best_score = ordered[0].score
    threshold = max(min_score, best_score * 0.7)
    return [item for item in ordered if item.score >= threshold][:match_limit]


def match_tasks(tasks: list[ZenTaoTask], commits: list[CommitRecord], min_score: float, match_limit: int) -> tuple[list[tuple[ZenTaoTask, list[CommitEvidence]]], list[ZenTaoTask]]:
    matched: list[tuple[ZenTaoTask, list[CommitEvidence]]] = []
    unmatched: list[ZenTaoTask] = []
    for task in tasks:
        evidence = [item for item in (score_task_against_commit(task, commit) for commit in commits) if item]
        selected = supporting_evidence(evidence, min_score, match_limit)
        if selected and selected[0].score >= min_score:
            matched.append((task, selected))
        else:
            unmatched.append(task)
    return matched, unmatched


def parse_numeric(value: str) -> float:
    cleaned = (value or "").strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_hours(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def finish_task(
    client: ZenTaoClient,
    task: ZenTaoTask,
    finished_date: str,
    comment: str,
    assigned_to: str | None,
    current_consumed: str | None,
) -> None:
    if not task.finish_path:
        raise RuntimeError(f"Task #{task.task_id} has no finish action")

    finish_url = page_url(client, task.finish_path)
    form_defaults = parse_finish_form_defaults(client._open(finish_url))

    if current_consumed is None:
        current_value = parse_numeric(task.left)
        current_consumed = format_hours(current_value if current_value > 0 else 0.0)

    total_consumed = parse_numeric(form_defaults.get("consumed", "0")) + parse_numeric(current_consumed)
    form_defaults["currentConsumed"] = current_consumed
    form_defaults["consumed"] = format_hours(total_consumed)
    form_defaults["assignedTo"] = assigned_to or form_defaults.get("assignedTo", "")
    form_defaults["finishedDate"] = finished_date
    form_defaults["status"] = "done"
    form_defaults["comment"] = comment

    payload = urllib.parse.urlencode(form_defaults, doseq=True).encode("utf-8")
    client._open(
        finish_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    status_key, status_label = read_task_status(client, task.task_id)
    if status_key != "done":
        raise RuntimeError(f"ZenTao finish verification failed for #{task.task_id}: current status is {status_label or status_key}")


def read_task_status(client: ZenTaoClient, task_id: int) -> tuple[str, str]:
    view_html = client._open(page_url(client, f"task-view-{task_id}.html"))
    match = re.search(r"status-task\s+status-([a-z]+)[^>]*>.*?(未开始|进行中|已完成|已关闭|已取消|暂停)", view_html, re.S)
    if not match:
        return "", ""
    return match.group(1).lower(), match.group(2).strip()


def build_comment(template: str, finished_date: str, evidence: list[CommitEvidence]) -> str:
    commits = "；".join(f"{item.commit.date} {item.commit.short_sha} {item.commit.subject}" for item in evidence)
    return template.format(date=finished_date, commits=commits)


def parse_task_id_filter(raw_value: str | None) -> set[int] | None:
    if not raw_value:
        return None
    values = {int(part.strip()) for part in raw_value.split(",") if part.strip()}
    return values or None


def print_report(
    tasks: list[ZenTaoTask],
    matched: list[tuple[ZenTaoTask, list[CommitEvidence]]],
    unmatched: list[ZenTaoTask],
) -> None:
    print(f"[tasks-scanned] {len(tasks)}")
    print(f"[tasks-matched] {len(matched)}")
    print(f"[tasks-unmatched] {len(unmatched)}")

    if matched:
        print("")
        print("## Matched Tasks")
        for task, evidence in matched:
            commit_date = max(item.commit.date for item in evidence)
            print(f"- #{task.task_id} {task.title} -> {commit_date} (best score: {evidence[0].score})")
            print(f"  project: {task.project_name} | status: {task.status_label} | left: {task.left or '0'}")
            for item in evidence:
                reasons = "；".join(item.reasons)
                print(f"  - {item.commit.date} {item.commit.short_sha} {item.commit.subject}")
                if reasons:
                    print(f"    reasons: {reasons}")

    if unmatched:
        print("")
        print("## Unmatched Tasks")
        for task in unmatched:
            print(f"- #{task.task_id} {task.title} | {task.project_name} | {task.status_label}")


def main() -> int:
    args = parse_args()
    since = args.since or week_start().isoformat()
    until = args.until or date.today().isoformat()

    account = os.environ.get("ZENTAO_ACCOUNT")
    password = os.environ.get("ZENTAO_PASSWORD")
    if not account or not password:
        raise SystemExit("ZENTAO_ACCOUNT and ZENTAO_PASSWORD must be set")

    report = load_git_report(args.root, since, until)
    commits = build_commit_records(report, args.diff_char_limit, args.skip_diff)

    client = ZenTaoClient(args.base_url, account, password)
    client.login()

    allowed_task_ids = parse_task_id_filter(args.task_ids)
    tasks = fetch_pending_tasks(
        client=client,
        page_path=args.page_path,
        max_pages=max(1, args.max_pages),
        allowed_task_ids=allowed_task_ids,
        project_keywords=args.project_keyword,
    )
    matched, unmatched = match_tasks(tasks, commits, args.min_score, max(1, args.match_limit))
    print_report(tasks, matched, unmatched)

    if not args.apply:
        return 0

    print("")
    print("## Apply")
    for task, evidence in matched:
        finished_date = max(item.commit.date for item in evidence)
        comment = build_comment(args.comment_template, finished_date, evidence)
        finish_task(
            client=client,
            task=task,
            finished_date=finished_date,
            comment=comment,
            assigned_to=args.assigned_to,
            current_consumed=args.current_consumed,
        )
        print(f"FINISHED\t{task.task_id}\t{finished_date}\t{task.title}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
