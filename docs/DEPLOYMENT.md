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

## Smoke Checks

After deploy:

```bash
curl https://your-service.up.railway.app/health
curl https://your-service.up.railway.app/api/email
```

If Chromium fails to start on a small Railway plan, temporarily set `DEMO_MODE=true` to verify the API and UI while investigating resource limits.

## Docker Locally

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000`.

