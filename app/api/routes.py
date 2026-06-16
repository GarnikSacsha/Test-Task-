from fastapi import APIRouter, Depends, Request

from app.automation.service import TempMailService
from app.models.schemas import EmailAddressResponse, EmailContentResponse, HealthResponse, InboxResponse

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
    )


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
