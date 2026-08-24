"""Telegram adapter for the group-only, configurable The Mind bot."""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from mind_game import GameManager, PlayResult

load_dotenv()
logging.basicConfig(level=logging.INFO)

router = Router()
manager = GameManager()
default_reward = os.getenv("MIND_REWARD", "")


def lobby_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="JOIN", callback_data="mind:join"), InlineKeyboardButton(text="SETTINGS", callback_data="mind:settings")],
        [InlineKeyboardButton(text="START GAME", callback_data="mind:start")],
    ])


def settings_keyboard(game) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LIVES −", callback_data="mind:set:lives:-1"), InlineKeyboardButton(text=f"LIVES {game.lives} +", callback_data="mind:set:lives:1")],
        [InlineKeyboardButton(text="STARS −", callback_data="mind:set:stars:-1"), InlineKeyboardButton(text=f"STARS {game.stars} +", callback_data="mind:set:stars:1")],
        [InlineKeyboardButton(text="LEVELS −", callback_data="mind:set:levels:-1"), InlineKeyboardButton(text=f"LEVELS {game.max_level} +", callback_data="mind:set:levels:1")],
        [InlineKeyboardButton(text="BACK", callback_data="mind:settings:back")],
    ])


def round_keyboard(game) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="MY CARDS", callback_data="mind:show"), InlineKeyboardButton(text="PLAY LOWEST", callback_data="mind:play")],
        [InlineKeyboardButton(text=f"USE STAR · {game.stars}", callback_data="mind:star")],
    ])


def level_complete_keyboard(game) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="NEXT LEVEL", callback_data="mind:next"), InlineKeyboardButton(text="NEW LOBBY", callback_data="mind:new")],
    ])


def new_game_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="NEW LOBBY", callback_data="mind:new")]])


def lobby_text(game) -> str:
    names = "\n".join(f"• {player.name}" for player in game.players.values()) or "—"
    return (
        "THE MIND\n"
        "────────────────\n\n"
        f"LIVES {game.lives}  ·  STARS {game.stars}  ·  LEVELS {game.max_level}\n\n"
        f"PLAYERS · {len(game.players)}\n{names}\n\n"
        "Join the table, then start when everyone is ready."
    )


def settings_text(game) -> str:
    return (
        "SETTINGS\n"
        "────────────────\n\n"
        f"LIVES   {game.lives}\n"
        f"STARS   {game.stars}\n"
        f"LEVELS  {game.max_level}\n"
        f"REWARD  {game.reward or 'none'}\n\n"
        "Use the controls below to adjust the table."
    )


def round_text(game) -> str:
    played = " → ".join(map(str, game.played_numbers)) or "—"
    return (
        "THE MIND\n"
        "────────────────\n\n"
        f"LEVEL {game.level} / {game.max_level}\n"
        f"LIVES {game.lives}  ·  STARS {game.stars}\n\n"
        f"CENTER\n{played}\n\n"
        f"CARDS IN PLAY  {game.cards_remaining}\n\n"
        "No words. No signs.\nPlay when you feel your card is lowest."
    )


def finished_text(game, result: PlayResult) -> str:
    if result is PlayResult.GAME_LOST:
        return round_text(game) + "\n\nGAME OVER\nAll lives are gone."
    if result is PlayResult.VICTORY:
        reward = f"\n\n🏆 Reward: {game.reward}" if game.reward else ""
        return round_text(game) + "\n\nVICTORY\nAll levels complete." + reward
    if result is PlayResult.LEVEL_COMPLETE:
        reward = f"\n🎁 Reward: {game.reward}" if game.reward else ""
        return round_text(game) + f"\n\nLEVEL COMPLETE{reward}"
    if result is PlayResult.LIFE_LOST:
        return round_text(game) + "\n\nLIFE LOST\nLower cards were discarded."
    return round_text(game)


