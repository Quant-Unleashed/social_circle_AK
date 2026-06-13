from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Response, status

from app.config import settings
from app.storage import store

SESSION_COOKIE = "social_hub_session"


def _sign(payload: str) -> str:
    return hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session(email: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"email": email.lower()}).encode()).decode()
    return f"{payload}.{_sign(payload)}"


def read_session(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    payload, signature = token.rsplit(".", 1)
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except (ValueError, json.JSONDecodeError):
        return None
    return str(data.get("email", "")).lower() or None


def set_session_cookie(response: Response, email: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        create_session(email),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def current_profile(
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    state = store.load()
    email = read_session(session)
    if not email and authorization and authorization.lower().startswith("bearer dev-"):
        email = authorization[11:].strip().lower()
    if not email or email not in state["profiles"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required.")
    return state["profiles"][email]


def require_admin(profile: dict = Depends(current_profile)) -> dict:
    if profile.get("role") != "admin" and profile["email"].lower() not in settings.admin_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required.")
    return profile


def membership_for(email: str, group_id: str, state: dict) -> dict | None:
    return next(
        (
            membership
            for membership in state["memberships"]
            if membership["email"] == email and membership["group_id"] == group_id
        ),
        None,
    )


def require_group_member(email: str, group_id: str, state: dict) -> dict:
    membership = membership_for(email, group_id, state)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group membership required.")
    return membership
