# State

## Current Architecture

- `app/main.py`: FastAPI application factory, lifespan hooks, exception mapping, static UI mount.
- `app/api/routes.py`: API endpoint definitions.
- `app/automation/scraper.py`: Playwright automation adapter for tempail.com.
- `app/automation/service.py`: service boundary, demo backend, request timeout wrapper.
- `app/models/schemas.py`: Pydantic response models.
- `app/static/`: operator console.
- `tests/`: API contract tests using demo mode.

## Implemented Features

- Required REST endpoints.
- Health endpoint.
- Browser startup and shutdown through FastAPI lifespan.
- Configurable target URL, timeouts, polling, CORS, headless mode, and demo mode.
- Dockerfile and Docker Compose.
- Railway config.
- Documentation pack.

## Main Design Decisions

- FastAPI was selected for async support and OpenAPI documentation.
- Playwright was selected because it has a native async API and strong browser lifecycle control.
- Demo mode exists to keep tests deterministic and to provide a fallback for demos when tempail.com is temporarily unavailable.

