import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("generate_weekly_report_summary.py")
SPEC = importlib.util.spec_from_file_location("weekly_report_summary", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WeeklyReportSummaryTests(unittest.TestCase):
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
            any("initialize ai project docs" in item or "add ai collaboration audit docs" in item for item in completed_sections["技术优化"])
        )


if __name__ == "__main__":
    unittest.main()
