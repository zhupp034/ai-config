#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="/Users/zpp/.codex"
TARGET_REPO="/Users/zpp/Desktop/codex-config"
TARGET_ROOT="$TARGET_REPO/.codex"

require_path() {
  local path="$1"
  local label="$2"
  if [[ ! -e "$path" ]]; then
    echo "[sync-failed] missing $label: $path" >&2
    exit 1
  fi
}

copy_dir() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  rm -rf "$dst"
  cp -R "$src" "$dst"
}

copy_file() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
}

require_path "$SOURCE_ROOT" "source root"
require_path "$TARGET_REPO" "target repo"

if [[ ! -d "$TARGET_REPO/.git" ]]; then
  echo "[sync-failed] target repo is not a git repository: $TARGET_REPO" >&2
  exit 1
fi

mkdir -p "$TARGET_ROOT"

copy_dir "$SOURCE_ROOT/skills" "$TARGET_ROOT/skills"
copy_dir "$SOURCE_ROOT/rules" "$TARGET_ROOT/rules"
copy_file "$SOURCE_ROOT/config.toml" "$TARGET_ROOT/config.toml"
copy_file "$SOURCE_ROOT/AGENTS.md" "$TARGET_ROOT/AGENTS.md"

mkdir -p "$TARGET_ROOT/memories"
copy_file "$SOURCE_ROOT/memories/term-glossary.json" "$TARGET_ROOT/memories/term-glossary.json"

find "$TARGET_REPO" -name '.DS_Store' -delete

git -C "$TARGET_REPO" add -A

if [[ -z "$(git -C "$TARGET_REPO" diff --cached --name-only)" ]]; then
  echo "[sync-skipped] no codex config changes to commit"
  exit 0
fi

commit_message="chore: sync codex config"
git -C "$TARGET_REPO" commit -m "$commit_message" >/dev/null
echo "[sync-committed] $commit_message"

if [[ -z "$(git -C "$TARGET_REPO" remote)" ]]; then
  echo "[sync-failed] target repo has no configured git remote" >&2
  exit 1
fi

if git -C "$TARGET_REPO" push >/dev/null 2>&1; then
  echo "[sync-pushed] origin updated"
  exit 0
fi

git -C "$TARGET_REPO" push -u origin HEAD >/dev/null
echo "[sync-pushed] origin updated"
