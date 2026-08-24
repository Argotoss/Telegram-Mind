"""Pure in-memory game rules for the configurable group-only The Mind bot."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class PlayResult(Enum):
    CONTINUE = "continue"
    LIFE_LOST = "life_lost"
    LEVEL_COMPLETE = "level_complete"
    VICTORY = "victory"
    GAME_LOST = "game_lost"


@dataclass
class Player:
    name: str
    cards: list[int] = field(default_factory=list)


class Game:
    def __init__(
        self,
        chat_id: int,
        players: dict[int, Player],
        *,
        level: int = 1,
        max_level: int = 10,
        lives: int = 3,
        stars: int = 1,
        reward: str = "",
        status: str = "lobby",
    ):
        self.chat_id = chat_id
        self.players = players
        self.level = level
        self.max_level = max_level
        self.lives = lives
        self.stars = stars
        self.reward = reward
        self.status = status
        self.played_numbers: list[int] = []
        self.discarded_numbers: list[int] = []
        self.star_votes: set[int] = set()

    @classmethod
    def start(
        cls,
        chat_id: int,
        players: dict[int, str],
        *,
        level: int = 1,
        max_level: int = 10,
        lives: int = 3,
        stars: int = 1,
        reward: str = "",
        rng_seed: int | None = None,
    ) -> "Game":
        if len(players) < 2:
            raise ValueError("At least two players are required")
        if not 1 <= level <= max_level:
            raise ValueError("Level must be between 1 and max level")
        if lives < 1 or stars < 0 or max_level < 1:
            raise ValueError("Invalid game settings")
        rng = random.Random(rng_seed)
        numbers = rng.sample(range(1, 101), len(players) * level)
        hands = {
            user_id: Player(name=name, cards=sorted(numbers[index * level : (index + 1) * level]))
            for index, (user_id, name) in enumerate(players.items())
        }
        return cls(chat_id, hands, level=level, max_level=max_level, lives=lives, stars=stars, reward=reward, status="active")

    @classmethod
    def with_cards(cls, chat_id: int, cards: dict[int, list[int]], **settings) -> "Game":
        return cls(
            chat_id,
            {user_id: Player(name=f"Player {user_id}", cards=sorted(hand)) for user_id, hand in cards.items()},
            status="active",
            **settings,
        )

    @property
    def cards_remaining(self) -> int:
        return sum(len(player.cards) for player in self.players.values())

    @property
    def players_remaining(self) -> int:
        return sum(bool(player.cards) for player in self.players.values())

    def private_number_text(self, user_id: int) -> str:
        cards = self.players[user_id].cards
        return "Your cards: " + (", ".join(map(str, cards)) if cards else "none")

    def play_card(self, user_id: int) -> PlayResult:
        if self.status != "active":
            raise ValueError("Round is not active")
        player = self.players[user_id]
        if not player.cards:
            raise ValueError("You have no cards remaining")
        card = player.cards.pop(0)
        lower_cards = [other_card for other in self.players.values() for other_card in other.cards if other_card < card]
        self.played_numbers.append(card)
        if lower_cards:
            for other in self.players.values():
                kept = [other_card for other_card in other.cards if other_card >= card]
                self.discarded_numbers.extend(other_card for other_card in other.cards if other_card < card)
                other.cards = kept
            self.lives -= 1
            return self._after_life_loss()
        if self.cards_remaining == 0:
            if self.level == self.max_level:
                self.status = "victory"
                return PlayResult.VICTORY
            self.status = "level_complete"
            return PlayResult.LEVEL_COMPLETE
        return PlayResult.CONTINUE

    def _after_life_loss(self) -> PlayResult:
        if self.lives <= 0:
            self.status = "lost"
            return PlayResult.GAME_LOST
        return PlayResult.LIFE_LOST

    def request_star(self, user_id: int) -> bool:
        if self.status != "active":
            raise ValueError("Round is not active")
        if self.stars <= 0:
            raise ValueError("No stars remaining")
        if user_id not in self.players:
            raise KeyError(user_id)
        self.star_votes.add(user_id)
        if self.star_votes != set(self.players):
            return False
        for player in self.players.values():
            if player.cards:
                self.discarded_numbers.append(player.cards.pop(0))
        self.stars -= 1
        self.star_votes.clear()
        return True


class GameManager:
    def __init__(self):
        self.games: dict[int, Game] = {}

    def create_lobby(self, chat_id: int) -> Game:
        game = Game(chat_id, {})
        self.games[chat_id] = game
        return game

    def get(self, chat_id: int) -> Game | None:
        return self.games.get(chat_id)

    def configure(self, chat_id: int, *, lives: int | None = None, stars: int | None = None, max_level: int | None = None) -> Game:
        game = self.games[chat_id]
        if game.status != "lobby":
            raise ValueError("Settings can only be changed in the lobby")
        if lives is not None:
            game.lives = lives
        if stars is not None:
            game.stars = stars
        if max_level is not None:
            game.max_level = max_level
        return game

    def join(self, chat_id: int, user_id: int, name: str) -> bool:
        game = self.games[chat_id]
        if game.status != "lobby" or user_id in game.players:
            return False
        game.players[user_id] = Player(name=name)
        return True

    def start(
        self,
        chat_id: int,
        *,
        max_level: int | None = None,
        lives: int | None = None,
        stars: int | None = None,
        rng_seed: int | None = None,
        reward: str = "",
    ) -> Game:
        game = self.games[chat_id]
        started = Game.start(
            chat_id,
            {user_id: player.name for user_id, player in game.players.items()},
            lives=game.lives if lives is None else lives,
            stars=game.stars if stars is None else stars,
            max_level=game.max_level if max_level is None else max_level,
            reward=reward,
            rng_seed=rng_seed,
        )
        self.games[chat_id] = started
        return started

    def next_level(self, chat_id: int, *, rng_seed: int | None = None) -> Game:
        game = self.games[chat_id]
        if game.status != "level_complete":
            raise ValueError("Level is not complete")
        started = Game.start(
            chat_id,
            {user_id: player.name for user_id, player in game.players.items()},
            level=game.level + 1,
            max_level=game.max_level,
            lives=game.lives,
            stars=game.stars,
            reward=game.reward,
            rng_seed=rng_seed,
        )
        self.games[chat_id] = started
        return started

    def new_game(self, chat_id: int) -> Game:
        return self.create_lobby(chat_id)
