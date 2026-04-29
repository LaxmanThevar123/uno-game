# 🃏 UNO Card Game

A fully playable UNO card game built with Python.

## Features
- Player vs AI (1-3 bots)
- Full UNO rules: Skip, Reverse, Draw Two, Wild, Wild Draw Four
- 108-card deck
- Automatic UNO declaration
- Terminal-based UI

## Requirements
- Python 3.9+

## How to Play (Local)
```bash
python main.py
```

## Rules
- Match cards by color, number, or type
- Wild cards can be played anytime
- Draw a card if you can't play
- First player to empty their hand wins!

## Project Structure
```
uno-game/
├── main.py
├── game/
│   ├── card.py
│   ├── deck.py
│   ├── player.py
│   └── game.py
├── ui/
│   └── terminal_ui.py
├── requirements.txt
└── README.md
```
