# Cursor / Codex Handoff

You are working in `Gravity Ho, Matey!`, a standard-library-first Python arcade skeleton.

## Hard constraints

- Preserve the `src/` layout.
- Keep gameplay independent from Tkinter.
- Keep renderer code in `render/`.
- Keep scene flow in `scenes/`.
- Keep core math/collision helpers in `core/`.
- Do not add external dependencies unless explicitly approved.
- Run `python -m unittest discover -s tests -v` after logic changes.

## Current playable loop

The player pilots a small ship through a gravity cove. Collect all beacons, then fly into the finish gate. Gravity wells bend ship movement and projectiles. Drifting asteroids chip the hull on collision.

## Good next tasks

1. Add a timer and best-time display.
2. Add moving sea mines that patrol paths.
3. Add cannon targets that open locked gates.
4. Add boost fuel and refill buoys.
5. Add a second level and level-select scene.
6. Add a fixed-step accumulator for more stable physics.
7. Add sprite-like pixel art using Canvas polygon/rectangle batches.

## Warning

Do not collapse the architecture into one file. This repo is intentionally structured as a serious base for extension.
