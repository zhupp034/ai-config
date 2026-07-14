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

## Superpowers switch

Use the helper below to toggle native skill discovery for `superpowers`:

```bash
/Users/zpp/.codex/scripts/toggle-superpowers.sh status
/Users/zpp/.codex/scripts/toggle-superpowers.sh off
/Users/zpp/.codex/scripts/toggle-superpowers.sh on
```

There is also a `superpowers-toggle` skill for natural-language requests such as
"关掉 superpowers", "打开 superpowers", or "看一下 superpowers 是否开启".

The switch only manages this symlink:

```text
~/.agents/skills/superpowers -> ~/.codex/superpowers/skills
```

It does not delete `/Users/zpp/.codex/superpowers`. Restart Codex after `on` or `off` so skill discovery refreshes.
