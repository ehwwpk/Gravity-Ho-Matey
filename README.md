# Gravity Ho, Matey!

A surprisingly fun Python minigame built while testing DevGov software pre-beta.

A standard-library-first Python arcade project skeleton for a pirate-flavored gravity race / maze game.

You pilot a tiny pixel-art ship through a dangerous cove full of gravity wells, walls, reefs, and tight corridors. Shots curve. Routes curve. Momentum matters. Collect every beacon, then hit the finish gate.

This repo is intentionally structured like a serious project base rather than a single-file toy. It is designed so you can hand it to Cursor, Codex, or another coding agent and continue vibecoding from a clean foundation.

## Current state

This starter includes:

- a runnable Tkinter prototype
- separated game loop, scenes, world, renderer, assets, utilities, and core math
- one playable gravity race / maze level
- curved projectiles affected by gravity wells
- beacon collection and finish gate flow
- simple pixel-art-style ships, shots, gravity wells, walls, and HUD drawn with Tkinter primitives
- light unit tests for deterministic core logic
- planning docs and architecture notes

## Why Tkinter?

The brief asked for core Python or mainly core Python. Tkinter ships with CPython on most desktop installs, so this base avoids external dependencies while still supporting:

- a real window
- keyboard input
- 2D drawing
- a credible rapid-prototype loop

That keeps the project easy to open and iterate on in coding agents.

## Quick start

From the repo root:

```bash
python run_game.py
```

Or as a module:

```bash
python -m gravity_ho_matey
```

If your shell does not automatically see the `src` layout:

```bash
PYTHONPATH=src python -m gravity_ho_matey
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m gravity_ho_matey
```

## Controls

- `A` / `D` or `Left` / `Right`: rotate
- `W` or `Up`: thrust
- `Shift`: boost
- `Space`: fire
- `R`: restart level
- `Esc`: back to title
- `Enter`: start from title or continue after win/loss

## Project layout

```text
GravityHoMatey/
├─ docs/
├─ src/gravity_ho_matey/
│  ├─ assets/
│  ├─ core/
│  ├─ gameplay/
│  ├─ levels/
│  ├─ render/
│  ├─ scenes/
│  ├─ util/
│  ├─ app.py
│  ├─ main.py
│  └─ settings.py
└─ tests/
```

## Test

```bash
python -m unittest discover -s tests -v
```

No third-party packages are required.

## Design target

This should feel like an arcade maze racer, not Snake with a gravity wrapper. The ship has inertia, gravity bends routes and shots, walls create cove-like corridors, and the win condition forces a route-planning loop: collect beacons first, then escape through the gate.
