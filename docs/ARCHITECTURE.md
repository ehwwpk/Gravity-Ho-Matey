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

- `TitleScene`: paginated pre-flight terminals (welcome, mission, helm, combat, deploy); Enter opens holo chart via `start_chart_briefing`.
- `PlayScene`: owns per-level `GameWorld` + cross-level `CampaignState`; camera toggle and win/loss transitions.
- `ChartBriefingScene`: diegetic holo-map preview before every launch — inaugural chart from title or post-clear transition to the next sector.
- `EndScene`: win/loss screen; retries, campaign complete, or return to title on game over.

Win with a next sector routes to `ChartBriefingScene` before the next `PlayScene`. Starting sector 1 from title uses the same holo HUD and `ChartMapOverlay` in **initial brief** mode (`cleared_level_id=None`).

Scene transitions that start gameplay should go through `scenes/game_flow.start_play` so campaign wiring stays consistent. Holo chart transitions use `game_flow.start_chart_briefing`. Scene modules use **lazy imports** inside methods to avoid import cycles (`game_flow` ↔ `play` ↔ `end`).

## Campaign progress

`gameplay/progress.py` tracks which levels are selectable from the title screen. Beating a level unlocks the next entry in `LEVEL_ORDER`. Level 2 direct select is gated until Cove is cleared at least once (session-persistent for the process lifetime).

## Campaign vs level state

| Object | Lifetime | Owns |
|--------|----------|------|
| `CampaignState` | Whole campaign (3 lives, collected power-ups) | lives, `hull_chunks`, `powerups` set |
| `GameWorld` | Single level attempt | ship, asteroids, enemies, pickups, beacons, projectiles, invuln timer |

`gameplay/session.wire_world_for_campaign()` applies carried bonuses and connects pickup collection to the campaign. `capture_level_spawn()` + `respawn_ship_at_spawn()` handle in-level chip respawns with 1s invulnerability. `ensure_active_life_hull()` refills hull only when entering play with zero chunks (new life); partial hull carries between levels.

## Damage model

`gameplay/damage.py` defines chip vs lethal sources:

| Source | Severity |
|--------|----------|
| Asteroid, out-of-bounds, enemy | 1 hull chunk (in-level respawn) |
| Gravity maw (singularity, planet, cove well) | Lethal (whole life) |

Three hull chunks per life; three chips on one life costs one campaign life. Partial hull carries between levels. Only `PlayScene` applies damage to `CampaignState`.

## Gameplay model

`GameWorld` owns mutable per-level state:

- `Ship`, `Projectile`, `PatrolEnemy`, `PowerUpPickup`
- `Asteroid`, `GravityWell`, `Beacon`, `FinishGate`
- `gameplay/asteroid_shape.py` — seeded procedural convex silhouettes
- `gameplay/asteroid_motion.py` — drift profiles (slow/medium/fast/ring/shower), integration, spawn
- `gameplay/asteroid_tiers.py` — SMALL/LARGE tiers, hit budgets, generation cap
- `gameplay/asteroid_mass.py` — polygon mass, fragment scaling, explosion scale helpers
- `gameplay/asteroid_combat.py` — projectile hit resolution, breakup, list mutation contract
- `levels/asteroid_placements.py` — per-level field layout
- `GameStatus`, optional `on_powerup_collected` callback

`WorldConfig` owns tuning constants and `level_theme` / `level_name`.

## Asteroid combat

Destructible asteroids use tiered hit budgets rolled once at spawn:

| Tier | `size_class` | Hits to break | On final hit |
|------|--------------|---------------|--------------|
| LARGE | `boulder` | 5–10 (seeded) | 50% mass → breakup FX; 50% → 2–4 SMALL fragments |
| MEDIUM | large `rock` (radius ≥ 51) | 3–5 (seeded) | 50% mass → breakup FX; 50% → 2–3 SMALL fragments |
| SMALL | `pebble`, typical `rock` | 1–3 (seeded) | Removed completely |

- Friendly and hostile projectiles call `asteroid_combat.apply_projectile_hit` with the same tier rules.
- Fragment spawns inherit velocity + outward impulse; ring metadata is cleared so belt gaps persist naturally.
- `GameWorld` refreshes `asteroid_threat_snapshots` after any combat list mutation so `_check_loss` never uses stale hulls.
- Generation depth caps at 2 — deeper fragments vaporize instead of splitting again.
- Global cap: 48 asteroids; at cap, breakup is vapor-only (no new fragments).

Chip hits reuse `PROJECTILE_IMPACT`; final small/large hits use `ASTEROID_DESTROYED` / `ASTEROID_BREAKUP` (mass-scaled). Render adds extra craters from `hits_max - hits_remaining`.

## Levels

- `level_registry.py`: `LEVEL_BUILDERS`, `LEVEL_ORDER`, `build_level()`, startup validation.
- `level_data.py`: geometry and wells per level.
- `solar_patrols.py`: enemy patrol definitions for level 2 only.

## Rendering model

Presentation is split from simulation:

| Module | Role |
|--------|------|
| `render/camera.py` | `ViewCamera`, `CameraMode` — follow + projection only |
| `render/lighting.py` | `LightRig`, `MaterialTones`, shade bands — shared entity lighting |
| `render/lit_draw.py` | Faceted illustrated polygons, lit ship hull, map glyphs |
| `render/light_compose.py` | B-lite well glow layer (B-full multiply reserved for Pillow) |
| `render/chase_fx.py` | Parallax sky, fog glow, speed streaks, engine bloom |
| `render/chase_ground.py` | Purple gravity floor wash (no threat coloring) |
| `render/asteroid_viz.py` | Tactical/chase/map asteroid collection + draw |
| `render/chase_wells.py` | Lit floor rings + cores (segment-stitched) |
| `render/chase_entities.py` | Chase beacons, gates, enemies, pickups |
| `render/view_renderers.py` | Tactical pan + chase pipeline orchestration |
| `gameplay/gravity_field.py` | Baked well field for heatmap, chase floor, holo chart |
| `render/chart_map_overlay.py` | Between-level holo table |
| `render/hud_overlay.py` | Command overlay (lives, hull, cargo, camera mode) |

`V` cycles tactical ↔ chase cam without changing physics or `ControlIntent`.

## Agent workflow (DevGov)

Every coding session that touches the repo should run the DevGov loop — **check before edits**, **run after edits**, then read `Artifacts/DevGov/agent/session_context.json` (MCP `devgov_*` tools when connected, CLI fallback). Honest usage notes go in `docs/DEVGOV_JOURNAL.md`. Do not claim DevGov gated a change if check/run were skipped on that diff.

## Tests

Coverage includes vector math, gravity, beacon/finish flow, level builders, campaign lives/power-ups, hull chip/lethal damage, enemy patrol/combat, camera projection, gravity field bake, registry alignment, drifting asteroid shape/motion/collision/render paths, and destructible asteroid combat (tiers, breakup, threat snapshot refresh).
