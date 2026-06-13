from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Social Hub"
    session_secret: str = os.getenv("SESSION_SECRET", "dev-session-secret-change-me")
    app_invite_code: str = os.getenv("APP_INVITE_CODE", "SOCIALHUB")
    admin_emails: tuple[str, ...] = tuple(
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "aman@example.com").split(",")
        if email.strip()
    )
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_anon_key: str | None = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key and self.supabase_service_role_key)


settings = Settings()
