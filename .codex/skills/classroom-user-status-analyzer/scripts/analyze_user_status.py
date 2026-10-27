#!/usr/bin/env python3
"""Decode interact-classroom compact user tuples from JSON logs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


MEETING_VERSION = 5
FILE_SERVER = "https://file.leke.cn"

ROLE_IDS = {
    "teacher": 101,
    "student": 100,
    "educational": 104,
    "support": 110,
    "assist": 113,
    "groupAssistant": 1000,
    "master": 100001,
    "participant": 100002,
    "audience": 100004,
    "meetingRecorder": 100005,
    "AI": 100006,
    "record": 1100000,
}

PERSON_TYPES = {
    0: "padTeacher",
    1: "teacher",
    2: "student",
    5: "support",
    6: "assist",
    7: "padStudent",
    8: "educational",
    10: "groupAssist",
}

PERSON_TYPE_TO_ROLE = {
    0: ROLE_IDS["teacher"],
    1: ROLE_IDS["teacher"],
    2: ROLE_IDS["student"],
    5: ROLE_IDS["support"],
    6: ROLE_IDS["assist"],
    7: ROLE_IDS["student"],
    8: ROLE_IDS["educational"],
    10: ROLE_IDS["groupAssistant"],
}

ROLE_NAMES = {value: key for key, value in ROLE_IDS.items()}
CLIENT_TYPES = {-1: "null", 0: "flash", 2: "H5", 11: "PC", 21: "PAD", 31: "Android", 32: "IOS"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze compact interact-classroom user-info tuples."
    )
    parser.add_argument("input", nargs="?", help="JSON/JSONL log file, or - for stdin")
    parser.add_argument("--tuple-json", help="Analyze one tuple supplied as JSON")
    parser.add_argument("--teacher", action="store_true", help="Select teacherinfo entries")
    parser.add_argument("--user-id", type=int, help="Select a user ID")
    parser.add_argument("--name", help="Select users by case-insensitive name substring")
    parser.add_argument("--all", action="store_true", help="Return every detected user tuple")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--meeting", action="store_true", help="Force meeting decoding")
    mode.add_argument("--classroom", action="store_true", help="Force classroom decoding")
    args = parser.parse_args()
    if not args.input and not args.tuple_json:
        parser.error("provide an input file/stdin or --tuple-json")
    if args.input and args.tuple_json:
        parser.error("input and --tuple-json are mutually exclusive")
    return args


def load_json_documents(text: str) -> list[Any]:
    text = text.strip()
    if not text:
        raise ValueError("input is empty")
    try:
        value = json.loads(text)
        for _ in range(3):
            if not isinstance(value, str):
                break
            value = json.loads(value)
        return [value]
    except json.JSONDecodeError:
        documents = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON on line {line_number}: {error.msg}"
                ) from error
        if not documents:
            raise ValueError("input contains no JSON documents")
        return documents


def is_user_tuple(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 12
        and isinstance(value[0], (int, float))
        and not isinstance(value[0], bool)
        and isinstance(value[1], (int, float))
        and not isinstance(value[1], bool)
        and isinstance(value[11], dict)
    )


def find_user_tuples(value: Any, path: str = "$", source_key: str = "") -> Iterable[dict[str, Any]]:
    if is_user_tuple(value):
        yield {"path": path, "sourceKey": source_key, "raw": value}
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield from find_user_tuples(child, f"{path}.{key}", str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from find_user_tuples(child, f"{path}[{index}]", source_key)


def walk_values(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


def infer_meeting(documents: list[Any]) -> bool:
    for document in documents:
        for key, value in walk_values(document):
            normalized = key.lower().replace("_", "")
            if normalized == "ismeeting" and value is True:
                return True
            if normalized == "version" and value == MEETING_VERSION:
                return True
            if normalized in {"route", "scene"} and isinstance(value, str):
                lowered = value.lower()
                if lowered.startswith("/meeting") or lowered == "meeting":
                    return True
    return False


def get_person_type(status: int, is_meeting: bool) -> int:
    if is_meeting:
        value = (status >> 11) & 7
        if 1 <= value <= 6:
            return value
        if value == 0:
            return 1
        return 2
    value = (status >> 20) & 31
    if value == 0:
        return 1
    if value == 7:
        return 2
    return value


def trans_null(value: Any) -> Any:
    return "" if value == "null" else value


def format_user(item: list[Any], is_meeting: bool) -> dict[str, Any]:
    status_value = int(item[1] or 0)
    permission_value = int(item[9] or 0)
    person_type = get_person_type(status_value, is_meeting)
    other = item[11] or {}
    avatar_value = trans_null(item[10])

    result = {
        "userId": item[0],
        "status": status_value,
        "statusBinary": format(status_value & 0xFFFFFFFF, "032b"),
        "videoUrl": trans_null(item[2]),
        "audioUrl": trans_null(item[3]),
        "userName": item[6],
        "avatar": f"{FILE_SERVER}/{avatar_value}" if avatar_value else avatar_value,
        "online": bool(item[7]),
        "clientType": item[8],
        "isHandUp": bool((status_value >> 2) & 1),
        "isTalking": bool(status_value & 8),
        "personPermission": bool((status_value >> 3) & 1),
        "personType": person_type,
        "connecting": bool((status_value >> 14) & 1),
        "banned": bool((status_value >> 15) & 1),
        "videoInvite": bool((status_value >> 16) & 1),
        "audioInvite": bool((status_value >> 17) & 1),
        "canAudio": bool(permission_value & 1),
        "canVideo": bool((permission_value >> 1) & 1),
        "canDraw": bool((permission_value >> 2) & 1),
        "canScreen": bool((permission_value >> 3) & 1),
        "roleId": other.get("roleId") or PERSON_TYPE_TO_ROLE.get(person_type),
        "groupId": other.get("assistantGroupId") or 0,
    }

    if is_meeting:
        result["sort"] = (
            (1000 if result["isHandUp"] else 0)
            + (10000 if result["canAudio"] else 0)
            + (100000 if result["canVideo"] else 0)
            + (1000000 if result["online"] else 0)
            + (10000000 if result["canScreen"] else 0)
            + (0 if result["roleId"] == ROLE_IDS["audience"] else 1)
            + (0.1 if result["personPermission"] else 0)
        )
    else:
        result["sort"] = (
            (1000000 if result["online"] else 0)
            + (100000 if result["isHandUp"] else 0)
            + (10000 if result["canAudio"] else 0)
            + (1000 if result["canVideo"] else 0)
        )
    return result


def summarize(formatted: dict[str, Any], is_meeting: bool) -> dict[str, Any]:
    warnings = []
    if formatted["audioUrl"] and not formatted["canAudio"]:
        warnings.append("audioUrl exists while canAudio is false")
    if formatted["videoUrl"] and not formatted["canVideo"]:
        warnings.append("videoUrl exists while canVideo is false")
    return {
        "mode": "meeting" if is_meeting else "classroom",
        "role": ROLE_NAMES.get(formatted["roleId"], "unknown"),
        "personType": PERSON_TYPES.get(formatted["personType"], "unknown"),
        "client": CLIENT_TYPES.get(formatted["clientType"], "unknown"),
        "online": formatted["online"],
        "interaction": {
            key: formatted[key]
            for key in (
                "isHandUp",
                "isTalking",
                "personPermission",
                "connecting",
                "banned",
                "videoInvite",
                "audioInvite",
            )
        },
        "permissions": {
            key: formatted[key]
            for key in ("canAudio", "canVideo", "canDraw", "canScreen")
        },
        "media": {
            "hasAudioUrl": bool(formatted["audioUrl"]),
            "hasVideoUrl": bool(formatted["videoUrl"]),
        },
        "warnings": warnings,
    }


def select_candidates(candidates: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = candidates
    if args.teacher:
        selected = [item for item in selected if item["sourceKey"].lower() == "teacherinfo"]
    if args.user_id is not None:
        selected = [item for item in selected if int(item["raw"][0]) == args.user_id]
    if args.name:
        needle = args.name.casefold()
        selected = [item for item in selected if needle in str(item["raw"][6]).casefold()]

    has_selector = args.teacher or args.user_id is not None or bool(args.name) or args.all
    if not has_selector:
        teachers = [item for item in selected if item["sourceKey"].lower() == "teacherinfo"]
        if teachers:
            return teachers
        if len(selected) == 1:
            return selected
        choices = [f"{item['raw'][0]}:{item['raw'][6]}" for item in selected[:20]]
        raise ValueError(
            "multiple users found; select with --teacher, --user-id, --name, or --all. "
            f"Candidates: {', '.join(choices)}"
        )
    return selected


def main() -> int:
    args = parse_args()
    try:
        if args.tuple_json:
            documents = load_json_documents(args.tuple_json)
        else:
            text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
            documents = load_json_documents(text)

        is_meeting = args.meeting or (not args.classroom and infer_meeting(documents))
        candidates = []
        for document_index, document in enumerate(documents):
            found = list(find_user_tuples(document))
            for item in found:
                item["documentIndex"] = document_index
            candidates.extend(found)
        if not candidates:
            raise ValueError("no compact user-info tuples were found")

        selected = select_candidates(candidates, args)
        if not selected:
            raise ValueError("no user matched the supplied selector")

        users = []
        for candidate in selected:
            formatted = format_user(candidate["raw"], is_meeting)
            users.append(
                {
                    "documentIndex": candidate["documentIndex"],
                    "sourcePath": candidate["path"],
                    "raw": candidate["raw"],
                    "formatted": formatted,
                    "summary": summarize(formatted, is_meeting),
                }
            )
        print(
            json.dumps(
                {"mode": "meeting" if is_meeting else "classroom", "count": len(users), "users": users},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
