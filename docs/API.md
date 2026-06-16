# API Documentation

Base URL for local development: `http://127.0.0.1:8000`

## `GET /api/email`

Returns the current temporary email address.

```json
{
  "email": "example@tempail.com",
  "meta": {
    "requested_at": "2026-06-16T18:00:00Z",
    "source": "tempail.com"
  }
}
```

## `GET /api/inbox`

Returns the current inbox.

```json
{
  "email": "example@tempail.com",
  "count": 1,
  "messages": [
    {
      "id": "welcome-demo",
      "sender": "robot@example.com",
      "subject": "Verification code",
      "time": "now",
      "preview": "Your code is 482913"
    }
  ],
  "meta": {
    "requested_at": "2026-06-16T18:00:00Z",
    "source": "tempail.com"
  }
}
```

## `GET /api/email/{id}`

Returns full content for one email.

```json
{
  "id": "welcome-demo",
  "sender": "robot@example.com",
  "subject": "Verification code",
  "time": "now",
  "text": "Your code is 482913",
  "html": "<p>Your code is <strong>482913</strong></p>",
  "raw": {},
  "meta": {
    "requested_at": "2026-06-16T18:00:00Z",
    "source": "tempail.com"
  }
}
```

## `POST /api/email/refresh`

Refreshes the current session and returns the new address.

```json
{
  "email": "new@example.com",
  "meta": {
    "requested_at": "2026-06-16T18:00:00Z",
    "source": "tempail.com"
  }
}
```

## `GET /api/history`

Returns persisted scraper activity from SQLite.

```json
{
  "database_path": "data/tempail.sqlite3",
  "emails": [],
  "messages": [],
  "events": []
}
```

## Error Format

```json
{
  "error": "Message 'abc' was not found",
  "detail": null,
  "code": "message_not_found"
}
```

Common error codes:

| Code | Meaning |
| --- | --- |
| `target_timeout` | The target page or API operation exceeded the configured timeout. |
| `element_missing` | Expected tempail.com DOM elements were not present. |
| `message_not_found` | The requested email ID is not visible in the current inbox. |
| `anti_bot_challenge` | tempail.com presented a captcha or robot-verification page. |
