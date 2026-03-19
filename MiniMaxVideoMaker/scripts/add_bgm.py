#!/usr/bin/env python3
"""
Add background music to a video using FFmpeg.

Supports:
  - Adding an audio file as background music to a video
  - Generating background music via MiniMax Music API, then merging
  - Adjusting music volume relative to original audio
  - Fade-in/fade-out effects on the music track

Usage:
  # Add existing audio file as BGM
  python add_bgm.py --video input.mp4 --audio bgm.mp3 --output output.mp4

  # Generate BGM via MiniMax Music API then merge
  python add_bgm.py --video input.mp4 --generate-bgm \
      --music-prompt "gentle piano, warm, peaceful" \
      --output output.mp4

  # With volume and fade control
  python add_bgm.py --video input.mp4 --audio bgm.mp3 \
      --bgm-volume 0.3 --fade-in 1 --fade-out 1 \
      --output output.mp4
"""

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
import time

import requests


MUSIC_API_URL = "https://api.minimaxi.com/v1/music_generation"
POLL_INTERVAL = 5
MAX_WAIT_TIME = 900
REQUEST_TIMEOUT = 180
MAX_CONSECUTIVE_FAILURES = 5


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())


def download_with_retry(url: str, output_path: str, max_retries: int = 3) -> str:
    """Download a file with retry and SSL fallback."""
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=180, verify=True)
            resp.raise_for_status()
            path.write_bytes(resp.content)
            return output_path
        except requests.exceptions.SSLError:
            # Some MiniMax CDN endpoints have cert issues; retry with verify=False
            print(f"[warning] SSL error, retrying without verification...", file=sys.stderr)
            try:
                resp = requests.get(url, timeout=180, verify=False)
                resp.raise_for_status()
                path.write_bytes(resp.content)
                return output_path
            except Exception as e:
                if attempt >= max_retries - 1:
                    raise
                print(f"[warning] Download failed, retry {attempt + 1}...", file=sys.stderr)
                time.sleep(5)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt >= max_retries - 1:
                raise
            backoff = 5 * (2 ** attempt)
            print(f"[warning] Download failed: {e}, retry {attempt + 1} (backoff {backoff}s)...", file=sys.stderr)
            time.sleep(backoff)


