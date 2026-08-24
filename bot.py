"""Telegram adapter for the group-only The Mind bot."""

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
round_messages: dict[int, int] = {}


def is_group(message: Message) -> bool:
    return message.chat.type in {"group", "supergroup"}


def lobby_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Join", callback_data="mind:join")],
        [InlineKeyboardButton(text="▶️ Start Game", callback_data="mind:start")],
    ])


def round_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Show my number", callback_data="mind:show")],
        [InlineKeyboardButton(text="🃏 Play my card", callback_data="mind:play")],
    ])


def finished_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Next round", callback_data="mind:next")],
        [InlineKeyboardButton(text="New game", callback_data="mind:new")],
    ])


def lobby_text(game) -> str:
    names = "\n".join(f"• {player.name}" for player in game.players.values()) or "—"
    return f"THE MIND\n\nPlayers ({len(game.players)}):\n{names}\n\nPress Join to enter."


def round_text(game) -> str:
    played = " → ".join(map(str, game.played_numbers)) or "—"
    return f"THE MIND\n\nCards played: {played}\nPlayers remaining: {game.players_remaining}"


def finished_text(game, result: PlayResult) -> str:
    if result is PlayResult.LOST:
        return round_text(game) + "\n\n❌ Round lost"
    return round_text(game) + "\n\n✅ Round complete"


@router.message(Command("mind"), F.chat.type.in_({"group", "supergroup"}))
async def start_lobby(message: Message) -> None:
    game = manager.create_lobby(message.chat.id)
    sent = await message.answer(lobby_text(game), reply_markup=lobby_keyboard())
    round_messages[message.chat.id] = sent.message_id


async def edit_shared(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(F.data == "mind:join")
async def join(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game:
        await callback.answer("Start a new game with /mind first.", show_alert=True)
        return
    name = callback.from_user.full_name
    if not manager.join(game.chat_id, callback.from_user.id, name):
        await callback.answer("You are already in this lobby, or it has started.", show_alert=True)
        return
    await callback.answer("Joined!")
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
        game = manager.start(game.chat_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Game started!")
    await edit_shared(callback, round_text(game), round_keyboard())


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
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Card played.")
    await edit_shared(callback, finished_text(game, result) if result is not PlayResult.CONTINUE else round_text(game), finished_keyboard() if result is not PlayResult.CONTINUE else round_keyboard())


@router.callback_query(F.data == "mind:next")
async def next_round(callback: CallbackQuery) -> None:
    game = manager.get(callback.message.chat.id)
    if not game:
        await callback.answer("No game found.", show_alert=True)
        return
    try:
        game = manager.next_round(game.chat_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Next round!")
    await edit_shared(callback, round_text(game), round_keyboard())


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
