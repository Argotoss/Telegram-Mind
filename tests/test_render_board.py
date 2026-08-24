from mind_game import Game
from render_board import render_board


def test_render_board_returns_a_telegram_ready_png_with_a_fixed_table_size():
    game = Game.with_cards(chat_id=10, cards={1: [12, 37], 2: [45, 61]})
    game.played_numbers.append(12)

    image_bytes = render_board(game)

    assert image_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert image_bytes[16:20] == (900).to_bytes(4, "big")
    assert image_bytes[20:24] == (620).to_bytes(4, "big")
