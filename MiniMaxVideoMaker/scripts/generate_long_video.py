#!/usr/bin/env python3
"""
MiniMax Long Video Generation CLI

Generates long videos (30s+) by:
1. Generating sequential video clips (6-10s each)
2. Using the last frame of each clip as the first frame of the next clip (i2v mode)
3. Stitching all clips together with FFmpeg
4. Generating instrumental BGM in parallel using music-2.5+
5. Merging final video with BGM

Usage:
  python generate_long_video.py \
    --scenes "Scene 1 description" "Scene 2 description" "Scene 3 description" \
    --music-prompt "Background music description" \
    --output final_video.mp4
"""

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import shutil
import subprocess
import sys
import time

# Add current directory to path so we can import generate_video
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import requests

# Import from existing generate_video.py (same directory)
from generate_video import (
    create_task,
    poll_task,
    download_video,
    resolve_image,
    build_payload,
    API_BASE,
    QUERY_URL,
    FILE_RETRIEVE_URL,
    REQUEST_TIMEOUT,
    POLL_INTERVAL,
    MAX_WAIT_TIME,
)

MUSIC_API_URL = f"{API_BASE}/music_generation"
MUSIC_POLL_INTERVAL = 5
MUSIC_MAX_WAIT_TIME = 900  # 15 minutes for instrumental music


