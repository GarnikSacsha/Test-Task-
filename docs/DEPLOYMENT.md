# Deployment

## Railway

1. Push the repository to GitHub.
2. Create a new Railway project from the GitHub repository.
3. Railway detects `railway.json` and builds with the Dockerfile.
4. Configure variables:

```text
APP_ENV=production
LOG_LEVEL=INFO
BROWSER_HEADLESS=true
DEMO_MODE=false
```

Railway provides `PORT`, so no manual port value is required.

The container starts through `scripts/start.sh`, which prints the selected port before launching Uvicorn. In Railway logs, a healthy startup should include a line like:

```text
Starting Tempail Scraper API on port 12345
```

## Smoke Checks

After deploy:

```bash
curl https://your-service.up.railway.app/health
curl https://your-service.up.railway.app/api/email
```

If Chromium fails to start on a small Railway plan, temporarily set `DEMO_MODE=true` to verify the API and UI while investigating resource limits.

If `tempail.com` presents a captcha to Railway's headless browser, the API returns `code: "anti_bot_challenge"`. This is expected external-site protection, not a process crash. Keep `DEMO_MODE=true` for presentation environments where the live target blocks automation.

## Persistent Storage

To persist SQLite data across Railway redeploys:

1. Add a Railway Volume to the `web` service.
2. Set the volume mount path to `/app/data`.
3. Keep these variables:

```text
STORAGE_ENABLED=true
DATA_DIR=data
```

If no volume is attached, the app still runs, but `data/tempail.sqlite3` is stored on ephemeral container storage.

## Docker Locally

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000`.
