#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=project_ai_init_common.sh
source "$SCRIPT_DIR/project_ai_init_common.sh"

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

conditional_labels=()
conditional_targets=()
conditional_existing=()
missing_core=()
missing_recommended=()
missing_conditional=()

exists_file() {
  project_ai_init_target_file_exists "$1"
}

has_routes="no"
has_events="no"
has_integrations="no"
has_domain_context="no"

if project_ai_init_matches_product_code 'react-router|vue-router|next/navigation|next/router|Route::|gin\.|mux\.|chi\.' || project_ai_init_matches_product_path '(^|/)(routes?|router)\.(ts|js|tsx|jsx|mjs|cjs|py|go|rb|php)$|(^|/)urls\.py$'; then
  has_routes="yes"
  conditional_labels+=("routes")
  conditional_targets+=("docs/ROUTES_AND_ACCESS.md")
fi

if project_ai_init_matches_product_code 'websocket|socket\.io|WebSocket|event bus|eventbus|pubsub|pub/sub|message queue|kafka|rabbitmq|nats|consumer|producer|stream handler'; then
  has_events="yes"
  conditional_labels+=("events")
  conditional_targets+=("docs/EVENT_AND_MESSAGE_FLOW.md")
fi

if project_ai_init_detect_integrations; then
  has_integrations="yes"
fi
if [[ "$has_integrations" == "yes" ]]; then
  conditional_labels+=("integrations")
  conditional_targets+=("docs/INTEGRATION_DEPENDENCIES.md")
fi

if project_ai_init_matches_product_code 'workflow|state machine|approval|审批|permission|权限|tenant|租户|role|状态流转|domain model|聚合|订单|支付|库存|subscription'; then
  has_domain_context="yes"
  conditional_labels+=("domain")
  conditional_targets+=("docs/DOMAIN_CONTEXT.md")
fi

legacy_equivalent() {
  case "$1" in
    "docs/DOMAIN_CONTEXT.md")
      exists_file "docs/BUSINESS_SCENARIO_MAP.md"
      ;;
    "docs/EVENT_AND_MESSAGE_FLOW.md")
      exists_file "docs/SOCKET_PROTOCOL_MAP.md"
      ;;
    "docs/INTEGRATION_DEPENDENCIES.md")
      exists_file "docs/SDK_USAGE.md"
      ;;
    *)
      return 1
      ;;
  esac
}

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

for index in "${!conditional_targets[@]}"; do
  target="${conditional_targets[$index]}"
  if exists_file "$target"; then
    conditional_existing+=("$target")
    continue
  fi
  if legacy_equivalent "$target"; then
    case "$target" in
      "docs/DOMAIN_CONTEXT.md") conditional_existing+=("docs/BUSINESS_SCENARIO_MAP.md (legacy)") ;;
      "docs/EVENT_AND_MESSAGE_FLOW.md") conditional_existing+=("docs/SOCKET_PROTOCOL_MAP.md (legacy)") ;;
      "docs/INTEGRATION_DEPENDENCIES.md") conditional_existing+=("docs/SDK_USAGE.md (legacy)") ;;
    esac
    continue
  fi
  missing_conditional+=("$target")
done

readme_has_nav="no"
agents_has_docs_index="no"
agents_has_delivery_flow="no"
agents_has_md_sync_rule="no"
workflow_has_md_sync_rule="no"
task_template_has_md_sync_fields="no"

if exists_file "README.md" && rg -n '文档导航|Documentation|Docs Index|Project Docs' "$PROJECT_AI_INIT_TARGET_ROOT/README.md" >/dev/null 2>&1; then
  readme_has_nav="yes"
fi

if exists_file "AGENTS.md" && rg -n '项目文档索引|Project Docs Index|关键 Markdown|Markdown 文档' "$PROJECT_AI_INIT_TARGET_ROOT/AGENTS.md" >/dev/null 2>&1; then
  agents_has_docs_index="yes"
fi

if exists_file "AGENTS.md" && rg -n '计划|review|测试|复测|报告|交付|delivery|traceability|task record' "$PROJECT_AI_INIT_TARGET_ROOT/AGENTS.md" >/dev/null 2>&1; then
  agents_has_delivery_flow="yes"
fi

if exists_file "AGENTS.md" && rg -n '文档同步|Markdown 同步|无对应文档.*新建|skills/md-doc-sync/SKILL.md' "$PROJECT_AI_INIT_TARGET_ROOT/AGENTS.md" >/dev/null 2>&1; then
  agents_has_md_sync_rule="yes"
fi

if exists_file "docs/AI_COLLAB_WORKFLOW.md" && rg -n '无对应文档.*新建|skills/md-doc-sync/SKILL.md|Markdown' "$PROJECT_AI_INIT_TARGET_ROOT/docs/AI_COLLAB_WORKFLOW.md" >/dev/null 2>&1; then
  workflow_has_md_sync_rule="yes"
fi

if exists_file "docs/TASK_RECORD_TEMPLATE.md" && rg -n '同步更新文档|新建文档|未更新原因|Documentation Sync' "$PROJECT_AI_INIT_TARGET_ROOT/docs/TASK_RECORD_TEMPLATE.md" >/dev/null 2>&1; then
  task_template_has_md_sync_fields="yes"
fi

