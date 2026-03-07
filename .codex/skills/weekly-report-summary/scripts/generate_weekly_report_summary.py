#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

GITLAB_ROOT = Path("/Users/zpp/Desktop/gitlab")
GIT_WEEKLY_REPORT_DIR = Path("/Users/zpp/Desktop/workspace/git-weekly-report")
WEEKLY_REPORT_OUTPUT_DIR = Path("/Users/zpp/Desktop/workspace/weekly-report")
WEEKLY_REPORT_NOTES_DIR = Path("/Users/zpp/Desktop/workspace/weekly-report-notes")
GIT_WEEKLY_SUMMARY_SCRIPT = Path(
    "/Users/zpp/.codex/skills/git-weekly-summary/scripts/collect_weekly_commits.py"
)
ZENTAO_WEEKLY_SCRIPT = Path(
    "/Users/zpp/.codex/skills/zentao-weekly-summary/scripts/fetch_zentao_weekly.py"
)
SHARED_GLOSSARY_PATH = Path("/Users/zpp/.codex/memories/term-glossary.json")
LOCAL_GLOSSARY_PATH = Path("/Users/zpp/.codex/skills/git-weekly-summary/term-glossary.json")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Refresh git-weekly-report markdown, then summarize it into a polished weekly report."
    )
    parser.add_argument("--root", default=str(GITLAB_ROOT))
    parser.add_argument("--report-dir", default=str(GIT_WEEKLY_REPORT_DIR))
    parser.add_argument("--output-dir", default=str(WEEKLY_REPORT_OUTPUT_DIR))
    parser.add_argument("--notes-dir", default=str(WEEKLY_REPORT_NOTES_DIR))
    parser.add_argument("--write-output", action="store_true")
    parser.add_argument("--skip-zentao-refresh", action="store_true")
    parser.add_argument("--zentao-base-url", default=os.environ.get("ZENTAO_BASE_URL", "http://192.168.20.9/pro/"))
    parser.add_argument("--zentao-account", default=os.environ.get("ZENTAO_ACCOUNT"))
    parser.add_argument("--zentao-password", default=os.environ.get("ZENTAO_PASSWORD"))
    return parser.parse_args()


def current_week_start(now):
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def load_glossary_file(path):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {key: value for key, value in data.items() if isinstance(key, str) and isinstance(value, str)}


def load_term_glossary():
    glossary = load_glossary_file(LOCAL_GLOSSARY_PATH)
    glossary.update(load_glossary_file(SHARED_GLOSSARY_PATH))
    return glossary


def refresh_weekly_reports(root, report_dir):
    command = [
        "python3",
        str(GIT_WEEKLY_SUMMARY_SCRIPT),
        "--root",
        str(root),
        "--mine",
        "--write-report",
        "--write-json-report",
        "--report-dir",
        str(report_dir),
    ]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "refresh failed")
    stdout = completed.stdout
    json_match = re.search(r"^\[report-json-written\]\s+(.+)$", stdout, re.MULTILINE)
    if not json_match:
        raise RuntimeError("missing structured report path from git-weekly-summary output")
    json_path = Path(json_match.group(1).strip())
    if not json_path.exists():
        raise RuntimeError(f"structured report not found: {json_path}")
    return stdout, json_path


def refresh_zentao_notes(notes_dir, base_url=None, account=None, password=None, skip_refresh=False):
    if skip_refresh:
        print("[zentao-refresh-skipped] skipped by --skip-zentao-refresh", file=sys.stderr)
        return
    if not account or not password:
        print(
            "[zentao-refresh-skipped] missing ZenTao credentials; pass --zentao-account/--zentao-password or export ZENTAO_ACCOUNT/ZENTAO_PASSWORD",
            file=sys.stderr,
        )
        return

    command = [
        "python3",
        str(ZENTAO_WEEKLY_SCRIPT),
        "--notes-dir",
        str(notes_dir),
        "--base-url",
        base_url or "http://192.168.20.9/pro/",
        "--account",
        account,
        "--password",
        password,
    ]
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        print("[zentao-refresh-skipped] zentao refresh timed out", file=sys.stderr)
        return
    if completed.returncode != 0:
        print(
            f"[zentao-refresh-skipped] {completed.stderr.strip() or completed.stdout.strip() or 'zentao refresh failed'}",
            file=sys.stderr,
        )
        return
    stdout = completed.stdout.strip()
    if stdout:
        print(stdout, file=sys.stderr)


