from fastapi.testclient import TestClient

from app.main import app
from app.storage import store


def test_unauthenticated_hub_is_rejected():
    store.reset()
    client = TestClient(app)
    response = client.get("/api/hub")
    assert response.status_code == 401


def test_invite_code_login_grants_group_and_modules():
    store.reset()
    client = TestClient(app)
    response = client.post(
        "/api/login",
        json={"email": "friend@example.com", "name": "Friend", "invite_code": "BADMINTON2026"},
    )
    assert response.status_code == 200

    hub = client.get("/api/hub").json()
    assert hub["profile"]["email"] == "friend@example.com"
    assert [group["id"] for group in hub["groups"]] == ["drw-badminton"]
    assert any(module["id"] == "sports" for module in hub["modules"])


def test_invalid_invite_code_is_rejected():
    store.reset()
    client = TestClient(app)
    response = client.post(
        "/api/login",
        json={"email": "stranger@example.com", "name": "Stranger", "invite_code": "NOPE"},
    )
    assert response.status_code == 403


def test_fifa_link_is_external_only():
    store.reset()
    client = TestClient(app)
    client.post("/api/login", json={"email": "friend@example.com", "name": "Friend", "invite_code": "SOCIALHUB"})
    hub = client.get("/api/hub").json()
    assert hub["fifa_link"]["url"] == "https://aman-fifa-sweepstake.onrender.com"
    assert client.get("/api/dashboard").status_code == 404
