# Telegram The Mind Bot Design

## Goal

Build a minimal Telegram group bot for The Mind where shared state stays in the group and each player's card is revealed only through a private callback alert.

## Architecture

`mind_game.py` contains pure, testable game rules and in-memory state. `bot.py` wires those rules to aiogram callback buttons and edits one shared group message. The bot accepts no private chat flow and never includes card values in shared text.

## Scope

- `/mind` starts a lobby in a group or supergroup.
- Join and Start Game callbacks update the lobby message.
- Cards are unique random integers from 1 through 100.
- “Show my number” uses `answerCallbackQuery(show_alert=True)`.
- “Play my card” validates the player, records the card, and detects a lost or completed round.
- Next round re-deals to the same players; New game returns to a fresh lobby.
- State is in memory and keyed by `chat_id`.

## Safety and errors

Only group/supergroup messages are handled. Callback users must be registered players for player-only actions. Invalid or stale actions receive an ephemeral callback response. Numbers are absent from lobby and round messages.

## Verification

Unit tests cover unique card dealing, private reveal text construction, correct ascending play, lost rounds, and round completion. A Telegram token is required only for live operation.
