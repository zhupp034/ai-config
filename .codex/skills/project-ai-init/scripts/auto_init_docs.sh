#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
MODE="${2:-apply}" # apply | dry-run
ROOT="$(cd "$ROOT" && pwd)"

say() { printf '%s\n' "$*"; }
create_if_missing() {
  local rel="$1"
  local content="$2"
  local abs="$ROOT/$rel"
  if [[ -f "$abs" ]]; then
    say "[skip] $rel"
    return 0
  fi
  say "[create] $rel"
  [[ "$MODE" == "dry-run" ]] && return 0
  mkdir -p "$(dirname "$abs")"
  printf '%s\n' "$content" > "$abs"
}

has_file() { [[ -f "$ROOT/$1" ]]; }

stack="unknown"
if has_file "package.json"; then
  if rg -n '"umi"|"react"|"typescript"' "$ROOT/package.json" >/dev/null 2>&1; then
    stack="frontend-ts"
  fi
fi

repo_name="$(basename "$ROOT")"

has_routes="no"
has_socket="no"
has_sdk="no"
has_business_scenario="no"

if rg -n --glob '!node_modules/**' --glob '!.git/**' 'routes(\.ts|\.js)|react-router|umi' "$ROOT" >/dev/null 2>&1; then
  has_routes="yes"
fi

if rg -n --glob '!node_modules/**' --glob '!.git/**' 'websocket|socket\.io|businessSocket|WebSocket' "$ROOT" >/dev/null 2>&1; then
  has_socket="yes"
fi

if [[ -d "$ROOT/sdk" || -d "$ROOT/src/SDK" || -d "$ROOT/SDK" ]]; then
  has_sdk="yes"
fi

if rg -n --glob '!node_modules/**' --glob '!.git/**' 'classroom|meeting|recordPlay|lessonId|roleType|roleCode|scene|scenario|workflow|flowId|业务流程|业务场景|互动课堂|会议|回放' "$ROOT" >/dev/null 2>&1; then
  has_business_scenario="yes"
fi

agents_content="# AGENTS.md

## 项目概览

- stack: $stack
- repo: $repo_name

## AI 工作流

