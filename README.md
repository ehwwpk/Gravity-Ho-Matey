# Gravity Ho, Matey!

A surprisingly fun Python minigame built while testing DevGov software pre-beta.

You pilot a tiny pixel-art ship through gravity wells, drifting asteroids, relay sieges, and open-sector runs. Shots curve. Routes curve. Momentum matters. Collect beacons, defend stations, seal brood nests — then hit the gate or RTB dock.

This repo is structured like a serious project base rather than a single-file toy — easy to hand to Cursor or another agent and keep vibecoding from a clean foundation.

## Current state

**Six playable levels** (campaign order):

| # | Id | Name |
|---|-----|------|
| 1 | `cove` | Smuggler's Cove |
| 2 | `solar` | Singularity Crossing |
| 3 | `drift` | The Drift |
| 4 | `rift` | Relay Hold |
| 5 | `siege` | The Siege Line |
| 6 | `brood_moon` | The Brood Moon |

**Core loop:** title → level intro GIF → faster launch countdown → play → shop / skill tree between levels → next sector.

**Gameplay:** gravity-bent shots and routes, beacon collection, finish gates, chart radiation on L1–2, reactor burst, asteroid tiers (pebble → boulder), patrol enemies, relay defense waves (3-wave hold), Brood Moon surface seal / orbital return.

**Cameras:** tactical top-down (`V` toggles) and chase rig with banking, boost FOV kick, engine exhaust, and shared starfield / gravity heatmap polish.

**Tech:** standard-library-first — runnable Tkinter prototype, separated scenes / world / render / levels / narrative, 570+ pytest cases, planning docs under `docs/`.

**Recent tuning:** L1–2 play chart expanded ~12.5% outward (wells, rocks, beacons unchanged); launch countdown halved (~1.5s 3-2-1); chase boost FX and camera switch cleanup.

## Why Tkinter?

The brief asked for core Python or mainly core Python. Tkinter ships with CPython on most desktop installs, so this base avoids external dependencies while still supporting a real window, keyboard input, 2D drawing, and a credible rapid-prototype loop.

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
- `Shift` (tap): reactor burst — instant speed kick in the direction you're pointing (~32% of max speed; costs reactor charge)
- `Space`: fire
- `V`: toggle tactical ↔ chase camera
- `R`: restart level
- `Esc`: back to title
- `Enter`: start from title or continue after win/loss
- `E` (hold): Brood Moon landing / ascent transitions

## Project layout

```text
GravityHoMatey/
├─ docs/
├─ src/gravity_ho_matey/
│  ├─ assets/
│  ├─ core/
│  ├─ gameplay/
│  ├─ levels/
│  ├─ narrative/
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
python -m pytest tests -q
```

Or unittest discovery:

```bash
python -m unittest discover -s tests -v
```

No third-party packages are required.

## Design target

This should feel like an arcade maze racer, not Snake with a gravity wrapper. The ship has inertia, gravity bends routes and shots, drifting asteroids create moving hazards (most rocks and pebbles shatter in 1–3 hits; only the biggest rocks and boulders split into smaller debris), and win conditions force route-planning: collect beacons, survive the chart, then escape through the gate.
