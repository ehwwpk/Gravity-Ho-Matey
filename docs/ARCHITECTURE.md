# Architecture

## Dependency direction

```text
app -> scenes -> gameplay -> core
app -> render -> core
levels -> gameplay/core data only
```

The renderer can read game state, but gameplay should not import Tkinter.

## Runtime flow

1. `__main__.py` calls `main.run()`.
2. `main.run()` creates `GravityHoMateyApp`.
3. The app owns the Tk root, canvas, scene stack, input tracker, and timer loop.
4. The active scene receives input and update ticks.
5. The active scene asks the renderer to draw the current state.

## Scene model

- `TitleScene`: static title screen and controls.
- `PlayScene`: owns a `GameWorld`, updates simulation, and handles restart/title shortcuts.
- `EndScene`: win/loss screen with restart/title flow.

## Gameplay model

`GameWorld` owns mutable state:

- `Ship`
- `Projectile` list
- `Wall` list
- `GravityWell` list
- `Beacon` list
- `FinishGate`
- `GameStatus`

`WorldConfig` owns tuning constants.

## Rendering model

The Tk renderer converts world state into canvas primitives. No game rules should live here.

## Tests

The tests currently cover:

- vector math
- gravity force direction and strength shape
- beacon collection and finish unlocking flow
- projectile integration basics

This test suite is intentionally small but establishes the right seams.
