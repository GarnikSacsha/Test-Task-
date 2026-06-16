from fastapi import APIRouter, Depends, Request

from app.automation.service import TempMailService
from app.models.schemas import (
    EmailAddressResponse,
    EmailContentResponse,
    HealthResponse,
    HistoryResponse,
    InboxResponse,
    ModeResponse,
)

router = APIRouter()


def get_service(request: Request) -> TempMailService:
    return request.app.state.mail_service


service_dependency = Depends(get_service)


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(service: TempMailService = service_dependency) -> HealthResponse:
    return HealthResponse(
        status="ok" if not service.backend.last_error else "degraded",
        browser="ready" if service.backend.browser_ready else "not_ready",
        current_email=service.backend.current_email,
        inbox_count=service.backend.inbox_count,
        demo_mode=service.settings.demo_mode,
        storage="enabled" if service.settings.storage_enabled else "disabled",
    )


@router.get("/api/mode", response_model=ModeResponse, tags=["system"])
async def mode(service: TempMailService = service_dependency) -> ModeResponse:
    live = not service.settings.demo_mode
    note = (
        "Live Playwright scraper is active. tempail.com may still return an anti-bot challenge."
        if live
        else "Demo mode is active for stable public presentation. Set DEMO_MODE=false to use live Playwright scraping."
    )
    return ModeResponse(mode="live" if live else "demo", live_scraper_enabled=live, note=note)


@router.get("/api/email", response_model=EmailAddressResponse, tags=["mail"])
async def get_email(service: TempMailService = service_dependency) -> EmailAddressResponse:
    return EmailAddressResponse(email=await service.email())


@router.get("/api/inbox", response_model=InboxResponse, tags=["mail"])
async def get_inbox(service: TempMailService = service_dependency) -> InboxResponse:
    messages = await service.inbox()
    return InboxResponse(email=service.backend.current_email, count=len(messages), messages=messages)


@router.get("/api/email/{message_id}", response_model=EmailContentResponse, tags=["mail"])
async def get_email_content(
    message_id: str,
    service: TempMailService = service_dependency,
) -> EmailContentResponse:
    return await service.content(message_id)


@router.post("/api/email/refresh", response_model=EmailAddressResponse, tags=["mail"])
async def refresh_email(service: TempMailService = service_dependency) -> EmailAddressResponse:
    return EmailAddressResponse(email=await service.refresh())


@router.get("/api/history", response_model=HistoryResponse, tags=["mail"])
async def get_history(limit: int = 25, service: TempMailService = service_dependency) -> HistoryResponse:
    return HistoryResponse(**service.history(limit=min(max(limit, 1), 100)))
