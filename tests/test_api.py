import os
import tempfile

os.environ["DEMO_MODE"] = "true"
os.environ["APP_ENV"] = "test"
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="tempail-tests-")

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


def test_history_contract_records_activity() -> None:
    with make_client() as client:
        client.get("/api/email")
        client.get("/api/inbox")
        response = client.get("/api/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database_path"]
    assert payload["emails"][0]["address"] == "demo.tempail@example.com"
    assert payload["events"]


def test_email_content_and_refresh_contracts() -> None:
    with make_client() as client:
        content_response = client.get("/api/email/welcome-demo")
        refresh_response = client.post("/api/email/refresh")

    assert content_response.status_code == 200
    assert "482913" in content_response.json()["text"]
    assert refresh_response.status_code == 200
    assert refresh_response.json()["email"] == "fresh.demo.tempail@example.com"


def test_settings_accept_railway_values_with_trailing_spaces() -> None:
    os.environ["APP_ENV"] = "production "
    os.environ["DEMO_MODE"] = "true "
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_env == "production"
    assert settings.demo_mode is True

    os.environ["APP_ENV"] = "test"
    os.environ["DEMO_MODE"] = "true"
    get_settings.cache_clear()
