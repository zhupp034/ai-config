import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("collect_weekly_commits.py")
SPEC = importlib.util.spec_from_file_location("git_weekly_summary", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GitWeeklySummaryTests(unittest.TestCase):
    def test_build_repo_themes_should_aggregate_theme_analysis_from_commit_analysis(self):
        repo = {
            "name": "interact-classroom",
            "commits": [
                {
                    "sha": "a" * 40,
                    "short_sha": "aaaaaaaa",
                    "subject": "fix: reconnect cleanup",
                    "files": ["src/utils/websocket.ts"],
                    "analysis": {
                        "summary": "修复重连过程中的状态清理与再次调度问题。",
                        "files": [
                            {
                                "path": "src/utils/websocket.ts",
                                "summary": "调整重连前的状态清理顺序。",
                                "changes": ["重连前先清理 socket 状态。"],
                                "impact": "减少重复重连带来的状态错乱。",
                            }
                        ],
                        "risks": ["弱网场景仍需继续观察重连稳定性。"],
                    },
                },
                {
                    "sha": "b" * 40,
                    "short_sha": "bbbbbbbb",
                    "subject": "feat: reconnect test",
                    "files": ["src/hooks/useCommonSocketListeners.tsx"],
                    "analysis": {
                        "summary": "补充断线重连测试链路，覆盖 reconnect 关键事件处理。",
                        "files": [
                            {
                                "path": "src/hooks/useCommonSocketListeners.tsx",
                                "summary": "补充 reconnect 测试回调。",
                                "changes": ["增加 reconnect 相关测试用例。"],
                                "impact": "便于回归验证重连链路。",
                            }
                        ],
                        "risks": [],
                    },
                },
            ],
        }

        themes = MODULE.build_repo_themes(repo)

        self.assertEqual(1, len(themes))
        analysis = themes[0]["analysis"]
        self.assertIn("补充断线重连测试链路，覆盖 reconnect 关键事件处理。", analysis["completed_sections"]["需求开发"])
        self.assertIn("修复重连过程中的状态清理与再次调度问题。", analysis["completed_sections"]["问题修复"])
        self.assertEqual(
            [
                "修复重连过程中的状态清理与再次调度问题。",
                "补充断线重连测试链路，覆盖 reconnect 关键事件处理。",
            ],
            analysis["project_summary"],
        )
        self.assertEqual(["弱网场景仍需继续观察重连稳定性。"], analysis["risks"])
        self.assertEqual([], analysis["reflections"])
        self.assertEqual([], analysis["next_steps"])

    def test_build_repo_themes_should_group_related_commits_for_downstream_consumption(self):
        repo = {
            "name": "interact-classroom",
            "commits": [
                {
                    "sha": "a" * 40,
                    "short_sha": "aaaaaaaa",
                    "subject": "fix: update",
                    "files": ["src/utils/websocket.ts", "src/layouts/MeetingLayout.tsx"],
                    "analysis": {
                        "summary": "调整 WebSocket 连接超时和重连调度，补强断线重连稳定性。",
                        "files": [],
                        "risks": [],
                    },
                },
                {
                    "sha": "b" * 40,
                    "short_sha": "bbbbbbbb",
                    "subject": "feat: reconnect test",
                    "files": ["src/utils/websocket.ts", "src/hooks/useCommonSocketListeners.tsx"],
                    "analysis": {
                        "summary": "补充断线清理和重连流程测试，覆盖 reconnect 事件处理。",
                        "files": [],
                        "risks": [],
                    },
                },
            ],
        }

        themes = MODULE.build_repo_themes(repo)

        self.assertEqual(1, len(themes))
        self.assertEqual(2, themes[0]["commit_count"])
        self.assertIn("websocket", themes[0]["title"].lower())
        self.assertIn("aaaaaaaa", themes[0]["commit_shas"])

    def test_ai_analyzed_repo_should_render_full_commit_information(self):
        repo = {
            "name": "demo",
            "path": "/tmp/demo",
            "commit_count": 1,
            "authors": ["tester"],
            "touched_files_count": 2,
            "commits": [
                {
                    "short_sha": "abc12345",
                    "date": "2026-03-18",
                    "subject": "fix: update",
                    "files": ["src/browser/index.ts", "src/config.ts"],
                    "analysis": {
                        "summary": "将 beautyEnabled 的默认值改为读取配置项，并补充浏览器侧兼容处理。",
                        "files": [
                            {
                                "path": "src/browser/index.ts",
                                "summary": "把 beautyEnabled 从硬编码 false 调整为读取 config.beautyEnabled。",
                                "changes": [
                                    "删除本地默认值 false。",
                                    "改为通过 Boolean(config.beautyEnabled) 统一计算开关。"
                                ],
                                "impact": "避免浏览器场景下美颜开关行为和配置不一致。"
                            }
                        ],
                        "risks": ["仍需关注未传 config.beautyEnabled 时的默认行为。"]
                    },
                }
            ],
        }

        lines = MODULE.summarize_repo(repo)

        joined = "\n".join(lines)
        self.assertIn("beautyEnabled", joined)
        self.assertIn("src/browser/index.ts", joined)
        self.assertIn("默认值", joined)

    def test_generic_commit_message_should_use_diff_hints(self):
        commits = [
            {
                "subject": "chore: update",
                "files": ["src/browser/index.ts", "tests/ci.test.mjs"],
                "diff": """
+ const beautyEnabled = Boolean(config.beautyEnabled);
- const beautyEnabled = false;
 expect(result.beautyEnabled).toBe(true);
                """,
            }
        ]

        phrases = MODULE.summarize_commit_group(commits)

        self.assertTrue(any("beautyEnabled" in phrase and "config.beautyEnabled" in phrase for phrase in phrases))
        self.assertFalse(any(phrase.strip() == "update" for phrase in phrases))

    def test_repo_summary_should_not_repeat_vague_subject_when_diff_has_real_change(self):
        repo = {
            "commit_count": 1,
            "touched_files_count": 2,
            "commits": [
                {
                    "subject": "refactor: cleanup",
                    "files": ["src/utils/htmlEntitiesToEmoji.ts", "src/hooks/useMessage.ts"],
                    "diff": """
- export const convert = () => {};
+ export const htmlEntitiesToEmoji = () => {};
+ logger.info('rtc stream');
                    """,
                }
            ],
        }

        lines = MODULE.summarize_repo(repo)

        joined = "\n".join(lines)
        self.assertIn("htmlEntitiesToEmoji", joined)
        self.assertNotIn("cleanup", joined)

    def test_diff_assignment_change_should_summarize_before_after_content(self):
        phrase = MODULE.summarize_commit_phrase(
            {
                "subject": "fix: update",
                "files": ["src/browser/index.ts"],
                "diff": """
- const beautyEnabled = false;
+ const beautyEnabled = Boolean(config.beautyEnabled);
                """,
            }
        )

        self.assertIn("beautyEnabled", phrase)
        self.assertIn("config.beautyEnabled", phrase)
        self.assertNotIn("update", phrase)

    def test_build_report_should_include_stable_schema_metadata(self):
        report = MODULE.build_report(
            roots=[Path("/tmp/gitlab")],
            repos=[],
            since="2026-03-17 00:00:00",
            until="2026-03-18 18:00:00",
            author_name="tester",
            author_email="tester@example.com",
            include_merges=False,
            current_branch_only=False,
        )

        self.assertEqual("git-weekly-summary", report["report_type"])
        self.assertEqual("1.0", report["schema_version"])
        self.assertEqual("rule", report["analysis_mode"])

    def test_resolve_report_dir_should_default_to_workspace_git_weekly_report(self):
        resolved = MODULE.resolve_report_dir(Path("/tmp/gitlab"), None)
        self.assertEqual(MODULE.WORKSPACE_ROOT / "git-weekly-report", resolved)


if __name__ == "__main__":
    unittest.main()
