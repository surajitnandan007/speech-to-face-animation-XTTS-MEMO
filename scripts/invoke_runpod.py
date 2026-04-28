from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit a job to a RunPod Serverless endpoint.")
    parser.add_argument("--endpoint-id", default=os.getenv("RUNPOD_ENDPOINT_ID"))
    parser.add_argument("--api-key", default=os.getenv("RUNPOD_API_KEY"))
    parser.add_argument("--input-json", required=True, help="JSON string for the RunPod input object.")
    parser.add_argument("--sync", action="store_true", help="Use /runsync instead of /run + /status polling.")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    return parser.parse_args()


def request_json(method: str, url: str, *, api_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.request(
        method,
        url,
        headers={
            "accept": "application/json",
            "authorization": api_key,
            "content-type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    args = parse_args()
    if not args.endpoint_id:
        raise SystemExit("Set RUNPOD_ENDPOINT_ID or pass --endpoint-id.")
    if not args.api_key:
        raise SystemExit("Set RUNPOD_API_KEY or pass --api-key.")

    job_input = json.loads(args.input_json)
    base_url = f"https://api.runpod.ai/v2/{args.endpoint_id}"

    if args.sync:
        result = request_json("POST", f"{base_url}/runsync", api_key=args.api_key, payload={"input": job_input})
        print(json.dumps(result, indent=2))
        return 0

    submitted = request_json("POST", f"{base_url}/run", api_key=args.api_key, payload={"input": job_input})
    job_id = submitted["id"]
    print(json.dumps(submitted, indent=2))

    deadline = time.monotonic() + args.timeout_seconds
    while time.monotonic() < deadline:
        time.sleep(args.poll_seconds)
        result = request_json("GET", f"{base_url}/status/{job_id}", api_key=args.api_key)
        print(json.dumps(result, indent=2))
        if result.get("status") in {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}:
            return 0 if result.get("status") == "COMPLETED" else 1

    print(f"Timed out waiting for job {job_id}.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
