class ScraperError(Exception):
    code = "scraper_error"
    status_code = 502


class BrowserUnavailableError(ScraperError):
    code = "browser_unavailable"
    status_code = 503


class TargetTimeoutError(ScraperError):
    code = "target_timeout"
    status_code = 504


class ElementMissingError(ScraperError):
    code = "element_missing"
    status_code = 502


class MessageNotFoundError(ScraperError):
    code = "message_not_found"
    status_code = 404

