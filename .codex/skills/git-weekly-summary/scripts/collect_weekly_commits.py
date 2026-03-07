#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".idea", ".vscode"}
SHARED_GLOSSARY_PATH = Path("/Users/zpp/.codex/memories/term-glossary.json")
LOCAL_GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "term-glossary.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect weekly git commits across multiple repositories."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Directory containing one or more git repositories. Defaults to current directory.",
    )
    parser.add_argument(
        "--extra-root",
        action="append",
        default=[],
        help="Additional directories to scan for repositories.",
    )
    parser.add_argument(
        "--since",
        help="Start date/time accepted by git log. Defaults to current week Monday 00:00.",
    )
    parser.add_argument(
        "--until",
        help="End date/time accepted by git log. Defaults to now.",
    )
    parser.add_argument(
        "--author",
        help="Optional author filter forwarded to git log.",
    )
    parser.add_argument(
        "--author-email",
        help="Optional author email filter applied in addition to --author.",
    )
    parser.add_argument(
        "--mine",
        action="store_true",
        help="Filter to the current git identity from global config.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan descendant directories for git repositories.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "summary"),
        default="summary",
        help="Output format. Defaults to summary.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=8,
        help="Maximum files to show per commit in markdown output. Defaults to 8.",
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include repositories with zero commits in markdown output.",
    )
    parser.add_argument(
        "--include-merges",
        action="store_true",
        help="Include merge commits. Excluded by default to reduce report noise.",
    )
    parser.add_argument(
        "--current-branch-only",
        action="store_true",
        help="Only scan the current branch. By default all refs are scanned.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write the generated summary into a weekly markdown file.",
    )
    parser.add_argument(
        "--write-json-report",
        action="store_true",
        help="Write the structured JSON report alongside the markdown report.",
    )
    parser.add_argument(
        "--report-dir",
        help="Directory used for weekly summary markdown files. Defaults to /Users/zpp/Desktop/workspace/git-weekly-report.",
    )
    return parser.parse_args()


def current_week_start():
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def extract_report_date(report):
    return report["generated_at"].split("T")[0]


def resolve_roots(root, extra_roots):
    roots = [root.resolve()]
    for extra_root in extra_roots:
        candidate = Path(extra_root).resolve()
        if candidate.exists() and candidate.is_dir():
            roots.append(candidate)

    primary = roots[0]
    sibling_github = primary.parent / "github"
    if primary.name == "gitlab" and sibling_github.exists() and sibling_github.is_dir():
        roots.append(sibling_github.resolve())

    deduped = []
    seen = set()
    for item in roots:
        key = str(item)
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def git_output(repo, args):
    command = ["git", "-C", str(repo), *args]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def git_run(repo, args):
    command = ["git", "-C", str(repo), *args]
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def is_empty_repo_error(message):
    return "does not have any commits yet" in message


