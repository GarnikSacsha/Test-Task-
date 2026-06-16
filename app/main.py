from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.automation.exceptions import ScraperError
from app.automation.service import TempMailService
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.models.schemas import ErrorPayload


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.mail_service = TempMailService(settings)
    await app.state.mail_service.startup()
    yield
    await app.state.mail_service.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="REST API and operator console for a Playwright-powered tempail.com scraper.",
        lifespan=lifespan,
    )

    origins = ["*"] if settings.cors_origins == "*" else [item.strip() for item in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ScraperError)
    async def scraper_exception_handler(_: Request, exc: ScraperError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorPayload(error=str(exc), code=exc.code).model_dump(mode="json"),
        )

    app.include_router(router)
    app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
    return app


app = create_app()

