# Telegram The Mind Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal group-only Telegram bot for The Mind with private callback-card reveals.

**Architecture:** Keep game rules in a pure in-memory module and Telegram integration in a thin aiogram module. Group messages show only public state; callback alerts show private cards.

**Tech Stack:** Python 3.11+, aiogram 3, pytest

**Spec:** `docs/superpowers/specs/2026-08-24-telegram-mind-design.md`

## Global Constraints

- No DMs or private chats are used.
- A player's number must never appear in a group message.
- Cards are unique integers from 1 through 100 per round.
- Initial state is in memory, keyed by `chat_id`.

---

### Task 1: Pure game rules

**Files:**
- Create: `mind_game.py`
- Test: `tests/test_mind_game.py`

- [ ] Write failing tests for dealing, private reveal text, ascending play, lost rounds, and completion.
- [ ] Run `python -m pytest tests/test_mind_game.py -q` and confirm missing-module failure.
- [ ] Implement the smallest `Game` and `GameManager` API needed by the tests.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Telegram bot wiring

**Files:**
- Create: `bot.py`
- Create: `requirements.txt`
- Create: `.env.example`

- [ ] Implement group-only `/mind`, lobby callbacks, round callbacks, and shared-message rendering.
- [ ] Ensure “Show my number” calls `answer(show_alert=True)` with the user's number.
- [ ] Run `python -m py_compile mind_game.py bot.py`.

### Task 3: Runbook

**Files:**
- Create: `README.md`
- Create: `.gitignore`

- [ ] Document bot creation, environment setup, group permissions, and launch command.
- [ ] Run the full test suite and compile check.
