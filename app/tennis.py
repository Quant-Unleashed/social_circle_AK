from __future__ import annotations

POINT_LABELS = ["0", "15", "30", "40"]


def new_session(payload: dict) -> dict:
    return {
        "id": payload["id"],
        "group_id": payload["group_id"],
        "format": payload.get("format", "best_of_3"),
        "scoring": payload.get("scoring", "advantage"),
        "tiebreak_points": int(payload.get("tiebreak_points", 7)),
        "match_tiebreak_points": int(payload.get("match_tiebreak_points", 10)),
        "team_a": payload.get("team_a", ["Player A"]),
        "team_b": payload.get("team_b", ["Player B"]),
        "sets": [{"games": [0, 0], "tiebreak": None}],
        "points": [0, 0],
        "history": [],
        "winner": None,
    }


def score_point(session: dict, side: int) -> dict:
    if session.get("winner"):
        return session
    session["history"].append(snapshot(session))
    points = session["points"]
    other = 1 - side
    if session["sets"][-1].get("tiebreak"):
        points[side] += 1
        target = session["sets"][-1]["tiebreak"]["target"]
        if points[side] >= target and points[side] - points[other] >= 2:
            finish_game(session, side)
        return session

    points[side] += 1
    if session.get("scoring") == "no_ad" and points[side] >= 4:
        finish_game(session, side)
    elif points[side] >= 4 and points[side] - points[other] >= 2:
        finish_game(session, side)
    return session


def undo(session: dict) -> dict:
    if session.get("history"):
        previous = session["history"].pop()
        previous["history"] = session["history"]
        return previous
    return session


def display_score(session: dict) -> dict:
    points = session["points"]
    if session["sets"][-1].get("tiebreak"):
        point_text = f"{points[0]}-{points[1]}"
    elif points[0] >= 3 and points[1] >= 3:
        if points[0] == points[1]:
            point_text = "Deuce"
        elif points[0] > points[1]:
            point_text = "Ad A"
        else:
            point_text = "Ad B"
    else:
        point_text = f"{POINT_LABELS[min(points[0], 3)]}-{POINT_LABELS[min(points[1], 3)]}"
    return {
        "sets": session["sets"],
        "points": points,
        "point_text": point_text,
        "winner": session.get("winner"),
        "team_a": session["team_a"],
        "team_b": session["team_b"],
    }


def finish_game(session: dict, side: int) -> None:
    current_set = session["sets"][-1]
    current_set["games"][side] += 1
    session["points"] = [0, 0]
    if set_is_won(current_set["games"], side):
        current_set["winner"] = side
        if match_is_won(session, side):
            session["winner"] = side
        else:
            session["sets"].append({"games": [0, 0], "tiebreak": None})
    elif current_set["games"] == [6, 6]:
        current_set["tiebreak"] = {"target": session.get("tiebreak_points", 7)}


def set_is_won(games: list[int], side: int) -> bool:
    other = 1 - side
    return games[side] >= 6 and games[side] - games[other] >= 2 or games[side] == 7


def match_is_won(session: dict, side: int) -> bool:
    required = 3 if session.get("format") == "best_of_5" else 2
    if session.get("format") in {"one_set", "pro_set"}:
        required = 1
    won = sum(1 for item in session["sets"] if item.get("winner") == side)
    return won >= required


def snapshot(session: dict) -> dict:
    return {
        key: value
        for key, value in {
            "id": session["id"],
            "group_id": session["group_id"],
            "format": session["format"],
            "scoring": session["scoring"],
            "tiebreak_points": session["tiebreak_points"],
            "match_tiebreak_points": session["match_tiebreak_points"],
            "team_a": list(session["team_a"]),
            "team_b": list(session["team_b"]),
            "sets": [
                {"games": list(item["games"]), "tiebreak": item.get("tiebreak"), "winner": item.get("winner")}
                for item in session["sets"]
            ],
            "points": list(session["points"]),
            "winner": session.get("winner"),
        }.items()
    }
