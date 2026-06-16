# Status

## Done

- Project scaffold.
- FastAPI REST API.
- Playwright scraper implementation.
- Operator console.
- JSON error mapping.
- Environment configuration.
- SQLite persistence for scraper events, email addresses, and message snapshots.
- Docker and Railway files.
- API contract tests.
- Documentation.

## Verification

- `pytest` should validate API contracts in demo mode.
- `ruff check .` should validate lint rules.
- Manual live validation should be done against tempail.com after installing Playwright browsers.

## Known Risks

- The target site can change selectors or anti-automation behavior.
- `tempail.com` can present a captcha/anti-bot challenge. The API detects it and returns a structured `anti_bot_challenge` JSON error instead of failing silently.
- A single shared browser session is intentionally simple; it is stable for this task, but a production multi-user API would need a browser/session pool.
- Railway memory limits can affect Chromium startup on smaller plans.

## Next Improvements

- Add session tokens for multiple independent inboxes.
- Add a background inbox watcher with Server-Sent Events for live UI updates.
