import os

os.environ["DEMO_MODE"] = "true"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def make_client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(create_app())


def test_health_reports_demo_backend() -> None:
    with make_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["demo_mode"] is True


def test_email_and_inbox_contracts() -> None:
    with make_client() as client:
        email_response = client.get("/api/email")
        inbox_response = client.get("/api/inbox")

    assert email_response.status_code == 200
    assert email_response.json()["email"] == "demo.tempail@example.com"
    assert inbox_response.status_code == 200
    assert inbox_response.json()["count"] == 1
    assert inbox_response.json()["messages"][0]["id"] == "welcome-demo"


def test_email_content_and_refresh_contracts() -> None:
    with make_client() as client:
        content_response = client.get("/api/email/welcome-demo")
        refresh_response = client.post("/api/email/refresh")

    assert content_response.status_code == 200
    assert "482913" in content_response.json()["text"]
    assert refresh_response.status_code == 200
    assert refresh_response.json()["email"] == "fresh.demo.tempail@example.com"

