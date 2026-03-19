#!/usr/bin/env python3
"""
MiniMax Video Generation CLI

Supports four generation modes:
  1. Text-to-Video (t2v): Generate video from text prompt
  2. Image-to-Video (i2v): Generate video from first-frame image + prompt
  3. Start-End Frame (sef): Generate video from first + last frame images + prompt
  4. Subject Reference (ref): Generate video with face consistency from reference photo + prompt

Usage:
  python generate_video.py --mode t2v --prompt "A cat walks on the beach" --output video.mp4
  python generate_video.py --mode i2v --first-frame image.jpg --prompt "The cat starts running" --output video.mp4
  python generate_video.py --mode sef --first-frame start.jpg --last-frame end.jpg --prompt "A girl grows up" --output video.mp4
  python generate_video.py --mode ref --subject-image face.jpg --prompt "A man walks in the park" --output video.mp4
"""

import argparse
import base64
import mimetypes
import os
import pathlib
import sys
import time

import requests

API_BASE = "https://api.minimaxi.com/v1"
VIDEO_GENERATION_URL = f"{API_BASE}/video_generation"
QUERY_URL = f"{API_BASE}/query/video_generation"
FILE_RETRIEVE_URL = f"{API_BASE}/files/retrieve"

POLL_INTERVAL = 10  # seconds between status checks
MAX_WAIT_TIME = 600  # max 10 minutes
REQUEST_TIMEOUT = 60  # per-request HTTP timeout
MAX_CONSECUTIVE_FAILURES = 5

# Model defaults per mode
MODE_MODELS = {
    "t2v": "MiniMax-Hailuo-2.3",
    "i2v": "MiniMax-Hailuo-2.3",
    "sef": "MiniMax-Hailuo-02",
    "ref": "S2V-01",
}

# Valid models per mode
VALID_MODELS = {
    "t2v": ["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-2.3-Fast", "MiniMax-Hailuo-02", "T2V-01-Director", "T2V-01"],
    "i2v": ["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-2.3-Fast", "MiniMax-Hailuo-02", "I2V-01-Director", "I2V-01-live", "I2V-01"],
    "sef": ["MiniMax-Hailuo-02"],
    "ref": ["S2V-01"],
}


def image_to_data_url(image_path: str) -> str:
    """Convert a local image file to a base64 data URL."""
    path = pathlib.Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        mime_type = "image/jpeg"

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{data}"


def resolve_image(image_input: str) -> str:
    """Resolve image input to a URL or data URL.

    If it starts with http:// or https://, return as-is.
    If it starts with data:, return as-is.
    Otherwise, treat as local file path and convert to data URL.
    """
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input
    return image_to_data_url(image_input)


def build_payload(args) -> dict:
    """Build API request payload based on generation mode."""
    model = args.model or MODE_MODELS[args.mode]

    # Validate model for mode
    if model not in VALID_MODELS[args.mode]:
        valid = ", ".join(VALID_MODELS[args.mode])
        print(
            f"[warning] Model '{model}' may not be optimal for mode '{args.mode}'. "
            f"Recommended: {valid}",
            file=sys.stderr,
        )

    payload = {
        "model": model,
    }

    if args.prompt:
        payload["prompt"] = args.prompt

    if args.duration:
        payload["duration"] = args.duration

    if args.resolution:
        payload["resolution"] = args.resolution

    if args.prompt_optimizer is not None:
        payload["prompt_optimizer"] = args.prompt_optimizer

    if args.fast_pretreatment:
        payload["fast_pretreatment"] = True

    if args.aigc_watermark:
        payload["aigc_watermark"] = True

    if args.callback_url:
        payload["callback_url"] = args.callback_url

    # Mode-specific parameters
    if args.mode == "i2v":
        if not args.first_frame:
            print("Error: --first-frame is required for image-to-video mode", file=sys.stderr)
            sys.exit(1)
        payload["first_frame_image"] = resolve_image(args.first_frame)

    elif args.mode == "sef":
        if not args.first_frame or not args.last_frame:
            print("Error: --first-frame and --last-frame are required for start-end frame mode", file=sys.stderr)
            sys.exit(1)
        payload["first_frame_image"] = resolve_image(args.first_frame)
        payload["last_frame_image"] = resolve_image(args.last_frame)

    elif args.mode == "ref":
        if not args.subject_image:
            print("Error: --subject-image is required for subject reference mode", file=sys.stderr)
            sys.exit(1)
        payload["subject_reference"] = [
            {
                "type": "character",
                "image": [resolve_image(args.subject_image)],
            }
        ]

    return payload


