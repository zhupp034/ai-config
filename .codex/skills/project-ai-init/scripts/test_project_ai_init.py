import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CHECK_SCRIPT = SCRIPT_DIR / "check_ai_init.sh"
AUTO_INIT_SCRIPT = SCRIPT_DIR / "auto_init_docs.sh"


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
            ]
        ),
    )
    write_file(root, "TESTING.md", "# TESTING.md\n")
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


class ProjectAiInitScriptTests(unittest.TestCase):
    def test_check_should_ignore_generic_http_calls_for_integrations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_initialized_baseline(repo_root)
            write_file(
                repo_root,
                "src/index.ts",
                "const client = axios.create({ baseURL: '/api' });\nfetch('/api/orders');\n",
            )

            result = run_command("bash", str(CHECK_SCRIPT), str(repo_root))

            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("detected_integrations: no", result.stdout)
            self.assertNotIn("docs/INTEGRATION_DEPENDENCIES.md", result.stdout)

    def test_check_should_detect_explicit_integration_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_initialized_baseline(repo_root)
            write_file(repo_root, "config/openapi/order-openapi.json", "{\n  \"openapi\": \"3.0.0\"\n}\n")

            result = run_command("bash", str(CHECK_SCRIPT), str(repo_root))

            self.assertEqual(1, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("detected_integrations: yes", result.stdout)
            self.assertIn("docs/INTEGRATION_DEPENDENCIES.md", result.stdout)

    def test_check_scope_should_ignore_other_apps_in_monorepo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            app_a = repo_root / "apps/app-a"
            app_b = repo_root / "apps/app-b"
            write_initialized_baseline(app_a)
            write_file(app_a, "src/index.ts", "fetch('/local-api');\n")
            write_initialized_baseline(app_b)
            write_file(app_b, "sdk/client.ts", "export const sdkClient = true;\n")

            result = run_command("bash", str(CHECK_SCRIPT), str(repo_root), "--scope", "apps/app-a")

            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("scope: apps/app-a", result.stdout)
            self.assertIn("detected_integrations: no", result.stdout)

    def test_check_should_recommend_audit_for_mature_repo_with_small_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_initialized_baseline(repo_root)
            write_file(repo_root, "src/router.ts", "export const routes = [];\n")

            result = run_command("bash", str(CHECK_SCRIPT), str(repo_root))

            self.assertEqual(1, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("state: **partial**", result.stdout)
            self.assertIn("recommended_follow_up: project-ai-audit", result.stdout)

    def test_check_should_keep_init_follow_up_for_not_initialized_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_file(repo_root, "src/index.ts", "export const app = true;\n")

            result = run_command("bash", str(CHECK_SCRIPT), str(repo_root))

            self.assertEqual(2, result.returncode, msg=result.stdout + result.stderr)
            self.assertIn("state: **not_initialized**", result.stdout)
            self.assertIn("recommended_follow_up: project-ai-init", result.stdout)

    def test_auto_init_should_create_docs_inside_scope_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            app_root = repo_root / "apps/app-a"
            write_file(app_root, "README.md", "# app-a\n")
            write_file(app_root, "package.json", "{\n  \"name\": \"app-a\"\n}\n")

            result = run_command(
                "bash",
                str(AUTO_INIT_SCRIPT),
                str(repo_root),
                "apply",
                "--scope",
                "apps/app-a",
            )

            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
            self.assertTrue((app_root / "AGENTS.md").exists())
            self.assertTrue((app_root / "docs/AI_COLLAB_WORKFLOW.md").exists())
            self.assertFalse((repo_root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
