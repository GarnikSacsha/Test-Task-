# Features

## Core

- Current temporary email retrieval.
- Inbox retrieval.
- Full message content retrieval.
- Email/session refresh.
- JSON-only API responses.

## Extra Polish

- Operator console at `/`.
- OpenAPI docs at `/docs`.
- Health endpoint with browser readiness.
- Demo backend for deterministic tests and presentations.
- Typed response schemas.
- Centralized scraper error mapping.
- Docker/Railway deployment path.

## Operational Details

- Browser lifecycle is managed by the FastAPI lifespan.
- Shared page actions are protected by an async lock.
- DOM parsing uses selector cascades and text fallbacks to reduce brittleness.

