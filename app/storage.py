from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.seed import initial_state

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "social_hub_state.json"


class LocalStore:
    def __init__(self, path: Path = STATE_FILE):
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            self.save(initial_state())
        with self.path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        return self._merge_defaults(state)

    def save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")

    def reset(self) -> dict[str, Any]:
        state = initial_state()
        self.save(state)
        return state

    def _merge_defaults(self, state: dict[str, Any]) -> dict[str, Any]:
        merged = copy.deepcopy(initial_state())
        for key, value in state.items():
            merged[key] = value
        return merged


class SupabaseStore:
    def __init__(self) -> None:
        self.base_url = f"{settings.supabase_url.rstrip('/')}/rest/v1"
        self.headers = {
            "apikey": settings.supabase_service_role_key or "",
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }

    def load(self) -> dict[str, Any]:
        state = {
            "profiles": {
                row["email"]: row
                for row in self._get("profiles")
            },
            "groups": {
                row["id"]: row
                for row in self._get("groups")
            },
            "memberships": self._get("memberships"),
            "invite_codes": {
                row["code"]: {"group_ids": row["group_ids"], "role": row["role"]}
                for row in self._get("invite_codes")
            },
            "activity": self._get("activity", order="created_at.desc"),
            "sports_players": self._get("sports_players", order="ladder_rank.asc"),
            "sports_matches": self._get("sports_matches", order="created_at.desc"),
            "tennis_sessions": {
                row["id"]: row["state"]
                for row in self._get("tennis_sessions")
            },
            "events": self._get("events", order="created_at.desc"),
            "life_entries": self._get("life_entries", order="created_at.desc"),
            "relationship_notes": self._get("relationship_notes", order="created_at.desc"),
        }
        if not state["profiles"]:
            state = initial_state()
            self.save(state)
        return state

    def save(self, state: dict[str, Any]) -> None:
        rows = {
            "profiles": list(state["profiles"].values()),
            "groups": list(state["groups"].values()),
            "memberships": state["memberships"],
            "invite_codes": [
                {"code": code, "group_ids": value["group_ids"], "role": value["role"]}
                for code, value in state["invite_codes"].items()
            ],
            "activity": state["activity"],
            "sports_players": state["sports_players"],
            "sports_matches": state["sports_matches"],
            "tennis_sessions": [
                {"id": session_id, "group_id": session["group_id"], "state": session}
                for session_id, session in state["tennis_sessions"].items()
            ],
            "events": state["events"],
            "life_entries": state["life_entries"],
            "relationship_notes": state["relationship_notes"],
        }
        for table in [
            "relationship_notes",
            "life_entries",
            "events",
            "tennis_sessions",
            "sports_matches",
            "sports_players",
            "activity",
            "memberships",
            "invite_codes",
            "groups",
            "profiles",
        ]:
            self._delete(table)
        for table in [
            "profiles",
            "groups",
            "invite_codes",
            "memberships",
            "activity",
            "sports_players",
            "sports_matches",
            "tennis_sessions",
            "events",
            "life_entries",
            "relationship_notes",
        ]:
            self._insert(table, rows[table])

    def reset(self) -> dict[str, Any]:
        state = initial_state()
        self.save(state)
        return state

    def _get(self, table: str, order: str | None = None) -> list[dict]:
        params = {"select": "*"}
        if order:
            params["order"] = order
        with httpx.Client(timeout=15) as client:
            response = client.get(f"{self.base_url}/{table}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    def _delete(self, table: str) -> None:
        with httpx.Client(timeout=30) as client:
            delete_response = client.delete(
                f"{self.base_url}/{table}",
                headers=self.headers | {"Prefer": "return=minimal"},
                params={"id": "not.is.null"} if table not in {"profiles", "memberships", "invite_codes"} else self._delete_filter(table),
            )
            delete_response.raise_for_status()

    def _insert(self, table: str, rows: list[dict]) -> None:
        if not rows:
            return
        with httpx.Client(timeout=30) as client:
            post_response = client.post(
                f"{self.base_url}/{table}",
                headers=self.headers | {"Prefer": "return=minimal"},
                json=rows,
            )
            post_response.raise_for_status()

    def _delete_filter(self, table: str) -> dict[str, str]:
        if table == "profiles":
            return {"email": "not.is.null"}
        if table == "memberships":
            return {"email": "not.is.null"}
        if table == "invite_codes":
            return {"code": "not.is.null"}
        return {"id": "not.is.null"}


store = SupabaseStore() if settings.supabase_enabled else LocalStore()
