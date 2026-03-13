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

has_file() {
  [[ -f "$ROOT/$1" ]]
}

matches_product_code() {
  local pattern="$1"
  rg -n \
    --glob 'src/**' \
    --glob 'app/**' \
    --glob 'apps/**' \
    --glob 'packages/**' \
    --glob 'services/**' \
    --glob 'server/**' \
    --glob 'client/**' \
    --glob 'clients/**' \
    --glob 'api/**' \
    --glob 'cmd/**' \
    --glob 'pkg/**' \
    --glob 'internal/**' \
    --glob 'lib/**' \
    --glob 'config/**' \
    --glob '*.go' \
    --glob '*.py' \
    --glob '*.rb' \
    --glob '*.php' \
    --glob '*.js' \
    --glob '*.jsx' \
    --glob '*.ts' \
    --glob '*.tsx' \
    --glob '*.mjs' \
    --glob '*.cjs' \
    --glob '*.java' \
    --glob '*.kt' \
    --glob '*.rs' \
    --glob '*.json' \
    --glob '*.toml' \
    --glob '*.yml' \
    --glob '*.yaml' \
    --glob '!node_modules/**' \
    --glob '!.git/**' \
    --glob '!dist/**' \
    --glob '!build/**' \
    --glob '!coverage/**' \
    --glob '!docs/**' \
    --glob '!skills/**' \
    --glob '!scripts/**' \
    --glob '!test/**' \
    --glob '!tests/**' \
    --glob '!**/*.md' \
    "$pattern" "$ROOT" >/dev/null 2>&1
}

matches_product_path() {
  rg --files "$ROOT" | rg -v '/(docs|skills|scripts|test|tests)/' | rg -n "$1" >/dev/null 2>&1
}

append_line() {
  local current="$1"
  local next="$2"
  if [[ -z "$current" ]]; then
    printf '%s' "$next"
  else
    printf '%s\n%s' "$current" "$next"
  fi
}

repo_name="$(basename "$ROOT")"

doc_language="zh-CN"
if has_file "README.md" && rg -n '^(#|##|###)[[:space:]]+[A-Z][A-Za-z0-9 _:/()-]{3,}$' "$ROOT/README.md" >/dev/null 2>&1; then
  if ! rg -n '[一-龥]' "$ROOT/README.md" >/dev/null 2>&1; then
    doc_language="en"
  fi
fi

stack_signals=""
if has_file "package.json"; then
  stack_signals="$(append_line "$stack_signals" "node")"
fi
if has_file "tsconfig.json"; then
  stack_signals="$(append_line "$stack_signals" "typescript")"
fi
if has_file "pyproject.toml" || has_file "requirements.txt"; then
  stack_signals="$(append_line "$stack_signals" "python")"
fi
if has_file "go.mod"; then
  stack_signals="$(append_line "$stack_signals" "go")"
fi
if has_file "Cargo.toml"; then
  stack_signals="$(append_line "$stack_signals" "rust")"
fi
if has_file "pom.xml" || has_file "build.gradle" || has_file "build.gradle.kts"; then
  stack_signals="$(append_line "$stack_signals" "jvm")"
fi
if has_file "Gemfile"; then
  stack_signals="$(append_line "$stack_signals" "ruby")"
fi
if has_file "composer.json"; then
  stack_signals="$(append_line "$stack_signals" "php")"
fi
if [[ -d "$ROOT/apps" || -d "$ROOT/packages" || -f "$ROOT/pnpm-workspace.yaml" || -f "$ROOT/turbo.json" ]]; then
  stack_signals="$(append_line "$stack_signals" "monorepo")"
fi

stack_summary="unknown"
if [[ -n "$stack_signals" ]]; then
  stack_summary="$(printf '%s\n' "$stack_signals" | awk 'NF { if (count > 0) printf ", "; printf "%s", $0; count += 1 } END { printf "\n" }' | tr -d '\n')"
fi

has_routes="no"
has_events="no"
has_integrations="no"
has_domain_context="no"