def load_structured_report(json_path):
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid json report: {error}") from error


def unique_keep_order(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def classify_subject(subject):
    lowered = subject.lower()
    if lowered.startswith("feat"):
        return "feat"
    if lowered.startswith("fix"):
        return "fix"
    if lowered.startswith("refactor"):
        return "refactor"
    if lowered.startswith("chore"):
        return "chore"
    if lowered.startswith("build:"):
        return "build"
    return "other"


def humanize_subject(subject):
    cleaned = subject.strip()
    if ":" in cleaned:
        prefix, rest = cleaned.split(":", 1)
        if prefix.lower() in {"feat", "fix", "refactor", "chore", "build", "docs", "test"}:
            cleaned = rest.strip()
    return cleaned


def format_term(term, glossary):
    explanation = glossary.get(term)
    if explanation:
        return f"{explanation}（{term}）"
    return term


def top_areas(repo, glossary):
    counts = {}
    for commit in repo["commits"]:
        for path in commit["files"]:
            area = path.split("/", 1)[0]
            if area in {"dist", "src", "test"} and "/" in path:
                parts = path.split("/")
                if len(parts) > 1:
                    area = parts[1]
            counts[area] = counts.get(area, 0) + 1
    return [format_term(name, glossary) for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]]


def top_phrases(commits, limit=3):
    phrases = []
    seen = set()
    for commit in commits:
        phrase = humanize_subject(commit["subject"])
        if not phrase or phrase in seen:
            continue
        seen.add(phrase)
        phrases.append(phrase)
        if len(phrases) == limit:
            break
    return phrases


def is_low_value_phrase(phrase):
    normalized = normalize_note_for_match(phrase)
    low_value = {
        "dist",
        "更新dist",
        "updatedist",
        "builddist",
        "同步dist",
    }
    return normalized in low_value


def classify_phrase_bucket(phrase):
    lowered = phrase.lower()
    if is_low_value_phrase(phrase):
        return "skip"
    if any(keyword in phrase for keyword in ["修复", "补强", "适配", "问题", "联测"]) or "fix" in lowered:
        return "问题修复"
    if any(keyword in phrase for keyword in ["发布", "优化", "调整", "迁移", "整理", "重构", "工具层", "日志输出", "bundle", "依赖"]) or "release" in lowered:
        return "技术优化"
    return "需求开发"


def top_phrases_from_repos(repos, categories, limit=5):
    phrases = []
    seen = set()
    for repo in repos:
        for commit in repo["commits"]:
            if classify_subject(commit["subject"]) not in categories:
                continue
            phrase = humanize_subject(commit["subject"])
            if is_low_value_phrase(phrase):
                continue
            normalized = normalize_note_for_match(phrase)
            if not phrase or normalized in seen:
                continue
            seen.add(normalized)
            phrases.append(phrase)
            if len(phrases) == limit:
                return phrases
    return phrases


def join_phrases(phrases):
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]}，同时{phrases[1]}"
    return f"{phrases[0]}，同时{phrases[1]}，并且{phrases[2]}"


def render_repo_section(repo, glossary):
    commits = repo["commits"]
    grouped = {"feat": [], "fix": [], "refactor": [], "chore": [], "other": [], "build": []}
    for commit in commits:
        grouped[classify_subject(commit["subject"])].append(commit)

    lines = []
    is_doc_only = False

    doc_only = all(commit["files"] and all(path.lower().endswith(".md") for path in commit["files"]) for commit in commits)
    if doc_only:
        is_doc_only = True
        phrases = top_phrases(commits, limit=2)
        if phrases:
            lines.append(f"- 这个项目这周主要是文档整理和内容沉淀，重点补充了{join_phrases(phrases)}。")
        return lines, is_doc_only

    if grouped["feat"]:
        phrases = top_phrases(grouped["feat"])
        if phrases:
            lines.append(f"- 这周主要推进了{join_phrases(phrases)}。")
    if grouped["fix"]:
        phrases = top_phrases(grouped["fix"])
        if phrases:
            lines.append(f"- 问题修复这块，重点处理了{join_phrases(phrases)}。")
    if grouped["refactor"] or grouped["chore"]:
        phrases = top_phrases(grouped["refactor"] + grouped["chore"], limit=2)
        if phrases:
            lines.append(f"- 另外还做了一些整理和维护，比如{join_phrases(phrases)}。")
    if not lines:
        lines.append("- 本周以常规维护和结果同步为主。")
    return lines, is_doc_only