def create_task(payload: dict, headers: dict) -> str:
    """Submit video generation task and return task_id."""
    print("[info] Submitting video generation task...", file=sys.stderr)

    try:
        resp = requests.post(
            VIDEO_GENERATION_URL,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise RuntimeError(
                f"API error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}"
            )

        task_id = data.get("task_id")
        if not task_id:
            raise RuntimeError("No task_id returned from API")

        print(f"[info] Task created: {task_id}", file=sys.stderr)
        return task_id

    except requests.exceptions.RequestException as e:
        print(f"Error creating task: {e}", file=sys.stderr)
        sys.exit(1)


def poll_task(task_id: str, headers: dict) -> str:
    """Poll task status until completion, return file_id."""
    print("[info] Polling task status...", file=sys.stderr)

    start_time = time.time()
    consecutive_failures = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_TIME:
            raise TimeoutError(
                f"Video generation timed out after {int(elapsed)}s "
                f"(limit: {MAX_WAIT_TIME}s)"
            )

        time.sleep(POLL_INTERVAL)

        try:
            resp = requests.get(
                QUERY_URL,
                params={"task_id": task_id},
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            consecutive_failures = 0

            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                raise RuntimeError(
                    f"Query API error: {base_resp.get('status_code')} - "
                    f"{base_resp.get('status_msg')}"
                )

            status = data.get("status", "")
            print(
                f"[info] Status: {status} ({int(elapsed)}s elapsed)",
                file=sys.stderr,
            )

            if status == "Success":
                file_id = data.get("file_id")
                width = data.get("video_width")
                height = data.get("video_height")
                if width and height:
                    print(f"[info] Video resolution: {width}x{height}", file=sys.stderr)
                return file_id

            elif status == "Fail":
                error_msg = data.get("error_message", "Unknown error")
                raise RuntimeError(f"Video generation failed: {error_msg}")

            # Preparing, Queueing, Processing — continue polling

        except requests.exceptions.RequestException as e:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise RuntimeError(
                    f"Too many consecutive failures ({MAX_CONSECUTIVE_FAILURES}): {e}"
                )
            backoff = min(POLL_INTERVAL * (2 ** (consecutive_failures - 1)), 60)
            print(
                f"[warning] Request failed: {e}, retry "
                f"{consecutive_failures}/{MAX_CONSECUTIVE_FAILURES} "
                f"(backoff {backoff}s)...",
                file=sys.stderr,
            )
            time.sleep(backoff)


def download_video(file_id: str, output_path: str, headers: dict):
    """Retrieve download URL and save video file."""
    print(f"[info] Retrieving video file (file_id: {file_id})...", file=sys.stderr)

    resp = requests.get(
        FILE_RETRIEVE_URL,
        params={"file_id": file_id},
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    download_url = data.get("file", {}).get("download_url")
    if not download_url:
        raise RuntimeError("No download_url returned from file retrieve API")

    print("[info] Downloading video...", file=sys.stderr)
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        try:
            video_resp = requests.get(download_url, timeout=300)
            video_resp.raise_for_status()
            path.write_bytes(video_resp.content)
            size_mb = len(video_resp.content) / (1024 * 1024)
            print(f"[info] Video saved: {path} ({size_mb:.1f} MB)", file=sys.stderr)
            print(str(path))
            return
        except requests.exceptions.RequestException:
            if attempt >= 2:
                raise
            backoff = 5 * (2 ** attempt)
            print(
                f"[warning] Download failed, retry {attempt + 1}/3 (backoff {backoff}s)...",
                file=sys.stderr,
            )
            time.sleep(backoff)


def main():
    parser = argparse.ArgumentParser(
        description="Generate video with MiniMax Video Generation API"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["t2v", "i2v", "sef", "ref"],
        help="Generation mode: t2v (text-to-video), i2v (image-to-video), "
             "sef (start-end frame), ref (subject reference)",
    )
    parser.add_argument("--prompt", default=None, help="Video description (max 2000 chars)")
    parser.add_argument("--model", default=None, help="Model name (auto-selected per mode if not specified)")
    parser.add_argument("--duration", type=int, default=6, help="Video duration in seconds (default: 6)")
    parser.add_argument("--resolution", default="1080P", help="Video resolution (default: 1080P)")
    parser.add_argument("--first-frame", default=None, help="First frame image (URL or local path)")
    parser.add_argument("--last-frame", default=None, help="Last frame image (URL or local path, for sef mode)")
    parser.add_argument("--subject-image", default=None, help="Subject reference image (URL or local path, for ref mode)")
    parser.add_argument(
        "--prompt-optimizer",
        type=lambda v: v.lower() == "true",
        default=None,
        help="Auto-optimize prompt (default: true)",
    )
    parser.add_argument("--fast-pretreatment", action="store_true", help="Shorten prompt optimizer duration")
    parser.add_argument("--callback-url", default=None, help="Webhook URL for status updates")
    parser.add_argument("--aigc-watermark", action="store_true", help="Add watermark to video")
    parser.add_argument("--output", required=True, help="Output file path (e.g., ./video.mp4)")

    args = parser.parse_args()

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("Error: MINIMAX_API_KEY is not set", file=sys.stderr)
        print("Set it with: export MINIMAX_API_KEY=\"your-api-key\"", file=sys.stderr)
        sys.exit(1)

    if args.mode == "t2v" and not args.prompt:
        print("Error: --prompt is required for text-to-video mode", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = build_payload(args)
    task_id = create_task(payload, headers)
    file_id = poll_task(task_id, headers)
    download_video(file_id, args.output, headers)


if __name__ == "__main__":
    main()
