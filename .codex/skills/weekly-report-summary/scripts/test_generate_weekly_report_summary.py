import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("generate_weekly_report_summary.py")
SPEC = importlib.util.spec_from_file_location("weekly_report_summary", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WeeklyReportSummaryTests(unittest.TestCase):
    def test_default_paths_should_be_derived_from_desktop_and_codex_roots(self):
        self.assertEqual(MODULE.DESKTOP_ROOT / "gitlab", MODULE.GITLAB_ROOT)
        self.assertEqual(MODULE.WORKSPACE_ROOT / "git-weekly-report", MODULE.GIT_WEEKLY_REPORT_DIR)
        self.assertEqual(MODULE.WORKSPACE_ROOT / "weekly-report", MODULE.WEEKLY_REPORT_OUTPUT_DIR)
        self.assertEqual(MODULE.WORKSPACE_ROOT / "weekly-report-notes", MODULE.WEEKLY_REPORT_NOTES_DIR)
        self.assertTrue(MODULE.GIT_WEEKLY_SUMMARY_SCRIPT.name.endswith("collect_weekly_commits.py"))
        self.assertTrue(MODULE.ZENTAO_WEEKLY_SCRIPT.name.endswith("fetch_zentao_weekly.py"))

    def test_build_completed_sections_should_prefer_repo_themes(self):
        active_repos = [
            {
                "name": "interact-classroom",
                "themes": [
                    {
                        "title": "websocket",
                        "categories": ["fix", "feat"],
                        "commit_count": 2,
                        "commit_shas": ["aaaaaaaa", "bbbbbbbb"],
                        "key_files": ["src/utils/websocket.ts"],
                        "summaries": [
                            "调整 WebSocket 连接超时和重连调度，补强断线重连稳定性。",
                            "补充断线清理和重连流程测试，覆盖 reconnect 事件处理。",
                        ],
                    }
                ],
                "commits": [
                    {"subject": "fix: update", "files": ["src/utils/websocket.ts"], "diff": ""},
                    {"subject": "feat: reconnect test", "files": ["src/utils/websocket.ts"], "diff": ""},
                ],
            }
        ]

        completed_sections = MODULE.build_completed_sections(active_repos, [])

        self.assertIn("补充断线清理和重连流程测试，覆盖 reconnect 事件处理。", completed_sections["需求开发"])
        self.assertIn("调整 WebSocket 连接超时和重连调度，补强断线重连稳定性。", completed_sections["问题修复"])

    def test_build_completed_sections_should_prefer_theme_analysis_fields(self):
        active_repos = [
            {
                "name": "interact-classroom",
                "themes": [
                    {
                        "title": "websocket",
                        "categories": ["fix", "feat"],
                        "commit_count": 2,
                        "commit_shas": ["aaaaaaaa", "bbbbbbbb"],
                        "key_files": ["src/utils/websocket.ts"],
                        "summaries": ["旧的 summary，不应该优先使用。"],
                        "analysis": {
                            "completed_sections": {
                                "需求开发": ["补充断线重连测试链路，覆盖 reconnect 事件处理。"],
                                "问题修复": ["调整 WebSocket 连接超时和重连调度逻辑。"],
                                "技术优化": ["梳理重连相关状态清理流程，减少重复触发。"],
                            }
                        },
                    }
                ],
                "commits": [],
            }
        ]

        completed_sections = MODULE.build_completed_sections(active_repos, [])

        self.assertIn("补充断线重连测试链路，覆盖 reconnect 事件处理。", completed_sections["需求开发"])
        self.assertIn("调整 WebSocket 连接超时和重连调度逻辑。", completed_sections["问题修复"])
        self.assertIn("梳理重连相关状态清理流程，减少重复触发。", completed_sections["技术优化"])
        self.assertNotIn("旧的 summary，不应该优先使用。", completed_sections["问题修复"])

    def test_build_project_sections_should_render_repo_themes(self):
        glossary = {}
        active_repos = [
            {
                "name": "interact-classroom",
                "commit_count": 2,
                "themes": [
                    {
                        "title": "websocket",
                        "categories": ["fix", "feat"],
                        "commit_count": 2,
                        "commit_shas": ["aaaaaaaa", "bbbbbbbb"],
                        "key_files": [
                            "src/utils/websocket.ts",
                            "src/hooks/useCommonSocketListeners.tsx",
                        ],
                        "summaries": [
                            "调整 WebSocket 连接超时和重连调度，补强断线重连稳定性。",
                            "补充断线清理和重连流程测试，覆盖 reconnect 事件处理。",
                        ],
                    }
                ],
                "commits": [],
            }
        ]

        sections = MODULE.build_project_sections(active_repos, glossary)

        joined = "\n".join(sections[0][1])
        self.assertIn("WebSocket", joined)
        self.assertIn("src/utils/websocket.ts", joined)

    def test_build_project_sections_should_prefer_theme_analysis_project_summary(self):
        glossary = {}
        active_repos = [
            {
                "name": "interact-classroom",
                "commit_count": 2,
                "themes": [
                    {
                        "title": "websocket",
                        "categories": ["fix", "feat"],
                        "commit_count": 2,
                        "commit_shas": ["aaaaaaaa", "bbbbbbbb"],
                        "key_files": ["src/utils/websocket.ts"],
                        "summaries": ["旧 summary"],
                        "analysis": {
                            "project_summary": [
                                "本周重点处理课堂侧 WebSocket 重连与状态清理逻辑。",
                                "同步补充断线重连测试，覆盖 reconnect 关键路径。"
                            ],
                            "risks": ["弱网场景仍需继续观察重连稳定性。"],
                            "next_steps": ["继续补充弱网和断网恢复验证。"],
                            "reflections": ["重连链路拆清后，问题定位效率明显提升。"]
                        },
                    }
                ],
                "commits": [],
            }
        ]

        sections = MODULE.build_project_sections(active_repos, glossary)

        joined = "\n".join(sections[0][1])
        self.assertIn("本周重点处理课堂侧 WebSocket 重连与状态清理逻辑。", joined)
        self.assertNotIn("旧 summary", joined)

    def test_build_project_sections_should_merge_identical_repo_summaries(self):
        glossary = {}
        active_repos = [
            {
                "name": "micro-frontends-beike",
                "commit_count": 2,
                "themes": [
                    {
                        "title": "依赖配置（package.json） / pnpm-lock.yaml",
                        "analysis": {
                            "project_summary": [
                                "处理了 React 与类型约束相关问题，并同步调整 Babel 实现细节。"
                            ]
                        },
                    }
                ],
                "commits": [],
            },
            {
                "name": "micro-frontends-web",
                "commit_count": 2,
                "themes": [
                    {
                        "title": "依赖配置（package.json） / pnpm-lock.yaml",
                        "analysis": {
                            "project_summary": [
                                "处理了 React 与类型约束相关问题，并同步调整 Babel 实现细节。"
                            ]
                        },
                    }
                ],
                "commits": [],
            },
        ]

        sections = MODULE.build_project_sections(active_repos, glossary)

        self.assertEqual(1, len(sections))
        self.assertEqual("micro-frontends-beike / micro-frontends-web", sections[0][0])
        self.assertEqual(
            ["- 处理了 React 与类型约束相关问题，并同步调整 Babel 实现细节。"],
            sections[0][1],
        )

    def test_theme_analysis_risk_and_next_steps_should_suppress_generic_fallbacks(self):
        active_repos = [
            {
                "name": "interact-classroom",
                "commit_count": 2,
                "themes": [
                    {
                        "title": "websocket reconnect",
                        "categories": ["fix"],
                        "commit_count": 2,
                        "commit_shas": ["aaaaaaaa", "bbbbbbbb"],
                        "key_files": ["src/utils/websocket.ts"],
                        "analysis": {
                            "risks": ["会议系统与课堂侧的断线重连相关改动仍需继续关注联测稳定性和线上表现。"],
                            "next_steps": ["继续跟进会议系统和课堂侧断线重连相关优化，补充联测和稳定性验证。"],
                        },
                    }
                ],
                "commits": [
                    {"subject": "fix: reconnect", "files": ["src/utils/websocket.ts"], "diff": ""}
                ],
            },
            {
                "name": "cnstrong-WebRTC",
                "commit_count": 1,
                "themes": [],
                "commits": [],
            },
        ]

        risk_items = MODULE.build_risk_section(active_repos, ["会议联测进行中"])
        next_plan_items = MODULE.build_next_plan_section(active_repos, ["AI 禅道调研"])

        self.assertEqual(
            ["会议系统与课堂侧的断线重连相关改动仍需继续关注联测稳定性和线上表现。"],
            risk_items,
        )
        self.assertEqual(
            ["继续跟进会议系统和课堂侧断线重连相关优化，补充联测和稳定性验证。"],
            next_plan_items,
        )

    def test_docs_only_repo_should_not_fall_back_to_regular_maintenance(self):
        repo = {
            "name": "cnstrong-WebRTC",
            "commits": [
                {
                    "subject": "docs: initialize ai project docs",
                    "files": ["README.md", "docs/SDK_USAGE.md"],
                },
                {
                    "subject": "docs: add ai collaboration audit docs",
                    "files": ["AGENTS.md", "docs/AI_COLLAB_WORKFLOW.md"],
                },
            ],
        }

        lines = MODULE.render_repo_summary(repo)

        self.assertFalse(any("常规维护" in line for line in lines))
        self.assertTrue(any("文档" in line or "AI" in line for line in lines))

    def test_business_issue_notes_should_flow_into_fix_and_risk_sections(self):
        active_repos = []
        extra_notes = ["排查作业报告奖品，批改状态显示不对的问题"]

        completed_sections = MODULE.build_completed_sections(active_repos, extra_notes)
        risk_items = MODULE.build_risk_section(active_repos, extra_notes)

        self.assertIn("排查作业报告奖品，批改状态显示不对的问题", completed_sections["问题修复"])
        self.assertTrue(any("批改状态显示不对" in item for item in risk_items))

    def test_docs_commits_should_be_classified_as_optimization_not_demand(self):
        active_repos = [
            {
                "name": "cnstrong-WebRTC",
                "commits": [
                    {
                        "subject": "docs: initialize ai project docs",
                        "files": ["README.md", "docs/SDK_USAGE.md"],
                    },
                    {
                        "subject": "docs: add ai collaboration audit docs",
                        "files": ["AGENTS.md", "docs/AI_COLLAB_WORKFLOW.md"],
                    },
                ],
            }
        ]

        completed_sections = MODULE.build_completed_sections(active_repos, [])

        self.assertEqual([], completed_sections["需求开发"])
        self.assertTrue(
            any("README" in item or "SDK_USAGE" in item or "AI_COLLAB_WORKFLOW" in item for item in completed_sections["技术优化"])
        )

    def test_completed_sections_should_humanize_commit_style_and_english_subjects(self):
        active_repos = [
            {
                "name": "interact-classroom",
                "commits": [
                    {
                        "subject": "fix: reload page when not in mobile webview",
                        "files": ["src/pages/Meeting/RtcInitMeetingCom.tsx"],
                        "diff": "",
                    },
                    {
                        "subject": "refactor: move htmlEntitiesToEmoji to utils",
                        "files": ["src/utils/index.ts", "src/components/ChatMessage/index.tsx"],
                        "diff": "",
                    },
                ],
            }
        ]

        completed_sections = MODULE.build_completed_sections(active_repos, [])

        self.assertIn("补充特定场景下的页面自动刷新处理", completed_sections["问题修复"])
        self.assertIn("将表情转换能力下沉到工具层", completed_sections["技术优化"])

    def test_repo_summary_should_not_expose_raw_commit_prefixes(self):
        repo = {
            "name": "repository",
            "commits": [
                {
                    "subject": "feat(repository): add zxxk entry and dialog flow",
                    "files": ["src/page/index.tsx", "src/utils/dialog.ts"],
                    "diff": "",
                },
                {
                    "subject": "fix(api): update whitelist endpoint",
                    "files": ["src/services/resource.ts"],
                    "diff": "",
                },
            ],
        }

        lines = MODULE.render_repo_summary(repo)

        joined = "\n".join(lines)
        self.assertNotIn("feat(", joined)
        self.assertNotIn("fix(", joined)


if __name__ == "__main__":
    unittest.main()