1. 先阅读需求和相关文件，再开始改动。
2. 非简单任务在编码前先把计划写入项目文档。
3. 多人协作时记录计划评审结论。
4. 保持最小改动，并让每次提交只承载一个主要意图。
5. 在实现前或实现过程中补充测试用例。
6. 将代码评审、实际测试结果、缺陷修复和复测证据记录到仓库文档中。
7. 提交前执行 \`skills/md-doc-sync/SKILL.md\` 的文档同步检查。
8. 输出用户可见变化、影响范围、验证方式和风险说明。

## 审计要求

- 每个非简单任务都应映射到 \`docs/tasks/\` 或其他已约定任务目录中的任务记录。
- 任务记录应覆盖：计划、计划评审、实现、代码评审、测试用例设计、测试用例评审、测试执行、缺陷修复/复测、最终报告。
- 提交应能追溯到任务或缺陷，并使用 Conventional Commits。
- 避免在同一个提交里混入重构、生成产物、依赖变更和功能修复。
- 只要使用了 AI，就要保证仓库文档足以让其他评审者还原变更过程。

## 约束

- 不要覆盖无关文件。
- 未经确认不要执行破坏性 git 操作。
- 重点文件（如 \`src/\`、\`config/\`、\`scripts/\`、\`test/\`、\`package.json\`、\`tsconfig.json\`）改动后，必须同步更新对应 Markdown；若无对应文档，先新建再补充内容。
- 涉及用户可见链路时，验证 loading / empty / error / success 关键状态。
- 对有意义的逻辑变更优先补测试；若未补测试，需记录原因。

## 项目文档索引

- \`README.md\`
- \`TESTING.md\`
- \`docs/AI_COLLAB_WORKFLOW.md\`
- \`docs/TASK_RECORD_TEMPLATE.md\`
- \`docs/TEST_CASE_MATRIX.md\`
- \`docs/DELIVERY_REPORT_TEMPLATE.md\`
- \`docs/GIT_COMMIT_GUIDE.md\`
- \`docs/LINT_AND_BUILD_KNOWN_ISSUES.md\`
- \`skills/md-doc-sync/SKILL.md\`
"

testing_content="# TESTING.md

## 命令

- unit: \`yarn test\`
- unit(ci): \`yarn test:ci\`
- e2e: \`yarn e2e\`

## 说明

- 测试应尽量靠近被修改模块。
- 涉及用户链路时覆盖 loading / empty / error / success 关键状态。
- 每个任务都记录实际执行的命令、手工步骤和复测结果。
"

workflow_content="# AI_COLLAB_WORKFLOW.md

## 目标

让 AI 参与交付的完整链路可以被同事和管理者复核。

## 必需流程

1. 计划
2. 计划评审
3. 任务文档落盘到仓库
4. 代码实现
5. 代码评审
6. 创建或更新测试用例
7. 测试用例评审
8. 实际测试执行
9. 缺陷修复与复测
10. 最终交付报告

## 证据规则

- 每个功能、缺陷或有意义的重构都使用一条独立任务记录。
- 条件允许时，在 PR 和提交信息中关联任务编号或文档路径。
- 重点文件改动后必须同步更新 Markdown；若无对应文档则先新建。
- 提交前按 \`skills/md-doc-sync/SKILL.md\` 执行文档同步检查。
- 评审结论和风险决策优先记录在仓库文档或 PR 描述中，而不是只留在聊天工具里。
"

task_record_content="# TASK_RECORD_TEMPLATE.md

## 基本信息

- task:
- owner:
- reviewers:
- related issue:

## 计划

## 计划评审

## 实现

## 文档同步

- 更新的 Markdown:
- 新建文档（如有）:
- 未更新原因（如无文档改动）:

## 代码评审

## 测试用例设计

## 测试用例评审

## 测试执行

## 缺陷修复与复测

## 最终报告
"

md_sync_skill_content="---
name: md-doc-sync
description: 在项目内执行“代码改动后的 Markdown 同步检查”。提交前先判断是否需要更新文档；若需要且不存在对应文档，先新建再补内容。
---

# MD Doc Sync (Project Local)

## 目标

在本仓库内统一执行“代码改动 -> 文档同步”的交付动作，不依赖 git hook 强制拦截。

## 执行步骤

1. 查看改动范围
- \`git diff --name-only\`
- \`git diff --cached --name-only\`

2. 判断是否涉及文档同步
- 若改动涉及 \`src/\`、\`config/\`、\`scripts/\`、\`test/\`、\`package.json\` 等代码/配置文件，必须检查对应 Markdown 是否要更新。

3. 更新或新建文档
- 优先更新已有文档（例如 \`README.md\`、\`docs/*\`、模块说明、流程文档）。
- 若没有对应文档，按项目规则在合适目录新建 Markdown（通常在 \`docs/\` 或模块目录）。

4. 记录理由
- 在任务记录中填写：
  - \`同步更新文档\`
  - \`新建文档（如有）\`
  - \`未更新理由（如无文档改动）\`

5. 提交前复核
- 确认本次 commit 至少包含“必要的代码改动 + 对应 Markdown 变更（或明确理由）”。
"

business_scenario_content="# BUSINESS_SCENARIO_MAP.md

## 目标

沉淀需要单独说明的业务场景、入口路由、角色差异和关键状态切换。

## 建议补充

- 场景名称与入口
- 关键路由或页面跳转
- 角色差异与权限边界
- 关键参数、状态切换与异常分支
"

routes_access_content="# ROUTES_AND_ACCESS.md

## Purpose

Document route matching order, access rules, and wrapper behavior.
"

socket_map_content="# SOCKET_PROTOCOL_MAP.md

## Purpose

Document websocket send/consume modules and change-impact checklist.
"

sdk_usage_content="# SDK_USAGE.md

## Purpose

Document local SDK usage and boundary with external SDK packages.
"

test_matrix_content="# TEST_CASE_MATRIX.md

## 目标

按模块跟踪已覆盖和待补齐的测试。

## 建议字段

- module
- scenario
- type
- status
- owner
- last_verified_at
- notes
"

delivery_report_content="# DELIVERY_REPORT_TEMPLATE.md

## 用户可见变化

## 影响范围

## 验证方式

## 风险点

## 回滚方案
"

git_commit_guide_content="# GIT_COMMIT_GUIDE.md

## 目标

让提交更容易统计、评审，并能映射到有意义的产出。

## 规则

- 使用 Conventional Commits。
- \`type(scope)\` 前缀保持英文，摘要和补充说明以中文为主。
- 一个提交只表达一个主要意图。
- 条件允许时，让每个提交能关联到任务、缺陷或评审项。
- 将生成文件、依赖升级、重构和业务变更尽量拆开。
- 优先使用一小串边界清晰的提交，而不是一个混杂的大提交。
- 摘要不要只写结果词，尽量交代改动对象、行为变化和原因。
- 复杂改动建议补充正文，说明背景、影响范围、兼容性或验证信息。

## 推荐格式

- \`type(scope): 中文摘要\`
- 正文可按需补充：
  - 变更背景
  - 关键改动
  - 影响范围
  - 验证方式

## 示例

- \`feat(order): 支持批量取消待支付订单\`
- \`fix(login): 修复验证码刷新后仍提交旧 token 的问题\`
- \`docs(ai): 补充任务记录与交付报告串联说明\`

## 需要避免的低价值模式

- 没有业务目的的大面积格式化
- 混入无关文件改动
- 使用 \`misc fix\`、\`update files\` 这类模糊摘要
- 使用 \`fix bug\`、\`调整一下\`、\`继续修改\` 这类信息不足的简短描述
"

issues_content="# LINT_AND_BUILD_KNOWN_ISSUES.md

## 目标

记录已知的 lint / build / e2e 环境问题及处理方式。
"

readme_nav_section='## 文档导航

- `AGENTS.md`
- `TESTING.md`
- `docs/AI_COLLAB_WORKFLOW.md`
- `docs/TASK_RECORD_TEMPLATE.md`
- `docs/TEST_CASE_MATRIX.md`
- `docs/DELIVERY_REPORT_TEMPLATE.md`
- `docs/GIT_COMMIT_GUIDE.md`
- `docs/LINT_AND_BUILD_KNOWN_ISSUES.md`
- `skills/md-doc-sync/SKILL.md`
'

create_if_missing "AGENTS.md" "$agents_content"
create_if_missing "TESTING.md" "$testing_content"
create_if_missing "docs/AI_COLLAB_WORKFLOW.md" "$workflow_content"
create_if_missing "docs/TASK_RECORD_TEMPLATE.md" "$task_record_content"
create_if_missing "docs/TEST_CASE_MATRIX.md" "$test_matrix_content"
create_if_missing "docs/DELIVERY_REPORT_TEMPLATE.md" "$delivery_report_content"
create_if_missing "docs/GIT_COMMIT_GUIDE.md" "$git_commit_guide_content"
create_if_missing "docs/LINT_AND_BUILD_KNOWN_ISSUES.md" "$issues_content"
create_if_missing "skills/md-doc-sync/SKILL.md" "$md_sync_skill_content"

if [[ "$has_business_scenario" == "yes" ]]; then
  create_if_missing "docs/BUSINESS_SCENARIO_MAP.md" "$business_scenario_content"
fi

if [[ "$has_routes" == "yes" ]]; then
  create_if_missing "docs/ROUTES_AND_ACCESS.md" "$routes_access_content"
fi

if [[ "$has_socket" == "yes" ]]; then
  create_if_missing "docs/SOCKET_PROTOCOL_MAP.md" "$socket_map_content"
fi

if [[ "$has_sdk" == "yes" ]]; then
  create_if_missing "docs/SDK_USAGE.md" "$sdk_usage_content"
fi

if has_file "README.md"; then
  if rg -n '文档导航|Documentation' "$ROOT/README.md" >/dev/null 2>&1; then
    say "[skip] README.md docs nav"
  else
    say "[append] README.md docs nav"
    if [[ "$MODE" != "dry-run" ]]; then
      printf '\n%s\n' "$readme_nav_section" >> "$ROOT/README.md"
    fi
  fi
else
  create_if_missing "README.md" "# $repo_name\n\n$readme_nav_section"
fi

say "[done] mode=$MODE root=$ROOT"