def render_repo_summary(repo):
    grouped = {"feat": [], "fix": [], "refactor": [], "chore": [], "other": [], "build": []}
    for commit in repo["commits"]:
        grouped[classify_subject(commit["subject"])].append(commit)

    lines = []
    if grouped["feat"]:
        phrases = top_phrases(grouped["feat"], limit=2)
        if phrases:
            lines.append(f"- 本周主要推进了{join_phrases(phrases)}。")
    if grouped["fix"]:
        phrases = top_phrases(grouped["fix"], limit=2)
        if phrases:
            lines.append(f"- 同步处理了{join_phrases(phrases)}。")
    if grouped["refactor"] or grouped["chore"]:
        phrases = top_phrases(grouped["refactor"] + grouped["chore"], limit=2)
        if phrases:
            lines.append(f"- 另外完成了{join_phrases(phrases)}。")
    if not lines:
        lines.append("- 本周以常规维护和结果同步为主。")
    return lines[:3]


def build_overview(report, active_repos):
    total_commits = sum(repo["commit_count"] for repo in active_repos)
    glossary = load_term_glossary()
    repo_names = "、".join(format_term(repo["name"], glossary) for repo in active_repos)
    themes = []
    if any(any(classify_subject(commit["subject"]) == "feat" for commit in repo["commits"]) for repo in active_repos):
        themes.append("功能迭代")
    if any(any(classify_subject(commit["subject"]) == "fix" for commit in repo["commits"]) for repo in active_repos):
        themes.append("问题修复")
    if any(any(classify_subject(commit["subject"]) == "refactor" for commit in repo["commits"]) for repo in active_repos):
        themes.append("代码整理")
    if any(any(classify_subject(commit["subject"]) == "build" for commit in repo["commits"]) for repo in active_repos):
        themes.append("构建产物同步")
    lines = [
        f"这周一共提交了 {total_commits} 次，主要集中在 {len(active_repos)} 个仓库。",
        f"主要投入的项目是 {repo_names}。",
    ]
    if themes:
        lines.append(f"工作重点还是围绕 {'、'.join(themes)}。")
    if len(report.get("roots", [])) > 1:
        root_names = "、".join(Path(item).name for item in report["roots"])
        lines.append(f"本次扫描目录包括 {root_names}。")
    return lines


def load_weekly_notes(notes_dir, since):
    lines = []
    primary = notes_dir / f"{since.strftime('%Y-%m-%d')}.md"
    candidates = []
    if primary.exists():
        candidates.append(primary)
    for notes_path in sorted(notes_dir.glob(f"{since.strftime('%Y-%m-%d')}*.md")):
        if notes_path == primary:
            continue
        candidates.append(notes_path)
    for notes_path in candidates:
        for raw_line in notes_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("- "):
                lines.append(line[2:].strip())
            else:
                lines.append(line)
    return lines


def classify_note_theme(note):
    lowered = note.lower()
    if "[zentao-warning]" in note:
        return "zentao-warning"
    if "面试" in note:
        return "interview"
    if "健康会议" in note:
        return "health-meeting"
    if "会议" in note or "联测" in note or "断线重连" in note:
        return "meeting-work"
    if "禅道联调" in note or "禅道导出" in note:
        return "ai-tooling"
    if "调研 ai 接入" in lowered or ("禅道" in note and "飞书云文档" in note) or "腾讯云文档" in note:
        return "ai-research"
    if "ai" in lowered or "skill" in lowered or "工作流" in note or "禅道导出" in note:
        return "ai-tooling"
    return note


def normalize_note_for_match(note):
    return re.sub(r"[\s，。、“”‘’；：:,.（）()]+", "", note).lower()


def simplify_note_fragment(note):
    fragment = note.strip().rstrip("。")
    prefixes = [
        "本周在禅道侧主要跟进了",
        "本周在禅道侧还推进了",
        "本周在禅道侧同步记录了",
        "本周在禅道侧还补充了",
        "本周在禅道侧主要推进了",
    ]
    for prefix in prefixes:
        if fragment.startswith(prefix):
            fragment = fragment[len(prefix):]
            break
    suffixes = ["等相关事项", "相关事项"]
    for suffix in suffixes:
        if fragment.endswith(suffix):
            fragment = fragment[: -len(suffix)]
            break
    return fragment.strip("，、； ")


