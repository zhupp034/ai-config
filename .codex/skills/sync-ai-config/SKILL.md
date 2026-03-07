---
name: sync-ai-config
description: Sync the portable subset of the local Codex configuration to the dedicated git repository at `/Users/zpp/Desktop/codex-config` and push it to the configured remote. Use when `.codex` skills, glossary, rules, or config files change and those changes should be copied, committed, and synced to GitHub.
---

# Sync AI Config

## Overview

Keep the tracked Codex configuration in `/Users/zpp/Desktop/codex-config` aligned with the live files under `/Users/zpp/.codex`, then commit and push the result when anything changed.

## Workflow

1. Use `scripts/sync_codex_config.sh`.
2. Let the script copy the portable subset from `/Users/zpp/.codex` into `/Users/zpp/Desktop/codex-config/.codex`.
3. Review the sync summary:
   - `[sync-skipped]` means there were no file changes
   - `[sync-committed]` means a local commit was created
   - `[sync-pushed]` means the remote push succeeded
4. If the command reports a missing git remote or non-git target directory, fix the repository setup before retrying.
5. If the command fails on push because of network restrictions, rerun it with the required permission so the remote sync can complete.

## Tracked Config Scope

The sync script copies only the portable config subset:

- `/Users/zpp/.codex/skills/`
- `/Users/zpp/.codex/memories/term-glossary.json`
- `/Users/zpp/.codex/rules/`
- `/Users/zpp/.codex/config.toml`
- `/Users/zpp/.codex/AGENTS.md`

It does not copy runtime state such as auth, sessions, sqlite databases, history, logs, or temporary files.

## Quick Start

```bash
bash scripts/sync_codex_config.sh
```

## Resources

- `scripts/sync_codex_config.sh`: Sync the tracked Codex config subset into `/Users/zpp/Desktop/codex-config`, create a git commit if needed, and push the repository remote.