if matches_product_code 'react-router|vue-router|next/navigation|next/router|Route::|gin\.|mux\.|chi\.' || matches_product_path '(^|/)(routes?|router)\.(ts|js|tsx|jsx|mjs|cjs|py|go|rb|php)$|(^|/)urls\.py$'; then
  has_routes="yes"
fi

if matches_product_code 'websocket|socket\.io|WebSocket|event bus|eventbus|pubsub|pub/sub|message queue|kafka|rabbitmq|nats|consumer|producer|stream handler'; then
  has_events="yes"
fi

if [[ -d "$ROOT/sdk" || -d "$ROOT/integrations" || -d "$ROOT/clients" || -d "$ROOT/third_party" ]]; then
  has_integrations="yes"
fi
if [[ "$has_integrations" == "no" ]] && matches_product_code 'openapi|swagger|grpc|protobuf|sdk|client[[:space:]_-]wrapper|third[- ]party|external api|axios\.create|fetch\('; then
  has_integrations="yes"
fi

if matches_product_code 'workflow|state machine|approval|审批|permission|权限|tenant|租户|role|状态流转|domain model|聚合|订单|支付|库存|subscription'; then
  has_domain_context="yes"
fi

detect_js_runner() {
  if has_file "package.json"; then
    local detected_pm=""
    if command -v python3 >/dev/null 2>&1; then
      detected_pm="$(python3 - "$ROOT/package.json" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)
package_manager = data.get("packageManager") or ""
print(package_manager.split("@", 1)[0])
PY
)"
    fi
    if [[ -n "$detected_pm" ]]; then
      printf '%s' "$detected_pm"
      return 0
    fi
  fi

  if has_file "pnpm-lock.yaml"; then
    printf 'pnpm'
  elif has_file "yarn.lock"; then
    printf 'yarn'
  elif has_file "bun.lockb" || has_file "bun.lock"; then
    printf 'bun'
  else
    printf 'npm'
  fi
}

format_js_runner() {
  local runner="$1"
  local script_name="$2"
  case "$runner" in
    yarn) printf 'yarn %s' "$script_name" ;;
    pnpm) printf 'pnpm %s' "$script_name" ;;
    bun) printf 'bun run %s' "$script_name" ;;
    *) printf 'npm run %s' "$script_name" ;;
  esac
}

test_commands=""
js_runner="$(detect_js_runner)"

if has_file "package.json" && command -v python3 >/dev/null 2>&1; then
  js_script_lines="$(python3 - "$ROOT/package.json" "$js_runner" <<'PY'
import json
import sys

path = sys.argv[1]
runner = sys.argv[2]
labels = [
    "test",
    "test:ci",
    "test:unit",
    "test:integration",
    "test:e2e",
    "lint",
    "build",
    "e2e",
]

with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)

scripts = data.get("scripts") or {}

def invoke(pm: str, script_name: str) -> str:
    if pm == "yarn":
        return f"yarn {script_name}"
    if pm == "pnpm":
        return f"pnpm {script_name}"
    if pm == "bun":
        return f"bun run {script_name}"
    return f"npm run {script_name}"

for name in labels:
    command = scripts.get(name)
    if command:
        print(f"{name}\t{invoke(runner, name)}\t{command}")