def polish_fragment_text(fragment):
    polished = fragment.strip().rstrip("。")
    polished = polished.replace("AI ", "AI ")
    polished = polished.replace("和AI ", "、AI ")
    polished = polished.replace("和禅道", "、禅道")
    return polished.strip("，、； ")


def merge_note_text(existing, incoming):
    existing_norm = normalize_note_for_match(existing)
    incoming_norm = normalize_note_for_match(incoming)
    if not incoming_norm:
        return existing
    if incoming_norm in existing_norm:
        return existing
    if existing_norm in incoming_norm:
        return incoming

    incoming_fragment = polish_fragment_text(simplify_note_fragment(incoming))
    existing_fragment = polish_fragment_text(simplify_note_fragment(existing))
    incoming_fragment_norm = normalize_note_for_match(incoming_fragment)
    if incoming_fragment_norm and incoming_fragment_norm in existing_norm:
        return existing
    if "面试" in existing and "面试" in incoming:
        return existing
    if existing_fragment and existing.startswith("本周在禅道侧") and not incoming.startswith("本周在禅道侧"):
        return f"{incoming.rstrip('。')}；同时补充了{existing_fragment}。"
    if incoming.startswith("本周在禅道侧") and not existing.startswith("本周在禅道侧"):
        return f"{existing.rstrip('。')}，并补充了{incoming_fragment}。"
    return f"{existing.rstrip('。')}；同时补充了{incoming_fragment or incoming.rstrip('。')}。"


def merge_extra_notes(notes):
    merged = []
    index_by_theme = {}
    for note in notes:
        theme = classify_note_theme(note)
        if theme in index_by_theme:
            index = index_by_theme[theme]
            merged[index] = merge_note_text(merged[index], note)
        else:
            index_by_theme[theme] = len(merged)
            merged.append(note)
    return merged


def note_matches(note, keywords):
    return any(keyword in note for keyword in keywords)


