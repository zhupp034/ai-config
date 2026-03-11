#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

exists_file() {
  [[ -f "$ROOT/$1" ]]
}

find_task_dir() {
  local candidate
  for candidate in "docs/tasks" "docs/ai-workflow" "docs/task-records"; do
    if [[ -d "$ROOT/$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

status="ready"
issues=()

task_dir=""
if task_dir="$(find_task_dir)"; then
  task_count=$(find "$ROOT/$task_dir" -type f \( -name '*.md' -o -name '*.markdown' \) | wc -l | tr -d ' ')
else
  task_count=0
fi

if ! exists_file "AGENTS.md"; then
  status="not_ready"
  issues+=("missing AGENTS.md")
fi

if ! exists_file "README.md"; then
  status="not_ready"
  issues+=("missing README.md")
fi

for f in   "TESTING.md"   "docs/AI_COLLAB_WORKFLOW.md"   "docs/TASK_RECORD_TEMPLATE.md"   "docs/TEST_CASE_MATRIX.md"   "docs/DELIVERY_REPORT_TEMPLATE.md"   "docs/GIT_COMMIT_GUIDE.md"
 do
  if ! exists_file "$f"; then
    [[ "$status" == "ready" ]] && status="partial"
    issues+=("missing $f")
  fi
done

if exists_file "README.md" && ! rg -n "文档导航|Documentation" "$ROOT/README.md" >/dev/null 2>&1; then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("README.md has no docs navigation")
fi

if exists_file "AGENTS.md" && ! rg -n "计划|plan review|测试用例|复测|报告|Audit Requirements" "$ROOT/AGENTS.md" >/dev/null 2>&1; then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("AGENTS.md does not describe auditable AI workflow")
fi

if exists_file "TESTING.md" && ! rg -n "test|lint|build|验证|validation" "$ROOT/TESTING.md" >/dev/null 2>&1; then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("TESTING.md lacks concrete validation guidance")
fi

if (( task_count == 0 )); then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("no real task records found")
fi

printf '# Project AI Audit

'
printf -- '- repository: %s
' "$ROOT"
printf -- '- status: **%s**
' "$status"
if [[ -n "$task_dir" ]]; then
  printf -- '- task_dir: %s
' "$task_dir"
else
  printf -- '- task_dir: not_found
'
fi
printf -- '- task_record_count: %s

' "$task_count"

printf '## Issues
'
if ((${#issues[@]} == 0)); then
  printf -- '- none
'
else
  for item in "${issues[@]}"; do
    printf -- '- %s
' "$item"
  done
fi

case "$status" in
  ready) exit 0 ;;
  partial) exit 1 ;;
  not_ready) exit 2 ;;
  *) exit 3 ;;
esac
