# codex-config

This repository tracks the portable subset of the local Codex configuration.

Included:

- `.codex/skills/`
- `.codex/memories/term-glossary.json`
- `.codex/rules/`
- `.codex/config.toml`
- `.codex/AGENTS.md`

Excluded from sync:

- auth or credential files
- session history and logs
- sqlite databases and runtime state
- shell snapshots and temp files

Recommended update flow:

1. Edit the real files under `/Users/zpp/.codex/`.
2. Copy changed portable files into this repo.
3. Commit and push this repo.
