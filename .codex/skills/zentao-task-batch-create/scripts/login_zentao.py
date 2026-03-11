#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.parse

from create_zentao_tasks import DEFAULT_BASE_URL, ZenTaoClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Log in to ZenTao and optionally open a target page.")
    parser.add_argument("--base-url", default=os.environ.get("ZENTAO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--target-path", help="ZenTao path under the base URL, such as task-view-138596.html")
    parser.add_argument("--target-url", help="Absolute ZenTao URL to open after login")
    return parser.parse_args()


def resolve_target_url(base_url: str, target_path: str | None, target_url: str | None) -> str | None:
    if target_path and target_url:
        raise SystemExit("Use only one of --target-path or --target-url")
    if target_path:
        return urllib.parse.urljoin(base_url.rstrip("/") + "/", target_path.lstrip("/"))
    if target_url:
        return target_url
    return None


def main() -> int:
    args = parse_args()
    account = os.environ.get("ZENTAO_ACCOUNT")
    password = os.environ.get("ZENTAO_PASSWORD")
    if not account or not password:
        raise SystemExit("ZENTAO_ACCOUNT and ZENTAO_PASSWORD must be set")

    client = ZenTaoClient(args.base_url, account, password)
    client.login()

    target_url = resolve_target_url(args.base_url, args.target_path, args.target_url)
    result = {
        "base_url": client.base_url,
        "session_name": "zentaosid",
        "session_id": client.session_id,
        "login_url": urllib.parse.urljoin(client.base_url, f"index.html?zentaosid={client.session_id}"),
    }

    if target_url:
        body = client._open(target_url)  # Reuse authenticated opener to validate access.
        result["target_url"] = target_url
        result["target_ok"] = True
        result["target_size"] = len(body)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
