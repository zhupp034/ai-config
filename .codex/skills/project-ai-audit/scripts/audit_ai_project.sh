#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT_DIR="$(cd "$SCRIPT_DIR/../../project-ai-init/scripts" && pwd)"
# shellcheck source=project_ai_init_common.sh
source "$INIT_SCRIPT_DIR/project_ai_init_common.sh"

ROOT="."
SCOPE="."

while (($# > 0)); do
  case "$1" in
    --scope)
      SCOPE="${2:?missing value for --scope}"
      shift 2
      ;;
    --help|-h)
      printf 'usage: %s [repo-root] [--scope <path>]\n' "$(basename "$0")"
      exit 0
      ;;
    *)
      ROOT="$1"
      shift
      ;;
  esac
done

project_ai_init_resolve_scope "$ROOT" "$SCOPE"

exists_file() {
  [[ -f "$PROJECT_AI_INIT_TARGET_ROOT/$1" ]]
}

find_task_dir() {
  local candidate
  for candidate in "docs/tasks" "docs/ai-workflow" "docs/task-records"; do
    if [[ -d "$PROJECT_AI_INIT_TARGET_ROOT/$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

status="ready"
issues=()
recommended_next_action="none"
baseline_state="unknown"
baseline_maturity_profile="unknown"
baseline_recommended_follow_up="unknown"

baseline_output="$(bash "$INIT_SCRIPT_DIR/check_ai_init.sh" "$PROJECT_AI_INIT_REPO_ROOT" --scope "$PROJECT_AI_INIT_SCOPE" 2>&1 || true)"
baseline_state="$(printf '%s\n' "$baseline_output" | sed -n 's/^- state: \*\*\(.*\)\*\*$/\1/p' | head -n 1)"
baseline_maturity_profile="$(printf '%s\n' "$baseline_output" | sed -n 's/^- maturity_profile: \(.*\)$/\1/p' | head -n 1)"
baseline_recommended_follow_up="$(printf '%s\n' "$baseline_output" | sed -n 's/^- recommended_follow_up: \(.*\)$/\1/p' | head -n 1)"

if [[ "$baseline_recommended_follow_up" == "project-ai-init" ]]; then
  status="not_ready"
  recommended_next_action="project-ai-init"
  issues+=("baseline suggests running project-ai-init first")
fi

task_dir=""
if task_dir="$(find_task_dir)"; then
  task_count=$(find "$PROJECT_AI_INIT_TARGET_ROOT/$task_dir" -type f \( -name '*.md' -o -name '*.markdown' \) | wc -l | tr -d ' ')
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

if exists_file "README.md" && ! rg -n "文档导航|Documentation" "$PROJECT_AI_INIT_TARGET_ROOT/README.md" >/dev/null 2>&1; then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("README.md has no docs navigation")
fi

if exists_file "AGENTS.md" && ! rg -n "计划|plan review|测试用例|复测|报告|Audit Requirements" "$PROJECT_AI_INIT_TARGET_ROOT/AGENTS.md" >/dev/null 2>&1; then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("AGENTS.md does not describe auditable AI workflow")
fi

if exists_file "TESTING.md" && ! rg -n "test|lint|build|验证|validation" "$PROJECT_AI_INIT_TARGET_ROOT/TESTING.md" >/dev/null 2>&1; then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("TESTING.md lacks concrete validation guidance")
fi

if (( task_count == 0 )); then
  [[ "$status" == "ready" ]] && status="partial"
  issues+=("no real task records found")
fi

if [[ "$recommended_next_action" == "none" ]]; then
  case "$status" in
    ready) recommended_next_action="none" ;;
    partial) recommended_next_action="manual_refinement" ;;
    not_ready) recommended_next_action="project-ai-init" ;;
  esac
fi

printf '# Project AI Audit

'
printf -- '- repository: %s
' "$PROJECT_AI_INIT_REPO_ROOT"
printf -- '- target_root: %s
' "$PROJECT_AI_INIT_TARGET_ROOT"
printf -- '- scope: %s
' "$PROJECT_AI_INIT_SCOPE"
printf -- '- status: **%s**
' "$status"
printf -- '- baseline_state: %s
' "$baseline_state"
printf -- '- baseline_maturity_profile: %s
' "$baseline_maturity_profile"
printf -- '- baseline_recommended_follow_up: %s
' "$baseline_recommended_follow_up"
printf -- '- recommended_next_action: %s
' "$recommended_next_action"
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
