#!/usr/bin/env python3

import argparse
import html
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from http.cookiejar import CookieJar
from pathlib import Path

DEFAULT_BASE_URL = "http://192.168.20.9/pro/"
DEFAULT_NOTES_DIR = Path("/Users/zpp/Desktop/workspace/weekly-report-notes")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch this week's ZenTao dynamic activity and write a weekly markdown note."
    )
    parser.add_argument("--base-url", default=os.environ.get("ZENTAO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--account", default=os.environ.get("ZENTAO_ACCOUNT"))
    parser.add_argument("--password", default=os.environ.get("ZENTAO_PASSWORD"))
    parser.add_argument("--notes-dir", default=str(DEFAULT_NOTES_DIR))
    return parser.parse_args()


def current_week_start(now):
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def build_opener():
    jar = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def post(opener, url, data, headers):
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
    with opener.open(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="ignore")


def get(opener, url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener.open(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="ignore")


def login(opener, base_url, account, password):
    login_url = urllib.parse.urljoin(base_url, "user-login.html")
    payload = {
        "account": account,
        "password": password,
        "passwordStrength": "2",
        "referer": "/pro/",
        "verifyRand": "209305225",
        "keepLogin": "1",
    }
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
    }
    response = post(opener, login_url, payload, headers)
    if '"result":"success"' not in response:
        raise RuntimeError(f"ZenTao login failed: {response[:200]}")


def parse_cn_date(text, now):
    if text == "今天":
        return now.date()
    if text == "昨天":
        return (now - timedelta(days=1)).date()
    month_day = re.search(r"(\d{1,2})月(\d{1,2})日", text)
    if month_day:
        month = int(month_day.group(1))
        day = int(month_day.group(2))
        year = now.year
        return datetime(year, month, day).date()
    return None


def strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def parse_next_page_link(html_text, base_url):
    match = re.search(r"href='([^']*my-dynamic-[^']*-next\.html)'", html_text, re.I)
    if not match:
        match = re.search(r'href="([^"]*my-dynamic-[^"]*-next\.html)"', html_text, re.I)
    if not match:
        return None
    return urllib.parse.urljoin(base_url, html.unescape(match.group(1)))


def parse_dynamic_page(html_text, since, now):
    entries = []
    oldest_date = None
    section_pattern = re.compile(
        r'<div class="dynamic[^"]*">.*?<span class="date-label">(.*?)</span>.*?<span class="date-text">(.*?)</span>.*?<ul class="timeline[^"]*">(.*?)</ul>',
        re.S,
    )
    item_pattern = re.compile(r"<li\b.*?>.*?</li>", re.S)

    for date_label, date_text, timeline_html in section_pattern.findall(html_text):
        date_value = parse_cn_date(date_label.strip(), now) or parse_cn_date(date_text.strip(), now)
        if date_value and (oldest_date is None or date_value < oldest_date):
            oldest_date = date_value
        if not date_value or date_value < since.date():
            continue
        for item_html in item_pattern.findall(timeline_html):
            time_match = re.search(r'<span class="timeline-tag">(.*?)</span>', item_html, re.S)
            text_match = re.search(r'<span class="timeline-text">(.*?)</span>\s*</div>', item_html, re.S)
            if not time_match or not text_match:
                continue
            time_text = strip_tags(time_match.group(1))
            text_html = text_match.group(1)
            item_plain = strip_tags(item_html)
            if any(noise in item_plain for noise in ["登录系统", "退出登录"]):
                continue
            action_match = re.search(r"<span class='label-action'>(.*?)</span>", text_html, re.S)
            type_match = re.search(r'<span class="text-muted">(.*?)</span>', text_html, re.S)
            title_match = re.search(r"<a [^>]*>(.*?)</a>", text_html, re.S)
            action = strip_tags(action_match.group(1)) if action_match else ""
            item_type = strip_tags(type_match.group(1)) if type_match else ""
            title = strip_tags(title_match.group(1)) if title_match else strip_tags(text_html)
            entries.append(
                {
                    "date": date_value.isoformat(),
                    "time": time_text,
                    "action": action,
                    "type": item_type,
                    "title": title,
                }
            )
    return entries, oldest_date


def fetch_weekly_dynamic(opener, base_url, since, now, max_pages=20):
    next_url = urllib.parse.urljoin(base_url, "my-dynamic-all.html")
    all_entries = []
    pages_seen = set()

    for _ in range(max_pages):
        if not next_url or next_url in pages_seen:
            break
        pages_seen.add(next_url)
        html_text = get(opener, next_url)
        page_entries, oldest_date = parse_dynamic_page(html_text, since, now)
        all_entries.extend(page_entries)
        if oldest_date and oldest_date < since.date():
            break
        next_url = parse_next_page_link(html_text, base_url)

    return all_entries


def summarize(entries):
    def sort_key(entry):
        return (entry.get("date", ""), entry.get("time", ""))

    unique_entries = []
    seen_titles = set()
    for entry in sorted(entries, key=sort_key, reverse=True):
        title = entry["title"].strip()
        if not title or title.startswith("/pro/") or ".html" in title:
            continue
        key = (entry["type"] or "其他", title)
        if key not in seen_titles:
            seen_titles.add(key)
            normalized_entry = dict(entry)
            normalized_entry["title"] = title
            unique_entries.append(normalized_entry)

    if not unique_entries:
        return []

    return [entry["title"] for entry in unique_entries]


def write_note(lines, notes_dir, since):
    notes_dir.mkdir(parents=True, exist_ok=True)
    path = notes_dir / f"{since.strftime('%Y-%m-%d')}-zentao.md"
    content = "\n".join(f"- {line}" for line in lines) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def main():
    args = parse_args()
    if not args.account or not args.password:
        print("Missing ZENTAO_ACCOUNT or ZENTAO_PASSWORD.", file=sys.stderr)
        return 1

    now = datetime.now()
    since = current_week_start(now)
    opener = build_opener()
    base_url = args.base_url.rstrip("/") + "/"
    login(opener, base_url, args.account, args.password)
    entries = fetch_weekly_dynamic(opener, base_url, since, now)
    if not entries:
        print("No ZenTao activity found for the current week.", file=sys.stderr)
        return 1
    lines = summarize(entries)
    note_path = write_note(lines, Path(args.notes_dir), since)
    print("\n".join(f"- {line}" for line in lines))
    print(f"[zentao-note-written] {note_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
