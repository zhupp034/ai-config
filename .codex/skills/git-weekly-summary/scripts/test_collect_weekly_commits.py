import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("collect_weekly_commits.py")
SPEC = importlib.util.spec_from_file_location("git_weekly_summary", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GitWeeklySummaryTests(unittest.TestCase):
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

        self.assertTrue(any("beautyEnabled" in phrase for phrase in phrases))
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


if __name__ == "__main__":
    unittest.main()
