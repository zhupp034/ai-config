#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
TASK_SLUG="${2:-task}"
ROOT="$(cd "$ROOT" && pwd)"
TASK_DIR="$ROOT/docs/tasks"
TASK_FILE="$TASK_DIR/${TASK_SLUG}.md"
TODAY="$(date +%F)"

mkdir -p "$TASK_DIR"

if [[ -f "$TASK_FILE" ]]; then
  printf '[skip] %s
' "$TASK_FILE"
  exit 0
fi

cat > "$TASK_FILE" <<EOF
# ${TASK_SLUG}

## Basic Info

- date: ${TODAY}
- owner:
- reviewers:
- related issue:

## Plan

## Plan Review

## Implementation

## Code Review

## Test Case Design

## Test Case Review

## Test Execution

## Bugfix And Retest

## Final Report
EOF

printf '[create] %s
' "$TASK_FILE"
