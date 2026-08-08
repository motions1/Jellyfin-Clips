# Jellyfin Theme Clips

Generates 10-second theme video clips for every movie in your library.
Jellyfin automatically serves these as backdrop previews.

No Python packages required — just `ffmpeg`.


## Docker Compose

Create a `compose.yml` (included in the repo) or paste:

```yaml
services:
  theme-clips:
    image: ghcr.io/motions1/jellyfin-clips
    volumes:
      - /path/to/your/movies:/movies
    environment:
      - JELLYFIN_URL=
      - JELLYFIN_API_KEY=
    command:
      - "--length=15"               # seconds for each clip
      - "--start-buffer=600"        # skip first N seconds (credits, logos)
      - "--end-ignore=0.8"          # ignore last 80% of the movie (0.0–1.0)
      - "--max-height=720"          # scale taller videos down to this height (720, 1080)
      # - "--force"                  # uncomment to rebuild clips that already exist
```

Then run:

```bash
docker compose run --rm theme-clips
```

### Schedule with cron + compose

```cron
0 3 * * * cd /path/to/Jellyfin-Clips && docker compose run --rm theme-clips >> clips.log 2>&1
```


## Quick start (Docker CLI)

```bash
docker run --rm -v /path/to/your/movies:/movies ghcr.io/motions1/jellyfin-clips
```

Movies without a `Backdrops/` folder get a clip. Existing ones are skipped,
so it's safe to run daily.

### With Jellyfin refresh (optional)

Pass your Jellyfin URL and API key as environment variables:

```bash
docker run --rm \
  -v /path/to/movies:/movies \
  -e JELLYFIN_URL=http://192.168.1.100:8096 \
  -e JELLYFIN_API_KEY=your-api-key \
  ghcr.io/motions1/jellyfin-clips
```

Generate an API key at: Jellyfin Dashboard > API Keys > +

### Override defaults

```bash
docker run --rm -v /path/to/movies:/movies ghcr.io/motions1/jellyfin-clips \
  --length 15 --start-buffer 600 --end-ignore 0.8 --force
```


## Direct usage (no Docker)

### Clone

```bash
git clone https://github.com/motions1/Jellyfin-Clips.git
cd Jellyfin-Clips
```

### Requirements
- Python 3.8+
- ffmpeg + ffprobe on PATH

### Setup

```bash
# Linux (Debian/Ubuntu)
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows — download from https://ffmpeg.org
```

### Run

```bash
python3 theme_clips.py /path/to/movies
```


## Automating with cron (Linux)

```bash
crontab -e
```

Add:

```cron
0 3 * * * cd /path/to/Jellyfin-Clips && /usr/bin/python3 theme_clips.py >> clips.log 2>&1
```

Runs nightly at 3 AM. New movies get picked up automatically.


## How it works

1. Scans each movie folder and picks the largest video file (skips trailers/featurettes)
2. Probes the file with ffprobe to get duration and resolution
3. Picks a random timestamp inside the first half of the movie (skipping intro credits)
4. Re-encodes a short clip to h264 + stereo AAC at 720p
5. Saves it as `MovieFolder/Backdrops/theme.mp4`
6. Optionally triggers a Jellyfin library refresh

Already-processed movies are skipped on subsequent runs, making this safe to schedule.


## License

MIT