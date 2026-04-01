#!/usr/bin/env bash

project_ai_init_resolve_scope() {
  local repo_root_input="${1:-.}"
  local scope_input="${2:-.}"

  PROJECT_AI_INIT_REPO_ROOT="$(cd "$repo_root_input" && pwd)"

  local target_input="$PROJECT_AI_INIT_REPO_ROOT"
  if [[ "$scope_input" != "." ]]; then
    target_input="$PROJECT_AI_INIT_REPO_ROOT/$scope_input"
  fi

  PROJECT_AI_INIT_TARGET_ROOT="$(cd "$target_input" && pwd)"

  case "$PROJECT_AI_INIT_TARGET_ROOT" in
    "$PROJECT_AI_INIT_REPO_ROOT"|"$PROJECT_AI_INIT_REPO_ROOT"/*) ;;
    *)
      printf 'scope must stay inside repo root: %s\n' "$scope_input" >&2
      return 1
      ;;
  esac

  if [[ "$PROJECT_AI_INIT_TARGET_ROOT" == "$PROJECT_AI_INIT_REPO_ROOT" ]]; then
    PROJECT_AI_INIT_SCOPE="."
  else
    PROJECT_AI_INIT_SCOPE="${PROJECT_AI_INIT_TARGET_ROOT#$PROJECT_AI_INIT_REPO_ROOT/}"
  fi
}

project_ai_init_target_file_exists() {
  [[ -f "$PROJECT_AI_INIT_TARGET_ROOT/$1" ]]
}

project_ai_init_target_dir_exists() {
  [[ -d "$PROJECT_AI_INIT_TARGET_ROOT/$1" ]]
}

project_ai_init_matches_product_code() {
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
    "$pattern" "$PROJECT_AI_INIT_TARGET_ROOT" >/dev/null 2>&1
}

project_ai_init_matches_product_path() {
  rg --files "$PROJECT_AI_INIT_TARGET_ROOT" \
    | rg -v '/(docs|skills|scripts|test|tests)/' \
    | rg -n "$1" >/dev/null 2>&1
}

project_ai_init_detect_integrations() {
  PROJECT_AI_INIT_INTEGRATIONS_SIGNAL=""

  if project_ai_init_target_dir_exists "sdk" \
    || project_ai_init_target_dir_exists "integrations" \
    || project_ai_init_target_dir_exists "clients" \
    || project_ai_init_target_dir_exists "third_party" \
    || project_ai_init_target_dir_exists "proto" \
    || project_ai_init_target_dir_exists "protobuf"; then
    PROJECT_AI_INIT_INTEGRATIONS_SIGNAL="directory"
    return 0
  fi

  if project_ai_init_matches_product_path '(^|/)(openapi|swagger)([^/]*\.(json|ya?ml|ts|js)|/)|(^|/).*\.proto$|(^|/)(proto|protobuf)(/|$)'; then
    PROJECT_AI_INIT_INTEGRATIONS_SIGNAL="path"
    return 0
  fi

  if project_ai_init_matches_product_code 'openapi-generator|swagger-codegen|openapi[[:space:]_-]generator|grpc|protobuf|\.proto|third[- ]party|client[[:space:]_-]wrapper'; then
    PROJECT_AI_INIT_INTEGRATIONS_SIGNAL="code"
    return 0
  fi

  return 1
}
