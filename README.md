# Gravity Ho, Matey!

A gravity-bent arcade minigame in pure Python — pilot a pixel ship through wells, drifting rocks, relay sieges, and open-sector runs. Shots curve. Routes curve. Momentum matters.

**Requires Python 3.11+** and nothing else (Tkinter ships with standard CPython). No pip packages needed to play.

---

## Run the game

Clone the repo, then use **one** of the options below from the project root (`GravityHoMatey/`).

### Windows (PowerShell or Command Prompt)

```powershell
git clone https://github.com/ehwwpk/Gravity-Ho-Matey.git
cd Gravity-Ho-Matey
python run_game.py
```

If `python` is not found, try `py run_game.py` (Python launcher) or install [python.org](https://www.python.org/downloads/) and tick **Add to PATH**.

Alternative module entry:

```powershell
$env:PYTHONPATH="src"
python -m gravity_ho_matey
```

### macOS (Terminal)

```bash
git clone https://github.com/ehwwpk/Gravity-Ho-Matey.git
cd Gravity-Ho-Matey
python3 run_game.py
```

Use the same `python3` you installed from [python.org](https://www.python.org/downloads/) or Homebrew (`brew install python@3.12`). System `/usr/bin/python3` on older macOS may lack Tkinter — if the window fails to open, switch to a python.org or Homebrew build.

Alternative module entry:

```bash
PYTHONPATH=src python3 -m gravity_ho_matey
```

### Optional: editable install

Works on either OS if you prefer running as an installed package:

```bash
pip install -e .
python -m gravity_ho_matey
```

---

## Controls

### In flight

| Key | Action |
|-----|--------|
| `A` / `D` or `←` / `→` | Rotate |
| `W` or `↑` | Thrust |
| `Shift` (tap) | Reactor burst — speed kick in your facing direction (uses boost meter) |
| `Space` | Fire |
| `V` | Toggle tactical (top-down) ↔ chase camera |
| `R` | Restart current level |
| `Esc` | Return to title / nav station |
| `E` (hold) | Brood Moon land / ascend |

Aim by rotating the ship — there is no mouse aim in flight.

### Title & mission select

| Key | Action |
|-----|--------|
| `Enter` | Launch selected chart / continue |
| `Tab` / `[` `]` | Cycle briefing pages |
| `↑` `↓` or `W` `S` | Move deploy focus (Deploy page) |
| `1` – `6` | Quick-launch level 1–6 |
| `B` | Holo Bazaar (shop overlay) |

---

## Game overview

**Loop:** title briefing → level intro → launch countdown → fly the chart → shop / skill tree between sectors → next level.

**Goal:** collect nav beacons, survive hazards, then reach the finish gate (or complete the sector objective). You have **3 lives**; hull damage comes from impacts, radiation, enemies, and gravity maws.

**Six campaign levels:**

| # | Sector | Vibe |
|---|--------|------|
| 1 | Smuggler's Cove | Tutorial reef — wells, light rocks, chart radiation if you leave the mapped zone |
| 2 | Singularity Crossing | Vertical star strip around a central black hole |
| 3 | The Drift | Huge open belt, titan wells, void squids |
| 4 | Relay Hold | Defend a friendly station through timed assault waves |
| 5 | The Siege Line | Two-fleet skirmish — clear roster kills to unlock the exit |
| 6 | The Brood Moon | Orbital approach, surface seal run, RTB dock |

**Standouts:** gravity bends movement and shots; asteroid tiers and breakup; weapon doctrines (lance / scatter / nova) with overheat; reactor burst; tactical + chase cameras with banking and boost FOV; jewel treasury and radial skill deck between levels.

---

## Tests

```bash
python -m pytest tests -q
```

570+ tests, stdlib only — no third-party test deps.

## Project layout

```text
GravityHoMatey/
├─ docs/                  planning & specs
├─ src/gravity_ho_matey/  gameplay, levels, render, scenes
├─ tests/
└─ run_game.py            quickest entry point
```

Built as a clean prototype base (scenes / world / render / levels split) — easy to extend in Cursor or hand to another agent.
