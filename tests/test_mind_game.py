import pytest

from mind_game import Game, GameManager, PlayResult


def test_level_deals_level_number_of_unique_cards_per_player():
    game = Game.start(chat_id=10, players={1: "Ada", 2: "Bob"}, level=2, rng_seed=7)
    assert all(len(player.cards) == 2 for player in game.players.values())
    cards = [card for player in game.players.values() for card in player.cards]
    assert len(cards) == len(set(cards))
    assert all(1 <= card <= 100 for card in cards)


def test_private_reveal_contains_only_requesting_players_cards():
    game = Game.with_cards(chat_id=10, cards={1: [12, 37], 2: [45, 61]})
    text = game.private_number_text(1)
    assert text == "Your cards: 12, 37"
    assert "45" not in text and "61" not in text


def test_playing_lowest_card_continues_and_removes_it_from_hand():
    game = Game.with_cards(chat_id=10, cards={1: [12, 37], 2: [45, 61]})
    result = game.play_card(1)
    assert result is PlayResult.CONTINUE
    assert game.played_numbers == [12]
    assert game.players[1].cards == [37]


def test_out_of_order_play_loses_life_and_discards_lower_unplayed_cards():
    game = Game.with_cards(chat_id=10, cards={1: [12, 37], 2: [45, 61]}, lives=2)
    result = game.play_card(2)
    assert result is PlayResult.LIFE_LOST
    assert game.lives == 1
    assert game.players[1].cards == []
    assert game.players[2].cards == [61]
    assert game.status == "active"


def test_losing_last_life_ends_game():
    game = Game.with_cards(chat_id=10, cards={1: [12], 2: [45]}, lives=1)
    result = game.play_card(2)
    assert result is PlayResult.GAME_LOST
    assert game.status == "lost"


def test_all_cards_complete_level():
    game = Game.with_cards(chat_id=10, cards={1: [12], 2: [45]}, max_level=2)
    game.play_card(1)
    result = game.play_card(2)
    assert result is PlayResult.LEVEL_COMPLETE
    assert game.level == 1
    assert game.status == "level_complete"


def test_star_requires_all_players_and_discards_one_lowest_card_each():
    game = Game.with_cards(chat_id=10, cards={1: [12, 37], 2: [45, 61]}, stars=1)
    assert game.request_star(1) is False
    assert game.request_star(2) is True
    assert game.stars == 0
    assert game.players[1].cards == [37]
    assert game.players[2].cards == [61]


def test_manager_next_level_keeps_settings_and_increases_hand_size():
    manager = GameManager()
    manager.create_lobby(10)
    manager.join(10, 1, "Ada")
    manager.join(10, 2, "Bob")
    game = manager.start(10, max_level=3, rng_seed=4)
    game.status = "level_complete"
    next_game = manager.next_level(10, rng_seed=5)
    assert next_game.level == 2
    assert all(len(player.cards) == 2 for player in next_game.players.values())
    assert next_game.max_level == 3
    assert next_game.lives == game.lives
    assert next_game.stars == game.stars


def test_unknown_player_cannot_reveal_or_play():
    game = Game.with_cards(chat_id=10, cards={1: [12]})
    with pytest.raises(KeyError):
        game.private_number_text(99)
    with pytest.raises(KeyError):
        game.play_card(99)