def generate_music(prompt: str, api_key: str, output_path: str, instrumental: bool = False) -> str:
    """Generate background music via MiniMax Music API with robust retry logic."""
    print("[info] Generating background music...", file=sys.stderr)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if instrumental:
        # Pure instrumental mode - generates ~4min music
        # FFmpeg trims to video length anyway
        # Note: API still requires lyrics field even for instrumental, use empty lyrics
        payload = {
            "model": "music-2.5+",
            "prompt": prompt,
            "lyrics": "[Instrumental]",
            "instrumental": True,
            "output_format": "url",
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
            },
        }
    else:
        # Singing mode with short lyrics - generates ~40s (faster)
        # FFmpeg trims to video length anyway
        payload = {
            "model": "music-2.5+",
            "prompt": prompt,
            "lyrics": "[Intro]\nla da da\nla la la",
            "output_format": "url",
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
            },
        }

    start_time = time.time()
    consecutive_failures = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_TIME:
            raise TimeoutError(f"Music generation timed out after {int(elapsed)}s")

        try:
            resp = requests.post(
                MUSIC_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()

            consecutive_failures = 0  # reset on success

            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                status_code = base_resp.get("status_code")
                if status_code in [1002, 1008]:
                    print(f"[warning] API error ({status_code}): {base_resp.get('status_msg')}, retrying in 10s...", file=sys.stderr)
                    time.sleep(10)
                    continue
                raise RuntimeError(f"Music API error: {base_resp}")

            status = data.get("data", {}).get("status")
            if status == 2:
                audio_url = data["data"]["audio"]
                print("[info] Music generated, downloading...", file=sys.stderr)
                download_with_retry(audio_url, output_path)
                print(f"[info] BGM saved: {output_path}", file=sys.stderr)
                return output_path
            elif status == 1:
                print(f"[info] Music generating... {int(elapsed)}s elapsed", file=sys.stderr)
                time.sleep(POLL_INTERVAL)
            else:
                raise RuntimeError(f"Unexpected music status: {status}")

        except requests.exceptions.Timeout:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise TimeoutError(
                    f"Request timed out {MAX_CONSECUTIVE_FAILURES} consecutive times. "
                    f"Total elapsed: {int(elapsed)}s"
                )
            backoff = min(POLL_INTERVAL * (2 ** (consecutive_failures - 1)), 30)
            print(
                f"[warning] Request timed out, retry {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES} "
                f"(backoff {backoff}s)...",
                file=sys.stderr,
            )
            time.sleep(backoff)

        except requests.exceptions.ConnectionError:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise
            backoff = min(POLL_INTERVAL * (2 ** (consecutive_failures - 1)), 30)
            print(
                f"[warning] Connection error, retry {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES} "
                f"(backoff {backoff}s)...",
                file=sys.stderr,
            )
            time.sleep(backoff)

        except requests.exceptions.RequestException as e:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise
            backoff = min(POLL_INTERVAL * (2 ** (consecutive_failures - 1)), 30)
            print(
                f"[warning] Request failed: {e}, retry {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES} "
                f"(backoff {backoff}s)...",
                file=sys.stderr,
            )
            time.sleep(backoff)


def video_has_audio(video_path: str) -> bool:
    """Check if video file contains an audio stream."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "a",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            video_path,
        ],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    bgm_volume: float = 0.3,
    fade_in: float = 0,
    fade_out: float = 0,
    keep_original_audio: bool = True,
):
    """Merge video with background music using FFmpeg."""
    print("[info] Merging video with background music...", file=sys.stderr)

    video_duration = get_video_duration(video_path)
    has_audio = video_has_audio(video_path)

    # Build audio filter for BGM track
    bgm_filters = []

    # Trim BGM to video duration
    bgm_filters.append(f"atrim=0:{video_duration}")
    bgm_filters.append("asetpts=PTS-STARTPTS")

    # Apply fade effects
    if fade_in > 0:
        bgm_filters.append(f"afade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        fade_start = max(0, video_duration - fade_out)
        bgm_filters.append(f"afade=t=out:st={fade_start}:d={fade_out}")

    # Apply volume
    bgm_filters.append(f"volume={bgm_volume}")

    bgm_filter_str = ",".join(bgm_filters)

    if has_audio and keep_original_audio:
        # Mix original audio with BGM
        filter_complex = (
            f"[1:a]{bgm_filter_str}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ]
    else:
        # No original audio or replacing — add BGM directly
        if not has_audio:
            print("[info] Video has no audio track, adding BGM directly...", file=sys.stderr)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[1:a]{bgm_filter_str}[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[info] Output saved: {output_path} ({size_mb:.1f} MB)", file=sys.stderr)
    print(output_path)


def main():
    parser = argparse.ArgumentParser(description="Add background music to video")

    parser.add_argument("--video", required=True, help="Input video file path")
    parser.add_argument("--audio", default=None, help="Audio file to use as BGM")
    parser.add_argument("--generate-bgm", action="store_true", help="Generate BGM via MiniMax Music API")
    parser.add_argument("--instrumental", action="store_true", help="Generate pure instrumental music (no vocals/lyrics)")
    parser.add_argument("--music-prompt", default=None, help="Music style prompt for BGM generation")
    parser.add_argument("--bgm-volume", type=float, default=0.3, help="BGM volume (0.0-1.0, default: 0.3)")
    parser.add_argument("--fade-in", type=float, default=0.5, help="Fade-in duration in seconds (default: 0.5)")
    parser.add_argument("--fade-out", type=float, default=1.0, help="Fade-out duration in seconds (default: 1.0)")
    parser.add_argument("--replace-audio", action="store_true", help="Replace original audio instead of mixing")
    parser.add_argument("--output", required=True, help="Output video file path")

    args = parser.parse_args()

    if not args.audio and not args.generate_bgm:
        print("Error: provide --audio or --generate-bgm", file=sys.stderr)
        sys.exit(1)

    if args.generate_bgm and not args.music_prompt:
        print("Error: --music-prompt is required with --generate-bgm", file=sys.stderr)
        sys.exit(1)

    audio_path = args.audio

    if args.generate_bgm:
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            print("Error: MINIMAX_API_KEY is not set", file=sys.stderr)
            sys.exit(1)

        # Generate BGM to temp file
        bgm_dir = pathlib.Path(args.output).parent / "tmp"
        bgm_dir.mkdir(parents=True, exist_ok=True)
        audio_path = str(bgm_dir / "generated_bgm.mp3")
        generate_music(args.music_prompt, api_key, audio_path, instrumental=args.instrumental)

    merge_video_audio(
        video_path=args.video,
        audio_path=audio_path,
        output_path=args.output,
        bgm_volume=args.bgm_volume,
        fade_in=args.fade_in,
        fade_out=args.fade_out,
        keep_original_audio=not args.replace_audio,
    )


if __name__ == "__main__":
    main()
