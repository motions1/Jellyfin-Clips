# Jellyfin Theme Clips

Generates short video clips for every movie in your library to use as
Jellyfin backdrop previews.  Skips movies that already have a
`Backdrops/` folder, so it's safe to run on a schedule.

**Requirements either way:** a cron job on your host to run it nightly.
This tool runs once and exits — it does not stay running.

---

## Option A — Docker (easiest)

No Python or ffmpeg install needed.  The Docker image includes everything.

### One-time run

```bash
docker run --rm -v /path/to/your/movies:/movies ghcr.io/motions1/jellyfin-clips
```

### With compose

Edit `compose.yml` (included in the repo) to set your movie path, then:

```bash
docker compose run --rm theme-clips
```

### Nightly schedule via cron

Add one of these to your crontab (`crontab -e`):

```cron
# Using docker run directly
0 3 * * * docker run --rm -v /path/to/movies:/movies ghcr.io/motions1/jellyfin-clips >> clips.log 2>&1

# Or using compose (run from the repo folder)
0 3 * * * cd /path/to/Jellyfin-Clips && docker compose run --rm theme-clips >> clips.log 2>&1
```

### Optional — Jellyfin auto-refresh

After generating clips, the script can tell Jellyfin to scan for the new
`Backdrops/` folders so they show up immediately instead of waiting for
the next scheduled library scan.

**Docker** — pass as environment variables:

```bash
docker run --rm \
  -v /path/to/movies:/movies \
  -e JELLYFIN_URL=http://192.168.1.100:8096 \
  -e JELLYFIN_API_KEY=your-api-key \
  ghcr.io/motions1/jellyfin-clips
```

Or in `compose.yml`:

```yaml
environment:
  - JELLYFIN_URL=http://192.168.1.100:8096
  - JELLYFIN_API_KEY=your-api-key
```

**Direct** — set the variables before running, or hardcode them in the script:

```bash
# Set them per-run
JELLYFIN_URL=http://192.168.1.100:8096 JELLYFIN_API_KEY=your-api-key python3 theme_clips.py /path/to/movies
```

Or edit `theme_clips.py` directly (lines near the top):

```python
JELLYFIN_URL = "http://192.168.1.100:8096"
JELLYFIN_API_KEY = "your-api-key"
```

Generate an API key at: Jellyfin Dashboard > API Keys > +

### Custom settings

```bash
docker run --rm -v /path/to/movies:/movies ghcr.io/motions1/jellyfin-clips \
  --length 15 --start-buffer 600 --end-ignore 0.8 --force
```

Or edit `compose.yml` and uncomment/change the `command` section.

---

## Option B — Direct (no Docker)

Only ffmpeg needed — no Python packages required.

### Setup

```bash
git clone https://github.com/motions1/Jellyfin-Clips.git
cd Jellyfin-Clips

# Install ffmpeg if you don't have it
sudo apt install ffmpeg          # Debian/Ubuntu
brew install ffmpeg              # macOS
# Download from https://ffmpeg.org  # Windows
```

### One-time run

```bash
python3 theme_clips.py /path/to/movies
```

### Nightly schedule via cron

```cron
0 3 * * * cd /path/to/Jellyfin-Clips && /usr/bin/python3 theme_clips.py >> clips.log 2>&1
```

### Custom settings

```bash
python3 theme_clips.py /path/to/movies --length 15 --start-buffer 600 --end-ignore 0.8 --force
```

---

## How it works

1. Scans each movie folder and picks the largest video file (skips trailers/featurettes)
2. Probes the file with ffprobe to get duration and resolution
3. Picks a random timestamp inside the specified portion of the movie
4. Re-encodes a 15-second clip to h264 + stereo AAC at 720p
5. Saves it as `MovieFolder/Backdrops/theme.mp4`
6. Optionally triggers a Jellyfin library refresh

Already-processed movies are skipped on subsequent runs, making this safe
to run on a daily schedule.  Only new movies (without a `Backdrops/` folder)
are processed.

---

## License

MIT