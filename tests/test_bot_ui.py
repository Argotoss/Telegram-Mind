from bot import lobby_keyboard, lobby_text, round_keyboard
from mind_game import Game


def test_lobby_uses_compact_action_labels():
    game = Game(10, {})
    labels = [button.text for row in lobby_keyboard().inline_keyboard for button in row]

    assert labels == ["JOIN", "START"]
    text = lobby_text(game)
    assert "THE MIND" in text
    assert "_" not in text
    assert "PLAYERS · 0" in text
    rows = lobby_keyboard().inline_keyboard
    assert rows[0][0].style == "success"
    assert rows[0][1].style == "success"


def test_round_uses_compact_action_labels():
    game = Game.with_cards(chat_id=10, cards={1: [12], 2: [37]})
    labels = [button.text for row in round_keyboard(game).inline_keyboard for button in row]

    assert labels == ["MY CARDS", "PLAY LOWEST", "STAR · 1"]
    assert len(round_keyboard(game).inline_keyboard) == 1
    assert [button.style for button in round_keyboard(game).inline_keyboard[0]] == ["primary", "success", "primary"]
