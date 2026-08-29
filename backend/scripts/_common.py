"""Shared helpers for the one-off FortyGuard API exploration scripts. See README.md."""

import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.config import settings  # noqa: E402

BASE_URL = "https://api.fortyguard.com"
HEADERS = {"api-key": settings.fortyguard_api_key, "Content-Type": "application/json"}

# Small AOI (~450m box) and a date already confirmed to have real data, to keep cost/time down.
TEST_POLYGON_COORDS = [
    [-112.0740, 33.4484],
    [-112.0700, 33.4484],
    [-112.0700, 33.4524],
    [-112.0740, 33.4524],
    [-112.0740, 33.4484],
]
TEST_LAT, TEST_LON = 33.4484, -112.0740
TEST_DATE = "2025-07-15"


def _print_json(label: str, obj: dict) -> None:
    print(f"{label}:\n{json.dumps(obj, indent=2)[:2000]}\n")


def submit_and_poll(path: str, payload: dict, timeout_s: int = 180, poll_s: int = 5) -> dict:
    """POST to submit, then poll the flat /v1/status/{id} endpoint until Completed/Failed."""
    if not settings.fortyguard_api_key:
        raise RuntimeError("FORTYGUARD_API_KEY is not set in backend/.env")

    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
        print(f"POST {path} -> {resp.status_code}")
        body = resp.json()
        _print_json("submit response", body)
        resp.raise_for_status()
        activity_id = body["data"]["activity_id"]

        elapsed = 0
        while elapsed < timeout_s:
            status_resp = client.get(f"{BASE_URL}/v1/status/{activity_id}", headers=HEADERS)
            data = status_resp.json()["data"]
            status = str(data.get("status", "")).lower()
            print(f"  [{elapsed}s] status={status}")
            if status == "completed":
                return data.get("result", {})
            if status == "failed":
                raise RuntimeError(f"activity failed: {data}")
            time.sleep(poll_s)
            elapsed += poll_s
        print(f"  still processing after {timeout_s}s — giving up waiting, but the path/payload worked")
        return {}


def probe_paths(paths: list[str], payload: dict) -> str | None:
    """Try candidate submission paths; return the first the API actually routes to
    (i.e. not a 404 'Endpoint not found'). Cheap — a bad path fails instantly, no credit cost."""
    with httpx.Client(timeout=30) as client:
        for path in paths:
            resp = client.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
            body = resp.json()
            is_unknown_route = resp.status_code == 404 and "not found" in json.dumps(body).lower()
            print(f"  probe {path} -> {resp.status_code}" + (" (unknown route)" if is_unknown_route else ""))
            if is_unknown_route:
                continue
            _print_json(f"  response from {path}", body)
            return path
    return None
