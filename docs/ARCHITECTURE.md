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

- `TitleScene`: static title screen; starts a new campaign via `game_flow.start_play`.
- `PlayScene`: owns per-level `GameWorld` + cross-level `CampaignState`; handles win/loss transitions.
- `EndScene`: win/loss screen; advances campaign, retries level, or returns to title on game over.

Scene transitions that start gameplay should go through `scenes/game_flow.start_play` so campaign wiring stays consistent. Scene modules use **lazy imports** inside methods to avoid import cycles (`game_flow` ↔ `play` ↔ `end`).

## Campaign progress

`gameplay/progress.py` tracks which levels are selectable from the title screen. Beating a level unlocks the next entry in `LEVEL_ORDER`. Level 2 direct select is gated until Cove is cleared at least once (session-persistent for the process lifetime).

## Campaign vs level state

| Object | Lifetime | Owns |
|--------|----------|------|
| `CampaignState` | Whole campaign (3 lives, collected power-ups) | lives, `powerups` set |
| `GameWorld` | Single level attempt | ship, enemies, pickups, beacons, projectiles |

`gameplay/session.wire_world_for_campaign()` applies carried bonuses and connects pickup collection to the campaign. This keeps `CampaignState` free of `GameWorld` imports.

## Gameplay model

`GameWorld` owns mutable per-level state:

- `Ship`, `Projectile`, `PatrolEnemy`, `PowerUpPickup`
- `Wall`, `GravityWell`, `Beacon`, `FinishGate`
- `GameStatus`, optional `on_powerup_collected` callback

`WorldConfig` owns tuning constants and `level_theme` / `level_name`.

## Levels

- `level_registry.py`: `LEVEL_BUILDERS`, `LEVEL_ORDER`, `build_level()`, startup validation.
- `level_data.py`: geometry and wells per level.
- `solar_patrols.py`: enemy patrol definitions for level 2 only.

## Rendering model

The Tk renderer converts world + campaign HUD data into canvas primitives. No game rules live here.

## Tests

Coverage includes vector math, gravity, beacon/finish flow, level builders, campaign lives/power-ups, enemy patrol/combat, and registry alignment.