PY
)"

  while IFS=$'\t' read -r script_name script_invoke script_body; do
    [[ -z "${script_name:-}" ]] && continue
    if [[ "$doc_language" == "en" ]]; then
      test_commands="$(append_line "$test_commands" "- ${script_name}: \`${script_invoke}\` (script: \`${script_body}\`)")"
    else
      test_commands="$(append_line "$test_commands" "- ${script_name}: \`${script_invoke}\`（脚本内容：\`${script_body}\`）")"
    fi
  done <<< "$js_script_lines"
fi

if has_file "pyproject.toml" || has_file "requirements.txt"; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="$(append_line "$test_commands" "- python test (common default, verify first): \`pytest\`")"
  else
    test_commands="$(append_line "$test_commands" "- python test（常见默认命令，需先核对）: \`pytest\`")"
  fi
fi

if has_file "go.mod"; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="$(append_line "$test_commands" "- go test (common default, verify first): \`go test ./...\`")"
  else
    test_commands="$(append_line "$test_commands" "- go test（常见默认命令，需先核对）: \`go test ./...\`")"
  fi
fi

if has_file "Cargo.toml"; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="$(append_line "$test_commands" "- rust test (common default, verify first): \`cargo test\`")"
  else
    test_commands="$(append_line "$test_commands" "- rust test（常见默认命令，需先核对）: \`cargo test\`")"
  fi
fi

if has_file "pom.xml"; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="$(append_line "$test_commands" "- maven test (common default, verify first): \`mvn test\`")"
  else
    test_commands="$(append_line "$test_commands" "- maven test（常见默认命令，需先核对）: \`mvn test\`")"
  fi
fi

if has_file "build.gradle" || has_file "build.gradle.kts"; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="$(append_line "$test_commands" "- gradle test (common default, verify first): \`./gradlew test\`")"
  else
    test_commands="$(append_line "$test_commands" "- gradle test（常见默认命令，需先核对）: \`./gradlew test\`")"
  fi
fi

if has_file "Makefile" && rg -n '^test:' "$ROOT/Makefile" >/dev/null 2>&1; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="$(append_line "$test_commands" "- make test: \`make test\`")"
  else
    test_commands="$(append_line "$test_commands" "- make test: \`make test\`")"
  fi
fi

if [[ -z "$test_commands" ]]; then
  if [[ "$doc_language" == "en" ]]; then
    test_commands="- TODO: replace with this repository's real test / lint / build / e2e or smoke commands."
  else
    test_commands="- 待补充：请替换为本仓库真实的 test / lint / build / e2e 或 smoke 命令。"
  fi
fi

if [[ "$doc_language" == "en" ]]; then
  agents_content="# AGENTS.md

## Project Overview

- repo: $repo_name
- detected_stack: $stack_summary
- docs_language_hint: $doc_language

## AI Collaboration Principles

1. Read the requirement, README, and nearby module docs before editing.
2. For any non-trivial task, write down the plan before coding and record review decisions when needed.
3. Keep diffs focused so each commit carries one primary intent.
4. Make code, docs, tests, reviews, and delivery notes traceable to each other.
5. For user flows, API flows, or critical job flows, verify key success, empty, error, and loading states when relevant.
6. Run the Markdown sync check in \`skills/md-doc-sync/SKILL.md\` before commit.

## Delivery Requirements

- Every non-trivial task should map to a repository task record or an equivalent project document.
- Task records should cover plan, implementation, review, testing, retest, and final delivery notes.
- Use Conventional Commits and follow repository-specific rules first; if none exist, keep the \`type(scope)\` prefix in English but write the summary and body primarily in Chinese, even for English-first repositories. The commit message should include both a summary and a body, with enough detail to explain scope, intent, impact, risks, and validation.
- When key files change, update the matching Markdown docs; if no matching doc exists, create one first.
- Delivery notes should clearly describe user-visible changes, impact scope, validation, and risks.

## Constraints

- Do not overwrite unrelated files.
- Do not run destructive git operations without confirmation.
- Prefer adding tests for meaningful logic changes; if tests are skipped, record the reason.
- If the repository already has module docs, runbooks, or process docs, evaluate whether they also need updates.

## Project Docs Index

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

## Suggested Commands

$test_commands

## Notes

- Replace placeholders with commands that are actually used in this repository.
- For user flows, data views, API calls, or job orchestration, cover critical success, empty, error, and loading states when applicable.
- Each task should record the commands that were run, required environment assumptions, manual validation steps, and retest results.
- If there is no automated coverage yet, document the smallest reproducible manual validation path and the remaining risk.
"

  workflow_content="# AI_COLLAB_WORKFLOW.md

## Goal

Make AI-assisted analysis, implementation, testing, and delivery reviewable by other collaborators.

## Recommended Flow

1. Confirm requirements and nearby context
2. Record plan and risks
3. Capture plan review or key decisions
4. Implement code changes
5. Sync documentation
6. Review code
7. Design and execute tests
8. Fix issues and retest
9. Write final delivery notes

## Evidence Rules

- Each feature, bug fix, or meaningful refactor should have its own task record or equivalent evidence.
- Record key decisions in repository docs, PR descriptions, or the task system instead of leaving them only in chat.
- When key files change, update the matching Markdown docs; if no matching docs exist, create them first.
- Run the Markdown sync check in \`skills/md-doc-sync/SKILL.md\` before commit.
- If parts of the workflow were intentionally skipped, explain why in the task record.
"

  task_record_content="# TASK_RECORD_TEMPLATE.md

## Basics

- task:
- owner:
- reviewers:
- related issue:

## Plan

## Risks And Assumptions

## Plan Review

## Implementation

## Documentation Sync

- Updated Markdown:
- New docs created:
- Reason if docs were not updated:

## Code Review

## Test Design

## Test Execution

## Bug Fix And Retest

## Final Delivery Notes
"

  md_sync_skill_content="---
name: md-doc-sync
description: Run a Markdown sync check inside the repository after code changes. Decide whether docs must be updated before commit, and create missing Markdown first when needed.
---

# MD Doc Sync (Project Local)

## Goal

Keep code changes and Markdown updates aligned without relying on a blocking git hook.

## Steps

1. Inspect the changed files
- \`git diff --name-only\`
- \`git diff --cached --name-only\`

2. Decide whether docs must change
- If the change touches \`src/\`, \`app/\`, \`cmd/\`, \`pkg/\`, \`internal/\`, \`config/\`, \`scripts/\`, \`test/\`, build files, or dependency manifests, review the matching Markdown docs.

3. Update or create docs
- Prefer updating existing docs such as \`README.md\`, \`docs/*\`, module notes, runbooks, or API docs.
- If no matching doc exists, create Markdown in the appropriate project location first.

4. Record the reason
- In the task record, fill in:
  - \`Updated Markdown\`
  - \`New docs created\`
  - \`Reason if docs were not updated\`

5. Re-check before commit
- Confirm that each commit contains the required code changes plus matching Markdown changes, or a clear explanation for why docs did not change.
"

  domain_context_content="# DOMAIN_CONTEXT.md

## Goal

Summarize the main business entities, critical flows, role boundaries, and state transitions in the project.

## Suggested Sections

- Core entities or domain terms
- Main flows and entry points
- Roles, permissions, or tenant boundaries
- Important state transitions and exception branches
- Upstream and downstream external dependencies
"

  routes_access_content="# ROUTES_AND_ACCESS.md

## Goal

Document routes, entry points, access control, and navigation or call relationships.

## Suggested Sections

- Main entry points and trigger conditions
- Route or URL mapping rules
- Access control, auth, and redirect behavior
- Key navigation or request transitions
"

  event_flow_content="# EVENT_AND_MESSAGE_FLOW.md

## Goal

Document asynchronous events, message channels, subscriber relationships, and critical processing flows.

## Suggested Sections

- Event or message names
- Producers and consumers
- Trigger conditions and retry strategy
- Ordering, idempotency, and failure-handling rules
"

  integration_dependencies_content="# INTEGRATION_DEPENDENCIES.md

## Goal

Describe dependencies on external SDKs, third-party services, platform APIs, or shared internal clients.

## Suggested Sections

- Integration target and purpose
- Local wrapper location
- Key configuration and authentication method
- Fallback, rate limit, retry, and failure impact
"

  test_matrix_content="# TEST_CASE_MATRIX.md

## Goal

Track covered and missing test scenarios by module or capability.

## Suggested Fields

- module
- scenario
- type
- status
- owner
- last_verified_at
- notes
"

  delivery_report_content="# DELIVERY_REPORT_TEMPLATE.md

## User-Visible Changes

## Impact Scope

## Validation

## Risks

## Rollback Plan
"

  git_commit_guide_content="# GIT_COMMIT_GUIDE.md

## Goal

Make commits easier to review, summarize, and connect to meaningful delivery outputs.

## Rules

- Use Conventional Commits.
- Prefer \`type(scope): summary\`; when there is no clear scope, use \`type: summary\`.
- If the repository has no stricter local rule, keep the \`type(scope)\` prefix in English and write the summary/body primarily in Chinese, even for English-first repositories. The commit message should include both a summary and a body. The message should clearly explain the changed object, behavior, reason, impact, risks, and validation, and the summary should still stay concise when possible.
- Each commit should express one primary intent.
- When practical, connect commits to tasks, bugs, or review items.
- Split generated files, dependency upgrades, refactors, and product changes whenever possible.
- For complex changes, add a body with context, impact, compatibility, or validation details.

## Examples

- \`feat(auth): 补充 token 刷新失败后的降级处理\`
- \`fix(api): 修复分页接口返回空列表时的展示异常\`
- \`docs(ai): 补充任务交付流程与文档同步要求\`

## Suggested Body Template

Add a body after the summary by default. A practical structure is:

1. Background: why this change was needed
2. Key changes: what changed and where
3. Impact: affected modules, users, compatibility, or risks
4. Validation: executed tests, manual checks, and remaining known issues

## Example With Body

\`\`\`text
feat(auth): 补充 token 刷新失败后的降级处理

背景：
- 用户登录态过期后，部分请求在刷新失败时会一直停留在加载态

关键改动：
- 为 refresh token 失败分支补充登录态清理与跳转兜底
- 调整请求重试逻辑，避免重复提交失效请求

影响范围：
- 登录态续期链路
- 依赖鉴权的接口请求

验证方式：
- 已执行登录过期后的接口重试验证
- 已确认刷新失败时会跳转登录页且不再重复弹错
\`\`\`

## Low-Value Patterns To Avoid

- Broad formatting-only changes without a clear purpose
- Unrelated file changes mixed into one commit
- Vague summaries such as \`misc fix\`, \`update files\`, or \`continue changes\`
- Summaries that mention only an outcome without the object and behavior change
"

  issues_content="# LINT_AND_BUILD_KNOWN_ISSUES.md

## Goal

Record known lint, build, test, e2e, or environment issues and the current handling approach.

## Suggested Fields

- Problem description
- Impact scope
- Trigger condition
- Temporary workaround
- Long-term fix direction
"

  readme_nav_section='## Documentation

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
else
  agents_content="# AGENTS.md

## 项目概览

- repo: $repo_name
- detected_stack: $stack_summary
- docs_language_hint: $doc_language

## AI 协作原则

1. 先阅读需求、README 和相关模块文档，再开始改动。
2. 非简单任务先落计划，再开始编码；必要时补计划评审结论。
3. 保持最小改动，让每次提交只承载一个主要意图。
4. 代码、文档、测试、评审和交付证据要能互相追溯。
5. 涉及用户链路、接口链路或关键任务链路时，按需验证 success / empty / error / loading 等关键状态。
6. 提交前执行 \`skills/md-doc-sync/SKILL.md\` 的文档同步检查。

## 交付要求

- 每个非简单任务都应落到仓库内的任务记录或等价文档。
- 任务记录至少覆盖：计划、实现、评审、测试、复测、最终交付说明。
- 提交使用 Conventional Commits，并遵循仓库已有规则；如果仓库没有更具体约束，保持英文 \`type(scope)\` 前缀，但摘要和正文以中文为主，即使仓库整体文档偏英文也默认如此；提交信息默认要求“摘要 + 正文”同时存在，并尽量完整说明改动对象、意图、影响范围、风险和验证方式。
- 重点文件改动后必须同步更新对应 Markdown；若无对应文档，先新建再补内容。
- 交付说明应写清用户可见变化、影响范围、验证方式和风险点。

## 约束

- 不要覆盖无关文件。
- 未经确认不要执行破坏性 git 操作。
- 对有意义的逻辑变更优先补测试；若未补测试，需记录原因。
- 如果仓库已有更细的模块文档、运行手册或流程文档，修改后要评估是否同步更新。

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

## 建议命令

$test_commands

## 说明

- 将占位命令替换为本仓库实际使用的命令。
- 涉及用户链路、数据展示、接口调用或任务编排时，按需覆盖 success / empty / error / loading 等关键状态。
- 每个任务都记录实际执行的命令、环境前提、手工步骤和复测结果。
- 如果暂时没有自动化测试，也要记录最小可复现的手工验证路径和剩余风险。
"

  workflow_content="# AI_COLLAB_WORKFLOW.md

## 目标

让 AI 参与的分析、实现、测试和交付过程可以被其他协作者复核。

## 推荐流程

1. 需求理解与上下文确认
2. 计划与风险识别
3. 计划评审或关键决策记录
4. 代码实现
5. 文档同步
6. 代码评审
7. 测试设计与执行
8. 缺陷修复与复测
9. 最终交付说明

## 证据规则

- 每个功能、缺陷或有意义的重构都应有独立任务记录或等价证据。
- 优先在仓库文档、PR 描述或任务系统中记录关键决策，不只留在聊天记录里。
- 重点文件改动后必须同步更新 Markdown；若无对应文档则先新建。
- 提交前按 \`skills/md-doc-sync/SKILL.md\` 执行文档同步检查。
- 如果实际流程裁剪了某些环节，任务记录里要说明原因。
"

  task_record_content="# TASK_RECORD_TEMPLATE.md

## 基本信息

- task:
- owner:
- reviewers:
- related issue:

## 计划

## 风险与假设

## 计划评审

## 实现

## 文档同步

- 更新的 Markdown:
- 新建文档（如有）:
- 未更新原因（如无文档改动）:

## 代码评审

## 测试设计

## 测试执行

## 缺陷修复与复测

## 最终交付说明
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
- 若改动涉及 \`src/\`、\`app/\`、\`cmd/\`、\`pkg/\`、\`internal/\`、\`config/\`、\`scripts/\`、\`test/\`、构建文件或依赖清单，必须检查对应 Markdown 是否要更新。

3. 更新或新建文档
- 优先更新已有文档，例如 \`README.md\`、\`docs/*\`、模块说明、运行手册、接口文档。
- 若没有对应文档，按项目规则在合适目录新建 Markdown。

4. 记录理由
- 在任务记录中填写：
  - \`更新的 Markdown\`
  - \`新建文档（如有）\`
  - \`未更新原因（如无文档改动）\`

5. 提交前复核
- 确认本次 commit 至少包含“必要的代码改动 + 对应 Markdown 变更（或明确理由）”。
"

  domain_context_content="# DOMAIN_CONTEXT.md

## 目标

沉淀项目里的核心业务对象、关键流程、角色边界和状态流转。

## 建议补充

- 核心业务对象或领域术语
- 主要流程与入口
- 角色、权限或租户边界
- 关键状态流转与异常分支
- 与外部系统的上下游关系
"

  routes_access_content="# ROUTES_AND_ACCESS.md

## 目标

记录路由、入口、访问控制和页面或接口跳转关系。

## 建议补充

- 主要入口及触发条件
- 路由或 URL 映射规则
- 访问控制、鉴权与重定向行为
- 关键页面或接口之间的跳转关系
"

  event_flow_content="# EVENT_AND_MESSAGE_FLOW.md

## 目标

记录异步事件、消息通道、订阅关系和关键处理链路。

## 建议补充

- 事件或消息名称
- 生产方与消费方
- 触发条件和重试策略
- 顺序性、幂等性和异常处理约束
"

  integration_dependencies_content="# INTEGRATION_DEPENDENCIES.md

## 目标

记录对外部 SDK、第三方服务、平台接口或内部共享客户端的依赖边界。

## 建议补充

- 集成对象与用途
- 本地封装位置
- 关键配置与鉴权方式
- 降级、限流、重试和故障影响
"

  test_matrix_content="# TEST_CASE_MATRIX.md

## 目标

按模块或能力跟踪已覆盖和待补齐的测试。

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

让提交更容易统计、评审，并能映射到清晰的任务产出。

## 规则

- 使用 Conventional Commits。
- 格式优先为 \`type(scope): summary\`；没有明确 scope 时可用 \`type: summary\`。
- 若仓库没有更具体规则，保持英文 \`type(scope)\` 前缀，摘要和正文以中文为主；即使仓库整体文档偏英文，也默认沿用这一方式，并尽量写清改动对象、行为变化、背景原因、影响范围、风险和验证信息；摘要本身仍应尽量精炼。
- 一个提交只表达一个主要意图。
- 条件允许时，让每个提交能关联到任务、缺陷或评审项。
- 将生成文件、依赖升级、重构和业务变更尽量拆开。
- 提交摘要后默认补充正文，说明背景、关键改动、影响范围、风险和验证信息。

## 示例

- \`feat(auth): 补充 token 刷新失败后的降级处理\`
- \`fix(api): 修复分页接口返回空列表时的展示异常\`
- \`docs(ai): 补充任务交付流程与文档同步要求\`

## 推荐正文结构

提交摘要后默认补正文，可按下面结构补充：

1. 背景：为什么要改
2. 关键改动：改了什么、涉及哪些模块
3. 影响范围：影响哪些链路、角色或兼容性
4. 验证方式：执行了哪些测试、还有哪些已知风险

## 正文示例

\`\`\`text
feat(auth): 补充 token 刷新失败后的降级处理

背景：
- 用户登录态过期后，部分请求在刷新失败时会一直停留在加载态

关键改动：
- 为 refresh token 失败分支补充登录态清理与跳转兜底
- 调整请求重试逻辑，避免重复提交失效请求

影响范围：
- 登录态续期链路
- 依赖鉴权的接口请求

验证方式：
- 已执行登录过期后的接口重试验证
- 已确认刷新失败时会跳转登录页且不再重复弹错
\`\`\`

## 需要避免的低价值模式

- 没有明确目的的大面积格式化
- 混入无关文件改动
- 使用 \`misc fix\`、\`update files\`、\`continue changes\` 这类模糊摘要
- 只写结果词，不说明对象和行为变化
"

  issues_content="# LINT_AND_BUILD_KNOWN_ISSUES.md

## 目标

记录已知的 lint、build、test、e2e 或环境问题及处理方式。

## 建议字段

- 问题描述
- 影响范围
- 触发条件
- 临时绕过方式
- 长期修复方向
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
fi

create_if_missing "AGENTS.md" "$agents_content"
create_if_missing "TESTING.md" "$testing_content"
create_if_missing "docs/AI_COLLAB_WORKFLOW.md" "$workflow_content"
create_if_missing "docs/TASK_RECORD_TEMPLATE.md" "$task_record_content"
create_if_missing "docs/TEST_CASE_MATRIX.md" "$test_matrix_content"
create_if_missing "docs/DELIVERY_REPORT_TEMPLATE.md" "$delivery_report_content"
create_if_missing "docs/GIT_COMMIT_GUIDE.md" "$git_commit_guide_content"
create_if_missing "docs/LINT_AND_BUILD_KNOWN_ISSUES.md" "$issues_content"
create_if_missing "skills/md-doc-sync/SKILL.md" "$md_sync_skill_content"

if [[ "$has_domain_context" == "yes" ]] && [[ ! -f "$ROOT/docs/BUSINESS_SCENARIO_MAP.md" ]]; then
  create_if_missing "docs/DOMAIN_CONTEXT.md" "$domain_context_content"
fi

if [[ "$has_routes" == "yes" ]]; then
  create_if_missing "docs/ROUTES_AND_ACCESS.md" "$routes_access_content"
fi

if [[ "$has_events" == "yes" ]] && [[ ! -f "$ROOT/docs/SOCKET_PROTOCOL_MAP.md" ]]; then
  create_if_missing "docs/EVENT_AND_MESSAGE_FLOW.md" "$event_flow_content"
fi

if [[ "$has_integrations" == "yes" ]] && [[ ! -f "$ROOT/docs/SDK_USAGE.md" ]]; then
  create_if_missing "docs/INTEGRATION_DEPENDENCIES.md" "$integration_dependencies_content"
fi

if has_file "README.md"; then
  if rg -n '文档导航|Documentation|Docs Index|Project Docs' "$ROOT/README.md" >/dev/null 2>&1; then
    say "[skip] README.md docs nav"
  else
    say "[append] README.md docs nav"
    if [[ "$MODE" != "dry-run" ]]; then
      printf '\n%s\n' "$readme_nav_section" >> "$ROOT/README.md"
    fi
  fi
else
  create_if_missing "README.md" "# $repo_name

$readme_nav_section"
fi

say "[done] mode=$MODE root=$ROOT"
