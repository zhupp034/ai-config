#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

core_files=(
  "AGENTS.md"
  "README.md"
)

recommended_files=(
  "TESTING.md"
  "docs/AI_COLLAB_WORKFLOW.md"
  "docs/TASK_RECORD_TEMPLATE.md"
  "docs/TEST_CASE_MATRIX.md"
  "docs/DELIVERY_REPORT_TEMPLATE.md"
  "docs/GIT_COMMIT_GUIDE.md"
  "docs/LINT_AND_BUILD_KNOWN_ISSUES.md"
  "skills/md-doc-sync/SKILL.md"
)

conditional_files=()
missing_core=()
missing_recommended=()
missing_conditional=()

exists_file() {
  [[ -f "$ROOT/$1" ]]
}

has_routes="no"
has_socket="no"
has_sdk="no"
has_business_scenario="no"

if rg -n --glob '!node_modules/**' --glob '!.git/**' 'routes(\.ts|\.js)|react-router|umi' "$ROOT" >/dev/null 2>&1; then
  has_routes="yes"
  conditional_files+=("docs/ROUTES_AND_ACCESS.md")
fi

if rg -n --glob '!node_modules/**' --glob '!.git/**' 'websocket|socket\.io|businessSocket|WebSocket' "$ROOT" >/dev/null 2>&1; then
  has_socket="yes"
  conditional_files+=("docs/SOCKET_PROTOCOL_MAP.md")
fi

if [[ -d "$ROOT/sdk" || -d "$ROOT/src/SDK" || -d "$ROOT/SDK" ]]; then
  has_sdk="yes"
  conditional_files+=("docs/SDK_USAGE.md")
fi

if rg -n --glob '!node_modules/**' --glob '!.git/**' 'classroom|meeting|recordPlay|lessonId|roleType|roleCode|scene|scenario|workflow|flowId|业务流程|业务场景|互动课堂|会议|回放' "$ROOT" >/dev/null 2>&1; then
  has_business_scenario="yes"
  conditional_files+=("docs/BUSINESS_SCENARIO_MAP.md")
fi

for f in "${core_files[@]}"; do
  if ! exists_file "$f"; then
    missing_core+=("$f")
  fi
done

for f in "${recommended_files[@]}"; do
  if ! exists_file "$f"; then
    missing_recommended+=("$f")
  fi
done

for f in "${conditional_files[@]}"; do
  if ! exists_file "$f"; then
    missing_conditional+=("$f")
  fi
done

readme_has_nav="no"
agents_has_docs_index="no"
agents_has_audit_flow="no"
agents_has_md_sync_rule="no"
workflow_has_md_sync_rule="no"
task_template_has_md_sync_fields="no"

if exists_file "README.md" && rg -n "文档导航|Documentation" "$ROOT/README.md" >/dev/null 2>&1; then
  readme_has_nav="yes"
fi

if exists_file "AGENTS.md" && rg -n "项目内关键 Markdown 文档|关键 Markdown|Markdown 文档|Project Docs Index" "$ROOT/AGENTS.md" >/dev/null 2>&1; then
  agents_has_docs_index="yes"
fi

if exists_file "AGENTS.md" && rg -n "计划|plan review|测试用例|复测|报告|git 提交|有意义代码|Audit Requirements" "$ROOT/AGENTS.md" >/dev/null 2>&1; then
  agents_has_audit_flow="yes"
fi

if exists_file "AGENTS.md" && rg -n "文档同步|无对应文档.*新建|skills/md-doc-sync/SKILL.md" "$ROOT/AGENTS.md" >/dev/null 2>&1; then
  agents_has_md_sync_rule="yes"
fi

if exists_file "docs/AI_COLLAB_WORKFLOW.md" && rg -n "无对应文档.*新建|skills/md-doc-sync/SKILL.md|Markdown" "$ROOT/docs/AI_COLLAB_WORKFLOW.md" >/dev/null 2>&1; then
  workflow_has_md_sync_rule="yes"
fi

if exists_file "docs/TASK_RECORD_TEMPLATE.md" && rg -n "同步更新文档|新建文档|未更新理由" "$ROOT/docs/TASK_RECORD_TEMPLATE.md" >/dev/null 2>&1; then
  task_template_has_md_sync_fields="yes"
fi

state="initialized"
if ((${#missing_core[@]} > 0)); then
  state="not_initialized"
elif ((${#missing_recommended[@]} > 0)) || ((${#missing_conditional[@]} > 0)) || [[ "$readme_has_nav" == "no" ]] || [[ "$agents_has_docs_index" == "no" ]] || [[ "$agents_has_audit_flow" == "no" ]] || [[ "$agents_has_md_sync_rule" == "no" ]] || [[ "$workflow_has_md_sync_rule" == "no" ]] || [[ "$task_template_has_md_sync_fields" == "no" ]]; then
  state="partial"
fi

printf "# AI Init Check

"
printf -- "- repository: %s
" "$ROOT"
printf -- "- state: **%s**
" "$state"
printf -- "- readme_has_docs_nav: %s
" "$readme_has_nav"
printf -- "- agents_has_docs_index: %s
" "$agents_has_docs_index"
printf -- "- agents_has_audit_flow: %s
" "$agents_has_audit_flow"
printf -- "- agents_has_md_sync_rule: %s
" "$agents_has_md_sync_rule"
printf -- "- workflow_has_md_sync_rule: %s
" "$workflow_has_md_sync_rule"
printf -- "- task_template_has_md_sync_fields: %s
" "$task_template_has_md_sync_fields"
printf -- "- detected_routes: %s
" "$has_routes"
printf -- "- detected_socket: %s
" "$has_socket"
printf -- "- detected_sdk: %s
" "$has_sdk"
printf -- "- detected_business_scenario: %s

" "$has_business_scenario"

printf "## Core Files
"
for f in "${core_files[@]}"; do
  if exists_file "$f"; then
    printf -- "- [x] %s
" "$f"
  else
    printf -- "- [ ] %s
" "$f"
  fi
done

printf "
## Recommended Files
"
for f in "${recommended_files[@]}"; do
  if exists_file "$f"; then
    printf -- "- [x] %s
" "$f"
  else
    printf -- "- [ ] %s
" "$f"
  fi
done

if ((${#conditional_files[@]} > 0)); then
  printf "
## Conditional Files
"
  for f in "${conditional_files[@]}"; do
    if exists_file "$f"; then
      printf -- "- [x] %s
" "$f"
    else
      printf -- "- [ ] %s
" "$f"
    fi
  done
fi

if ((${#missing_core[@]} > 0)); then
  printf "
## Missing Core
"
  for f in "${missing_core[@]}"; do
    printf -- "- %s
" "$f"
  done
fi

if ((${#missing_recommended[@]} > 0)); then
  printf "
## Missing Recommended
"
  for f in "${missing_recommended[@]}"; do
    printf -- "- %s
" "$f"
  done
fi

if ((${#missing_conditional[@]} > 0)); then
  printf "
## Missing Conditional
"
  for f in "${missing_conditional[@]}"; do
    printf -- "- %s
" "$f"
  done
fi

case "$state" in
  initialized) exit 0 ;;
  partial) exit 1 ;;
  not_initialized) exit 2 ;;
  *) exit 3 ;;
esac
