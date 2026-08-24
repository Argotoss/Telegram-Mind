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
   Optionally set `MIND_REWARD` to text shown when the group completes a level and wins.
5. Add the bot to a Telegram group and run:

   ```powershell
   python bot.py
   ```

## How to play

In the group, send `/mind`. Everyone presses **Join**. Use **⚙️ Settings** before starting to configure lives, stars, and the number of levels. Then press **Start Game**.

Sending `/mind` again resets the current game to a fresh empty lobby. Everyone must press **Join game** again.

You can set a group-specific reward before starting with `/mind_reward Golden crown`.

At level 1 each player receives one card, level 2 gives two cards, and so on. **Show my cards** privately reveals only that player's hand. **Play my lowest card** plays the lowest card in that hand when the player feels the timing is right. If it is too early, the group loses a life and all smaller unplayed cards are discarded.

To use a star, every player presses **⭐ Use star**. Once everyone has raised a hand, one lowest card from each player's hand is discarded simultaneously.

The bot never puts an unplayed player's number into the shared group message. It uses `answerCallbackQuery(show_alert=True)` for the private reveal.

## Checks

```powershell
python -m pytest -q
python -m py_compile mind_game.py bot.py
```
