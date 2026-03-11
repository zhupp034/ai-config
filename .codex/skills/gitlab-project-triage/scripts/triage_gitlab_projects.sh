#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

printf '# GitLab Project Triage

'
printf '| repo | stack_signal | agents | readme | priority_hint | next_action |
'
printf '| --- | --- | --- | --- | --- | --- |
'

find "$ROOT" -mindepth 1 -maxdepth 1 -type d | sort | while read -r repo; do
  name="$(basename "$repo")"
  if [[ ! -d "$repo/.git" ]]; then
    continue
  fi

  stack_signal="none"
  if [[ -f "$repo/package.json" ]]; then
    stack_signal="node"
  elif [[ -f "$repo/pyproject.toml" || -f "$repo/requirements.txt" ]]; then
    stack_signal="python"
  elif [[ -f "$repo/go.mod" ]]; then
    stack_signal="go"
  fi

  agents="no"
  [[ -f "$repo/AGENTS.md" ]] && agents="yes"

  readme="no"
  [[ -f "$repo/README.md" ]] && readme="yes"

  priority_hint="P1"
  next_action="project-ai-audit"

  if [[ "$agents" == "no" ]]; then
    priority_hint="P0"
    next_action="project-ai-init"
  elif [[ "$readme" == "no" ]]; then
    priority_hint="P0"
    next_action="project-ai-audit"
  fi

  if [[ "$stack_signal" == "none" ]]; then
    priority_hint="P2"
    next_action="none"
  fi

  printf '| %s | %s | %s | %s | %s | %s |
' "$name" "$stack_signal" "$agents" "$readme" "$priority_hint" "$next_action"
done
