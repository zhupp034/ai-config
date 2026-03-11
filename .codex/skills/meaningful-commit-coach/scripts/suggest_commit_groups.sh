#!/usr/bin/env bash
set -eo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

cd "$ROOT"

if [[ ! -d .git ]]; then
  echo "[error] not a git repository: $ROOT" >&2
  exit 2
fi

lines=()
while IFS= read -r line; do
  lines+=("$line")
done < <(git status --short)

diff_names=()
while IFS= read -r line; do
  [[ -n "$line" ]] && diff_names+=("$line")
done < <(git diff --name-only)

printf '# Commit Group Suggestion\n\n'
printf -- '- repository: %s\n' "$ROOT"

if ((${#lines[@]} == 0)); then
  printf -- '- status: clean\n\n'
  printf '## Suggested Groups\n- none\n'
  exit 0
fi

printf -- '- changed_files: %s\n\n' "${#lines[@]}"

doc_files=()
test_files=()
dep_files=()
generated_files=()
config_files=()
source_files=()
other_files=()
source_group_keys=()
source_group_values=()

contains_value() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

classify_source_group() {
  local file="$1"
  local prefix rest part1 part2
  prefix="${file%%/*}"
  rest="${file#*/}"
  if [[ "$rest" == "$file" ]]; then
    printf '%s' "$file"
    return
  fi
  part1="${rest%%/*}"
  if [[ "$rest" == "$part1" ]]; then
    printf '%s/%s' "$prefix" "$part1"
    return
  fi
  rest="${rest#*/}"
  part2="${rest%%/*}"
  if [[ -n "$part2" && "$part2" != "$rest" ]]; then
    printf '%s/%s/%s' "$prefix" "$part1" "$part2"
  else
    printf '%s/%s' "$prefix" "$part1"
  fi
}

append_group_file() {
  local key="$1"
  local file="$2"
  local i
  for i in "${!source_group_keys[@]}"; do
    if [[ "${source_group_keys[$i]}" == "$key" ]]; then
      if [[ -z "${source_group_values[$i]}" ]]; then
        source_group_values[$i]="$file"
      else
        source_group_values[$i]="${source_group_values[$i]}|$file"
      fi
      return
    fi
  done
  source_group_keys+=("$key")
  source_group_values+=("$file")
}

split_group_value() {
  local value="$1"
  GROUP_FILES=()
  local old_ifs="$IFS"
  IFS='|'
  read -r -a GROUP_FILES <<< "$value"
  IFS="$old_ifs"
}

join_files() {
  local out=""
  local f
  for f in "$@"; do
    if [[ -z "$out" ]]; then
      out="$(printf '%q' "$f")"
    else
      out="$out $(printf '%q' "$f")"
    fi
  done
  printf '%s' "$out"
}

print_group() {
  local title="$1"
  shift
  local -a files=("$@")
  printf '### %s\n' "$title"
  if ((${#files[@]} == 0)); then
    printf -- '- none\n\n'
    return
  fi
  local f
  for f in "${files[@]}"; do
    printf -- '- %s\n' "$f"
  done
  printf '\n'
}

print_suggestion() {
  local title="$1"
  local message="$2"
  shift 2
  local -a files=("$@")
  local add_cmd
  add_cmd="$(join_files "${files[@]}")"
  printf '### %s\n' "$title"
  printf 'message: `%s`\n' "$message"
  if [[ -n "$add_cmd" ]]; then
    printf 'stage: `git add %s`\n' "$add_cmd"
  else
    printf 'stage: inspect manually\n'
  fi
  printf '\n'
}

scope_from_group() {
  local key="$1"
  key="${key#src/}"
  key="${key#app/}"
  key="${key#lib/}"
  key="${key#server/}"
  key="${key#cli/}"
  key="${key#web/}"
  key="${key#shared/}"
  key="${key//\//-}"
  printf '%s' "$key"
}

file_stem() {
  local file="$1"
  local base
  base="${file##*/}"
  base="${base%.*}"
  base="${base%.test}"
  base="${base%.spec}"
  printf '%s' "$base"
}

file_tokens() {
  local file="$1"
  local stem dir tokens
  stem="$(file_stem "$file")"
  dir="${file%/*}"
  dir="${dir##*/}"
  tokens="$stem $dir"
  printf '%s' "$tokens" | tr '/._-' '    '
}

files_related() {
  local source_file="$1"
  local candidate="$2"
  local token
  for token in $(file_tokens "$source_file"); do
    if [[ ${#token} -ge 3 && "$candidate" == *"$token"* ]]; then
      return 0
    fi
  done
  return 1
}

diff_text_for_files() {
  if (($# == 0)); then
    return 0
  fi
  git diff -- "$@" 2>/dev/null || true
}

detect_change_type() {
  local diff_text="$1"
  local files_text="$2"

  if [[ "$files_text" == *"spec"* || "$files_text" == *"test"* ]]; then
    printf '%s' 'test'
    return
  fi
  if [[ "$files_text" == *"docs/"* || "$files_text" == *.md* ]]; then
    printf '%s' 'docs'
    return
  fi
  if [[ "$files_text" == *"package.json"* || "$files_text" == *"yarn.lock"* || "$files_text" == *"pnpm-lock.yaml"* || "$files_text" == *"requirements.txt"* || "$files_text" == *"pyproject.toml"* || "$files_text" == *"go.mod"* || "$files_text" == *"Cargo.toml"* ]]; then
    printf '%s' 'build'
    return
  fi
  if [[ "$diff_text" == *"fix"* || "$diff_text" == *"bug"* || "$diff_text" == *"error"* || "$diff_text" == *"fallback"* || "$diff_text" == *"null"* || "$diff_text" == *"undefined"* || "$diff_text" == *"catch"* || "$diff_text" == *"throw"* ]]; then
    printf '%s' 'fix'
    return
  fi
  if [[ "$diff_text" == *"rename"* || "$diff_text" == *"extract"* || "$diff_text" == *"cleanup"* || "$diff_text" == *"refactor"* ]]; then
    printf '%s' 'refactor'
    return
  fi
  printf '%s' 'feat'
}

build_message() {
  local type="$1"
  local scope="$2"
  case "$type" in
    feat) summary='update business implementation' ;;
    fix) summary='fix business behavior' ;;
    refactor) summary='refactor module structure' ;;
    test) summary='add or update coverage' ;;
    docs) summary='update project docs' ;;
    build) summary='update project dependencies' ;;
    chore) summary='update repository files' ;;
    *) summary='update implementation' ;;
  esac

  if [[ -n "$scope" && "$type" != 'docs' && "$type" != 'build' && "$type" != 'chore' ]]; then
    printf '%s' "$type($scope): $summary"
  else
    printf '%s' "$type: $summary"
  fi
}

for line in "${lines[@]}"; do
  file="${line:3}"
  if [[ "$file" == *" -> "* ]]; then
    file="${file##* -> }"
  fi

  case "$file" in
    docs/*|*.md|*.mdx)
      doc_files+=("$file")
      ;;
    *test*|*spec*|__tests__/*|tests/*|test/*)
      test_files+=("$file")
      ;;
    package.json|yarn.lock|package-lock.json|pnpm-lock.yaml|requirements.txt|pyproject.toml|Pipfile|go.mod|go.sum|Cargo.toml|Cargo.lock)
      dep_files+=("$file")
      ;;
    dist/*|build/*|coverage/*|*.min.js|*.map)
      generated_files+=("$file")
      ;;
    .github/*|.gitlab-ci.yml|.editorconfig|.prettierrc|.prettierrc.*|.eslintrc|.eslintrc.*|tsconfig*.json|vite.config.*|webpack.config.*|rollup.config.*|babel.config.*|jest.config.*)
      config_files+=("$file")
      ;;
    src/*|app/*|lib/*|server/*|cli/*|web/*|shared/*)
      source_files+=("$file")
      key="$(classify_source_group "$file")"
      append_group_file "$key" "$file"
      ;;
    *)
      other_files+=("$file")
      ;;
  esac
done

printf '## Diff Summary\n'
if ((${#diff_names[@]} == 0)); then
  printf -- '- working tree changes are untracked only or fully staged\n\n'
else
  git diff --stat
  printf '\n'
fi

printf '## File Buckets\n'
print_group 'docs' "${doc_files[@]}"
print_group 'tests' "${test_files[@]}"
print_group 'dependencies' "${dep_files[@]}"
print_group 'generated' "${generated_files[@]}"
print_group 'config' "${config_files[@]}"
print_group 'source' "${source_files[@]}"
print_group 'other' "${other_files[@]}"

printf '## Source Clusters\n'
if ((${#source_group_keys[@]} == 0)); then
  printf -- '- none\n\n'
else
  for i in "${!source_group_keys[@]}"; do
    split_group_value "${source_group_values[$i]}"
    print_group "${source_group_keys[$i]}" "${GROUP_FILES[@]}"
  done
fi

printf '## Suggested Commit Groups\n'
suggestion_count=0
used_doc_files=()
used_test_files=()

for i in "${!source_group_keys[@]}"; do
  group_key="${source_group_keys[$i]}"
  split_group_value "${source_group_values[$i]}"
  group_files=("${GROUP_FILES[@]}")
  scope="$(scope_from_group "$group_key")"
  files_text="$(printf '%s\n' "${group_files[@]}")"
  diff_text="$(diff_text_for_files "${group_files[@]}")"
  change_type="$(detect_change_type "$diff_text" "$files_text")"
  msg="$(build_message "$change_type" "$scope")"

  related_tests=()
  related_docs=()
  for src in "${group_files[@]}"; do
    for f in "${test_files[@]}"; do
      if files_related "$src" "$f"; then
        contains_value "$f" "${related_tests[@]}" || related_tests+=("$f")
        contains_value "$f" "${used_test_files[@]}" || used_test_files+=("$f")
      fi
    done
    for f in "${doc_files[@]}"; do
      if files_related "$src" "$f"; then
        contains_value "$f" "${related_docs[@]}" || related_docs+=("$f")
        contains_value "$f" "${used_doc_files[@]}" || used_doc_files+=("$f")
      fi
    done
  done

  combined=("${group_files[@]}" "${related_tests[@]}" "${related_docs[@]}")
  suggestion_count=$((suggestion_count + 1))
  print_suggestion "$suggestion_count. source cluster ${group_key}" "$msg" "${combined[@]}"
done

remaining_tests=()
for f in "${test_files[@]}"; do
  contains_value "$f" "${used_test_files[@]}" || remaining_tests+=("$f")
done
if ((${#remaining_tests[@]} > 0)); then
  suggestion_count=$((suggestion_count + 1))
  msg="$(build_message test '')"
  print_suggestion "$suggestion_count. standalone test change" "$msg" "${remaining_tests[@]}"
fi

remaining_docs=()
for f in "${doc_files[@]}"; do
  contains_value "$f" "${used_doc_files[@]}" || remaining_docs+=("$f")
done
if ((${#remaining_docs[@]} > 0)); then
  suggestion_count=$((suggestion_count + 1))
  msg="$(build_message docs '')"
  print_suggestion "$suggestion_count. standalone documentation change" "$msg" "${remaining_docs[@]}"
fi

if ((${#dep_files[@]} > 0)); then
  suggestion_count=$((suggestion_count + 1))
  msg="$(build_message build '')"
  print_suggestion "$suggestion_count. dependency change" "$msg" "${dep_files[@]}"
fi
if ((${#config_files[@]} > 0)); then
  suggestion_count=$((suggestion_count + 1))
  msg='chore: update project tooling config'
  print_suggestion "$suggestion_count. config/tooling change" "$msg" "${config_files[@]}"
fi
if ((${#generated_files[@]} > 0)); then
  suggestion_count=$((suggestion_count + 1))
  msg='build: update generated artifacts'
  print_suggestion "$suggestion_count. generated output change" "$msg" "${generated_files[@]}"
fi
if ((${#other_files[@]} > 0)); then
  suggestion_count=$((suggestion_count + 1))
  msg="$(build_message chore '')"
  print_suggestion "$suggestion_count. uncategorized change" "$msg" "${other_files[@]}"
fi
if ((suggestion_count == 0)); then
  printf -- '- no clear grouping found, inspect diffs manually\n\n'
fi

printf '## Risk Hints\n'
risk_found='no'
if ((${#source_group_keys[@]} > 1)); then
  printf -- '- multiple source clusters changed; avoid combining them into one commit unless they are one inseparable task\n'
  risk_found='yes'
fi
if ((${#generated_files[@]} > 0)) && (( ${#source_files[@]} > 0 )); then
  printf -- '- source and generated artifacts are mixed; split them unless the repo requires same-commit dist updates\n'
  risk_found='yes'
fi
if ((${#dep_files[@]} > 0)) && (( ${#source_files[@]} > 0 )); then
  printf -- '- dependency changes are mixed with source changes; separate if possible for easier rollback\n'
  risk_found='yes'
fi
if ((${#config_files[@]} > 0)) && (( ${#source_files[@]} > 0 )); then
  printf -- '- config/tooling updates may deserve a separate commit from behavior changes\n'
  risk_found='yes'
fi
if ((${#other_files[@]} > 0)); then
  printf -- '- uncategorized files exist; inspect them before staging the suggested groups\n'
  risk_found='yes'
fi
if [[ "$risk_found" == 'no' ]]; then
  printf -- '- no obvious mixed-signal risk from file categories\n'
fi
