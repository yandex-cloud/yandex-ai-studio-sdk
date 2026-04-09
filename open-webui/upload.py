#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests

ENV_TOKEN_VAR = "OPENWEBUI_API_TOKEN"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default='http://localhost:8000'
    )
    return parser.parse_args()


def get_token() -> str:
    token = os.environ.get(ENV_TOKEN_VAR, "").strip()
    if not token:
        print(f"Environment variable '{ENV_TOKEN_VAR}' is not set.", file=sys.stderr)
        sys.exit(1)
    return token


_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("filter", r"^class\s+Filter\s*[:(]"),
    ("action", r"^class\s+Action\s*[:(]"),
    ("pipe", r"^class\s+Pipe\s*[:(]"),
]


def detect_type(source: str) -> str:
    for func_type, pattern in _TYPE_PATTERNS:
        if re.search(pattern, source, re.MULTILINE):
            return func_type
    return "filter"


def to_func_id(folder_name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", folder_name.lower()).strip("_")


def to_func_name(folder_name: str) -> str:
    return folder_name.replace("-", " ").replace("_", " ").title()


def discover_functions(base_dir: Path) -> list[dict]:
    found = []
    for item in sorted(base_dir.iterdir()):
        if not item.is_dir():
            continue
        py_file = item / f"{item.name}.py"
        if py_file.is_file():
            found.append({"dir": item, "file": py_file, "folder_name": item.name})
    return found


def api_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def function_exists(base_url: str, headers: dict, func_id: str) -> bool:
    url = f"{base_url}/api/v1/functions/id/{func_id}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.status_code == 200
    except requests.RequestException:
        return False


def create_function(base_url: str, headers: dict, payload: dict) -> requests.Response:
    return requests.post(
        f"{base_url}/api/v1/functions/create",
        headers=headers,
        json=payload,
        timeout=30,
    )


def update_function(base_url: str, headers: dict, func_id: str, payload: dict) -> requests.Response:
    return requests.post(
        f"{base_url}/api/v1/functions/id/{func_id}/update",
        headers=headers,
        json=payload,
        timeout=30,
    )


def upload_function(base_url: str, headers: dict, info: dict) -> bool:
    folder_name: str = info["folder_name"]
    py_file: Path = info["file"]

    try:
        source = py_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"  Failed to read file: {exc}")
        return False

    func_id = to_func_id(folder_name)
    func_name = to_func_name(folder_name)
    func_type = detect_type(source)

    payload = {
        "id": func_id,
        "name": func_name,
        "type": func_type,
        "content": source,
        "meta": {
            "description": func_name,
            "manifest": {},
        },
        "is_active": True,
        "is_global": False,
    }

    exists = function_exists(base_url, headers, func_id)
    action = "update" if exists else "create"
    print(f"  {action} | id: {func_id} | type: {func_type}")

    response = update_function(base_url, headers, func_id, payload) if exists else create_function(base_url, headers, payload)

    if response.status_code == 200:
        print(f"  OK: {func_name}")
        return True

    print(f"  HTTP error {response.status_code}: {response.text[:300]}")
    return False


def main() -> None:
    args = parse_args()
    token = get_token()
    base_url = args.url.rstrip("/")
    headers = api_headers(token)
    script_dir = Path(__file__).parent.resolve()

    functions = discover_functions(script_dir)

    if not functions:
        print("No functions found.")
        sys.exit(0)

    print(f"Found {len(functions)} function(s)\n")

    ok_count = 0
    err_count = 0

    for info in functions:
        print(f"[{info['folder_name']}]")
        if upload_function(base_url, headers, info):
            ok_count += 1
        else:
            err_count += 1
        print()

    print(f"Done: {ok_count} succeeded, {err_count} failed")

    if err_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
