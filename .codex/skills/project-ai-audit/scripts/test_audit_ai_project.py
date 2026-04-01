import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
AUDIT_SCRIPT = SCRIPT_DIR / "audit_ai_project.sh"


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_initialized_baseline(root: Path) -> None:
    write_file(root, "README.md", "# Repo\n\n## 文档导航\n")
    write_file(
        root,
        "AGENTS.md",
        "\n".join(
            [
                "# AGENTS.md",
                "## AI 工作流",
                "1. 计划",
                "2. 测试",
                "3. 交付",
                "4. 提交前执行 skills/md-doc-sync/SKILL.md",
                "## 项目内关键 Markdown 文档",
                "- README.md",
                "- TESTING.md",
            ]
        ),
    )
    write_file(root, "TESTING.md", "# TESTING.md\n- test: pnpm test\n- lint: pnpm lint\n- build: pnpm build\n")
    write_file(root, "docs/AI_COLLAB_WORKFLOW.md", "# AI_COLLAB_WORKFLOW.md\n- Markdown\n- skills/md-doc-sync/SKILL.md\n")
    write_file(root, "docs/TASK_RECORD_TEMPLATE.md", "# TASK_RECORD_TEMPLATE.md\n- 同步更新文档\n- 未更新原因\n")
    write_file(root, "docs/TEST_CASE_MATRIX.md", "# TEST_CASE_MATRIX.md\n")
    write_file(root, "docs/DELIVERY_REPORT_TEMPLATE.md", "# DELIVERY_REPORT_TEMPLATE.md\n")
    write_file(root, "docs/GIT_COMMIT_GUIDE.md", "# GIT_COMMIT_GUIDE.md\n")
    write_file(root, "docs/LINT_AND_BUILD_KNOWN_ISSUES.md", "# LINT_AND_BUILD_KNOWN_ISSUES.md\n")
    write_file(
        root,
        "skills/md-doc-sync/SKILL.md",
        "---\nname: md-doc-sync\ndescription: test\n---\n",
    )


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


class ProjectAiAuditScriptTests(unittest.TestCase):
    def test_audit_should_recommend_init_when_baseline_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_file(repo_root, "src/index.ts", "export const app = true;\n")

            result = run_command("bash", str(AUDIT_SCRIPT), str(repo_root))

            self.assertEqual(2, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("baseline_recommended_follow_up: project-ai-init", result.stdout)
            self.assertIn("recommended_next_action: project-ai-init", result.stdout)

    def test_audit_should_keep_manual_refinement_for_mature_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_initialized_baseline(repo_root)
            write_file(repo_root, "src/router.ts", "export const routes = [];\n")

            result = run_command("bash", str(AUDIT_SCRIPT), str(repo_root))

            self.assertEqual(1, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("baseline_recommended_follow_up: project-ai-audit", result.stdout)
            self.assertIn("recommended_next_action: manual_refinement", result.stdout)
            self.assertIn("no real task records found", result.stdout)

    def test_audit_scope_should_follow_selected_app_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            app_a = repo_root / "apps/app-a"
            app_b = repo_root / "apps/app-b"
            write_initialized_baseline(app_a)
            write_file(app_a, "src/index.ts", "export const appA = true;\n")
            write_initialized_baseline(app_b)
            write_file(app_b, "docs/tasks/task-1.md", "# task\n")

            result = run_command("bash", str(AUDIT_SCRIPT), str(repo_root), "--scope", "apps/app-a")

            self.assertEqual(1, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("scope: apps/app-a", result.stdout)
            self.assertIn("task_record_count: 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
