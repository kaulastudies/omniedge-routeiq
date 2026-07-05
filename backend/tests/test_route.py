from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_status_endpoint_returns_provider_health():
    response = client.get("/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "providers" in payload


def test_route_sensitive_prompt_uses_local_or_fallback():
    response = client.post(
        "/route",
        json={
            "prompt": "Summarize this confidential patient insurance note. Phone: +91 9876543210",
            "privacy_level": "regulated",
            "task_type": "privacy_review",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["target"] == "local"
    assert payload["audit_timeline"]


def test_simulations_are_available():
    response = client.get("/simulations")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["scenarios"]) >= 3
