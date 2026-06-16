# Requirements

## Objective

Build a Python web application that automates interaction with `https://tempail.com/ua/`, a JavaScript-rendered temporary email service.

The application must expose the functionality as a REST API and return JSON for all API responses.

## Functional Scope

- Generate or retrieve the current temporary email address.
- Monitor the inbox and return received email metadata.
- Retrieve full email content by message ID.
- Refresh the current temporary email address.
- Handle empty inboxes, page load timeouts, missing DOM elements, stale sessions, browser crashes, and network issues.

## Required API

| Method | Endpoint | Required behavior |
| --- | --- | --- |
| `GET` | `/api/email` | Return current temporary email address. |
| `GET` | `/api/inbox` | Return list of received emails. |
| `GET` | `/api/email/{id}` | Return full content of a specific email. |
| `POST` | `/api/email/refresh` | Generate a new temporary email address. |

## Technical Requirements

- Python 3.10+.
- Any Python web framework is allowed.
- Browser automation must use Playwright or Selenium.
- Scraping with only `requests` and `BeautifulSoup` is not enough because the target site is rendered by JavaScript.
- Responses must be JSON.
- Include dependency file and setup instructions.

## Bonus Requirements

- Dockerfile.
- `docker-compose.yml`.
- Logging.
- Environment-based configuration.

## Acceptance Criteria

- All four required endpoints work and return JSON.
- The application does not crash on expected external-site failures.
- Automation code is separated from API code.
- Timeouts and runtime parameters are configurable.
- README contains setup and API usage examples.

