# Context

## Assessment Summary

The assessment asks for a clean, maintainable temp-mail scraper API. The central challenge is not HTTP parsing, but browser automation against a dynamic web page.

## Product Interpretation

The implementation treats the API as the main deliverable and adds an operator console as a presentation layer. The console helps reviewers see the current email, inbox, selected message content, request log, and browser health without needing to write curl commands first.

## Target

- Source site: `https://tempail.com/ua/`
- Rendering mode: JavaScript-rendered page.
- Automation layer: Playwright.
- API framework: FastAPI.

## Reliability Notes

The target site can change DOM selectors. The scraper therefore uses a cascade of selectors plus text-based fallbacks rather than depending on one brittle CSS selector.

The current implementation uses one shared browser session protected by an async lock. This is appropriate for the assessment scope and avoids concurrent clicks corrupting the same page state.

For higher throughput, the next step would be a session pool keyed by client token.

