# Telegram The Mind

A tiny group-only Telegram bot for playing The Mind. Shared game state stays in the group; each player's card is revealed privately through Telegram's callback alert.

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Install Python 3.11+.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set `BOT_TOKEN`.
5. Add the bot to a Telegram group and run:

   ```powershell
   python bot.py
   ```

## How to play

In the group, send `/mind`. Everyone presses **Join**, then a player presses **Start Game**. Use **Show my number** to privately view your card and **Play my card** when the group agrees it is your turn.

The bot never puts a player's number into the shared group message. It uses `answerCallbackQuery(show_alert=True)` for the private reveal.

## Checks

```powershell
python -m pytest -q
python -m py_compile mind_game.py bot.py
```
