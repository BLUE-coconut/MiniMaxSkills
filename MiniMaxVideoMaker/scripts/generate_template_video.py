#!/usr/bin/env python3
"""
MiniMax Video Template (Agent) Generation CLI

Generate videos using predefined video templates with media and text inputs.

Usage:
  python generate_template_video.py --template-id 393769180141805569 \
      --media "https://example.com/image.jpg" \
      --text "Player name" \
      --output video.mp4
"""

import argparse
import os
import pathlib
import sys
import time

import requests

API_BASE = "https://api.minimaxi.com/v1"
TEMPLATE_URL = f"{API_BASE}/video_template_generation"
TEMPLATE_QUERY_URL = f"{API_BASE}/query/video_template_generation"

POLL_INTERVAL = 10
MAX_WAIT_TIME = 600
REQUEST_TIMEOUT = 60
MAX_CONSECUTIVE_FAILURES = 5


def create_template_task(template_id: str, media_inputs: list, text_inputs: list, headers: dict) -> str:
    """Submit video template generation task."""
    print(f"[info] Submitting template task (template_id: {template_id})...", file=sys.stderr)

    payload = {
        "template_id": template_id,
    }
    if media_inputs:
        payload["media_inputs"] = media_inputs
    if text_inputs:
        payload["text_inputs"] = text_inputs

    resp = requests.post(TEMPLATE_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code") != 0:
        raise RuntimeError(f"API error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")

    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError("No task_id returned")

    print(f"[info] Template task created: {task_id}", file=sys.stderr)
    return task_id


def poll_template_task(task_id: str, headers: dict) -> str:
    """Poll template task status, return video_url."""
    print("[info] Polling template task status...", file=sys.stderr)

    start_time = time.time()
    consecutive_failures = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_TIME:
            raise TimeoutError(f"Template video generation timed out after {int(elapsed)}s")

        time.sleep(POLL_INTERVAL)

        try:
            resp = requests.get(
                TEMPLATE_QUERY_URL,
                params={"task_id": task_id},
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            consecutive_failures = 0

            status = data.get("status", "")
            print(f"[info] Status: {status} ({int(elapsed)}s elapsed)", file=sys.stderr)

            if status == "Success":
                video_url = data.get("video_url")
                if not video_url:
                    raise RuntimeError("No video_url returned on success")
                return video_url
            elif status == "Fail":
                raise RuntimeError("Template video generation failed")

        except requests.exceptions.RequestException as e:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise
            backoff = min(POLL_INTERVAL * (2 ** (consecutive_failures - 1)), 60)
            print(f"[warning] Request failed: {e}, retry {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}...", file=sys.stderr)
            time.sleep(backoff)


def download_video(video_url: str, output_path: str):
    """Download video from URL."""
    print("[info] Downloading video...", file=sys.stderr)
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        try:
            resp = requests.get(video_url, timeout=300)
            resp.raise_for_status()
            path.write_bytes(resp.content)
            size_mb = len(resp.content) / (1024 * 1024)
            print(f"[info] Video saved: {path} ({size_mb:.1f} MB)", file=sys.stderr)
            print(str(path))
            return
        except requests.exceptions.RequestException:
            if attempt >= 2:
                raise
            time.sleep(5 * (2 ** attempt))


def main():
    parser = argparse.ArgumentParser(description="Generate video from MiniMax video template")
    parser.add_argument("--template-id", required=True, help="Template ID")
    parser.add_argument("--media", action="append", default=[], help="Media input URL (can be repeated)")
    parser.add_argument("--text", action="append", default=[], help="Text input (can be repeated)")
    parser.add_argument("--output", required=True, help="Output file path")

    args = parser.parse_args()

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("Error: MINIMAX_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    task_id = create_template_task(args.template_id, args.media, args.text, headers)
    video_url = poll_template_task(task_id, headers)
    download_video(video_url, args.output)


if __name__ == "__main__":
    main()