def normalize_body(body):
    cleaned = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line == "```" or line.lower().startswith("co-authored-by:"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def git_config_get(key):
    completed = subprocess.run(
        ["git", "config", "--global", key],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def load_glossary_file(path):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    glossary = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            glossary[key] = value
    return glossary


def load_term_glossary():
    glossary = load_glossary_file(LOCAL_GLOSSARY_PATH)
    glossary.update(load_glossary_file(SHARED_GLOSSARY_PATH))
    return glossary


def resolve_author_filters(args):
    author_name = args.author
    author_email = args.author_email
    if args.mine:
        author_name = author_name or git_config_get("user.name")
        author_email = author_email or git_config_get("user.email")
    return author_name, author_email


def sanitize_subject(subject):
    return subject.replace("```", "").strip()


def looks_mostly_ascii(text):
    ascii_count = sum(1 for char in text if ord(char) < 128)
    return ascii_count >= max(6, len(text) * 0.6)


def humanize_english_phrase(text):
    normalized = " ".join(text.replace("-", " ").replace("_", " ").split())
    lowered = normalized.lower()
    replacements = [
        ("stabilize ", "稳定"),
        ("optimize ", "优化"),
        ("fix ", "修复"),
        ("update ", "更新"),
        ("upgrade ", "升级"),
        ("add ", "新增"),
        ("support ", "支持"),
        ("release ", "发布"),
        ("reload page when ", "在"),
        ("move ", "迁移"),
        ("improve ", "改进"),
    ]
    for source, target in replacements:
        if lowered.startswith(source):
            rest = normalized[len(source):].strip()
            if source == "reload page when ":
                return f"{target}{rest}时自动刷新页面"
            if source == "move " and " to " in lowered:
                left, right = normalized.split(" to ", 1)
                return f"将{left[5:].strip()}迁移到{right.strip()}"
            return f"{target}{rest}"
    if lowered.startswith("hide ") and " in " in lowered:
        target, scene = normalized[5:].split(" in ", 1)
        return f"在{scene.strip()}中隐藏{target.strip()}"
    if lowered.startswith("release "):
        return f"发布 {normalized[8:].strip()} 版本"
    return normalized


def humanize_summary_phrase(subject):
    phrase = normalize_summary_subject(subject)
    lowered = phrase.lower()
    if lowered.startswith("release "):
        return f"发布 {phrase[8:].strip()} 版本"
    if "flvplayer" in lowered:
        return "完善播放器能力和按需加载链路"
    if "htmlentitiestoemoji" in lowered:
        return "将表情转换能力下沉到工具层"
    if "device event" in lowered:
        return "修复设备事件响应逻辑"
    if "smoke test" in lowered or "smoke tests" in lowered:
        return "补强基础冒烟验证链路"
    if "message" in lowered and "闪烁" in phrase:
        return "修复重连过程中的消息闪烁问题"
    if "rtc包" in phrase:
        return "更新 RTC 依赖并同步联调能力"
    if "beautyenabled" in lowered:
        return "统一美颜开关配置并补充浏览器测试场景"
    if "并" not in phrase and "package exports" in lowered:
        return "稳定 npm 包导出和冒烟测试"
    if "webview" in lowered and "hide" in lowered:
        return "适配 WebView 场景下的音视频状态展示"
    if "reload page" in lowered:
        return "补充特定场景下的页面自动刷新处理"
    if "rtc" in lowered and "log" in lowered:
        return "优化 RTC 流日志输出"
    if "visibility logic" in lowered or "viewport width" in lowered:
        return "调整全屏显示可见性逻辑并优化页面视口表现"
    if "mobile" in lowered and "user list" in lowered:
        return "放开移动端用户列表展示能力"
    if "reconnect" in lowered:
        return "增强断线重连相关交互和稳定性"
    if looks_mostly_ascii(phrase):
        return humanize_english_phrase(phrase)
    return phrase


def normalize_summary_subject(subject):
    cleaned = sanitize_subject(subject)
    if ":" in cleaned:
        prefix, rest = cleaned.split(":", 1)
        if prefix.lower() in {"feat", "fix", "refactor", "chore", "build", "docs", "test", "perf"}:
            cleaned = rest.strip()
    return cleaned.lstrip("- ").strip()


def is_noise_commit(subject):
    normalized = sanitize_subject(subject).lower()
    return normalized.startswith("index on ") or normalized.startswith("wip on ")


def find_repositories(root, recursive):
    root = root.resolve()
    repos = []

    if (root / ".git").exists():
        repos.append(root)

    if recursive:
        for current_root, dirnames, _ in os.walk(root):
            dirnames[:] = [
                name for name in dirnames if name not in SKIP_DIRS and not name.startswith(".")
            ]
            current_path = Path(current_root)
            if current_path != root and (current_path / ".git").exists():
                repos.append(current_path)
                dirnames[:] = []
    else:
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if child.name in SKIP_DIRS or child.name.startswith("."):
                continue
            if (child / ".git").exists():
                repos.append(child)

    deduped = []
    seen = set()
    for repo in repos:
        key = str(repo)
        if key not in seen:
            deduped.append(repo)
            seen.add(key)
    return deduped


def collect_repo_commits(repo, since, until, author_name, author_email, include_merges, current_branch_only):
    pretty = "%H%x1f%an%x1f%ae%x1f%cd%x1f%s%x1f%b%x1e"
    commits = []
    args = [
        "log",
        "--date=short",
        f"--since={since}",
        f"--until={until}",
        f"--pretty=format:{pretty}",
    ]
    if not current_branch_only:
        args.append("--all")
    if not include_merges:
        args.append("--no-merges")

    try:
        output = git_output(repo, args).strip("\n\x1e")
    except RuntimeError as error:
        if is_empty_repo_error(str(error)):
            return commits
        raise
    if not output.strip():
        return commits

    for chunk in output.split("\x1e"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 5:
            continue
        if len(parts) == 5:
            sha, commit_author_name, commit_author_email, date, subject = parts
            body = ""
        else:
            sha, commit_author_name, commit_author_email, date, subject, body = parts[:6]
        if is_noise_commit(subject):
            continue
        if author_name and commit_author_name != author_name:
            continue
        if author_email and commit_author_email != author_email:
            continue
        files_output = git_output(repo, ["show", "--pretty=format:", "--name-only", sha])
        files = [line.strip() for line in files_output.splitlines() if line.strip()]
        commits.append(
            {
                "sha": sha,
                "short_sha": sha[:8],
                "author": commit_author_name,
                "author_email": commit_author_email,
                "date": date,
                "subject": sanitize_subject(subject),
                "body": normalize_body(body),
                "files": files,
            }
        )
    return commits


def build_report(roots, repos, since, until, author_name, author_email, include_merges, current_branch_only):
    report = {
        "root": str(roots[0]),
        "roots": [str(root) for root in roots],
        "since": since,
        "until": until,
        "author": author_name,
        "author_email": author_email,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "repositories": [],
    }

    for repo in repos:
        commits = collect_repo_commits(
            repo,
            since,
            until,
            author_name,
            author_email,
            include_merges,
            current_branch_only,
        )
        authors = sorted({item["author"] for item in commits})
        touched_files = sorted({path for item in commits for path in item["files"]})
        report["repositories"].append(
            {
                "name": repo.name,
                "path": str(repo),
                "commit_count": len(commits),
                "authors": authors,
                "touched_files_count": len(touched_files),
                "commits": commits,
            }
        )
    return report


def classify_subject(subject):
    lowered = subject.lower()
    if lowered.startswith("build:"):
        return "build"
    if lowered.startswith("fix"):
        return "fix"
    if lowered.startswith("feat"):
        return "feat"
    if lowered.startswith("refactor"):
        return "refactor"
    if lowered.startswith("chore"):
        return "chore"
    return "other"


def classify_area(path):
    cleaned = path.strip("/")
    if not cleaned:
        return None
    parts = [part for part in cleaned.split("/") if part not in {"src", "lib", "dist", "test", "tests"}]
    if not parts:
        return None
    area = parts[0]
    if "." in area and len(parts) > 1:
        area = parts[1]
    if area.startswith("."):
        return None
    return area[:40]


AREA_LABELS = load_term_glossary()


def format_area_label(area):
    explanation = AREA_LABELS.get(area)
    if explanation:
        return f"{explanation}（{area}）"
    return area


def format_repo_name(name):
    explanation = AREA_LABELS.get(name)
    if explanation:
        return f"{explanation}（{name}）"
    return name


def summarize_commit_group(commits):
    phrases = []
    seen = set()
    for commit in commits:
        phrase = humanize_summary_phrase(commit["subject"])
        normalized = phrase.lower()
        if not phrase or normalized in seen:
            continue
        seen.add(normalized)
        phrases.append(phrase)
        if len(phrases) == 3:
            break
    return phrases


def summarize_areas(commits):
    area_counts = defaultdict(int)
    for commit in commits:
        for path in commit["files"]:
            area = classify_area(path)
            if area:
                area_counts[area] += 1
    if not area_counts:
        return []
    ordered = sorted(area_counts.items(), key=lambda item: (-item[1], item[0]))
    return [format_area_label(name) for name, _ in ordered[:3]]


def format_summary_details(phrases, fallback_count, areas):
    detail = "；".join(phrases) if phrases else f"{fallback_count} 项改动"
    if areas:
        detail += f"。主要涉及 {', '.join(areas)}"
    return detail


def summarize_repo(repo):
    category_commits = defaultdict(list)

    for commit in repo["commits"]:
        category = classify_subject(commit["subject"])
        category_commits[category].append(commit)

    bullet_lines = []
    category_labels = {
        "feat": "功能迭代",
        "fix": "问题修复",
        "refactor": "代码整理",
        "chore": "工程维护",
        "other": "其他改动",
    }
    all_areas = summarize_areas(repo["commits"])

    if all_areas:
        bullet_lines.append(
            f"- 变更范围覆盖 {repo['touched_files_count']} 个文件，重点集中在 {', '.join(all_areas)}。"
        )

    for category in ("feat", "fix", "refactor", "chore", "other"):
        commits = category_commits.get(category, [])
        if not commits:
            continue
        phrases = summarize_commit_group(commits)
        areas = summarize_areas(commits)
        detail = format_summary_details(phrases, len(commits), areas)
        bullet_lines.append(f"- {category_labels[category]}方面，主要完成了：{detail}")
        if len(bullet_lines) >= 4:
            break

    build_count = len(category_commits["build"])
    if build_count:
        bullet_lines.append(f"- 同步更新构建产物 {build_count} 次")

    if not bullet_lines and repo["commit_count"]:
        bullet_lines.append(f"- 本周共有 {repo['commit_count']} 次提交")

    return bullet_lines


def render_summary(report):
    active_repos = [repo for repo in report["repositories"] if repo["commit_count"] > 0]
    total_commits = sum(repo["commit_count"] for repo in active_repos)
    lines = [
        "# 本周开发总结",
        "",
        f"统计周期：{report['since']} 至 {report['until']}",
        "",
        "## 总体情况",
        f"- 本周本人真实提交共 {total_commits} 条，涉及 {len(active_repos)} 个仓库。",
    ]

    if not active_repos:
        lines.append("- 本周未扫描到符合条件的非 merge 提交。")
        return "\n".join(lines).rstrip() + "\n"

    repo_names = "、".join(format_repo_name(repo["name"]) for repo in active_repos)
    lines.append(f"- 主要活跃仓库：{repo_names}。")

    themes = []
    if any(classify_subject(commit["subject"]) == "feat" for repo in active_repos for commit in repo["commits"]):
        themes.append("功能迭代")
    if any(classify_subject(commit["subject"]) == "fix" for repo in active_repos for commit in repo["commits"]):
        themes.append("问题修复")
    if any(classify_subject(commit["subject"]) == "refactor" for repo in active_repos for commit in repo["commits"]):
        themes.append("代码整理")
    if any(classify_subject(commit["subject"]) == "build" for repo in active_repos for commit in repo["commits"]):
        themes.append("构建产物同步")
    if themes:
        lines.append(f"- 主要工作类型：{'、'.join(themes)}。")
    if len(report.get("roots", [])) > 1:
        root_names = "、".join(Path(item).name for item in report["roots"])
        lines.append(f"- 本次扫描目录：{root_names}。")

    lines.extend(["", "## 各项目进展"])

    for repo in sorted(active_repos, key=lambda item: item["name"].lower()):
        lines.append(f"### {format_repo_name(repo['name'])}")
        lines.append(f"- 本周提交 {repo['commit_count']} 条。")
        lines.extend(summarize_repo(repo))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def resolve_report_dir(root, report_dir):
    if report_dir:
        return Path(report_dir).resolve()
    return Path("/Users/zpp/Desktop/workspace/git-weekly-report")


def write_weekly_report(report_text, report, root, report_dir):
    target_dir = resolve_report_dir(root, report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{extract_report_date(report)}.md"
    file_path.write_text(report_text, encoding="utf-8")
    return file_path


def write_structured_report(report, root, report_dir):
    target_dir = resolve_report_dir(root, report_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{extract_report_date(report)}.json"
    file_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return file_path


def sync_report_repo(file_paths, report):
    if not file_paths:
        return "[report-sync-skipped] 没有可同步的报告文件"

    repo_dir = file_paths[0].parent
    if not (repo_dir / ".git").exists():
        return "[report-sync-skipped] git-weekly-report 目录不是 git 仓库"

    remote_result = git_run(repo_dir, ["remote"])
    if remote_result.returncode != 0 or not remote_result.stdout.strip():
        return "[report-sync-skipped] 未配置 git 远端仓库"

    git_run(repo_dir, ["add", *[path.name for path in file_paths]])
    staged = git_run(repo_dir, ["diff", "--cached", "--name-only"])
    if staged.returncode != 0:
        return f"[report-sync-failed] {staged.stderr.strip() or 'git diff --cached failed'}"
    if not staged.stdout.strip():
        return "[report-sync-skipped] 报告内容无变化，未提交远端"

    commit_message = f"docs: update weekly report {extract_report_date(report)}"
    commit_result = git_run(repo_dir, ["commit", "-m", commit_message])
    if commit_result.returncode != 0:
        stderr = commit_result.stderr.strip()
        stdout = commit_result.stdout.strip()
        reason = stderr or stdout or "git commit failed"
        return f"[report-sync-failed] {reason}"

    push_result = git_run(repo_dir, ["push"])
    if push_result.returncode != 0:
        fallback_push = git_run(repo_dir, ["push", "-u", "origin", "HEAD"])
        if fallback_push.returncode != 0:
            reason = fallback_push.stderr.strip() or push_result.stderr.strip() or "git push failed"
            return f"[report-sync-failed] {reason}"

    return f"[report-synced] {commit_message}"


def render_markdown(report, max_files, include_inactive):
    active_repos = [repo for repo in report["repositories"] if repo["commit_count"] > 0]
    visible_repos = report["repositories"] if include_inactive else active_repos
    lines = [
        "# Weekly Git Activity",
        "",
        f"- Root: `{report['root']}`",
        f"- Scanned roots: `{', '.join(report.get('roots', [report['root']]))}`",
        f"- Period: `{report['since']}` -> `{report['until']}`",
        f"- Generated: `{report['generated_at']}`",
    ]
    if report["author"]:
        lines.append(f"- Author filter: `{report['author']}`")
    if report.get("author_email"):
        lines.append(f"- Author email filter: `{report['author_email']}`")
    lines.extend(
        [
            f"- Active repos: `{len(active_repos)}` / `{len(report['repositories'])}`",
            f"- Displayed repos: `{len(visible_repos)}`",
            "",
        ]
    )

    if not report["repositories"]:
        lines.append("No git repositories found.")
        return "\n".join(lines)
    if not visible_repos:
        lines.append("No commits found in the selected period.")
        return "\n".join(lines)

    for repo in sorted(visible_repos, key=lambda item: item["name"].lower()):
        lines.append(f"## {repo['name']}")
        lines.append(f"- Path: `{repo['path']}`")
        lines.append(f"- Commits: `{repo['commit_count']}`")
        if repo["authors"]:
            lines.append(f"- Authors: `{', '.join(repo['authors'])}`")
        lines.append("")

        if not repo["commits"]:
            lines.append("No commits in the selected period.")
            lines.append("")
            continue

        by_day = defaultdict(list)
        for commit in repo["commits"]:
            by_day[commit["date"]].append(commit)

        for day in sorted(by_day.keys(), reverse=True):
            lines.append(f"### {day}")
            for commit in by_day[day]:
                lines.append(f"- `{commit['short_sha']}` {commit['subject']}")
                detail = f"  - Author: {commit['author']}"
                if commit["body"]:
                    detail += f" | Body: {commit['body'].replace(chr(10), ' ').strip()}"
                lines.append(detail)
                if commit["files"]:
                    visible_files = commit["files"][:max_files]
                    lines.append(f"  - Files: {', '.join(visible_files)}")
                    remaining = len(commit["files"]) - len(visible_files)
                    if remaining > 0:
                        lines.append(f"  - More files: +{remaining}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root path does not exist: {root}", file=sys.stderr)
        return 1
    if not root.is_dir():
        print(f"Root path is not a directory: {root}", file=sys.stderr)
        return 1

    since = args.since or current_week_start().strftime("%Y-%m-%d %H:%M:%S")
    until = args.until or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    roots = resolve_roots(root, args.extra_root)
    repos = []
    for current_root in roots:
        repos.extend(find_repositories(current_root, args.recursive))
    author_name, author_email = resolve_author_filters(args)
    report = build_report(
        roots,
        repos,
        since,
        until,
        author_name,
        author_email,
        args.include_merges,
        args.current_branch_only,
    )

    if args.format == "json":
        output = json.dumps(report, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        output = render_markdown(report, args.max_files, args.include_inactive)
    else:
        output = render_summary(report)

    if args.write_report:
        file_path = write_weekly_report(output, report, root, args.report_dir)
        written_paths = [file_path]
        json_path = None
        if args.write_json_report:
            json_path = write_structured_report(report, root, args.report_dir)
            written_paths.append(json_path)
        print(output, end="" if output.endswith("\n") else "\n")
        print(f"\n[report-written] {file_path}")
        if json_path:
            print(f"[report-json-written] {json_path}")
        print(sync_report_repo(written_paths, report))
    else:
        print(output, end="" if output.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
