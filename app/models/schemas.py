from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiMeta(BaseModel):
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "tempail.com"


class ErrorPayload(BaseModel):
    error: str
    detail: str | None = None
    code: str


class EmailAddressResponse(BaseModel):
    email: str
    meta: ApiMeta = Field(default_factory=ApiMeta)


class InboxMessage(BaseModel):
    id: str
    sender: str | None = None
    subject: str | None = None
    time: str | None = None
    preview: str | None = None


class InboxResponse(BaseModel):
    email: str | None = None
    count: int
    messages: list[InboxMessage]
    meta: ApiMeta = Field(default_factory=ApiMeta)


class EmailContentResponse(BaseModel):
    id: str
    sender: str | None = None
    subject: str | None = None
    time: str | None = None
    text: str | None = None
    html: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    meta: ApiMeta = Field(default_factory=ApiMeta)


class HealthResponse(BaseModel):
    status: str
    browser: str
    current_email: str | None = None
    inbox_count: int = 0
    demo_mode: bool = False
    storage: str = "disabled"


class SessionSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    email: str | None = None
    inbox: list[InboxMessage] = Field(default_factory=list)
    last_error: str | None = None
    browser_ready: bool = False


class HistoryResponse(BaseModel):
    database_path: str | None = None
    emails: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    events: list[dict[str, Any]]
