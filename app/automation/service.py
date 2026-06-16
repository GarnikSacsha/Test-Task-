import asyncio
import logging
from typing import Protocol

from app.automation.exceptions import ScraperError, TargetTimeoutError
from app.automation.scraper import TempailScraper
from app.core.config import Settings
from app.core.storage import Storage
from app.models.schemas import EmailContentResponse, InboxMessage, SessionSnapshot

logger = logging.getLogger(__name__)


class MailBackend(Protocol):
    last_error: str | None
    browser_ready: bool
    current_email: str | None
    inbox_count: int

    async def start(self) -> None: ...
    async def close(self) -> None: ...
    async def get_current_email(self) -> str: ...
    async def get_inbox_list(self) -> list[InboxMessage]: ...
    async def get_email_body(self, msg_id: str) -> EmailContentResponse: ...
    async def refresh_session(self) -> str: ...


class DemoMailBackend:
    def __init__(self) -> None:
        self.last_error: str | None = None
        self.browser_ready = True
        self.current_email = "demo.tempail@example.com"
        self._messages = [
            InboxMessage(
                id="welcome-demo",
                sender="robot@unilime.test",
                subject="Demo verification code",
                time="now",
                preview="Your demo code is 482913. This is generated locally.",
            )
        ]

    @property
    def inbox_count(self) -> int:
        return len(self._messages)

    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get_current_email(self) -> str:
        return self.current_email

    async def get_inbox_list(self) -> list[InboxMessage]:
        return self._messages

    async def get_email_body(self, msg_id: str) -> EmailContentResponse:
        message = next((item for item in self._messages if item.id == msg_id), None)
        if message is None:
            from app.automation.exceptions import MessageNotFoundError

            raise MessageNotFoundError(f"Message '{msg_id}' was not found")
        return EmailContentResponse(
            id=message.id,
            sender=message.sender,
            subject=message.subject,
            time=message.time,
            text="Your demo code is 482913. This content is served by demo mode.",
            html="<p>Your demo code is <strong>482913</strong>.</p>",
        )

    async def refresh_session(self) -> str:
        self.current_email = "fresh.demo.tempail@example.com"
        self._messages = []
        return self.current_email


class TempMailService:
    def __init__(self, settings: Settings, backend: MailBackend | None = None):
        self.settings = settings
        self.backend: MailBackend = backend or (DemoMailBackend() if settings.demo_mode else TempailScraper(settings))
        self.storage = Storage(settings)

    async def startup(self) -> None:
        self.storage.initialize()
        try:
            await self.backend.start()
        except ScraperError as exc:
            self.backend.last_error = str(exc)
            logger.warning("Browser startup failed: %s", exc)

    async def shutdown(self) -> None:
        await self.backend.close()

    async def email(self) -> str:
        email = await self._with_timeout(self.backend.get_current_email())
        self.storage.record_email(email)
        return email

    async def inbox(self) -> list[InboxMessage]:
        messages = await self._with_timeout(self.backend.get_inbox_list())
        self.storage.record_messages(self.backend.current_email, messages)
        return messages

    async def content(self, msg_id: str) -> EmailContentResponse:
        content = await self._with_timeout(self.backend.get_email_body(msg_id))
        self.storage.record_content(content)
        return content

    async def refresh(self) -> str:
        email = await self._with_timeout(self.backend.refresh_session())
        self.storage.record_email(email)
        self.storage.record_event("email_refreshed", {"email": email})
        return email

    def history(self, limit: int = 25) -> dict:
        return self.storage.history(limit)

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            email=self.backend.current_email,
            inbox=[],
            last_error=self.backend.last_error,
            browser_ready=self.backend.browser_ready,
        )

    async def _with_timeout(self, awaitable):
        try:
            return await asyncio.wait_for(awaitable, timeout=self.settings.api_request_timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise TargetTimeoutError("API request exceeded configured timeout") from exc