def extract_last_frame(video_path: str, output_image_path: str) -> str:
    """Extract the last frame from a video as an image using FFmpeg.

    Improved method: Extract frame, upscale and enhance for better i2v input.
    """
    import shutil

    tmp_dir = pathlib.Path(video_path).parent / "tmp_frames"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_frame = tmp_dir / "tmp_frame.jpg"

    # Extract the last frame
    cmd = [
        "ffmpeg", "-y",
        "-sseof", "-0.3",  # Seek to 0.3 seconds before end for cleaner frame
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "1",
        str(tmp_frame),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: simpler extraction
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", "select=eq(n\,9999)",
            "-frames:v", "1",
            str(tmp_frame),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not tmp_frame.exists():
        raise RuntimeError(f"Failed to extract last frame")

    # Enhance the frame: upscale slightly and sharpen for better i2v input
    # Use a simpler approach that always works
    cmd = [
        "ffmpeg", "-y",
        "-i", str(tmp_frame),
        "-vf", "scale=1280:-1:flags=lanczos,unsharp=5:5:0.5:3:3:0.3",
        "-q:v", "1",
        output_image_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: just copy the raw frame
        shutil.copy(str(tmp_frame), output_image_path)

    # Clean up
    shutil.rmtree(tmp_dir, ignore_errors=True)

    return output_image_path


def concatenate_videos(video_paths: list, output_path: str):
    """Concatenate multiple videos into one using FFmpeg."""
    # Create a concat file
    concat_file = pathlib.Path(output_path).parent / "concat_list.txt"
    with open(concat_file, "w") as f:
        for video_path in video_paths:
            f.write(f"file '{pathlib.Path(video_path).absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to concatenate videos: {result.stderr}")

    # Clean up concat file
    concat_file.unlink()


def generate_music_instrumental(prompt: str, api_key: str, output_path: str) -> str:
    """Generate pure instrumental music via MiniMax Music API."""
    print("[info] Generating instrumental background music...", file=sys.stderr)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

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

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > MUSIC_MAX_WAIT_TIME:
            raise TimeoutError(f"Music generation timed out after {int(elapsed)}s")

        try:
            resp = requests.post(
                MUSIC_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()

            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                raise RuntimeError(f"Music API error: {base_resp}")

            status = data.get("data", {}).get("status")
            if status == 2:
                audio_url = data["data"]["audio"]
                print("[info] Music generated, downloading...", file=sys.stderr)
                download_music(audio_url, output_path)
                print(f"[info] BGM saved: {output_path}", file=sys.stderr)
                return output_path
            elif status == 1:
                print(f"[info] Music generating... {int(elapsed)}s elapsed", file=sys.stderr)
                time.sleep(MUSIC_POLL_INTERVAL)
            else:
                raise RuntimeError(f"Unexpected music status: {status}")

        except requests.exceptions.RequestException as e:
            print(f"[warning] Request failed: {e}, retrying...", file=sys.stderr)
            time.sleep(POLL_INTERVAL)


def download_music(url: str, output_path: str):
    """Download music file from URL."""
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=180)
            resp.raise_for_status()
            path.write_bytes(resp.content)
            return
        except requests.exceptions.RequestException:
            if attempt >= 2:
                raise
            time.sleep(5)


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


def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    bgm_volume: float = 0.4,
    fade_in: float = 1.0,
    fade_out: float = 1.5,
):
    """Merge video with background music using FFmpeg."""
    print("[info] Merging video with background music...", file=sys.stderr)

    video_duration = get_video_duration(video_path)

    # Build audio filter for BGM track
    bgm_filters = []
    bgm_filters.append(f"atrim=0:{video_duration}")
    bgm_filters.append("asetpts=PTS-STARTPTS")

    if fade_in > 0:
        bgm_filters.append(f"afade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        fade_start = max(0, video_duration - fade_out)
        bgm_filters.append(f"afade=t=out:st={fade_start}:d={fade_out}")

    bgm_filters.append(f"volume={bgm_volume}")
    bgm_filter_str = ",".join(bgm_filters)

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


def generate_video_segment(
    args: argparse.Namespace,
    prompt: str,
    first_frame_path: str = None,
    subject_reference_path: str = None,
    output_path: str = None,
    headers: dict = None,
) -> tuple:
    """Generate a single video segment.

    Args:
        args: Global arguments
        prompt: Scene description
        first_frame_path: First frame image for i2v mode
        subject_reference_path: Subject reference for S2V-01 mode (improves consistency)
        output_path: Output video path

    Returns:
        tuple: (output_path, last_frame_path)
    """
    # Create a temporary args object for this segment
    segment_args = argparse.Namespace(**vars(args))
    segment_args.prompt = prompt
    segment_args.output = output_path
    segment_args.model = None  # Use default model for each mode
    segment_args.duration = args.segment_duration  # Use segment duration
    # Ensure all optional args have defaults for build_payload
    segment_args.resolution = args.resolution
    segment_args.prompt_optimizer = args.prompt_optimizer
    segment_args.fast_pretreatment = args.fast_pretreatment
    segment_args.aigc_watermark = args.aigc_watermark
    segment_args.callback_url = None
    segment_args.last_frame = None
    segment_args.subject_image = None

    # Use S2V-01 for better character consistency if subject reference is provided
    if subject_reference_path:
        segment_args.mode = "ref"
        segment_args.subject_image = subject_reference_path
        print(f"[info] Using S2V-01 for character consistency", file=sys.stderr)
    elif first_frame_path:
        segment_args.mode = "i2v"
        segment_args.first_frame = first_frame_path
    else:
        segment_args.mode = "t2v"

    payload = build_payload(segment_args)
    task_id = create_task(payload, headers)
    file_id = poll_task(task_id, headers)

    # Download the segment
    download_video(file_id, output_path, headers)

    # Extract last frame for next segment
    last_frame_path = str(pathlib.Path(output_path).with_suffix(".last_frame.jpg"))
    extract_last_frame(output_path, last_frame_path)

    return output_path, last_frame_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate long video with MiniMax Video Generation API"
    )

    # Scene arguments
    parser.add_argument(
        "--scenes",
        nargs="+",
        required=True,
        help="List of scene descriptions, one per video segment",
    )
    parser.add_argument(
        "--segment-duration",
        type=int,
        default=6,
        help="Duration per segment in seconds (default: 6, max: 10)",
    )
    parser.add_argument(
        "--resolution",
        default="768P",
        help="Video resolution (default: 768P for longer videos)",
    )

    # BGM arguments
    parser.add_argument(
        "--music-prompt",
        default=None,
        help="Music style prompt for BGM generation (instrumental)",
    )
    parser.add_argument(
        "--bgm-volume",
        type=float,
        default=0.4,
        help="BGM volume (0.0-1.0, default: 0.4)",
    )
    parser.add_argument(
        "--fade-in",
        type=float,
        default=1.0,
        help="Fade-in duration in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--fade-out",
        type=float,
        default=1.5,
        help="Fade-out duration in seconds (default: 1.5)",
    )

    # Output
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path (e.g., ./video_long.mp4)",
    )

    # Additional options (passed to generate_video.py)
    parser.add_argument(
        "--prompt-optimizer",
        type=lambda v: v.lower() == "true",
        default=None,
        help="Auto-optimize prompt (default: true)",
    )
    parser.add_argument(
        "--fast-pretreatment",
        action="store_true",
        help="Shorten prompt optimizer duration",
    )
    parser.add_argument(
        "--aigc-watermark",
        action="store_true",
        help="Add watermark to video",
    )

    args = parser.parse_args()

    # Validate
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("Error: MINIMAX_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    if args.segment_duration > 10:
        print("Error: segment duration max is 10 seconds", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Create temp directory for segments
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_path.parent / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Generate segments sequentially
    segments = []
    last_frame_path = None

    num_scenes = len(args.scenes)
    print(f"[info] Generating {num_scenes} video segments...", file=sys.stderr)

    for i, scene_prompt in enumerate(args.scenes):
        segment_path = str(tmp_dir / f"segment_{i:02d}.mp4")

        print(f"\n[info] === Segment {i+1}/{num_scenes} ===", file=sys.stderr)
        print(f"[info] Prompt: {scene_prompt[:100]}...", file=sys.stderr)

        if last_frame_path:
            print(f"[info] Using last frame from previous segment as first frame", file=sys.stderr)

        segment_path, last_frame_path = generate_video_segment(
            args=args,
            prompt=scene_prompt,
            first_frame_path=last_frame_path,
            output_path=segment_path,
            headers=headers,
        )

        segments.append(segment_path)

    # Concatenate all segments
    print(f"\n[info] Concatenating {len(segments)} segments...", file=sys.stderr)
    concat_output = str(tmp_dir / "concatenated.mp4")
    concatenate_videos(segments, concat_output)

    # Generate BGM in parallel (if requested)
    bgm_path = None
    if args.music_prompt:
        print("\n[info] Generating instrumental BGM...", file=sys.stderr)
        bgm_path = str(tmp_dir / "generated_bgm.mp3")
        try:
            generate_music_instrumental(args.music_prompt, api_key, bgm_path)
        except Exception as e:
            print(f"[warning] BGM generation failed: {e}", file=sys.stderr)
            print("[warning] Continuing without BGM...", file=sys.stderr)
            bgm_path = None

    # Merge video with BGM or just rename
    if bgm_path and os.path.exists(bgm_path):
        print("\n[info] Merging video with BGM...", file=sys.stderr)
        merge_video_audio(
            video_path=concat_output,
            audio_path=bgm_path,
            output_path=args.output,
            bgm_volume=args.bgm_volume,
            fade_in=args.fade_in,
            fade_out=args.fade_out,
        )
    else:
        # Just rename the concatenated video
        import shutil
        shutil.move(concat_output, args.output)

    # Calculate total duration
    total_duration = get_video_duration(args.output)
    size_mb = os.path.getsize(args.output) / (1024 * 1024)

    print(f"\n[success] Long video generated successfully!")
    print(f"  Output: {args.output}")
    print(f"  Duration: {total_duration:.1f}s ({num_scenes} segments)")
    print(f"  Size: {size_mb:.1f} MB")

    if bgm_path:
        print(f"  BGM: instrumental music added")


if __name__ == "__main__":
    main()
