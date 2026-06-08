"""Smoke test: verify the FastAPI app object loads without import errors."""


def test_app_importable():
    from app.main import app

    assert app is not None


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
