from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import clear_session_cookie, current_profile, require_admin, require_group_member, set_session_cookie
from app.badminton import record_ladder_result
from app.config import settings
from app.seed import FIFA_LINK, MODULES, now_iso
from app.storage import ROOT, store
from app.tennis import display_score, new_session, score_point, undo

STATIC_DIR = ROOT / "static"

app = FastAPI(title="Social Hub")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/login")
async def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/")
async def index(_: dict = Depends(current_profile)) -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/groups/{group_id}")
async def group_page(group_id: str, profile: dict = Depends(current_profile)) -> FileResponse:
    state = store.load()
    require_group_member(profile["email"], group_id, state)
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/login")
async def login(payload: dict, response: Response) -> dict:
    email = str(payload.get("email", "")).strip().lower()
    name = str(payload.get("name") or email.split("@")[0]).strip() or "Friend"
    code = str(payload.get("invite_code", "")).strip().upper()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required.")

    state = store.load()
    invite = state["invite_codes"].get(code)
    if not invite:
        raise HTTPException(status_code=403, detail="Invite code is not valid.")

    profile = state["profiles"].setdefault(
        email,
        {
            "email": email,
            "name": name,
            "username": email.split("@")[0],
            "avatar_url": "",
            "role": "admin" if email in settings.admin_emails else "member",
            "created_at": now_iso(),
        },
    )
    profile["name"] = name
    if email in settings.admin_emails:
        profile["role"] = "admin"

    existing = {(item["email"], item["group_id"]) for item in state["memberships"]}
    for group_id in invite["group_ids"]:
        key = (email, group_id)
        if key not in existing:
            state["memberships"].append({"email": email, "group_id": group_id, "role": invite["role"]})
            state["activity"].insert(
                0,
                {
                    "id": f"act-{uuid4().hex[:8]}",
                    "group_id": group_id,
                    "type": "member",
                    "message": f"{name} joined {state['groups'][group_id]['name']}.",
                    "created_at": now_iso(),
                },
            )
    store.save(state)
    set_session_cookie(response, email)
    return {"ok": True, "profile": profile}


@app.post("/api/logout")
async def logout(response: Response) -> dict:
    clear_session_cookie(response)
    return {"ok": True}


@app.get("/api/config")
async def public_config() -> dict:
    return {
        "app_name": settings.app_name,
        "supabase_enabled": settings.supabase_enabled,
        "supabase_url": settings.supabase_url,
        "supabase_anon_key": settings.supabase_anon_key,
    }


