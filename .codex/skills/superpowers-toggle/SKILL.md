---
name: superpowers-toggle
description: Use when the user wants to turn Codex superpowers on or off, check whether superpowers skills are currently enabled, disable or enable the whole superpowers skill pack, or manage the `~/.agents/skills/superpowers` discovery symlink.
---

# Superpowers Toggle

Toggle the whole superpowers skill pack by managing the native skill discovery symlink:

```text
~/.agents/skills/superpowers -> ~/.codex/superpowers/skills
```

Use the helper script instead of editing the symlink by hand:

```bash
/Users/zpp/.codex/scripts/toggle-superpowers.sh status
/Users/zpp/.codex/scripts/toggle-superpowers.sh off
/Users/zpp/.codex/scripts/toggle-superpowers.sh on
```

## Workflow

1. Run `status` first and report whether superpowers is currently `on`, `off`, or `unknown`.
2. For requests like "关掉 superpowers", run `off`.
3. For requests like "打开 superpowers", run `on`.
4. Tell the user that Codex must be restarted or a new session opened after `on` or `off` so skill discovery refreshes.

## Safety

- The script only moves or creates the discovery symlink.
- It does not delete `/Users/zpp/.codex/superpowers`.
- If status is `unknown`, do not overwrite the path automatically; report the path conflict and inspect it first.