def dedupe_phrases(items, limit=None):
    results = []
    seen = set()
    for item in items:
        normalized = normalize_note_for_match(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        results.append(item)
        if limit and len(results) >= limit:
            break
    return results


def build_completed_sections(active_repos, extra_notes):
    demand_items = []
    fix_items = []
    optimization_items = []

    for repo in active_repos:
        for commit in repo["commits"]:
            phrase = humanize_subject(commit["subject"])
            if not phrase or is_low_value_phrase(phrase):
                continue
            bucket = classify_phrase_bucket(phrase)
            if bucket == "需求开发":
                demand_items.append(phrase)
            elif bucket == "问题修复":
                fix_items.append(phrase)
            elif bucket == "技术优化":
                optimization_items.append(phrase)

    for note in extra_notes:
        if note_matches(note, ["AI", "ai", "skill", "禅道", "调研", "优化"]):
            optimization_items.append(note.rstrip("。"))
        elif note_matches(note, ["联测", "发版", "会议", "断线重连"]):
            demand_items.append(note.rstrip("。"))

    return {
        "需求开发": dedupe_phrases(demand_items, limit=5),
        "问题修复": dedupe_phrases(fix_items, limit=5),
        "技术优化": dedupe_phrases(optimization_items, limit=5),
    }


def build_project_sections(active_repos, glossary):
    sections = []
    ordered_repos = sorted(active_repos, key=lambda repo: (-repo["commit_count"], repo["name"]))
    for repo in ordered_repos:
        sections.append((format_term(repo["name"], glossary), render_repo_summary(repo)))
    return sections


def build_risk_section(active_repos, extra_notes):
    items = []
    if any("断线重连" in humanize_subject(commit["subject"]) for repo in active_repos for commit in repo["commits"]):
        items.append("会议系统与课堂侧的断线重连相关改动仍需继续关注联测稳定性和线上表现。")
    if any(note_matches(note, ["联测", "会议"]) for note in extra_notes):
        items.append("跨项目联测事项较多，需要继续协调测试节奏和版本节奏。")
    for note in extra_notes:
        if "[zentao-warning]" in note:
            items.append(note.replace("[zentao-warning]", "禅道动态抓取提醒：").strip())
    return dedupe_phrases(items, limit=3)


def build_reflection_section(extra_notes):
    items = []
    if any(note_matches(note, ["AI", "ai", "skill", "禅道", "飞书云文档", "腾讯云文档"]) for note in extra_notes):
        items.append("本周继续沉淀 AI 工具和工作 skill 的配合方式，重复性整理工作进一步减少。")
    if any(note_matches(note, ["面试"]) for note in extra_notes):
        items.append("在面试过程中也进一步验证了前端基础能力、项目表达和工程思维的重要性。")
    return dedupe_phrases(items, limit=3)


def build_next_plan_section(active_repos, extra_notes):
    items = []
    if any("断线重连" in humanize_subject(commit["subject"]) for repo in active_repos for commit in repo["commits"]):
        items.append("继续跟进会议系统和课堂侧断线重连相关优化，补充联测和稳定性验证。")
    if any(repo["name"] == "cnstrong-WebRTC" for repo in active_repos):
        items.append("继续推进音视频播放器和 webrtc 组件库的稳定性优化与版本迭代。")
    if any(note_matches(note, ["AI", "ai", "禅道", "飞书云文档", "腾讯云文档"]) for note in extra_notes):
        items.append("继续推进 AI 接入禅道和文档平台的调研与落地，完善日常工作流。")
    return dedupe_phrases(items, limit=4)


def build_summary(report, since, until, extra_notes):
    glossary = load_term_glossary()
    active_repos = [repo for repo in report["repositories"] if repo["commit_count"] > 0]
    merged_notes = merge_extra_notes(extra_notes)
    completed_sections = build_completed_sections(active_repos, merged_notes)
    project_sections = build_project_sections(active_repos, glossary)
    risk_items = build_risk_section(active_repos, merged_notes)
    reflection_items = build_reflection_section(merged_notes)
    next_plan_items = build_next_plan_section(active_repos, merged_notes)
    lines = [
        "# 本周周报",
        "",
        f"统计周期：{since.strftime('%Y-%m-%d')} 至 {until.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 一、本周完成",
    ]

    for title in ("需求开发", "问题修复", "技术优化"):
        lines.append(f"### {title}")
        items = completed_sections[title]
        if items:
            for item in items:
                suffix = "" if item.endswith("。") else "。"
                lines.append(f"- {item}{suffix}")
        else:
            lines.append("- 暂无。")
        lines.append("")

    lines.append("## 二、项目维度汇总")
    for repo_name, repo_lines in project_sections:
        lines.append(f"### {repo_name}")
        for item in repo_lines:
            lines.append(item)
        lines.append("")

    lines.append("## 三、问题与风险")
    if risk_items:
        for item in risk_items:
            suffix = "" if item.endswith("。") else "。"
            lines.append(f"- {item}{suffix}")
    else:
        lines.append("- 暂无明显问题与风险。")
    lines.append("")

    lines.append("## 四、心得体会")
    if reflection_items:
        for item in reflection_items:
            suffix = "" if item.endswith("。") else "。"
            lines.append(f"- {item}{suffix}")
    else:
        lines.append("- 暂无。")
    lines.append("")

    lines.append("## 五、下周计划")
    if next_plan_items:
        for item in next_plan_items:
            suffix = "" if item.endswith("。") else "。"
            lines.append(f"- {item}{suffix}")
    else:
        lines.append("- 暂无。")

    return "\n".join(lines).rstrip() + "\n"


def write_output(summary, output_dir, report_date):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{report_date.strftime('%Y-%m-%d')}.md"
    output_path.write_text(summary, encoding="utf-8")
    return output_path


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    report_dir = Path(args.report_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    notes_dir = Path(args.notes_dir).resolve()
    now = datetime.now()
    since = current_week_start(now)

    refresh_zentao_notes(
        notes_dir,
        base_url=args.zentao_base_url,
        account=args.zentao_account,
        password=args.zentao_password,
        skip_refresh=args.skip_zentao_refresh,
    )
    _, json_path = refresh_weekly_reports(root, report_dir)
    report = load_structured_report(json_path)
    extra_notes = load_weekly_notes(notes_dir, since)
    summary = build_summary(report, since, now, extra_notes)
    print(summary, end="")
    if args.write_output:
        output_path = write_output(summary, output_dir, now)
        print(f"[summary-written] {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
