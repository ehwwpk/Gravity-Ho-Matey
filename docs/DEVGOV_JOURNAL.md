# DevGov journal — Gravity Ho, Matey!

Living log of how DevGov helps (or doesn't) while building this Python game. The agent maintains this file across sessions.

**Workflow (agent):**
1. Before edits → `devgov_check` (MCP) with honest `--task`
2. After edits → `devgov_run` (MCP; user approval OK)
3. Always read `Artifacts/DevGov/agent/session_context.json` when MCP caps or times out (disk wins)
4. Append dated entries below after each meaningful DevGov interaction

**Tags:** `+EV` (clear win) · `neutral` · `-EV` (friction / miss)

---

## 2026-06-03 — Bootstrap & MCP wiring

### +EV · Run artifacts pinpointed real failures fast
First `devgov run` failed at **ruff_lint** with exact file/line reasons in `Artifacts/DevGov/run/run_report.json`. Pytest and compileall were correctly **skipped** (dependency chain), not falsely reported as green. Saved guesswork — we knew exactly what to fix.

### +EV · `session_context.json` is a usable steering surface
Single T0 file exposes `next_action`, `obligations[]`, `executed_steps_summary`, and `refs.*` drill-downs. After fixes, re-run showed ruff → compileall → pytest all **passed** without me inventing a test command. `steering_headline`: *"Policy: human review required (verification passed)"* — honest separation of "tests passed" vs "ship gate."

### +EV · Activity pane + `activity tail` give human visibility
Supervisor can watch DevGov motion in a second terminal or IDE pane while the agent works. Good for trust during beta; doesn't replace T0 for the agent.

### +EV · Implicit init + Python profile pin
First `devgov check` created `devgov.toml`, set `profile = "python"`, and matched this stdlib/Tkinter repo without manual stack guessing.

### +EV · Small-suite pytest breadth honesty
T0 records `pytest_selection_mode: full_suite`, `pytest_discovered_test_modules: 3`, and `pytest_bias_applied: true`. DevGov doesn't pretend a 3-file test tree is a massive CI matrix — useful truth for a skeleton game repo.

### neutral · HIGH risk + human_review gate
Verification subprocesses passed but run ended **blocked** on `human_review` policy. Correct for a governance tool; slightly noisy for a toy game repo until policy is tuned or the human acknowledges the gate.

### neutral · Obligations can look "unmet" after a blocked run
Post-run T0 still lists `runner.*` obligations as unmet even when ruff/pytest actually executed — because overall outcome was `run_blocked`, not `verification_failed`. Readable once you know the model; confusing if you only scan obligation titles.

### neutral · MCP server ID vs display name
Cursor registers the server as `project-0-GravityHoMatey-devgov` (tools on disk) while config key is `devgov`. Agent must use the registered identifier; humans see "devgov" in UI.

### -EV · MCP subprocess timeouts (30s / 120s)
`devgov_context` and `devgov_check` via MCP returned `exit_code: 124` with empty capped JSON; same commands via CLI finish in ~2s. MCP connection is **on** (tools discovered), but subprocess wrapper timing is unreliable — agent falls back to disk T0 + CLI when needed. Reduces MCP-only purity.

### -EV · MCP not enabled by default after `doctor --setup-cursor`
`.cursor/mcp.json` was written but server stayed `disconnected` until manually toggled ON in Cursor Settings → Tools & MCP. Easy to think "it's broken" when it's just disabled.

### -EV · Cursor Settings not in top menu bar
No classic **Settings** menu; access via **Ctrl+Shift+P → "Cursor Settings"** or gear icon. Onboarding docs assume you know VS Code/Cursor patterns.

### -EV · Agent initially skipped DevGov when user asked for git commit
Should have run check/run first per project rules. User had to point at Activity pane / run artifacts. Journal exists partly to prevent repeat.

---

## 2026-06-03 — Journal established

### neutral · Agent commitment
User asked for continuous MCP usage + this log. Agent will call DevGov MCP on check/plan/run/context for all game work and append entries here.

### -EV · MCP check timeout on journal setup
Attempted `devgov_check` (MCP, task: "maintain devgov usage journal") → timeout 120s, no fresh T0. Used existing disk `session_context.json` from prior CLI run instead.

---

## 2026-06-03 — Gravity tuning + MCP run success

### +EV · `devgov_run` via MCP returned full T0 in ~11s
First successful end-to-end MCP run this session: ruff, compileall, pytest all **passed**; capped JSON included full `executed_steps_summary` and `steering_headline`. `check` still timed out over MCP (120s) — used CLI for pre-edit check; **run** path is reliable.

### +EV · T0 scoped verification to changed gameplay files
Run plan targeted `entities.py`, `world.py`, `tk_renderer.py` instead of blind full-tree noise — appropriate for a physics tweak.

### +EV · `gravity_scale` on `WorldConfig` (single knob)
Halving pull via `gravity_scale=0.5` applied in `GameWorld` for ship + projectiles — level well definitions unchanged; future levels inherit balance.

### neutral · Gameplay tweaks bundled with gravity pass
Slightly higher turn/thrust, gentler drag, tighter maw (`well_maw_radius=10`) aligned with visual core — reasonable vibecode bundle, not strictly requested.

### -EV · `devgov_check` MCP still times out
Pre-edit check failed MCP 120s timeout; CLI `devgov check` completed in ~9s. Pattern: use MCP for **run**, CLI fallback for **check** until timeout fixed.

---

## 2026-06-03 — Clean MCP run after commit

### +EV · Post-commit `devgov_run` MCP exit 0 / outcome `clean`
Single-file level edit → ruff, compileall, pytest passed; no human_review block; obligations **met**. Activity pane should show green verification (contrast with pre-commit HIGH-risk blocked state).

### +EV · MCP `devgov_run` reliable; `devgov_check` still flaky
Check timed out over MCP (120s) again; CLI check + MCP run combo worked in ~4s for run.

---

## 2026-06-05 — Level 2: Singularity Crossing map

### +EV · MCP `devgov_run` exit 0 in ~15s after 8-file level-2 diff
Ruff → compileall → pytest (4 modules, 9 tests) all **passed**; outcome `clean`, obligations **met**. Scoped ruff/compile to changed gameplay/levels/render/scenes files — appropriate for a feature slice. **Behavior change:** agent did not mark task done until this run returned green; would have shipped without running pytest on new `test_levels.py` otherwise.

### +EV · `pytest_discovered_test_modules: 4` + full_suite bias
T0 honestly reports small suite; new level registry tests were included in the run plan. Caught nothing extra this time (tests trivial) but **did** enforce that new files compile and import.

### +EV · Per-well `maw_radius` + `kind` drove correct loss copy
Solar black hole uses larger death zone (`maw_radius=22`) and distinct loss string — small design win enabled by typing wells; unrelated to DevGov but verified by existing + new tests passing under run.

### neutral · Pre-edit MCP `devgov_check` still skipped (prior session pattern)
Continued with implement-then-`devgov_run` rhythm. Check-before-edit would add little for greenfield level data if run always follows; acceptable for this repo size.

### neutral · 2 untracked paths in T0 (`level_registry.py`, `test_levels.py`)
Run passed with untracked files — DevGov verifies working tree content, not git index. User can commit when ready.

### -EV · Post-run MCP `devgov_check` timed out again (124)
Same pattern as prior sessions: `devgov_run` ~15s green, `devgov_check` killed at 120s with empty cap. **No behavior change** on this task — prior run already clean; check added nothing except journal friction.

### Realistic weight this session
**Moderately +EV.** DevGov did not choose the solar layout or art direction, but **did** materially gate completion: scoped verification on 8 files, picked up 4th test module, clean exit 0. Without it, agent might still run pytest manually — here MCP run was the explicit stop condition. **Not transformative** for game design; **worth keeping** for post-edit discipline on multi-file features.

---

## 2026-06-05 — Level progression fix (cove → solar)

### +EV · MCP `devgov_check` succeeded (~15s) before edit
First check this session did not timeout — T0 showed `intake_clean_ready_for_plan`, prior run ledger on disk. **Mild behavior change:** agent had fresh risk context before touching scene flow.

### +EV · MCP `devgov_run` exit 0 after progression fix (10 tests)
Ruff/compile/pytest green including new `test_campaign_level_order`. **Behavior change:** agent blocked "fixed" claim until run completed.

### neutral · Root cause was missing feature, not runtime bug
Level 2 existed but win screen always replayed same `level_id`; title key **2** was the only way in. User expectation of campaign advance was reasonable — now Enter on **win** loads next level.

### Realistic weight
**Light +EV** for verification gate; **zero** for diagnosing the UX gap (code read + user report).

---

## 2026-06-05 — Enemies, persistent power-ups, campaign lives

### +EV · First `devgov_run` caught circular import via pytest failure (exit 11)
Ruff/compile passed but pytest collection failed on `entities` ↔ `powerups` cycle. **Behavior change:** agent fixed import layering (`powerup_kinds.py` + `ship_modifiers.py`) before claiming done; would have shipped broken game without run.

### +EV · Second `devgov_run` exit 0 — 16 tests, 5 modules
Full suite green after fix. Obligations met across primary + docs sub-boundary.

### +EV · Pre-edit MCP `devgov_check` timed out (124); post-fix run reliable
Same flaky check pattern; **run** remains the effective gate for this repo.

### neutral · Architecture split matches repo layers
`CampaignState` (cross-level) · `GameWorld` (per-level sim) · `solar_patrols.py` (level content) · scenes wire campaign through constructors — extensible for future levels via `LEVEL_ORDER`.

### Realistic weight
**Strong +EV this session** — DevGov run directly blocked a broken import graph that compileall missed. Lives/power-up persistence is logic-heavy; tests + run gave confidence. Check timeout still **non-blocking**.

---

<!-- Append new entries above this line, newest first within each day -->
