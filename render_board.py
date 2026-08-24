"""Render The Mind's public table as a Telegram-ready PNG.

Only played cards are face-up. Cards still held by players are represented by
backs and counts, so the private-card rule remains intact.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


WIDTH = 900
HEIGHT = 620


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill: str) -> None:
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=font)
    x = left + (right - left - (bounds[2] - bounds[0])) / 2
    y = top + (bottom - top - (bounds[3] - bounds[1])) / 2 - bounds[1]
    draw.text((x, y), text, font=font, fill=fill)


def _pill(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, radius: int = 16) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _card(draw: ImageDraw.ImageDraw, x: int, y: int, value: int | None) -> None:
    box = (x, y, x + 100, y + 140)
    if value is None:
        _pill(draw, box, "#263c5c", 14)
        draw.rounded_rectangle((x + 8, y + 8, x + 92, y + 132), radius=10, outline="#49698e", width=2)
        _centered(draw, box, "?", _font(40, True), "#9bb7d8")
        return
    _pill(draw, box, "#f4f0e8", 14)
    _centered(draw, box, str(value), _font(32, True), "#172335")


def render_board(game) -> bytes:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#0e1826")
    draw = ImageDraw.Draw(image)

    draw.text((42, 28), "THE MIND", font=_font(32, True), fill="#f4f7fb")
    draw.text((44, 70), "SILENT CO-OP", font=_font(14, True), fill="#7692b3")

    status = f"LEVEL {game.level}/{game.max_level}    LIVES {game.lives}    STARS {game.stars}"
    _pill(draw, (430, 34, 858, 82), "#1b2a3e", 18)
    _centered(draw, (430, 34, 858, 82), status, _font(17, True), "#c8d7e8")

    _pill(draw, (32, 122, WIDTH - 32, 474), "#183b3b", 26)
    draw.text((58, 148), "THE TABLE", font=_font(15, True), fill="#80c7b0")

    played = list(game.played_numbers)
    hidden = game.cards_remaining
    total_slots = max(1, len(played) + hidden)
    card_w = 100
    gap = 14
    visible_slots = min(total_slots, 7)
    table_width = visible_slots * card_w + (visible_slots - 1) * gap
    start_x = (WIDTH - table_width) // 2
    y = 218
    for index in range(visible_slots):
        if index < len(played):
            _card(draw, start_x + index * (card_w + gap), y, played[index])
        else:
            _card(draw, start_x + index * (card_w + gap), y, None)

    if not played and not hidden:
        _centered(draw, (80, 240, WIDTH - 80, 340), "Waiting for the first deal", _font(22), "#9bb7a9")

    draw.text((58, 420), f"CENTER  {len(played)} played    ·    {hidden} hidden", font=_font(16, True), fill="#b9d8ca")

    players = list(game.players.values())
    if players:
        chip_w = (WIDTH - 84 - (min(len(players), 4) - 1) * 12) // min(len(players), 4)
        for index, player in enumerate(players[:4]):
            x = 42 + index * (chip_w + 12)
            _pill(draw, (x, 508, x + chip_w, 574), "#1b2a3e", 16)
            name = player.name[:18]
            draw.text((x + 16, 521), name, font=_font(16, True), fill="#f4f7fb")
            draw.text((x + 16, 548), f"{len(player.cards)} card" + ("s" if len(player.cards) != 1 else ""), font=_font(13), fill="#86a2c2")
    else:
        draw.text((42, 530), "Join the table to begin", font=_font(18), fill="#86a2c2")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
