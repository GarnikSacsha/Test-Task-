import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from app.automation.exceptions import (
    BrowserUnavailableError,
    ElementMissingError,
    MessageNotFoundError,
    TargetTimeoutError,
)
from app.core.config import Settings
from app.models.schemas import EmailContentResponse, InboxMessage

logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


@dataclass
class BrowserState:
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    playwright: object | None = None


class TempailScraper:
    """Async Playwright adapter for tempail.com.

    The site is JavaScript-rendered and has changed selectors over time, so the
    scraper uses a small cascade of semantic selectors and DOM fallbacks.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.state = BrowserState()
        self._lock = asyncio.Lock()
        self._email: str | None = None
        self._inbox: list[InboxMessage] = []
        self.last_error: str | None = None

    @property
    def browser_ready(self) -> bool:
        return self.state.page is not None and not self.state.page.is_closed()

    @property
    def current_email(self) -> str | None:
        return self._email

    @property
    def inbox_count(self) -> int:
        return len(self._inbox)

    async def start(self) -> None:
        async with self._lock:
            if self.browser_ready:
                return
            await self._start_unlocked()

    async def close(self) -> None:
        async with self._lock:
            await self._close_unlocked()

    async def get_current_email(self) -> str:
        async with self._lock:
            await self._ensure_page()
            email = await self._extract_email()
            self._email = email
            self.last_error = None
            return email

    async def get_inbox_list(self) -> list[InboxMessage]:
        async with self._lock:
            await self._ensure_page()
            for _ in range(max(1, self.settings.inbox_poll_attempts)):
                inbox = await self._extract_inbox()
                if inbox:
                    self._inbox = inbox
                    self.last_error = None
                    return inbox
                await self.state.page.wait_for_timeout(self.settings.inbox_poll_interval_ms)
            self._inbox = []
            self.last_error = None
            return []

    async def get_email_body(self, msg_id: str) -> EmailContentResponse:
        async with self._lock:
            await self._ensure_page()
            inbox = self._inbox or await self._extract_inbox()
            message = next((item for item in inbox if item.id == msg_id), None)
            if message is None:
                raise MessageNotFoundError(f"Message '{msg_id}' was not found in the current inbox")

            row = await self._find_message_row(message)
            if row is None:
                raise MessageNotFoundError(f"Message '{msg_id}' is no longer visible on the page")

            await row.click()
            page = self.state.page
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(500)

            text = await self._safe_visible_text(
                [
                    ".mail-content",
                    ".message-content",
                    ".email-content",
                    "article",
                    "main",
                    "body",
                ]
            )
            html = await page.locator("body").inner_html()
            self.last_error = None
            return EmailContentResponse(
                id=message.id,
                sender=message.sender,
                subject=message.subject,
                time=message.time,
                text=text,
                html=html,
                raw={"url": page.url},
            )

    async def refresh_session(self) -> str:
        async with self._lock:
            await self._ensure_page()
            page = self.state.page
            old_email = self._email
            clicked = await self._click_first_matching(
                [
                    "button:has-text('Refresh')",
                    "button:has-text('Змінити')",
                    "button:has-text('Оновити')",
                    "button:has-text('Refresh Email')",
                    "a:has-text('Refresh')",
                    "[title*='refresh' i]",
                    "[class*='refresh' i]",
                    "[id*='refresh' i]",
                ]
            )
            if not clicked:
                await page.reload(wait_until="domcontentloaded")

            try:
                await page.wait_for_function(
                    """oldEmail => {
                        const text = document.body.innerText || '';
                        const match = text.match(/[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}/);
                        return match && match[0] !== oldEmail;
                    }""",
                    arg=old_email,
                    timeout=self.settings.browser_timeout_ms,
                )
            except PlaywrightTimeoutError:
                logger.info("Refresh did not expose a different email before timeout; extracting current email")

            self._inbox = []
            self._email = await self._extract_email()
            self.last_error = None
            return self._email

    async def _start_unlocked(self) -> None:
        try:
            self.state.playwright = await async_playwright().start()
            chromium = self.state.playwright.chromium
            self.state.browser = await chromium.launch(
                headless=self.settings.browser_headless,
                slow_mo=self.settings.browser_slow_mo_ms,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            self.state.context = await self.state.browser.new_context(
                viewport={"width": 1440, "height": 1000},
                locale="uk-UA",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
                ),
            )
            self.state.page = await self.state.context.new_page()
            self.state.page.set_default_timeout(self.settings.browser_timeout_ms)
            await self.state.page.goto(self.settings.tempail_url, wait_until="domcontentloaded")
            logger.info("Started Playwright session for %s", self.settings.tempail_url)
        except PlaywrightTimeoutError as exc:
            await self._close_unlocked()
            raise TargetTimeoutError("Timed out while opening tempail.com") from exc
        except PlaywrightError as exc:
            await self._close_unlocked()
            raise BrowserUnavailableError(str(exc)) from exc

    async def _close_unlocked(self) -> None:
        try:
            if self.state.context:
                await self.state.context.close()
            if self.state.browser:
                await self.state.browser.close()
            if self.state.playwright:
                await self.state.playwright.stop()
        finally:
            self.state = BrowserState()

    async def _ensure_page(self) -> None:
        if not self.browser_ready:
            await self._close_unlocked()
            await self._start_unlocked()
        assert self.state.page is not None

    async def _extract_email(self) -> str:
        page = self.state.page
        assert page is not None
        await page.wait_for_load_state("domcontentloaded")

        candidates = [
            "#email",
            "#mail",
            "input[type='email']",
            "input[readonly]",
            "[data-email]",
            "[class*='email' i]",
            "[id*='email' i]",
            "[class*='mail' i]",
            "[id*='mail' i]",
        ]
        for selector in candidates:
            locator = page.locator(selector).first
            if await locator.count():
                value = await self._locator_value_or_text(locator)
                match = EMAIL_RE.search(value)
                if match:
                    return match.group(0)

        try:
            await page.wait_for_function(
                """() => /[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}/.test(document.body.innerText || '')""",
                timeout=self.settings.browser_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise ElementMissingError("Could not locate generated email on tempail.com") from exc

        body_text = await page.locator("body").inner_text()
        match = EMAIL_RE.search(body_text)
        if not match:
            raise ElementMissingError("Email-like text was not found after page load")
        return match.group(0)

    async def _extract_inbox(self) -> list[InboxMessage]:
        page = self.state.page
        assert page is not None
        await page.wait_for_load_state("domcontentloaded")
        await self._click_first_matching(
            [
                "button:has-text('Refresh')",
                "button:has-text('Оновити')",
                "button:has-text('Check')",
                "[class*='reload' i]",
            ]
        )

        rows = await page.locator(
            "table tbody tr, [class*='inbox' i] li, [class*='mail' i] li, "
            "[class*='message' i], a[href*='mail']"
        ).all()
        messages: list[InboxMessage] = []
        for index, row in enumerate(rows):
            try:
                text = " ".join((await row.inner_text()).split())
            except PlaywrightError:
                continue
            if not text or EMAIL_RE.fullmatch(text):
                continue
            message = self._message_from_text(text, index)
            if message and message.id not in {item.id for item in messages}:
                messages.append(message)
        return messages

    def _message_from_text(self, text: str, index: int) -> InboxMessage | None:
        lower = text.lower()
        empty_markers = ["empty", "no messages", "немає", "порож", "inbox is empty"]
        if any(marker in lower for marker in empty_markers):
            return None

        parts = [part.strip() for part in re.split(r"\s{2,}|\n|\t", text) if part.strip()]
        sender = next((part for part in parts if EMAIL_RE.search(part)), None)
        subject = next((part for part in parts if part != sender), text[:120])
        time = next((part for part in parts if re.search(r"\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}", part)), None)
        digest = hashlib.sha1(f"{index}:{text}".encode()).hexdigest()[:12]
        return InboxMessage(
            id=digest,
            sender=sender,
            subject=subject[:180] if subject else None,
            time=time,
            preview=text[:240],
        )

    async def _find_message_row(self, message: InboxMessage):
        page = self.state.page
        assert page is not None
        needles = [value for value in [message.sender, message.subject, message.preview] if value]
        for needle in needles:
            locator = page.get_by_text(needle[:80], exact=False).first
            try:
                if await locator.count():
                    return locator
            except PlaywrightError:
                continue
        return None

    async def _safe_visible_text(self, selectors: list[str]) -> str | None:
        page = self.state.page
        assert page is not None
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count():
                    text = await locator.inner_text(timeout=2_000)
                    if text.strip():
                        return text.strip()
            except PlaywrightError:
                continue
        return None

    async def _locator_value_or_text(self, locator) -> str:
        try:
            value = await locator.input_value(timeout=1_000)
            if value:
                return value
        except PlaywrightError:
            pass
        try:
            return await locator.inner_text(timeout=1_000)
        except PlaywrightError:
            return ""

    async def _click_first_matching(self, selectors: list[str]) -> bool:
        page = self.state.page
        assert page is not None
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count() and await locator.is_visible():
                    await locator.click(timeout=2_000)
                    return True
            except PlaywrightError:
                continue
        return False
