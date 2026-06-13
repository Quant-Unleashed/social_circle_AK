from __future__ import annotations

from datetime import datetime, timezone

MODULES = {
    "sports": {
        "name": "Sports",
        "summary": "Tennis scoring, badminton ladder, challenges, ratings, and match history.",
        "status": "active",
    },
    "events": {
        "name": "Events & Hosting",
        "summary": "RSVPs, bring-item lists, food/location polls, dietary notes, and simple splits.",
        "status": "active",
    },
    "life_map": {
        "name": "Life Map",
        "summary": "Private or shared snapshots of what people are into, learning, craving, and becoming.",
        "status": "active",
    },
    "taste_graph": {
        "name": "Taste Graph",
        "summary": "Future module for songs, foods, restaurants, films, activities, and overlap scores.",
        "status": "preview",
    },
    "cravings": {
        "name": "Craving Board",
        "summary": "Future module for spontaneous plans like Korean food, badminton, hikes, and pub quizzes.",
        "status": "preview",
    },
    "shopping": {
        "name": "Bulk Buying",
        "summary": "Future module for Costco runs, groceries, shared supplies, and grouped requests.",
        "status": "preview",
    },
}

FIFA_LINK = {
    "label": "Aman's FIFA Sweepstake",
    "url": "https://aman-fifa-sweepstake.onrender.com",
    "summary": "External hosted sweepstake dashboard. Opens outside Social Hub.",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def initial_state() -> dict:
    created_at = now_iso()
    return {
        "profiles": {
            "aman@example.com": {
                "email": "aman@example.com",
                "name": "Aman",
                "username": "aman",
                "avatar_url": "",
                "role": "admin",
                "created_at": created_at,
            }
        },
        "groups": {
            "friends-london": {
                "id": "friends-london",
                "name": "Friends London",
                "description": "Planning socials, sports, food, and memories with the London crew.",
                "enabled_modules": ["sports", "events", "life_map"],
                "created_at": created_at,
            },
            "drw-badminton": {
                "id": "drw-badminton",
                "name": "DRW Badminton",
                "description": "Badminton ladder, challenges, and weekly availability.",
                "enabled_modules": ["sports", "events"],
                "created_at": created_at,
            },
            "family": {
                "id": "family",
                "name": "Family",
                "description": "Family plans, gift ideas, food preferences, and life updates.",
                "enabled_modules": ["events", "life_map"],
                "created_at": created_at,
            },
        },
        "memberships": [
            {"email": "aman@example.com", "group_id": "friends-london", "role": "admin"},
            {"email": "aman@example.com", "group_id": "drw-badminton", "role": "admin"},
            {"email": "aman@example.com", "group_id": "family", "role": "admin"},
        ],
        "invite_codes": {
            "SOCIALHUB": {"group_ids": ["friends-london"], "role": "member"},
            "TENNIS2026": {"group_ids": ["friends-london"], "role": "member"},
            "BADMINTON2026": {"group_ids": ["drw-badminton"], "role": "member"},
            "BBQCREW": {"group_ids": ["friends-london"], "role": "member"},
            "FAMILY": {"group_ids": ["family"], "role": "member"},
        },
        "activity": [
            {
                "id": "act-001",
                "group_id": "friends-london",
                "type": "module",
                "message": "Social Hub is ready with Sports, Events, Life Map, and a FIFA external link.",
                "created_at": created_at,
            }
        ],
        "sports_players": [
            {"id": "p-aman", "group_id": "drw-badminton", "name": "Aman", "ladder_rank": 1, "elo": 1200},
            {"id": "p-james", "group_id": "drw-badminton", "name": "James", "ladder_rank": 2, "elo": 1200},
            {"id": "p-chris", "group_id": "drw-badminton", "name": "Chris", "ladder_rank": 3, "elo": 1200},
            {"id": "p-neesha", "group_id": "drw-badminton", "name": "Neesha", "ladder_rank": 4, "elo": 1200},
        ],
        "sports_matches": [],
        "tennis_sessions": {},
        "events": [
            {
                "id": "event-bbq",
                "group_id": "friends-london",
                "title": "BBQ planning",
                "starts_at": "2026-06-20T17:00:00+01:00",
                "location": "London",
                "description": "Food, location, bring-items, and cost split planning.",
                "rsvps": {"aman@example.com": "yes"},
                "bring_items": [{"name": "Paneer skewers", "claimed_by": "aman@example.com"}],
                "polls": [{"question": "Main food?", "options": ["BBQ", "Korean", "Pizza"], "votes": {}}],
                "costs": [{"label": "Coal and basics", "amount": 20.0, "paid_by": "aman@example.com"}],
                "dietary_notes": "Track vegetarian, allergies, and spice preferences here.",
                "comments": [],
                "created_at": created_at,
            }
        ],
        "life_entries": [
            {
                "id": "life-001",
                "email": "aman@example.com",
                "group_id": "friends-london",
                "category": "learning",
                "title": "Improving tennis match play",
                "body": "Working on consistency and smarter point construction.",
                "visibility": "selected_group",
                "created_at": created_at,
            }
        ],
        "relationship_notes": [],
    }
