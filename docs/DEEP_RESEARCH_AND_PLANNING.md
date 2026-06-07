# Gravity Ho, Matey! Deep Research and Planning

## Product target

Gravity Ho, Matey! should land between an arcade racer, a maze game, and a physics toy. The core hook is not merely "snake but gravity." The player pilots a small pirate ship through a cove-like maze where gravity wells bend both movement and cannon shots.

The first playable loop is deliberately compact:

1. Spawn in a dangerous cove.
2. Navigate corridors while gravity wells pull the ship off-line.
3. Collect all beacons.
4. Fire curved shots to clear hazards or interact with future targets.
5. Escape through the finish gate.

The repo should be simple enough for rapid vibecoding but structured enough that a coding agent can extend it without flattening the project into a toy script.

## Why standard-library first

The project starts with Tkinter because it ships with most CPython installations and supports a real window, keyboard events, timer-based loop, and 2D canvas drawing without external dependency setup. This is not the final engine decision. It is the correct first skeleton for a portable coding-agent handoff.

Future migrations could target pygame-ce, arcade, pyglet, Godot, or Unity. The current architecture keeps game logic independent enough that the renderer can be replaced later.

## Game pillars

### 1. Curved navigation

Movement should feel like sailing through an unstable gravity cove. Thrust gives intent, inertia carries consequence, and gravity wells perturb the path.

### 2. Curved shots

Cannon shots are not straight bullets. They inherit ship velocity and are pulled by wells. This creates trick-shot potential and makes the gravity mechanic visible.

### 3. Maze race pressure

The map has drifting asteroids, open routes, beacons, and a finish gate. Winning requires route planning, not just survival.

### 4. Pixel-art readability through primitives

Tkinter is not a sprite engine, but the renderer should still evoke pixel art: chunky triangle ships, small square beacons, ring wells, dotted trails, and crisp HUD labels.

## Current technical architecture

- `core`: math, vectors, rects, collision helpers, constants that must stay renderer-independent.
- `gameplay`: domain state and simulation systems.
- `levels`: data-driven level definitions.
- `render`: Tkinter renderer and primitive asset drawing.
- `scenes`: title, play, and end-state flow.
- `util`: input and timing helpers.
- `app.py`: Tkinter application shell.
- `main.py`: package entry point.

## Simulation model

The world updates on a fixed-ish frame interval using Tkinter's `after` loop. The logic accepts a delta time, clamps it, updates input-driven ship control, applies gravity, integrates projectiles, checks collisions, and computes win/loss state.

This is intentionally not a fully deterministic engine yet. It is a clean arcade prototype base. If the project evolves into deterministic replays or level validation, isolate random seeds and replace variable frame integration with a fixed-step accumulator.

## Expansion roadmap

### Milestone 1: Current starter

- One playable level.
- Ship steering and thrust.
- Gravity wells.
- Drifting procedural asteroids (rings, showers, scatter).
- Beacons.
- Finish gate.
- Curved shots.
- Win/restart/title flow.

### Milestone 2: Better race feel

- Timer and medals.
- Ghost trail for best run.
- Boost fuel and refill buoys.
- Moving hazard currents.
- Level select.

### Milestone 3: More pirate identity

- Cannon targets.
- Sea mines.
- Kraken gravity wells.
- Treasure route bonuses.
- Ship upgrades.

### Milestone 4: Engine hardening

- Fixed-step loop.
- Data-only level files.
- Replay input capture.
- Renderer abstraction tests.
- Optional pygame renderer.

## Coding-agent guardrails

- Keep core math independent of Tkinter.
- Do not put gameplay rules in renderer files.
- Do not put level geometry directly in scene classes.
- Prefer small files with explicit responsibilities.
- Add tests before changing vector, collision, or gravity behavior.
- Keep the standard-library-first constraint unless the human explicitly approves dependencies.

## Camera modes and flight instruments

Two presentation modes share the same simulation; HUD flight data must not be chase-only.

| Mode | Role | Gravity readout | Velocity readout |
|------|------|-----------------|------------------|
| **Tactical** | Top-down map; heatmap shows spatial pull | Compact summary (mini G-ball + F/R/G text) — complements heatmap, does not replace it | Compact bar + slip (bottom-left) |
| **Chase** | Cockpit follow-cam | Full G-ball + rear mirror heatmap | Full velocity panel + slip + boost |

### Shared implementation (`render/chase_helm.py`)

- `ship_frame_gravity(world, ship_angle)` — forward, lateral, total accel in ship frame (same math both modes).
- `slip_angle_rad`, `_G_REF`, `_SLIP_WARN` — shared tuning constants.
- `draw_tactical_flight_instruments(...)` — compact corners only; no canopy, horizon, reticle, or mirror.
- `draw_xwing_cockpit_hud(...)` — full chase helm (unchanged scope).

### Layout (tactical compact)

- **Bottom-left:** velocity label, numeric speed, scaled bar (≈108px), slip rail.
- **Bottom-right:** “GRAV” label, 32px direction dot in circle, `{total}G`, `F±nn R±nn`.
- Anchored inside playfield below command strip (`hud_top`); must not overlap edge-hint badges.

### Non-goals (v1)

- Path preview overlay on tactical (future).
- Duplicating chase canopy chrome on tactical.
- Ship-hull gravity chevron (optional later).

### Tests

- `tests/test_chase_instruments.py` — frame gravity math (existing).
- Draw smoke test: tactical instruments on canvas without TclError (skip if Tk unavailable).