@app.get("/api/me")
async def me(profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    memberships = [item for item in state["memberships"] if item["email"] == profile["email"]]
    groups = [state["groups"][item["group_id"]] | {"role": item["role"]} for item in memberships]
    enabled = sorted({module for group in groups for module in group["enabled_modules"]})
    return {"profile": profile, "groups": groups, "modules": [MODULES[key] | {"id": key} for key in enabled]}


@app.get("/api/hub")
async def hub(profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    member_group_ids = {item["group_id"] for item in state["memberships"] if item["email"] == profile["email"]}
    groups = [state["groups"][group_id] for group_id in member_group_ids]
    activity = [item for item in state["activity"] if item["group_id"] in member_group_ids][:20]
    enabled = sorted({module for group in groups for module in group["enabled_modules"]})
    return {
        "profile": profile,
        "groups": groups,
        "modules": [MODULES[key] | {"id": key} for key in enabled],
        "activity": activity,
        "fifa_link": FIFA_LINK,
    }


@app.get("/api/groups/{group_id}")
async def group_detail(group_id: str, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    require_group_member(profile["email"], group_id, state)
    group = state["groups"].get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")
    member_emails = [item["email"] for item in state["memberships"] if item["group_id"] == group_id]
    return {
        "group": group,
        "members": [state["profiles"][email] for email in member_emails if email in state["profiles"]],
        "modules": [MODULES[key] | {"id": key} for key in group["enabled_modules"]],
        "activity": [item for item in state["activity"] if item["group_id"] == group_id][:20],
        "events": [item for item in state["events"] if item["group_id"] == group_id],
        "sports_players": [item for item in state["sports_players"] if item["group_id"] == group_id],
        "life_entries": visible_life_entries(state, profile["email"], group_id),
    }


@app.post("/api/groups/{group_id}/events")
async def create_event(group_id: str, payload: dict, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    require_group_member(profile["email"], group_id, state)
    event = {
        "id": f"event-{uuid4().hex[:8]}",
        "group_id": group_id,
        "title": payload.get("title", "Untitled event"),
        "starts_at": payload.get("starts_at", ""),
        "location": payload.get("location", ""),
        "description": payload.get("description", ""),
        "rsvps": {profile["email"]: "yes"},
        "bring_items": payload.get("bring_items", []),
        "polls": payload.get("polls", []),
        "costs": payload.get("costs", []),
        "dietary_notes": payload.get("dietary_notes", ""),
        "comments": [],
        "created_at": now_iso(),
    }
    state["events"].insert(0, event)
    add_activity(state, group_id, "event", f"{profile['name']} created {event['title']}.")
    store.save(state)
    return {"ok": True, "event": event}


@app.post("/api/events/{event_id}/rsvp")
async def rsvp(event_id: str, payload: dict, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    event = find_by_id(state["events"], event_id)
    require_group_member(profile["email"], event["group_id"], state)
    status = payload.get("status", "maybe")
    if status not in {"yes", "maybe", "no"}:
        raise HTTPException(status_code=400, detail="RSVP must be yes, maybe, or no.")
    event["rsvps"][profile["email"]] = status
    add_activity(state, event["group_id"], "event", f"{profile['name']} RSVP'd {status} for {event['title']}.")
    store.save(state)
    return {"ok": True, "event": event}


@app.post("/api/groups/{group_id}/life")
async def create_life_entry(group_id: str, payload: dict, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    require_group_member(profile["email"], group_id, state)
    visibility = payload.get("visibility", "selected_group")
    if visibility not in {"only_me", "selected_group", "friends", "family"}:
        raise HTTPException(status_code=400, detail="Unsupported visibility.")
    entry = {
        "id": f"life-{uuid4().hex[:8]}",
        "email": profile["email"],
        "group_id": group_id,
        "category": payload.get("category", "learning"),
        "title": payload.get("title", ""),
        "body": payload.get("body", ""),
        "visibility": visibility,
        "created_at": now_iso(),
    }
    state["life_entries"].insert(0, entry)
    add_activity(state, group_id, "life_map", f"{profile['name']} added a Life Map update.")
    store.save(state)
    return {"ok": True, "entry": entry}


@app.post("/api/groups/{group_id}/tennis")
async def create_tennis_session(group_id: str, payload: dict, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    require_group_member(profile["email"], group_id, state)
    session_id = f"tennis-{uuid4().hex[:8]}"
    payload = payload | {"id": session_id, "group_id": group_id}
    session = new_session(payload)
    state["tennis_sessions"][session_id] = session
    add_activity(state, group_id, "sports", f"{profile['name']} started a tennis scoring session.")
    store.save(state)
    return {"ok": True, "session": session, "score": display_score(session)}


@app.post("/api/tennis/{session_id}/point")
async def tennis_point(session_id: str, payload: dict, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    session = state["tennis_sessions"].get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Tennis session not found.")
    require_group_member(profile["email"], session["group_id"], state)
    side = int(payload.get("side", 0))
    if side not in {0, 1}:
        raise HTTPException(status_code=400, detail="Side must be 0 or 1.")
    session = score_point(session, side)
    state["tennis_sessions"][session_id] = session
    store.save(state)
    return {"ok": True, "session": session, "score": display_score(session)}


@app.post("/api/tennis/{session_id}/undo")
async def tennis_undo(session_id: str, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    session = state["tennis_sessions"].get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Tennis session not found.")
    require_group_member(profile["email"], session["group_id"], state)
    session = undo(session)
    state["tennis_sessions"][session_id] = session
    store.save(state)
    return {"ok": True, "session": session, "score": display_score(session)}


@app.post("/api/groups/{group_id}/badminton/results")
async def badminton_result(group_id: str, payload: dict, profile: dict = Depends(current_profile)) -> dict:
    state = store.load()
    require_group_member(profile["email"], group_id, state)
    players = [item for item in state["sports_players"] if item["group_id"] == group_id]
    updated = record_ladder_result(
        players,
        str(payload.get("winner_id")),
        str(payload.get("loser_id")),
        bool(payload.get("disputed", False)),
    )
    others = [item for item in state["sports_players"] if item["group_id"] != group_id]
    state["sports_players"] = others + updated
    match = {
        "id": f"match-{uuid4().hex[:8]}",
        "group_id": group_id,
        "sport": "badminton",
        "winner_id": payload.get("winner_id"),
        "loser_id": payload.get("loser_id"),
        "score": payload.get("score", ""),
        "status": "disputed" if payload.get("disputed") else "confirmed",
        "created_by": profile["email"],
        "created_at": now_iso(),
    }
    state["sports_matches"].insert(0, match)
    add_activity(state, group_id, "sports", f"{profile['name']} recorded a badminton result.")
    store.save(state)
    return {"ok": True, "players": updated, "match": match}


@app.post("/api/admin/reset")
async def reset(_: dict = Depends(require_admin)) -> dict:
    return {"ok": True, "state": store.reset()}


def add_activity(state: dict, group_id: str, activity_type: str, message: str) -> None:
    state["activity"].insert(
        0,
        {"id": f"act-{uuid4().hex[:8]}", "group_id": group_id, "type": activity_type, "message": message, "created_at": now_iso()},
    )


def find_by_id(items: list[dict], item_id: str) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found.")


def visible_life_entries(state: dict, viewer_email: str, group_id: str) -> list[dict]:
    viewer_groups = {item["group_id"] for item in state["memberships"] if item["email"] == viewer_email}
    visible = []
    for entry in state["life_entries"]:
        if entry["email"] == viewer_email:
            visible.append(entry)
        elif entry["visibility"] == "selected_group" and entry["group_id"] == group_id and group_id in viewer_groups:
            visible.append(entry)
        elif entry["visibility"] in {"friends", "family"} and entry["group_id"] in viewer_groups:
            visible.append(entry)
    return visible
