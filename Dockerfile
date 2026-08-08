# ── Build ────────────────────────────────────────────────
# docker build -t ghcr.io/motions1/jellyfin-clips .
# docker push ghcr.io/motions1/jellyfin-clips
# docker run --rm -v /path/to/movies:/movies ghcr.io/motions1/jellyfin-clips

FROM python:3-slim

# ffmpeg is the only system dependency
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY theme_clips.py /app/theme_clips.py
WORKDIR /app

ENTRYPOINT ["python3", "theme_clips.py"]