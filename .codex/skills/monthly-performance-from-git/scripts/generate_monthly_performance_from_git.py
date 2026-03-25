#!/usr/bin/env python3

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent
CODEX_HOME = SKILL_ROOT.parent.parent
DESKTOP_ROOT = Path(os.environ.get("DESKTOP_ROOT", Path.home() / "Desktop")).resolve()
DEFAULT_ROOT = DESKTOP_ROOT
SHARED_GLOSSARY_PATH = Path(
    os.environ.get("CODEX_SHARED_GLOSSARY", CODEX_HOME / "memories" / "term-glossary.json")
).resolve()
SUMMARY_SCRIPT_PATH = Path(
    os.environ.get(
        "GIT_WEEKLY_SUMMARY_SCRIPT",
        CODEX_HOME / "skills" / "git-weekly-summary" / "scripts" / "collect_weekly_commits.py",
    )
).resolve()
NOISE_REPOS = {"codex-config", "git-weekly-report"}
NOISE_SUBJECT_PATTERNS = (
    re.compile(r"^chore:\s*sync codex config$", re.IGNORECASE),
    re.compile(r"^docs:\s*update weekly report", re.IGNORECASE),
    re.compile(r"^chore:\s*initial weekly report$", re.IGNORECASE),
)

_SUMMARY_MODULE = None


@dataclass
class ReportContext:
    month_label: str
    title: str
    since: str
    until: str
    root: str
    parent_page_id: str
    standard_page_url: str
    sample_page_url: str


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a monthly performance draft from personal git commits."
    )
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--month")
    parser.add_argument("--author")
    parser.add_argument("--author-email")
    parser.add_argument("--mine", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="json")
    parser.add_argument("--parent-page-id")
    parser.add_argument("--standard-page-url")
    parser.add_argument("--sample-page-url")
    return parser.parse_args(argv)


def git_output(args, cwd=None):
    completed = subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "git command failed")
    return completed.stdout


def resolve_identity(args):
    if args.author or args.author_email:
        return args.author, args.author_email
    if args.mine:
        name = git_output(["git", "config", "--global", "user.name"]).strip()
        email = git_output(["git", "config", "--global", "user.email"]).strip()
        return name or None, email or None
    return None, None


def month_bounds(month_arg, since, until):
    if since and until:
        month_date = datetime.fromisoformat(since.split(" ")[0])
        return since, until, month_date
    if month_arg:
        month_date = datetime.strptime(month_arg, "%Y-%m")
    else:
        month_date = datetime.now()
    start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_date.month == 12:
        next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
    else:
        next_month = month_date.replace(month=month_date.month + 1, day=1)
    end = next_month.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"), month_date


def build_page_title(target_date):
    return f"{target_date.year}年{target_date.month:02d}月个人绩效-git举证汇总"


def load_glossary():
    if not SHARED_GLOSSARY_PATH.exists():
        return {}
    try:
        data = json.loads(SHARED_GLOSSARY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {key: value for key, value in data.items() if isinstance(key, str) and isinstance(value, str)}


def load_summary_module():
    global _SUMMARY_MODULE
    if _SUMMARY_MODULE is not None:
        return _SUMMARY_MODULE
    spec = importlib.util.spec_from_file_location("git_weekly_summary", SUMMARY_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        _SUMMARY_MODULE = None
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _SUMMARY_MODULE = module
    return module


def summarize_commit_phrase(commit):
    if commit.get("summary"):
        return commit["summary"]
    module = load_summary_module()
    if module is not None:
        return module.summarize_commit_phrase(commit)
    subject = commit["subject"]
    match = re.match(r"^(feat|fix|refactor|chore|build|docs|test)(\([^)]+\))?:\s*(.+)$", subject, re.IGNORECASE)
    return match.group(3).strip() if match else subject.strip()


def discover_repos(root):
    repos = []
    for current_root, dirnames, _ in os.walk(root):
        path = Path(current_root)
        if ".git" in dirnames:
            repos.append(path)
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if name not in {".git", "node_modules", "dist", "build", ".next", ".idea"}
            and not name.startswith(".")
        ]
    return sorted(set(repos))


def commit_category(subject):
    lowered = subject.lower()
    for prefix in ("feat", "fix", "test", "docs", "refactor", "build", "chore"):
        if lowered.startswith(prefix):
            return prefix
    return "other"


def is_noise_commit(repo_name, subject, files):
    if repo_name in NOISE_REPOS:
        return True
    for pattern in NOISE_SUBJECT_PATTERNS:
        if pattern.search(subject):
            return True
    if files and all(Path(file_path).suffix in {".md", ".json"} for file_path in files):
        if all("git-weekly-report" in file_path or file_path.startswith("2026-") or file_path[:4].isdigit() for file_path in files):
            return True
    if files and all(file_path.startswith("dist/") for file_path in files):
        return True
    return False


def collect_repo_commits(repo_path, since, until, author_name=None, author_email=None):
    log_args = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"--since={since}",
        f"--until={until}",
        "--no-merges",
        "--pretty=format:%H\t%ad\t%s",
        "--date=short",
    ]
    if author_name:
        log_args.append(f"--author={author_name}")
    if author_email:
        log_args.append(f"--author={author_email}")
    try:
        output = git_output(log_args)
    except RuntimeError as error:
        if "does not have any commits yet" in str(error):
            return []
        raise
    commits = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, date, subject = line.split("\t", 2)
        files_output = git_output(
            ["git", "-C", str(repo_path), "show", "--name-only", "--pretty=format:", "--stat=0", sha]
        )
        files = [item for item in files_output.splitlines() if item.strip()]
        if is_noise_commit(repo_path.name, subject, files):
            continue
        diff_output = git_output(
            ["git", "-C", str(repo_path), "show", "--format=", "--unified=0", "--stat=0", sha]
        )
        commits.append(
            {
                "sha": sha,
                "short_sha": sha[:8],
                "date": date,
                "subject": subject,
                "files": files[:20],
                "diff": diff_output[:4000],
            }
        )
    return commits


