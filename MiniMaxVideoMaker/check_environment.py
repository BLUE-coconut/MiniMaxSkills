#!/usr/bin/env python3
"""
Environment Check Script for MiniMax Video Maker

Usage:
    python check_environment.py
"""

import os
import subprocess
import sys
import importlib.util


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    print(f"  {text}")


def check_python_version() -> bool:
    v = sys.version_info
    if v.major >= 3 and v.minor >= 8:
        print_success(f"Python version: {v.major}.{v.minor}.{v.micro}")
        return True
    else:
        print_error(f"Python version: {v.major}.{v.minor}.{v.micro} (Required: 3.8+)")
        return False


def check_package(name: str) -> bool:
    spec = importlib.util.find_spec(name)
    if spec is not None:
        print_success(f"Package '{name}' is installed")
        return True
    else:
        print_error(f"Package '{name}' is NOT installed")
        print_info(f"Install: pip install {name}")
        return False


def check_api_key() -> bool:
    api_key = os.getenv("MINIMAX_API_KEY")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print_success(f"MINIMAX_API_KEY is set: {masked}")
        return True
    else:
        print_error("MINIMAX_API_KEY is NOT set")
        print_info('Set it with: export MINIMAX_API_KEY="your-api-key"')
        return False


def check_ffmpeg() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_success(f"FFmpeg is installed: {version_line}")
            return True
        else:
            print_error("FFmpeg is installed but not working")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_error("FFmpeg is NOT installed (required for BGM feature)")
        print_info("  macOS:   brew install ffmpeg")
        print_info("  Ubuntu:  sudo apt install ffmpeg")
        return False


def check_scripts() -> bool:
    scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
    required = ["generate_video.py", "generate_template_video.py", "add_bgm.py"]
    missing = [f for f in required if not os.path.isfile(os.path.join(scripts_dir, f))]
    if not missing:
        print_success(f"All {len(required)} required scripts present")
        return True
    else:
        print_error(f"Missing scripts: {', '.join(missing)}")
        return False


def main():
    print_header("MiniMax Video Maker - Environment Check")
    results = {}

    print(f"\n{Colors.BOLD}1. Python Version{Colors.END}")
    results['python'] = check_python_version()

    print(f"\n{Colors.BOLD}2. Required Packages{Colors.END}")
    results['packages'] = check_package("requests")

    print(f"\n{Colors.BOLD}3. FFmpeg (for BGM){Colors.END}")
    results['ffmpeg'] = check_ffmpeg()

    print(f"\n{Colors.BOLD}4. API Key{Colors.END}")
    results['api_key'] = check_api_key()

    print(f"\n{Colors.BOLD}5. Scripts{Colors.END}")
    results['scripts'] = check_scripts()

    print_header("Summary")
    if all(results.values()):
        print_success(f"{Colors.BOLD}All checks passed!{Colors.END}")
        print_info("You're ready to use mmVideoMaker!")
        return 0
    else:
        failed = [k for k, v in results.items() if not v]
        print_error(f"{Colors.BOLD}Failed checks: {', '.join(failed)}{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
