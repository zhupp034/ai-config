#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="${HOME}/.agents/skills"
LINK_PATH="${SKILLS_DIR}/superpowers"
TARGET_PATH="${HOME}/.codex/superpowers/skills"
DISABLED_PATH="${SKILLS_DIR}/.superpowers.disabled"

usage() {
  cat <<'USAGE'
Usage: toggle-superpowers.sh on|off|status

Toggles Codex superpowers skill discovery by managing:
  ~/.agents/skills/superpowers -> ~/.codex/superpowers/skills

Restart Codex after changing the switch so skill discovery refreshes.
USAGE
}

status() {
  if [ -L "$LINK_PATH" ] && [ "$(readlink "$LINK_PATH")" = "$TARGET_PATH" ]; then
    echo "superpowers=on link=$LINK_PATH target=$TARGET_PATH"
    return 0
  fi

  if [ -e "$LINK_PATH" ]; then
    echo "superpowers=unknown path_exists=$LINK_PATH target=$(readlink "$LINK_PATH" 2>/dev/null || echo non_symlink)"
    return 1
  fi

  if [ -L "$DISABLED_PATH" ] || [ -e "$DISABLED_PATH" ]; then
    echo "superpowers=off disabled_path=$DISABLED_PATH"
    return 0
  fi

  echo "superpowers=off link_missing=$LINK_PATH"
}

enable_superpowers() {
  if [ ! -d "$TARGET_PATH" ]; then
    echo "target_missing=$TARGET_PATH" >&2
    exit 1
  fi

  mkdir -p "$SKILLS_DIR"

  if [ -L "$LINK_PATH" ] && [ "$(readlink "$LINK_PATH")" = "$TARGET_PATH" ]; then
    status
    return 0
  fi

  if [ -e "$LINK_PATH" ] || [ -L "$LINK_PATH" ]; then
    echo "refusing_to_overwrite=$LINK_PATH" >&2
    exit 1
  fi

  if [ -L "$DISABLED_PATH" ] && [ "$(readlink "$DISABLED_PATH")" = "$TARGET_PATH" ]; then
    mv "$DISABLED_PATH" "$LINK_PATH"
  else
    rm -f "$DISABLED_PATH"
    ln -s "$TARGET_PATH" "$LINK_PATH"
  fi

  status
  echo "restart_required=true"
}

disable_superpowers() {
  mkdir -p "$SKILLS_DIR"

  if [ -L "$LINK_PATH" ] && [ "$(readlink "$LINK_PATH")" = "$TARGET_PATH" ]; then
    rm -f "$DISABLED_PATH"
    mv "$LINK_PATH" "$DISABLED_PATH"
    status
    echo "restart_required=true"
    return 0
  fi

  if [ -e "$LINK_PATH" ]; then
    echo "refusing_to_modify_unknown_path=$LINK_PATH" >&2
    exit 1
  fi

  status
}

case "${1:-}" in
  on|enable)
    enable_superpowers
    ;;
  off|disable)
    disable_superpowers
    ;;
  status)
    status
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
