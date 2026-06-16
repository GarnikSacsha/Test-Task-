# Tempail Scraper API

Playwright-powered REST API for automating [tempail.com](https://tempail.com/ua/) temporary inboxes.

The project was built for a technical assessment: generate a temporary email address, monitor the inbox, fetch full message content, and refresh the current address. It also includes a small operator console at `/` and automatic OpenAPI docs at `/docs`.

## Highlights

- FastAPI app with typed JSON responses.
- Async Playwright browser automation for the JavaScript-rendered target site.
- Session manager with a lock around the shared browser page to keep concurrent API requests stable.
- Graceful JSON errors for timeouts, missing DOM elements, stale sessions, unavailable browser instances, and missing message IDs.
- Dockerfile and Railway configuration.
- Demo mode for UI demos and contract tests without touching the external site.
- Documentation pack: requirements, context, state, status, API, deployment, and feature notes.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/email` | Returns the current temporary email address. |
| `GET` | `/api/inbox` | Returns received emails with `id`, `sender`, `subject`, `time`, and `preview`. |
| `GET` | `/api/email/{id}` | Returns full content for a specific message. |
| `POST` | `/api/email/refresh` | Generates a new temporary email address. |
| `GET` | `/health` | Reports service, browser, and demo-mode status. |
| `GET` | `/api/history` | Returns persisted emails, messages, and scraper events from SQLite. |

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m playwright install chromium
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

- Operator console: `http://127.0.0.1:8000/`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

## Demo Mode

Set `DEMO_MODE=true` in `.env` to run the API and UI with deterministic local data. This is useful for screenshots, tests, and Railway smoke checks when the external service is unavailable.

## Anti-Bot Challenge

`tempail.com` may occasionally show a captcha to automated browsers. The API detects this and returns a structured JSON error with `code: "anti_bot_challenge"` instead of crashing.

For local manual validation, set `BROWSER_HEADLESS=false`, restart the server, and solve the captcha in the browser window. For UI demos and automated tests, use `DEMO_MODE=true`.

## Docker

```bash
docker compose up --build
```

The Docker image uses the official Playwright Python base image, so Chromium dependencies are already present.

## Railway

This repository includes `railway.json` and a Dockerfile. Create a Railway project from the GitHub repository and set these variables if needed:

```text
BROWSER_HEADLESS=true
APP_ENV=production
LOG_LEVEL=INFO
DEMO_MODE=false
```

Railway provides `PORT` automatically.

## Examples

```bash
curl http://127.0.0.1:8000/api/email
curl http://127.0.0.1:8000/api/inbox
curl http://127.0.0.1:8000/api/email/welcome-demo
curl -X POST http://127.0.0.1:8000/api/email/refresh
```

## Tests

```bash
pytest
ruff check .
```

Tests run in `DEMO_MODE=true`, so they validate API contracts without launching a real browser.

## Persistence

The app stores scraper activity in SQLite when `STORAGE_ENABLED=true`. By default it writes to `./data/tempail.sqlite3`.

On Railway, create a Volume and mount it to:

```text
/app/data
```

Railway exposes the mounted path through `RAILWAY_VOLUME_MOUNT_PATH`; the app uses it automatically. Without a volume, SQLite still works, but data is ephemeral and can disappear on redeploy.
