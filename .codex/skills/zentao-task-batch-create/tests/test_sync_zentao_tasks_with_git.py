from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_zentao_tasks_with_git.py"
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location("sync_zentao_tasks_with_git", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


TASK_PAGE_HTML = """
<form id='myTaskForm'>
  <table>
    <tbody>
      <tr>
        <td class="c-id">
          <div class="checkbox-primary">
            <input type='checkbox' name='taskIDList[]' value='138598' />
            <label></label>
          </div>
          138598
        </td>
        <td class='c-project' title="学科网对接V1.0"><a href='/pro/project-browse-1205.html'>学科网对接V1.0</a></td>
        <td class='c-name' title='资源库新增学科网tab-校本资源库'>
          <a href='/pro/task-view-138598.html'>资源库新增学科网tab-校本资源库</a>
        </td>
        <td class="c-assignedTo has-btn">
          <a href='/pro/task-assignTo-1205-138598.html?onlybody=yes' class='iframe btn btn-icon-left btn-sm'>
            <span title='朋朋 朱' class='text-red'>朋朋 朱</span>
          </a>
        </td>
        <td class='c-hours'>1</td>
        <td class='c-hours'>0</td>
        <td class='c-hours'>1</td>
        <td class='c-status'>
          <span class='status-task status-wait'> 未开始</span>
        </td>
        <td class='c-actions'>
          <a href='/pro/task-finish-138598.html?onlybody=yes' class='btn iframe' title='完成'><i class='icon-task-finish icon-checked'></i></a>
        </td>
      </tr>
      <tr>
        <td class="c-id">
          <div class="checkbox-primary">
            <input type='checkbox' name='taskIDList[]' value='136658' />
            <label></label>
          </div>
          136658
        </td>
        <td class='c-project' title="课堂项目"><a href='/pro/project-browse-1186.html'>课堂项目</a></td>
        <td class='c-name' title='冒烟'>
          <a href='/pro/task-view-136658.html'>冒烟</a>
        </td>
        <td class="c-assignedTo has-btn">
          <a href='/pro/task-assignTo-1186-136658.html?onlybody=yes' class='iframe btn btn-icon-left btn-sm'>
            <span title='朋朋 朱' class='text-red'>朋朋 朱</span>
          </a>
        </td>
        <td class='c-hours'>8</td>
        <td class='c-hours'>8</td>
        <td class='c-hours'>0</td>
        <td class='c-status'>
          <span class='status-task status-done'> 已完成</span>
        </td>
        <td class='c-actions'>
          <a href='/pro/task-close-136658.html?onlybody=yes' class='btn iframe' title='关闭'><i class='icon-task-close icon-off'></i></a>
        </td>
      </tr>
    </tbody>
  </table>
  <ul class='pager' data-page-cookie='pagerMyTask' data-rec-total='1605' data-rec-per-page='20' data-page='1' data-link-creator='/pro/my-task-assignedTo-id_desc-1605-{recPerPage}-{page}.html'></ul>
</form>
"""


FINISH_PAGE_HTML = """
<form method='post' enctype='multipart/form-data' target='hiddenwin'>
  <table class='table table-form'>
    <tr>
      <th>本次消耗</th>
      <td><input type='text' name='currentConsumed' id='currentConsumed' value='0' class='form-control' /></td>
    </tr>
    <tr>
      <th>总计消耗</th>
      <td><input type='hidden' name='consumed' id='consumed' value='0' /></td>
    </tr>
    <tr>
      <th>指派</th>
      <td>
        <select name='assignedTo' id='assignedTo' class='form-control chosen'>
          <option value='chenfeng1'>C:锋 陈</option>
          <option value='zhupengpeng' selected='selected'>Z:朋朋 朱</option>
        </select>
      </td>
    </tr>
    <tr>
      <th>实际完成</th>
      <td><input type='text' name='finishedDate' id='finishedDate' value='2026-03-12' class='form-control form-date' /></td>
    </tr>
    <tr class='hide'>
      <th>任务状态</th>
      <td><input type='hidden' name='status' id='status' value='done' /></td>
    </tr>
    <tr>
      <th>备注</th>
      <td><textarea name='comment' id='comment' rows='6' class='w-p98'></textarea></td>
    </tr>
  </table>
</form>
"""


class SyncZenTaoTasksWithGitTest(unittest.TestCase):
    def test_parse_task_rows_extracts_pending_task_details(self) -> None:
        tasks = MODULE.parse_task_rows(TASK_PAGE_HTML)
        self.assertEqual(len(tasks), 2)
        task = tasks[0]
        self.assertEqual(task.task_id, 138598)
        self.assertEqual(task.project_name, "学科网对接V1.0")
        self.assertEqual(task.title, "资源库新增学科网tab-校本资源库")
        self.assertEqual(task.status_key, "wait")
        self.assertEqual(task.left, "1")
        self.assertEqual(task.finish_path, "/pro/task-finish-138598.html?onlybody=yes")

    def test_parse_pager_config_reads_link_template(self) -> None:
        pager = MODULE.parse_pager_config(TASK_PAGE_HTML)
        self.assertEqual(pager, (1605, 20, 1, "/pro/my-task-assignedTo-id_desc-1605-{recPerPage}-{page}.html"))
        self.assertEqual(
            MODULE.build_page_path(pager[3], pager[1], 3),
            "/pro/my-task-assignedTo-id_desc-1605-20-3.html",
        )

    def test_parse_finish_form_defaults_keeps_selected_values(self) -> None:
        defaults = MODULE.parse_finish_form_defaults(FINISH_PAGE_HTML)
        self.assertEqual(
            defaults,
            {
                "currentConsumed": "0",
                "consumed": "0",
                "assignedTo": "zhupengpeng",
                "finishedDate": "2026-03-12",
                "status": "done",
                "comment": "",
            },
        )

    def test_match_prefers_commit_with_exact_task_fragment(self) -> None:
        task = MODULE.ZenTaoTask(
            task_id=138598,
            project_name="学科网对接V1.0",
            title="资源库新增学科网tab-校本资源库",
            status_key="wait",
            status_label="未开始",
            assigned_to_label="朋朋 朱",
            consumed="0",
            left="1",
            finish_path="/pro/task-finish-138598.html?onlybody=yes",
        )
        unrelated_commit = MODULE.CommitRecord(
            repo_name="interact-classroom",
            repo_path="/tmp/interact-classroom",
            sha="111",
            short_sha="111",
            date="2026-03-10",
            subject="fix(websocket): block reconnect after pre-login denied",
            body="",
            files=("src/utils/websocket.ts",),
            diff_excerpt="",
            search_lines=("interact-classroom", "fix(websocket): block reconnect after pre-login denied", "src/utils/websocket.ts"),
            normalized_search_text=MODULE.normalize_text("interact-classroom fix(websocket): block reconnect after pre-login denied src/utils/websocket.ts"),
        )
        related_commit = MODULE.CommitRecord(
            repo_name="repository",
            repo_path="/tmp/repository",
            sha="222",
            short_sha="222",
            date="2026-03-12",
            subject="feat(repository): add zxxk entry and dialog flow",
            body="在共享导航和各资源库 Header 中接入学科网入口，资源库新增学科网tab-校本资源库，并统一自动打开资源弹窗。",
            files=("src/page/repository-school/components/Header/index.tsx", "src/utils/zxxk.ts"),
            diff_excerpt="资源库新增学科网tab-校本资源库",
            search_lines=(
                "repository",
                "feat(repository): add zxxk entry and dialog flow",
                "在共享导航和各资源库 Header 中接入学科网入口，资源库新增学科网tab-校本资源库，并统一自动打开资源弹窗。",
                "src/page/repository-school/components/Header/index.tsx",
                "src/utils/zxxk.ts",
                "资源库新增学科网tab-校本资源库",
            ),
            normalized_search_text=MODULE.normalize_text(
                "repository feat(repository): add zxxk entry and dialog flow 在共享导航和各资源库 Header 中接入学科网入口，资源库新增学科网tab-校本资源库，并统一自动打开资源弹窗。 src/page/repository-school/components/Header/index.tsx src/utils/zxxk.ts 资源库新增学科网tab-校本资源库"
            ),
        )

        matched, unmatched = MODULE.match_tasks([task], [unrelated_commit, related_commit], min_score=7.5, match_limit=2)
        self.assertEqual(len(matched), 1)
        self.assertEqual(len(unmatched), 0)
        matched_task, evidence = matched[0]
        self.assertEqual(matched_task.task_id, 138598)
        self.assertEqual(evidence[0].commit.short_sha, "222")
        self.assertGreaterEqual(evidence[0].score, 7.5)

    def test_ngram_overlap_supports_partial_task_wording(self) -> None:
        task = MODULE.ZenTaoTask(
            task_id=138605,
            project_name="学科网对接V1.0",
            title="点击自动打开选择资源的弹窗",
            status_key="wait",
            status_label="未开始",
            assigned_to_label="朋朋 朱",
            consumed="0",
            left="1",
            finish_path="/pro/task-finish-138605.html?onlybody=yes",
        )
        related_commit = MODULE.CommitRecord(
            repo_name="repository",
            repo_path="/tmp/repository",
            sha="333",
            short_sha="333",
            date="2026-03-12",
            subject="feat(repository): add zxxk entry and dialog flow",
            body="用户点击学科网后，会把当前页带到我的资源库并自动打开资源类型弹窗。",
            files=("src/page/repository-my/components/SubTab/index.tsx",),
            diff_excerpt="自动打开资源类型弹窗，并与我的资源库添加备课资源入口复用同一 Dialog。",
            search_lines=(
                "repository",
                "feat(repository): add zxxk entry and dialog flow",
                "用户点击学科网后，会把当前页带到我的资源库并自动打开资源类型弹窗。",
                "src/page/repository-my/components/SubTab/index.tsx",
                "自动打开资源类型弹窗，并与我的资源库添加备课资源入口复用同一 Dialog。",
            ),
            normalized_search_text=MODULE.normalize_text(
                "repository feat(repository): add zxxk entry and dialog flow 用户点击学科网后，会把当前页带到我的资源库并自动打开资源类型弹窗。 src/page/repository-my/components/SubTab/index.tsx 自动打开资源类型弹窗，并与我的资源库添加备课资源入口复用同一 Dialog。"
            ),
        )

        matched, unmatched = MODULE.match_tasks([task], [related_commit], min_score=7.5, match_limit=2)
        self.assertEqual(len(matched), 1)
        self.assertEqual(len(unmatched), 0)
        self.assertEqual(matched[0][0].task_id, 138605)

    def test_short_generic_title_does_not_match_incidental_substring(self) -> None:
        task = MODULE.ZenTaoTask(
            task_id=138613,
            project_name="学科网对接V1.0",
            title="自测",
            status_key="wait",
            status_label="未开始",
            assigned_to_label="朋朋 朱",
            consumed="0",
            left="3",
            finish_path="/pro/task-finish-138613.html?onlybody=yes",
        )
        unrelated_commit = MODULE.CommitRecord(
            repo_name="interact-classroom",
            repo_path="/tmp/interact-classroom",
            sha="444",
            short_sha="444",
            date="2026-03-09",
            subject="chore(audit): align governance docs and commit rules",
            body="",
            files=("docs/tasks/2026-03-09-commit-rule-smoke.md",),
            diff_excerpt="# 2026-03-09 提交规范自测记录",
            search_lines=(
                "interact-classroom",
                "chore(audit): align governance docs and commit rules",
                "docs/tasks/2026-03-09-commit-rule-smoke.md",
                "# 2026-03-09 提交规范自测记录",
            ),
            normalized_search_text=MODULE.normalize_text(
                "interact-classroom chore(audit): align governance docs and commit rules docs/tasks/2026-03-09-commit-rule-smoke.md # 2026-03-09 提交规范自测记录"
            ),
        )

        matched, unmatched = MODULE.match_tasks([task], [unrelated_commit], min_score=7.5, match_limit=2)
        self.assertEqual(len(matched), 0)
        self.assertEqual(len(unmatched), 1)


if __name__ == "__main__":
    unittest.main()
