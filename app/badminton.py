from __future__ import annotations


def record_ladder_result(players: list[dict], winner_id: str, loser_id: str, disputed: bool = False) -> list[dict]:
    if disputed:
        return players
    by_id = {player["id"]: player for player in players}
    if winner_id not in by_id or loser_id not in by_id:
        return players

    winner = by_id[winner_id]
    loser = by_id[loser_id]
    winner_rank = int(winner["ladder_rank"])
    loser_rank = int(loser["ladder_rank"])
    if winner_rank > loser_rank:
        for player in players:
            rank = int(player["ladder_rank"])
            if loser_rank <= rank < winner_rank:
                player["ladder_rank"] = rank + 1
        winner["ladder_rank"] = loser_rank

    update_elo(winner, loser)
    return sorted(players, key=lambda item: item["ladder_rank"])


def update_elo(winner: dict, loser: dict) -> None:
    winner_elo = float(winner.get("elo", 1200))
    loser_elo = float(loser.get("elo", 1200))
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    change = round(24 * (1 - expected_winner))
    winner["elo"] = int(winner_elo + change)
    loser["elo"] = int(loser_elo - change)
