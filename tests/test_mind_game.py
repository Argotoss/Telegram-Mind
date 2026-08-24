import pytest

from mind_game import Game, GameManager, PlayResult


def test_start_deals_unique_numbers_between_one_and_one_hundred():
    game = Game.start(chat_id=10, players={1: "Ada", 2: "Bob", 3: "Cy"}, rng_seed=7)

    numbers = [player.number for player in game.players.values()]

    assert len(set(numbers)) == 3
    assert all(1 <= number <= 100 for number in numbers)
    assert game.players_remaining == 3


def test_private_reveal_text_contains_only_the_requesting_players_card():
    game = Game.start(chat_id=10, players={1: "Ada", 2: "Bob"}, rng_seed=2)

    text = game.private_number_text(1)

    assert text == f"Your number: {game.players[1].number}"
    assert str(game.players[2].number) not in text


def test_playing_lowest_remaining_card_advances_round():
    game = Game.with_numbers(chat_id=10, numbers={1: 12, 2: 37})

    result = game.play_card(1)

    assert result is PlayResult.CONTINUE
    assert game.played_numbers == [12]
    assert game.players[1].played is True
    assert game.players_remaining == 1


def test_playing_out_of_order_card_loses_round():
    game = Game.with_numbers(chat_id=10, numbers={1: 12, 2: 37, 3: 61})

    result = game.play_card(3)

    assert result is PlayResult.LOST
    assert game.status == "lost"
    assert game.played_numbers == [61]


def test_playing_all_cards_completes_round():
    game = Game.with_numbers(chat_id=10, numbers={1: 12, 2: 37})

    game.play_card(1)
    result = game.play_card(2)

    assert result is PlayResult.COMPLETE
    assert game.status == "complete"


def test_manager_creates_next_round_for_same_players():
    manager = GameManager()
    manager.create_lobby(10)
    manager.join(10, 1, "Ada")
    manager.join(10, 2, "Bob")
    game = manager.start(10, rng_seed=4)
    game.status = "complete"

    next_game = manager.next_round(10, rng_seed=5)

    assert set(next_game.players) == {1, 2}
    assert next_game.status == "active"
    assert next_game is manager.get(10)
    assert {p.number for p in game.players.values()} != {p.number for p in next_game.players.values()}


def test_unknown_player_cannot_reveal_or_play():
    game = Game.with_numbers(chat_id=10, numbers={1: 12})

    with pytest.raises(KeyError):
        game.private_number_text(99)
    with pytest.raises(KeyError):
        game.play_card(99)