recommended_total_count=${#recommended_files[@]}
recommended_present_count=$((recommended_total_count - ${#missing_recommended[@]}))
quality_signal_total_count=6
quality_signal_present_count=0

for quality_flag in \
  "$readme_has_nav" \
  "$agents_has_docs_index" \
  "$agents_has_delivery_flow" \
  "$agents_has_md_sync_rule" \
  "$workflow_has_md_sync_rule" \
  "$task_template_has_md_sync_fields"; do
  if [[ "$quality_flag" == "yes" ]]; then
    quality_signal_present_count=$((quality_signal_present_count + 1))
  fi
done

maturity_profile="bootstrap_needed"
recommended_follow_up="project-ai-init"
if ((${#missing_core[@]} == 0)) && ((quality_signal_present_count == quality_signal_total_count)) && ((recommended_present_count >= recommended_total_count - 1)); then
  maturity_profile="mature_baseline"
fi

state="initialized"
if ((${#missing_core[@]} > 0)); then
  state="not_initialized"
elif ((${#missing_recommended[@]} > 0)) || ((${#missing_conditional[@]} > 0)) || [[ "$readme_has_nav" == "no" ]] || [[ "$agents_has_docs_index" == "no" ]] || [[ "$agents_has_delivery_flow" == "no" ]] || [[ "$agents_has_md_sync_rule" == "no" ]] || [[ "$workflow_has_md_sync_rule" == "no" ]] || [[ "$task_template_has_md_sync_fields" == "no" ]]; then
  state="partial"
fi

case "$state" in
  initialized)
    recommended_follow_up="none"
    ;;
  partial)
    if [[ "$maturity_profile" == "mature_baseline" ]]; then
      recommended_follow_up="project-ai-audit"
    fi
    ;;
esac

printf "# AI Init Check\n\n"
printf -- "- repository: %s\n" "$PROJECT_AI_INIT_REPO_ROOT"
printf -- "- target_root: %s\n" "$PROJECT_AI_INIT_TARGET_ROOT"
printf -- "- scope: %s\n" "$PROJECT_AI_INIT_SCOPE"
printf -- "- state: **%s**\n" "$state"
printf -- "- maturity_profile: %s\n" "$maturity_profile"
printf -- "- recommended_follow_up: %s\n" "$recommended_follow_up"
printf -- "- recommended_docs_coverage: %s/%s\n" "$recommended_present_count" "$recommended_total_count"
printf -- "- quality_signal_coverage: %s/%s\n" "$quality_signal_present_count" "$quality_signal_total_count"
printf -- "- readme_has_docs_nav: %s\n" "$readme_has_nav"
printf -- "- agents_has_docs_index: %s\n" "$agents_has_docs_index"
printf -- "- agents_has_delivery_flow: %s\n" "$agents_has_delivery_flow"
printf -- "- agents_has_md_sync_rule: %s\n" "$agents_has_md_sync_rule"
printf -- "- workflow_has_md_sync_rule: %s\n" "$workflow_has_md_sync_rule"
printf -- "- task_template_has_md_sync_fields: %s\n" "$task_template_has_md_sync_fields"
printf -- "- detected_routes: %s\n" "$has_routes"
printf -- "- detected_events: %s\n" "$has_events"
printf -- "- detected_integrations: %s\n" "$has_integrations"
printf -- "- detected_domain_context: %s\n\n" "$has_domain_context"

printf "## Core Files\n"
for f in "${core_files[@]}"; do
  if exists_file "$f"; then
    printf -- "- [x] %s\n" "$f"
  else
    printf -- "- [ ] %s\n" "$f"
  fi
done

printf "\n## Recommended Files\n"
for f in "${recommended_files[@]}"; do
  if exists_file "$f"; then
    printf -- "- [x] %s\n" "$f"
  else
    printf -- "- [ ] %s\n" "$f"
  fi
done

if ((${#conditional_targets[@]} > 0)); then
  printf "\n## Conditional Files\n"
  for f in "${conditional_targets[@]}"; do
    if exists_file "$f"; then
      printf -- "- [x] %s\n" "$f"
    elif legacy_equivalent "$f"; then
      case "$f" in
        "docs/DOMAIN_CONTEXT.md") printf -- "- [x] docs/BUSINESS_SCENARIO_MAP.md (legacy)\n" ;;
        "docs/EVENT_AND_MESSAGE_FLOW.md") printf -- "- [x] docs/SOCKET_PROTOCOL_MAP.md (legacy)\n" ;;
        "docs/INTEGRATION_DEPENDENCIES.md") printf -- "- [x] docs/SDK_USAGE.md (legacy)\n" ;;
      esac
    else
      printf -- "- [ ] %s\n" "$f"
    fi
  done
fi

if ((${#missing_core[@]} > 0)); then
  printf "\n## Missing Core\n"
  for f in "${missing_core[@]}"; do
    printf -- "- %s\n" "$f"
  done
fi

if ((${#missing_recommended[@]} > 0)); then
  printf "\n## Missing Recommended\n"
  for f in "${missing_recommended[@]}"; do
    printf -- "- %s\n" "$f"
  done
fi

if ((${#missing_conditional[@]} > 0)); then
  printf "\n## Missing Conditional\n"
  for f in "${missing_conditional[@]}"; do
    printf -- "- %s\n" "$f"
  done
fi

case "$state" in
  initialized) exit 0 ;;
  partial) exit 1 ;;
  not_initialized) exit 2 ;;
  *) exit 3 ;;
esac
