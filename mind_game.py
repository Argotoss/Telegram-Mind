"""Pure in-memory game rules for Telegram The Mind."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class PlayResult(Enum):
    CONTINUE = "continue"
    LOST = "lost"
    COMPLETE = "complete"


@dataclass
class Player:
    name: str
    number: int | None = None
    played: bool = False


class Game:
    def __init__(self, chat_id: int, players: dict[int, Player], status: str = "lobby"):
        self.chat_id = chat_id
        self.players = players
        self.status = status
        self.played_numbers: list[int] = []

    @classmethod
    def start(cls, chat_id: int, players: dict[int, str], rng_seed: int | None = None) -> "Game":
        if len(players) < 2:
            raise ValueError("At least two players are required")
        rng = random.Random(rng_seed)
        numbers = rng.sample(range(1, 101), len(players))
        return cls(
            chat_id,
            {user_id: Player(name=name, number=number) for (user_id, name), number in zip(players.items(), numbers)},
            status="active",
        )

    @classmethod
    def with_numbers(cls, chat_id: int, numbers: dict[int, int]) -> "Game":
        return cls(
            chat_id,
            {user_id: Player(name=f"Player {user_id}", number=number) for user_id, number in numbers.items()},
            status="active",
        )

    @property
    def players_remaining(self) -> int:
        return sum(not player.played for player in self.players.values())

    def private_number_text(self, user_id: int) -> str:
        player = self.players[user_id]
        return f"Your number: {player.number}"

    def play_card(self, user_id: int) -> PlayResult:
        if self.status != "active":
            raise ValueError("Round is not active")
        player = self.players[user_id]
        if player.played:
            raise ValueError("Card already played")
        remaining = [p.number for p in self.players.values() if not p.played]
        if player.number != min(remaining):
            player.played = True
            self.played_numbers.append(player.number)
            self.status = "lost"
            return PlayResult.LOST
        player.played = True
        self.played_numbers.append(player.number)
        if self.players_remaining == 0:
            self.status = "complete"
            return PlayResult.COMPLETE
        return PlayResult.CONTINUE


class GameManager:
    def __init__(self):
        self.games: dict[int, Game] = {}

    def create_lobby(self, chat_id: int) -> Game:
        game = Game(chat_id, {})
        self.games[chat_id] = game
        return game

    def get(self, chat_id: int) -> Game | None:
        return self.games.get(chat_id)

    def join(self, chat_id: int, user_id: int, name: str) -> bool:
        game = self.games[chat_id]
        if game.status != "lobby" or user_id in game.players:
            return False
        game.players[user_id] = Player(name=name)
        return True

    def start(self, chat_id: int, rng_seed: int | None = None) -> Game:
        game = self.games[chat_id]
        started = Game.start(chat_id, {user_id: p.name for user_id, p in game.players.items()}, rng_seed)
        self.games[chat_id] = started
        return started

    def next_round(self, chat_id: int, rng_seed: int | None = None) -> Game:
        game = self.games[chat_id]
        if game.status not in {"lost", "complete"}:
            raise ValueError("Round is still active")
        return self.start_from_players(chat_id, {user_id: p.name for user_id, p in game.players.items()}, rng_seed)

    def start_from_players(self, chat_id: int, players: dict[int, str], rng_seed: int | None = None) -> Game:
        game = Game.start(chat_id, players, rng_seed)
        self.games[chat_id] = game
        return game

    def new_game(self, chat_id: int) -> Game:
        return self.create_lobby(chat_id)
