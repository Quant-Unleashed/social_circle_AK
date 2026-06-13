from fastapi.testclient import TestClient

from app.main import app
from app.storage import store


def logged_in_client(code="BADMINTON2026"):
    store.reset()
    client = TestClient(app)
    response = client.post("/api/login", json={"email": "player@example.com", "name": "Player", "invite_code": code})
    assert response.status_code == 200
    return client


def test_tennis_scoring_advantage_undo_and_display():
    client = logged_in_client()
    created = client.post(
        "/api/groups/drw-badminton/tennis",
        json={"team_a": ["Aman"], "team_b": ["James"], "format": "best_of_3", "scoring": "advantage"},
    ).json()
    session_id = created["session"]["id"]

    client.post(f"/api/tennis/{session_id}/point", json={"side": 0})
    client.post(f"/api/tennis/{session_id}/point", json={"side": 0})
    scored = client.post(f"/api/tennis/{session_id}/point", json={"side": 1}).json()
    assert scored["score"]["point_text"] == "30-15"

    undone = client.post(f"/api/tennis/{session_id}/undo").json()
    assert undone["score"]["point_text"] == "30-0"


def test_badminton_ladder_moves_lower_ranked_winner_above_loser():
    client = logged_in_client()
    detail = client.get("/api/groups/drw-badminton").json()
    james = next(player for player in detail["sports_players"] if player["name"] == "James")
    aman = next(player for player in detail["sports_players"] if player["name"] == "Aman")

    result = client.post(
        "/api/groups/drw-badminton/badminton/results",
        json={"winner_id": james["id"], "loser_id": aman["id"], "score": "21-18, 21-19"},
    ).json()
    ranks = {player["name"]: player["ladder_rank"] for player in result["players"]}
    assert ranks["James"] == 1
    assert ranks["Aman"] == 2


def test_disputed_badminton_result_does_not_move_ladder():
    client = logged_in_client()
    detail = client.get("/api/groups/drw-badminton").json()
    chris = next(player for player in detail["sports_players"] if player["name"] == "Chris")
    aman = next(player for player in detail["sports_players"] if player["name"] == "Aman")
    result = client.post(
        "/api/groups/drw-badminton/badminton/results",
        json={"winner_id": chris["id"], "loser_id": aman["id"], "score": "21-10", "disputed": True},
    ).json()
    ranks = {player["name"]: player["ladder_rank"] for player in result["players"]}
    assert ranks["Chris"] == 3
    assert result["match"]["status"] == "disputed"


def test_event_creation_and_rsvp():
    client = logged_in_client("SOCIALHUB")
    event = client.post(
        "/api/groups/friends-london/events",
        json={"title": "Pizza night", "location": "London", "description": "Vote on toppings"},
    ).json()["event"]
    assert event["rsvps"]["player@example.com"] == "yes"

    updated = client.post(f"/api/events/{event['id']}/rsvp", json={"status": "maybe"}).json()["event"]
    assert updated["rsvps"]["player@example.com"] == "maybe"


def test_life_map_visibility_hides_only_me_from_other_members():
    client = logged_in_client("SOCIALHUB")
    entry = client.post(
        "/api/groups/friends-london/life",
        json={"category": "learning", "title": "Spanish", "body": "Practicing weekly", "visibility": "only_me"},
    ).json()["entry"]
    assert entry["visibility"] == "only_me"

    other = TestClient(app)
    other.post("/api/login", json={"email": "other@example.com", "name": "Other", "invite_code": "SOCIALHUB"})
    detail = other.get("/api/groups/friends-london").json()
    assert all(item["id"] != entry["id"] for item in detail["life_entries"])
