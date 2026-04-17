#!/usr/bin/env python3
"""Send a Telegram Bot message using shared secret defaults plus optional overrides."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


COMMON_ENV_FILE = "/Users/zpp/.codex/secrets/common.env"
DEFAULT_ENV_FILE = "/Users/zpp/Desktop/github/ai-goofish-monitor/.env"
DEFAULT_API_BASE_URL = "https://api.telegram.org"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Send a Telegram Bot message. Defaults to "
            f"{COMMON_ENV_FILE} first, then {DEFAULT_ENV_FILE}, "
            "for TELEGRAM_* settings."
        )
    )
    parser.add_argument(
        "message",
        nargs="*",
        help="Message text when not using --stdin",
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help=f"Secondary .env file path. Defaults to {DEFAULT_ENV_FILE}",
    )
    parser.add_argument("--token", help="Override TELEGRAM_BOT_TOKEN")
    parser.add_argument("--chat-id", help="Override TELEGRAM_CHAT_ID")
    parser.add_argument("--api-base-url", help="Override TELEGRAM_API_BASE_URL")
    parser.add_argument(
        "--http-proxy",
        help="Override TELEGRAM_HTTP_PROXY / HTTP_PROXY for plain HTTP requests.",
    )
    parser.add_argument(
        "--https-proxy",
        help="Override TELEGRAM_HTTPS_PROXY / HTTPS_PROXY for HTTPS requests.",
    )
    parser.add_argument(
        "--parse-mode",
        choices=["HTML", "Markdown", "MarkdownV2", "none"],
        default="HTML",
        help="Telegram parse mode. Use 'none' to omit parse_mode.",
    )
    parser.add_argument(
        "--disable-preview",
        action="store_true",
        help="Disable web page preview generation.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read the message body from stdin instead of positional text.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds. Defaults to 10.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve config and payload but do not send the request.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    return parser.parse_args()


def parse_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path or not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as file_obj:
        for raw_line in file_obj:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if value and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            values[key] = value
    return values


def first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def lookup_value(keys: tuple[str, ...], *sources: dict[str, str]) -> str | None:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value:
                return value
    return None


def redact_token(token: str | None) -> str | None:
    if not token:
        return None
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}...{token[-4:]}"


def redact_chat_id(chat_id: str | None) -> str | None:
    if not chat_id:
        return None
    if len(chat_id) <= 4:
        return "*" * len(chat_id)
    return f"{chat_id[:2]}...{chat_id[-2:]}"


def redact_proxy_url(proxy_url: str | None) -> str | None:
    if not proxy_url:
        return None

    parsed = urllib.parse.urlsplit(proxy_url)
    if "@" not in parsed.netloc:
        return proxy_url

    _, hostinfo = parsed.netloc.rsplit("@", 1)
    redacted = urllib.parse.SplitResult(
        scheme=parsed.scheme,
        netloc=f"***:***@{hostinfo}",
        path=parsed.path,
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urllib.parse.urlunsplit(redacted)


def fail(message: str, *, json_output: bool = False, extra: dict[str, Any] | None = None) -> int:
    payload: dict[str, Any] = {"ok": False, "error": message}
    if extra:
        payload.update(extra)
    if json_output:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(message, file=sys.stderr)
    return 1


def emit(payload: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False))
        return

    if payload.get("ok") and payload.get("dry_run"):
        print("Dry run OK")
        print(f"env_file: {payload['env_file']}")
        print(f"token: {payload['token']}")
        print(f"chat_id: {payload['chat_id']}")
        print(f"api_base_url: {payload['api_base_url']}")
        print(f"message_length: {payload['message_length']}")
        return

    if payload.get("ok"):
        print(
            "Sent Telegram message "
            f"(chat_id={payload['chat_id']}, message_id={payload.get('message_id')})"
        )
        return

    print(payload.get("error", "Unknown error"), file=sys.stderr)


def resolve_message(args: argparse.Namespace) -> str:
    if args.stdin and args.message:
        raise ValueError("Pass message text either via stdin or positional args, not both.")

    if args.stdin:
        message = sys.stdin.read()
    else:
        message = " ".join(args.message)

    message = message.strip()
    if not message:
        raise ValueError("Message text is empty.")
    return message


def resolve_config(args: argparse.Namespace) -> tuple[dict[str, str], dict[str, Any]]:
    common_env_values = parse_env_file(COMMON_ENV_FILE)
    env_file_values = parse_env_file(args.env_file)
    config_sources = (common_env_values, env_file_values, os.environ)

    token = (
        args.token
        or common_env_values.get("TELEGRAM_BOT_TOKEN")
        or env_file_values.get("TELEGRAM_BOT_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN")
    )
    chat_id = (
        args.chat_id
        or common_env_values.get("TELEGRAM_CHAT_ID")
        or env_file_values.get("TELEGRAM_CHAT_ID")
        or os.environ.get("TELEGRAM_CHAT_ID")
    )
    api_base_url = (
        args.api_base_url
        or common_env_values.get("TELEGRAM_API_BASE_URL")
        or env_file_values.get("TELEGRAM_API_BASE_URL")
        or os.environ.get("TELEGRAM_API_BASE_URL")
        or DEFAULT_API_BASE_URL
    ).rstrip("/")
    http_proxy = first_non_empty(
        args.http_proxy,
        lookup_value(
            ("TELEGRAM_HTTP_PROXY", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"),
            *config_sources,
        ),
    )
    https_proxy = first_non_empty(
        args.https_proxy,
        lookup_value(
            (
                "TELEGRAM_HTTPS_PROXY",
                "HTTPS_PROXY",
                "https_proxy",
                "TELEGRAM_HTTP_PROXY",
                "HTTP_PROXY",
                "http_proxy",
                "ALL_PROXY",
                "all_proxy",
            ),
            *config_sources,
        ),
    )

    config = {
        "token": token or "",
        "chat_id": chat_id or "",
        "api_base_url": api_base_url,
        "http_proxy": http_proxy or "",
        "https_proxy": https_proxy or "",
    }
    meta = {
        "common_env_file": COMMON_ENV_FILE,
        "common_env_exists": os.path.exists(COMMON_ENV_FILE),
        "env_file": args.env_file,
        "env_file_exists": os.path.exists(args.env_file),
    }
    return config, meta


def send_message(
    *,
    token: str,
    chat_id: str,
    api_base_url: str,
    http_proxy: str,
    https_proxy: str,
    text: str,
    parse_mode: str,
    disable_preview: bool,
    timeout: float,
) -> dict[str, Any]:
    url = f"{api_base_url}/bot{token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_preview,
    }
    if parse_mode != "none":
        payload["parse_mode"] = parse_mode

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    proxies: dict[str, str] = {}
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy
    elif http_proxy:
        proxies["https"] = http_proxy
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))

    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
            description = parsed.get("description") or body
        except json.JSONDecodeError:
            description = body or f"HTTP {exc.code}"
        raise RuntimeError(f"Telegram HTTP error: {description}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Telegram request failed: {exc.reason}") from exc

    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Telegram returned non-JSON response: {body}") from exc

    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram returned ok=false"))

    return result


def main() -> int:
    args = parse_args()

    try:
        message = resolve_message(args)
    except ValueError as exc:
        return fail(str(exc), json_output=args.json)

    config, meta = resolve_config(args)
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", config["token"]),
            ("TELEGRAM_CHAT_ID", config["chat_id"]),
        )
        if not value
    ]
    if missing:
        return fail(
            f"Missing required config: {', '.join(missing)}",
            json_output=args.json,
            extra=meta,
        )

    dry_run_payload = {
        "ok": True,
        "dry_run": True,
        "common_env_file": meta["common_env_file"],
        "common_env_exists": meta["common_env_exists"],
        "env_file": meta["env_file"],
        "env_file_exists": meta["env_file_exists"],
        "token": redact_token(config["token"]),
        "chat_id": redact_chat_id(config["chat_id"]),
        "api_base_url": config["api_base_url"],
        "http_proxy": redact_proxy_url(config["http_proxy"]),
        "https_proxy": redact_proxy_url(config["https_proxy"]),
        "parse_mode": None if args.parse_mode == "none" else args.parse_mode,
        "disable_web_page_preview": args.disable_preview,
        "message_length": len(message),
    }

    if args.dry_run:
        emit(dry_run_payload, json_output=args.json)
        return 0

    try:
        result = send_message(
            token=config["token"],
            chat_id=config["chat_id"],
            api_base_url=config["api_base_url"],
            http_proxy=config["http_proxy"],
            https_proxy=config["https_proxy"],
            text=message,
            parse_mode=args.parse_mode,
            disable_preview=args.disable_preview,
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        return fail(
            str(exc),
            json_output=args.json,
            extra={
                "chat_id": config["chat_id"],
                "api_base_url": config["api_base_url"],
                "http_proxy": redact_proxy_url(config["http_proxy"]),
                "https_proxy": redact_proxy_url(config["https_proxy"]),
            },
        )

    output = {
        "ok": True,
        "chat_id": config["chat_id"],
        "api_base_url": config["api_base_url"],
        "http_proxy": redact_proxy_url(config["http_proxy"]),
        "https_proxy": redact_proxy_url(config["https_proxy"]),
        "message_id": (
            result.get("result", {}).get("message_id")
            if isinstance(result.get("result"), dict)
            else None
        ),
    }
    emit(output, json_output=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
