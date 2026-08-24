from bot import lobby_keyboard, lobby_text, round_keyboard
from mind_game import Game


def test_lobby_uses_compact_action_labels():
    game = Game(10, {})
    labels = [button.text for row in lobby_keyboard().inline_keyboard for button in row]

    assert labels == ["✅ Join game", "⚙️ Settings", "🚀 Start"]
    assert "🧠 THE MIND" in lobby_text(game)


def test_round_uses_compact_action_labels():
    game = Game.with_cards(chat_id=10, cards={1: [12], 2: [37]})
    labels = [button.text for row in round_keyboard(game).inline_keyboard for button in row]

    assert labels == ["👁 My cards", "🃏 Play lowest", "⭐ Use star · 1"]