def format_project_name(repo_name, glossary):
    return glossary.get(repo_name, repo_name)


def unique_keep_order(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def build_repo_theme(repo_name, commits):
    categories = Counter(commit_category(commit["subject"]) for commit in commits)
    phrases = unique_keep_order(summarize_commit_phrase(commit) for commit in commits)
    return {
        "repo_name": repo_name,
        "commit_count": len(commits),
        "categories": categories,
        "phrases": phrases[:6],
        "key_files": unique_keep_order(
            file_path for commit in commits for file_path in commit["files"] if not file_path.startswith("docs/")
        )[:8],
    }


def build_concise_section(repo_themes, glossary):
    lines = []
    top_repos = repo_themes[:4]
    if not top_repos:
        return lines
    project_names = [f"【{format_project_name(theme['repo_name'], glossary)}】" for theme in top_repos]
    lines.append(f"- 本月工作重点集中在{ '、'.join(project_names) }等主线。")
    for theme in top_repos:
        project_name = format_project_name(theme["repo_name"], glossary)
        summary = "；".join(theme["phrases"][:3])
        lines.append(f"- 【{project_name}】本月主要完成：{summary}。")
    return lines


def select_themes(repo_themes, categories, limit):
    picked = []
    for theme in repo_themes:
        if any(theme["categories"].get(category, 0) for category in categories):
            picked.append(theme)
    return picked[:limit]


def format_evidence_lines(themes, glossary, sentence_limit=3):
    lines = []
    for theme in themes:
        project_name = format_project_name(theme["repo_name"], glossary)
        summary = "；".join(theme["phrases"][:sentence_limit])
        lines.append(f"【{project_name}】{summary}。")
    return lines


def build_score_block(title, evidence_lines, baseline, bonuses):
    total = baseline + sum(bonuses)
    lines = [f"### {title}", "举证："]
    for index, (evidence, bonus) in enumerate(zip(evidence_lines, bonuses), start=1):
        lines.append(f"{index}. {evidence}+{bonus:.1f}")
    formula = "+".join([f"{baseline:.1f}"] + [f"{bonus:.1f}" for bonus in bonuses])
    lines.append(f"得分：{formula}={total:.1f}")
    return lines


def build_sections(repo_themes, glossary, aggressive=False):
    work_themes = select_themes(repo_themes, {"fix", "test", "build"}, 3) or repo_themes[:3]
    process_themes = select_themes(repo_themes, {"docs", "test", "chore"}, 2) or repo_themes[:2]
    progress_themes = select_themes(repo_themes, {"feat", "fix"}, 3) or repo_themes[:3]
    growth_themes = select_themes(repo_themes, {"test", "refactor", "docs"}, 2) or repo_themes[:2]
    value_themes = repo_themes[:2]

    if aggressive:
        bonuses = {
            "工作质量": [0.8, 0.7, 0.6],
            "流程规范": [0.6, 0.4],
            "进度与贡献": [0.7, 0.7, 0.8],
            "成长与分享": [0.4, 0.4],
            "价值共创": [0.7, 0.7, 0.2],
        }
        baseline = 6.5
    else:
        bonuses = {
            "工作质量": [0.7, 0.6, 0.5],
            "流程规范": [0.5, 0.3],
            "进度与贡献": [0.6, 0.6, 0.7],
            "成长与分享": [0.3, 0.3],
            "价值共创": [0.6, 0.6, 0.2],
        }
        baseline = 6.5

    value_lines = format_evidence_lines(value_themes, glossary, sentence_limit=3)
    if repo_themes:
        active_names = "、".join(f"【{format_project_name(theme['repo_name'], glossary)}】" for theme in repo_themes[:4])
        value_lines = [
            f"跨多个仓库推进工作，本月重点覆盖{active_names}等项目，既处理业务需求，也同步跟进测试、文档和流程沉淀。",
            "围绕多个项目持续切换支援，兼顾功能开发、兼容性修复、构建验证和协作文档建设。",
            "补充项目说明和共享资料，帮助后续成员更快理解项目背景与使用方式。",
        ]

    sections = [
        build_score_block("(1) 工作质量", format_evidence_lines(work_themes, glossary), baseline, bonuses["工作质量"]),
        build_score_block("(2) 流程规范", format_evidence_lines(process_themes, glossary, sentence_limit=2), baseline, bonuses["流程规范"]),
        build_score_block("(3) 进度与贡献", format_evidence_lines(progress_themes, glossary), baseline, bonuses["进度与贡献"]),
        build_score_block("(4) 成长与分享", format_evidence_lines(growth_themes, glossary, sentence_limit=2), baseline, bonuses["成长与分享"]),
        build_score_block("(5) 价值共创", value_lines, baseline, bonuses["价值共创"]),
    ]
    return sections


def build_markdown(context, repo_themes, glossary):
    lines = [
        f"# {context.title}",
        f"统计范围：{context.since} 至 {context.until} 的个人 Git 提交。",
        "统计口径：以业务开发、问题修复、测试补充、工程化建设和跨项目支持为主，弱化配置同步、周报产物类噪音提交。",
        "",
        "## 简洁版",
    ]
    lines.extend(build_concise_section(repo_themes, glossary))
    lines.extend(
        [
            "",
            "---",
            "",
            "## 稳妥打分版",
        ]
    )
    for section in build_sections(repo_themes, glossary, aggressive=False):
        lines.extend(section)
        lines.append("")
    lines.extend(["---", "", "## 积极打分版"])
    for section in build_sections(repo_themes, glossary, aggressive=True):
        lines.extend(section)
        lines.append("")
    lines.extend(
        [
            "## 备注",
            "- 以上内容仅基于本月个人 Git 提交整理。",
            "- 培训参与度、周报质量、线下支持、联调协作、线上值守等未体现在 Git 中的事项，可结合实际情况继续补充到正式绩效材料中。",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_context(args):
    if not args.parent_page_id:
        raise ValueError("missing required --parent-page-id")
    since, until, month_date = month_bounds(args.month, args.since, args.until)
    return ReportContext(
        month_label=f"{month_date.year}年{month_date.month:02d}月",
        title=build_page_title(month_date),
        since=since,
        until=until,
        root=str(Path(args.root).resolve()),
        parent_page_id=args.parent_page_id,
        standard_page_url=args.standard_page_url or "",
        sample_page_url=args.sample_page_url or "",
    )


def generate_report(args):
    context = build_context(args)
    glossary = load_glossary()
    author_name, author_email = resolve_identity(args)
    repo_themes = []
    for repo_path in discover_repos(context.root):
        if repo_path.name in NOISE_REPOS:
            continue
        commits = collect_repo_commits(repo_path, context.since, context.until, author_name, author_email)
        if commits:
            repo_themes.append(build_repo_theme(repo_path.name, commits))
    repo_themes.sort(key=lambda item: (-item["commit_count"], item["repo_name"]))
    markdown = build_markdown(context, repo_themes, glossary)
    return {
        "title": context.title,
        "content": markdown,
        "month_label": context.month_label,
        "parent_page_id": context.parent_page_id,
        "standard_page_url": context.standard_page_url,
        "sample_page_url": context.sample_page_url,
        "active_repos": [theme["repo_name"] for theme in repo_themes],
    }


def main():
    args = parse_args()
    report = generate_report(args)
    if args.format == "markdown":
        sys.stdout.write(report["content"])
        return
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
