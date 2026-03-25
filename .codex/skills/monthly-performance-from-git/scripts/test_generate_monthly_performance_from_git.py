import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("generate_monthly_performance_from_git.py")
SPEC = importlib.util.spec_from_file_location("monthly_performance_from_git", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MonthlyPerformanceFromGitTests(unittest.TestCase):
    def test_parse_args_should_not_bake_in_notion_targets(self):
        args = MODULE.parse_args([])

        self.assertIsNone(args.parent_page_id)
        self.assertIsNone(args.standard_page_url)
        self.assertIsNone(args.sample_page_url)

    def test_build_page_title_should_use_month_format(self):
        title = MODULE.build_page_title(MODULE.datetime(2026, 3, 25))
        self.assertEqual("2026年03月个人绩效-git举证汇总", title)

    def test_is_noise_commit_should_filter_sync_and_report_noise(self):
        self.assertTrue(MODULE.is_noise_commit("codex-config", "chore: sync codex config", [".codex/config.toml"]))
        self.assertTrue(MODULE.is_noise_commit("workspace", "docs: update weekly report 2026-03-20", ["2026-03-20.md", "2026-03-20.json"]))
        self.assertTrue(MODULE.is_noise_commit("interact-classroom", "build: dist", ["dist/index.html", "dist/umi.js"]))
        self.assertFalse(MODULE.is_noise_commit("repository", "fix(repository): 统一试卷入口跳转参数", ["src/utils/zxxk.ts"]))

    def test_build_repo_theme_should_keep_unique_phrases_and_categories(self):
        theme = MODULE.build_repo_theme(
            "repository",
            [
                {"subject": "feat: add zxxk entry", "summary": "新增学科网入口和弹窗链路。", "files": ["src/a.ts"]},
                {"subject": "fix: align zxxk visibility", "summary": "统一访问权限和跳转口径。", "files": ["src/b.ts"]},
                {"subject": "fix: align zxxk visibility", "summary": "统一访问权限和跳转口径。", "files": ["src/b.ts"]},
            ],
        )
        self.assertEqual(3, theme["commit_count"])
        self.assertEqual(["新增学科网入口和弹窗链路。", "统一访问权限和跳转口径。"], theme["phrases"])
        self.assertEqual(1, theme["categories"]["feat"])
        self.assertEqual(2, theme["categories"]["fix"])

    def test_build_markdown_should_render_three_versions(self):
        context = MODULE.ReportContext(
            month_label="2026年03月",
            title="2026年03月个人绩效-git举证汇总",
            since="2026-03-01 00:00:00",
            until="2026-03-25 23:59:59",
            root="/tmp/root",
            parent_page_id="parent-page-id",
            standard_page_url="https://example.com/standard",
            sample_page_url="https://example.com/sample",
        )
        repo_themes = [
            {
                "repo_name": "interact-classroom",
                "commit_count": 5,
                "categories": {"fix": 3, "feat": 2, "test": 1},
                "phrases": ["修复会议重连消息闪烁。", "补充断线重连测试。", "调整录像链路逻辑。"],
                "key_files": ["src/layouts/MeetingLayout.tsx"],
            },
            {
                "repo_name": "repository",
                "commit_count": 3,
                "categories": {"feat": 2, "fix": 1},
                "phrases": ["新增学科网入口和弹窗链路。", "统一访问权限和跳转口径。"],
                "key_files": ["src/utils/zxxk.ts"],
            },
        ]

        markdown = MODULE.build_markdown(context, repo_themes, {"interact-classroom": "互动课堂、会议主项目", "repository": "资源库web端"})

        self.assertIn("## 简洁版", markdown)
        self.assertIn("## 稳妥打分版", markdown)
        self.assertIn("## 积极打分版", markdown)
        self.assertIn("【互动课堂、会议主项目】", markdown)
        self.assertIn("【资源库web端】", markdown)

    def test_generate_report_should_require_parent_page_id(self):
        args = MODULE.parse_args(["--month", "2026-03", "--mine"])

        with self.assertRaises(ValueError):
            MODULE.generate_report(args)


if __name__ == "__main__":
    unittest.main()
