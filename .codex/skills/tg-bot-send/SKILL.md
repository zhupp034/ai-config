---
name: tg-bot-send
description: Use when the user wants to send a Telegram Bot message through the existing bot token and chat ID flow, especially when configuration is managed in /Users/zpp/.codex/secrets/common.env, falls back to /Users/zpp/Desktop/github/ai-goofish-monitor/.env, or should be overridden for another bot, chat, or proxy base URL.
---

# TG Bot Send

Send Telegram Bot messages through the Telegram Bot API.

## Default config source

By default the bundled script reads these config files in order:

- `/Users/zpp/.codex/secrets/common.env`
- `/Users/zpp/Desktop/github/ai-goofish-monitor/.env`

Expected keys:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_API_BASE_URL` (optional, defaults to `https://api.telegram.org`)
- `TELEGRAM_HTTP_PROXY` (optional, for local HTTP proxy such as `http://127.0.0.1:7897`)
- `TELEGRAM_HTTPS_PROXY` (optional, preferred for HTTPS Telegram Bot API traffic)

Config precedence is:

1. CLI flags
2. `~/.codex/secrets/common.env`
3. Default or supplied `.env` file
4. Current shell environment variables
5. Built-in API base URL default

This is intentional: `common.env` is already used for shared GitLab and ZenTao
credentials, so Telegram bot settings now follow the same primary secret source.

## Before sending

- Confirm the final message content and target with the user before executing a real send.
- Help, dry-run, and config inspection commands are safe to run without confirmation.

## Command

```bash
python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py "message text"
```

## Useful options

- `--env-file /path/to/.env`
- `--token <bot-token>`
- `--chat-id <chat-id>`
- `--api-base-url <proxy-or-api-base-url>`
- `--http-proxy <proxy-url>`
- `--https-proxy <proxy-url>`
- `--parse-mode HTML|Markdown|MarkdownV2|none`
- `--stdin` to read message text from stdin
- `--dry-run` to validate resolved config without sending
- `--json` for machine-readable output

## Examples

Send with the default secret chain:

```bash
python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py "测试消息"
```

Validate config without sending:

```bash
python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py --dry-run --json "测试消息"
```

Use another `.env` file:

```bash
python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py \
  --env-file /path/to/.env \
  "测试消息"
```

Pipe multiline content:

```bash
cat /tmp/message.txt | python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py --stdin
```

Override chat or token explicitly:

```bash
python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py \
  --token "$TELEGRAM_BOT_TOKEN" \
  --chat-id "$TELEGRAM_CHAT_ID" \
  "测试消息"
```

Use the shared local proxy explicitly when direct network access is blocked:

```bash
python3 /Users/zpp/.codex/skills/tg-bot-send/scripts/send_tg_bot.py \
  --https-proxy http://127.0.0.1:7897 \
  "测试消息"
```

## Failure handling

- If token or chat ID is missing, surface a clear configuration error.
- If Telegram returns `ok: false`, surface Telegram's `description`.
- If direct access to `api.telegram.org` is blocked, store `TELEGRAM_HTTPS_PROXY` in `common.env` or pass `--https-proxy` explicitly.