async def edit_shared(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    await callback.message.edit_text(text, reply_markup=markup)


@router.message(Command("mind"), F.chat.type.in_({"group", "supergroup"}))
async def start_lobby(message: Message) -> None:
    game = manager.create_lobby(message.chat.id)
    game.reward = default_reward
    await message.answer(lobby_text(game), reply_markup=lobby_keyboard())


@router.message(Command("mind_reward"), F.chat.type.in_({"group", "supergroup"}))
async def set_reward(message: Message) -> None:
    game = manager.get(message.chat.id)
    reward = message.text.partition(" ")[2].strip()
    if not game or game.status != "lobby":
        await message.answer("Start a lobby with /mind before setting a reward.")
        return
    game.reward = reward
    await message.answer(lobby_text(game), reply_markup=lobby_keyboard())


@router.callback_query(F.data == "mind:join")
async def join(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game:
        await callback.answer("Start a new game with /mind first.", show_alert=True)
        return
    if not manager.join(game.chat_id, callback.from_user.id, callback.from_user.full_name):
        await callback.answer("You are already in this lobby, or it has started.", show_alert=True)
        return
    await callback.answer("Joined!")
    await edit_shared(callback, lobby_text(game), lobby_keyboard())


@router.callback_query(F.data == "mind:settings")
async def settings(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game or game.status != "lobby":
        await callback.answer("Settings are only available before starting.", show_alert=True)
        return
    await callback.answer()
    await edit_shared(callback, settings_text(game), settings_keyboard(game))


@router.callback_query(F.data.startswith("mind:set:"))
async def change_setting(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game or game.status != "lobby":
        await callback.answer("Settings are only available before starting.", show_alert=True)
        return
    _, _, setting, direction = callback.data.split(":")
    current = {"lives": game.lives, "stars": game.stars, "levels": game.max_level}[setting]
    minimum, maximum = (1, 5) if setting == "lives" else ((0, 3) if setting == "stars" else (1, 10))
    value = max(minimum, min(maximum, current + int(direction)))
    manager.configure(game.chat_id, **({"max_level": value} if setting == "levels" else {setting: value}))
    await callback.answer(f"{setting.title()}: {value}")
    await edit_shared(callback, settings_text(game), settings_keyboard(game))


@router.callback_query(F.data == "mind:settings:back")
async def settings_back(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game:
        await callback.answer("No game found.", show_alert=True)
        return
    await callback.answer()
    await edit_shared(callback, lobby_text(game), lobby_keyboard())


@router.callback_query(F.data == "mind:start")
async def start_game(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game:
        await callback.answer("Start a new game with /mind first.", show_alert=True)
        return
    if callback.from_user.id not in game.players:
        await callback.answer("Join the game first.", show_alert=True)
        return
    try:
        game = manager.start(game.chat_id, reward=game.reward)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Game started!")
    await edit_shared(callback, round_text(game), round_keyboard(game))


@router.callback_query(F.data == "mind:show")
async def show_number(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game or callback.from_user.id not in game.players:
        await callback.answer("You are not a player in this game.", show_alert=True)
        return
    await callback.answer(game.private_number_text(callback.from_user.id), show_alert=True)


@router.callback_query(F.data == "mind:play")
async def play_card(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game or callback.from_user.id not in game.players:
        await callback.answer("You are not a player in this game.", show_alert=True)
        return
    try:
        result = game.play_card(callback.from_user.id)
    except (KeyError, ValueError) as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Lowest card played.")
    markup = round_keyboard(game) if result in {PlayResult.CONTINUE, PlayResult.LIFE_LOST} else (level_complete_keyboard(game) if result is PlayResult.LEVEL_COMPLETE else new_game_keyboard())
    await edit_shared(callback, finished_text(game, result), markup)


@router.callback_query(F.data == "mind:star")
async def use_star(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game or callback.from_user.id not in game.players:
        await callback.answer("You are not a player in this game.", show_alert=True)
        return
    try:
        activated = game.request_star(callback.from_user.id)
    except (KeyError, ValueError) as error:
        await callback.answer(str(error), show_alert=True)
        return
    if not activated:
        await callback.answer(f"Hand raised ({len(game.star_votes)}/{len(game.players)}).")
        return
    await callback.answer("⭐ Star used — one lowest card discarded from each player.")
    await edit_shared(callback, round_text(game), round_keyboard(game))


@router.callback_query(F.data == "mind:next")
async def next_level(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game:
        await callback.answer("No game found.", show_alert=True)
        return
    try:
        game = manager.next_level(game.chat_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Next level!")
    await edit_shared(callback, round_text(game), round_keyboard(game))


@router.callback_query(F.data == "mind:new")
async def new_game(callback: CallbackQuery) -> None:
    game = manager.new_game(callback.message.chat.id)
    await callback.answer("New lobby created.")
    await edit_shared(callback, lobby_text(game), lobby_keyboard())


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")
    bot = Bot(token=token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
