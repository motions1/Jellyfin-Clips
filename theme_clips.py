#!/usr/bin/env python3
"""Generate theme clips for Jellyfin movie Backdrops.

Docker entrypoint — expects movies mounted at /movies.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import urllib.request

# ── config (edit or use CLI args) ─────────────────────────

MOVIES_ROOT = "/movies"
JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "")
JELLYFIN_API_KEY = os.environ.get("JELLYFIN_API_KEY", "")
CLIP_LENGTH = 10
START_BUFFER = 180
END_IGNORE_PCT = 0.5
MAX_HEIGHT = 720

# ── helpers ──────────────────────────────────────────────

_INFO_CACHE: dict[str, tuple[int, float]] = {}


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg is required but not found on PATH.")
        sys.exit(1)


def probe_video(path: str) -> tuple[int, float]:
    if path not in _INFO_CACHE:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=height:format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(r.stdout)
        streams = data.get("streams", [])
        height = int(streams[0]["height"]) if streams else MAX_HEIGHT
        fmt = data.get("format", {})
        duration = float(fmt.get("duration", 0))
        _INFO_CACHE[path] = (height, duration)
    return _INFO_CACHE[path]


def find_movie_files(base_path: str, extensions: tuple[str, ...] | None = None):
    if extensions is None:
        extensions = (".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".m4v")
    skip_keywords = ["trailer", "featurette", "behindthescenes", "bts", "deletedscenes"]
    movies: list[tuple[str, str]] = []
    for entry in sorted(os.listdir(base_path)):
        folder = os.path.join(base_path, entry)
        if not os.path.isdir(folder):
            continue
        candidates: list[tuple[int, str]] = []
        for fname in os.listdir(folder):
            lower = fname.lower()
            if lower.endswith(extensions) and not any(k in lower for k in skip_keywords):
                fpath = os.path.join(folder, fname)
                try:
                    size = os.path.getsize(fpath)
                except OSError:
                    continue
                candidates.append((size, fpath))
        if candidates:
            movies.append((folder, max(candidates, key=lambda x: x[0])[1]))
    return movies


def pick_clip_start(duration: float, clip_length: float, start_buffer: float, end_ignore_pct: float) -> float:
    max_end = duration * (1.0 - end_ignore_pct)
    low = start_buffer
    high = max_end - clip_length
    if high <= low:
        high = low + 1.0
    return random.uniform(low, high)


def extract_clip(movie_path: str, output_path: str, start_time: int, clip_length: int, max_height: int = MAX_HEIGHT) -> bool:
    try:
        height = probe_video(movie_path)[0]
        cmd = ["ffmpeg", "-ss", str(start_time), "-i", movie_path, "-t", str(clip_length), "-y"]
        if height > max_height:
            cmd += ["-vf", f"scale='trunc(oh*a/2)*2':{max_height}"]
        cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k", "-ac", "2", output_path]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False)
        if result.returncode != 0:
            print(f"  ffmpeg error (exit {result.returncode})")
            return False
        return True
    except Exception as e:
        print(f"  Extract clip error: {e}")
        return False


def refresh_jellyfin_library() -> None:
    if not JELLYFIN_URL or not JELLYFIN_API_KEY:
        return
    url = f"{JELLYFIN_URL}/Library/Refresh?api_key={JELLYFIN_API_KEY}"
    try:
        req = urllib.request.Request(url, method="POST")
        urllib.request.urlopen(req, timeout=10)
        print("Jellyfin library refresh triggered.")
    except Exception as e:
        print(f"Jellyfin refresh failed: {e}")


def process_movies(base_path: str, clip_length: int = CLIP_LENGTH,
                   start_buffer: int = START_BUFFER, end_ignore_pct: float = END_IGNORE_PCT,
                   force: bool = False, max_height: int = MAX_HEIGHT) -> None:
    movies = find_movie_files(base_path)
    if not movies:
        print("No movie files found. Check the path and try again.")
        return
    print(f"\nFound {len(movies)} movie(s) to process.\n")
    for i, (folder, movie_path) in enumerate(movies, 1):
        movie_name = os.path.basename(movie_path)
        backdrop_dir = os.path.join(folder, "Backdrops")
        if os.path.isdir(backdrop_dir) and not force:
            print(f"  [{i}/{len(movies)}] Skipping {movie_name} — Backdrops exists.")
            continue
        print(f"  [{i}/{len(movies)}] Processing: {movie_name}")
        try:
            _, duration = probe_video(movie_path)
            duration = int(duration)
            start = pick_clip_start(duration, clip_length, start_buffer, end_ignore_pct)
            os.makedirs(backdrop_dir, exist_ok=True)
            output_path = os.path.join(backdrop_dir, "theme.mp4")
            ok = extract_clip(movie_path, output_path, int(start), clip_length, max_height)
            if ok:
                print(f"  [{i}/{len(movies)}] Saved: {output_path}")
        except Exception as e:
            print(f"  [{i}/{len(movies)}] Failed to process {movie_name}: {e}")
    refresh_jellyfin_library()
    print("\nDone.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate Jellyfin theme clips.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("path", nargs="?", default=MOVIES_ROOT, help="Movie directory")
    p.add_argument("--length", type=int, default=CLIP_LENGTH)
    p.add_argument("--start-buffer", type=int, default=START_BUFFER)
    p.add_argument("--end-ignore", type=float, default=END_IGNORE_PCT)
    p.add_argument("--max-height", type=int, default=MAX_HEIGHT)
    p.add_argument("--force", action="store_true")
    return p


def main() -> None:
    require_ffmpeg()
    args = build_parser().parse_args()
    process_movies(base_path=args.path, clip_length=args.length,
                   start_buffer=args.start_buffer, end_ignore_pct=args.end_ignore,
                   force=args.force, max_height=args.max_height)


if __name__ == "__main__":
    main()
