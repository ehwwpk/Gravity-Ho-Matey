# Pygame CE Migration Plan — Gravity Ho, Matey!

**Status:** Planning document (no implementation commitments)  
**Owner:** Project / agent  
**Last updated:** 2026-06-02 (L1 complete-loop test plan — final pass)  
**Purpose:** Single authoritative end-to-end plan to migrate the game from Tkinter canvas rendering to **Pygame CE**, validated first with a **full Level 1 (Cove) loop**, then expanded to full campaign parity.

---

## Table of contents

### Part I — Program-wide migration

1. [Executive summary](#1-executive-summary)
2. [Goals, non-goals, and success definition](#2-goals-non-goals-and-success-definition)
3. [Why Pygame CE (honest benefits)](#3-why-pygame-ce-honest-benefits)
4. [Current architecture inventory](#4-current-architecture-inventory)
5. [Target architecture](#5-target-architecture)
6. [The DrawContext abstraction (critical spine)](#6-the-drawcontext-abstraction-critical-spine)
7. [Application shell migration](#7-application-shell-migration)
8. [Input, timing, and windowing](#8-input-timing-and-windowing)
9. [Asset and narrative pipeline (GIFs, fonts, audio)](#9-asset-and-narrative-pipeline-gifs-fonts-audio)
10. [Hit testing and UI interaction](#10-hit-testing-and-ui-interaction)
11. [Render layer migration matrix](#11-render-layer-migration-matrix)
12. [Scene-by-scene migration order](#12-scene-by-scene-migration-order)
13. [Level 1 vertical slice — full loop specification](#13-level-1-vertical-slice--full-loop-specification)
14. [Phased rollout (Phases 0–8)](#14-phased-rollout-phases-08)
15. [Testing strategy](#15-testing-strategy)
16. [Performance and visual upgrade path](#16-performance-and-visual-upgrade-path)
17. [Packaging, dependencies, and CI](#17-packaging-dependencies-and-ci)
18. [Risk register and mitigations](#18-risk-register-and-mitigations)
19. [Rollback and dual-backend strategy](#19-rollback-and-dual-backend-strategy)
20. [Timeline estimates (solo + agent)](#20-timeline-estimates-solo--agent)
21. [Definition of done — full port complete](#21-definition-of-done--full-port-complete)
22. [Anti-patterns — do not do these](#22-anti-patterns--do-not-do-these)
23. [Appendix A — Tk-coupled file list](#appendix-a--tk-coupled-file-list)
24. [Appendix B — Portable file list (do not rewrite)](#appendix-b--portable-file-list-do-not-rewrite)
25. [Appendix C — Cove L1 acceptance checklist](#appendix-c--cove-l1-acceptance-checklist)

### Part II — L1 full game loop (final planning)

26. [L1 scope lock — what “full loop” means](#26-l1-scope-lock--what-full-loop-means)
27. [Complete scene FSM and transition table](#27-complete-scene-fsm-and-transition-table)
28. [GameRenderer API contract (Pygame parity)](#28-gamerenderer-api-contract-pygame-parity)
29. [Scene-by-scene final specification](#29-scene-by-scene-final-specification)
30. [Cove playfield — content and draw pipeline](#30-cove-playfield--content-and-draw-pipeline)
31. [Input matrix — every key and pointer per scene](#31-input-matrix--every-key-and-pointer-per-scene)
32. [L1 asset manifest](#32-l1-asset-manifest)
33. [Scene code changes (Tk decoupling)](#33-scene-code-changes-tk-decoupling)
34. [L1 work packages — dependency graph](#34-l1-work-packages--dependency-graph)
35. [L1 day-by-day implementation schedule](#35-l1-day-by-day-implementation-schedule)
36. [L1 test and parity verification plan](#36-l1-test-and-parity-verification-plan)
37. [L1 final sign-off gates](#37-l1-final-sign-off-gates)
38. [Complete player screen inventory (L1)](#38-complete-player-screen-inventory-l1)
39. [Loading, GIF, and transition timing spec](#39-loading-gif-and-transition-timing-spec)
40. [Title hub — all menu pages and hit regions](#40-title-hub--all-menu-pages-and-hit-regions)
41. [Chart briefing — inaugural Cove UI spec](#41-chart-briefing--inaugural-cove-ui-spec)
42. [Master L1 test matrix (automated + manual)](#42-master-l1-test-matrix-automated--manual)
43. [QA playbooks — three complete loop scripts](#43-qa-playbooks--three-complete-loop-scripts)

---

## 1. Executive summary

Gravity Ho Matey! is ~22k lines of Python with **488+ tests**, **6 campaign levels**, dual camera modes (tactical + chase), chart briefing, skill shop, GIF intros, and a mature gameplay layer that is **already backend-agnostic**.

**The migration is a renderer + shell swap, not a game rewrite.**

Strategy:

1. Introduce a **DrawContext** protocol so draw code stops depending on `tk.Canvas`.
2. Build a **Pygame CE app shell** parallel to `app.py`.
3. Ship a **Level 1 full loop** on Pygame first (title → intro/countdown → chart briefing → play Cove → win/loss → return flow).
4. Port remaining render modules and scenes in dependency order.
5. Add **audio and juice** once the Pygame loop is stable (biggest player-perceived upgrade).
6. Retire Tk when parity + tests pass.

**No 3D models, no new art pipeline, no Unity.** All visuals remain 2D vector / lit-polygon / code-drawn, optionally baked to surfaces for cache.

---

## 2. Goals, non-goals, and success definition

### Goals

| ID | Goal |
|----|------|
| G1 | Run the **full L1 campaign loop** on Pygame CE with identical gameplay outcomes (beacons, gate, lives, jewels). |
| G2 | Preserve **all existing gameplay tests** without rewriting simulation logic. |
| G3 | Match or exceed **60 FPS target** at 960×640 on modest hardware for Cove play scene. |
| G4 | Enable **game audio** (SFX + music hooks) as a first-class subsystem. |
| G5 | Support **alpha blending** for fog, glow, explosions, HUD overlays. |
| G6 | Provide a **clean packaging path** (PyInstaller / zip / itch upload). |
| G7 | Maintain **dual-backend** until full parity; Tk remains fallback during migration. |

### Non-goals (explicit)

| ID | Non-goal |
|----|----------|
| NG1 | 3D models, Blender pipeline, or art budget spend. |
| NG2 | Rewriting `gameplay/`, `levels/`, or campaign rules during port. |
| NG3 | Shader-heavy GPU pipeline in Phase 1 (optional later). |
| NG4 | Mobile / web port. |
| NG5 | Changing level design or adding L7+ content during core migration. |
| NG6 | Replacing GIF narrative with video cutscenes. |

### Success definition (L1 slice)

A stranger (or you, blind to backend) can:

1. Launch `run_game_pygame.py` (or env flag).
2. See startup splash (if enabled) → title → deploy Cove.
3. Watch Cove intro GIF or launch countdown.
4. Enter chart briefing (optional skip path OK for slice).
5. Play Cove in **tactical and chase** cam; collect beacons; finish gate.
6. See win screen; Esc returns to title.
7. Die to asteroid/well; lose life; restart works.

All **gameplay unit tests** still pass. **Render smoke tests** updated for Pygame surface assertions.

---

## 3. Why Pygame CE (honest benefits)

Pygame CE does **not** automatically look better. It removes ceilings:

| Capability | Tkinter today | Pygame CE |
|------------|---------------|-----------|
| Game audio | Effectively none | Native mixer, channels, streaming |
| Alpha / blend modes | Limited stipple hacks | Per-surface alpha, BLEND_ADD, etc. |
| Frame pacing | `root.after(16)` + full canvas delete | `clock.tick(60)`, dirty regions optional |
| Sprite cache | Manual PhotoImage | `Surface` reuse, `convert_alpha()` |
| Distribution | “Install Python + PYTHONPATH” | Executable / zip |
| Input | Keysym strings | Scancodes + unicode; gamepad possible |
| Fullscreen / scale | Awkward | Built-in display modes |

**Player perception jump** comes from **audio + juice + stable framerate**, enabled by Pygame — not from switching engines alone.

---

## 4. Current architecture inventory

### 4.1 Portable layers (keep as-is)

These modules should require **zero or cosmetic changes**:

```
core/           vector, geometry
gameplay/       world, entities, gravity, combat, campaign, shop, missions
levels/         layouts, profiles, registry, all *_layout.py / *_enemies.py
narrative/      level_intros text config (not GIF loader)
util/           timekeeper, input normalization (keysym layer swapped at app)
scenes/         play_session, game_flow — logic only; host protocol generalized
tests/          all gameplay-dominant tests (400+)
```

**~60% of codebase by value is already portable.**

### 4.2 Coupled layers (must migrate)

| Area | Files (approx) | Coupling |
|------|----------------|----------|
| App shell | `app.py`, `main.py` | Tk window, canvas, event bindings |
| Renderer facade | `render/tk_renderer.py` | Orchestrates all draw paths |
| View renderers | `render/view_renderers.py` | Tactical + perspective dispatch |
| Lit draw | `render/lit_draw.py` | `create_polygon` faceted rocks |
| Entity viz | ~25 `*_viz.py` | Canvas primitives |
| FX | chase_fx, explosion_fx, projectile_fx | Ovals, lines, rectangles |
| HUD / UI | hud_overlay, menu_ui, holo_shop, chart_map | Text + hit maps |
| Overlays | title, intro, splash, countdown, brood transition | GIF via PhotoImage |
| Animated assets | `render/animated_image.py` | Tk PhotoImage / optional Pillow |
| Scene host | `scenes/base.py` | Types `TkRenderer` |

**~55 render-related Python files** import tkinter (see Appendix A).

### 4.3 Scene graph (current)

```
StartupSplashScene (optional)
  → TitleScene
    → ChartBriefingScene (between levels / deploy)
      → LevelIntroScene OR LaunchCountdownScene
        → PlayScene
          → (brood landing cinematic overlay — L6 only)
          → EndScene (win/loss campaign)
            → ChartBriefingScene / TitleScene
```

All scenes call `host.renderer.*` and `host.input_state.*`.

### 4.4 Resolution and timing constants

From `settings.py`:

- Viewport: **960 × 640**
- Frame budget: **16 ms** (`FRAME_MS`)
- Max dt clamp: **1/30 s**
- Play HUD top offset: computed by `SciFiHudOverlay.playfield_top`

These constants **carry over unchanged** to Pygame.

---

## 5. Target architecture

```
┌─────────────────────────────────────────────────────────────┐
│  pygame_app.py (GravityHoMateyPygameApp)                    │
│  - pygame.display / pygame.time.Clock                       │
│  - event pump → InputState                                    │
│  - scene stack → Scene.update/draw                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  GameRenderer (protocol)                                      │
│  - PygameRenderer (production)                              │
│  - TkRenderer (legacy, deprecated after parity)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  DrawContext        AssetCache          AudioBus
  (2D primitives)    (fonts, GIF,        (SFX/Music
                      surfaces)           optional Phase 6)
        │
        ▼
  view_renderers / *_viz / overlays
  (backend-agnostic signatures)
```

### New modules (planned)

| Module | Responsibility |
|--------|----------------|
| `render/draw_context.py` | Protocol + shared types (Color, FontSpec) |
| `render/backends/tk_draw.py` | TkDrawContext implements protocol |
| `render/backends/pygame_draw.py` | PygameDrawContext implements protocol |
| `render/pygame_renderer.py` | Mirror of TkRenderer API |
| `render/asset_cache.py` | Fonts, GIF frames as Surfaces, color parsing |
| `render/audio_bus.py` | Thin wrapper over pygame.mixer (Phase 6) |
| `pygame_app.py` | Entry shell |
| `run_game_pygame.py` | Runner script at repo root |

### SceneHost generalization

Replace `renderer: TkRenderer` with `renderer: GameRenderer` protocol exposing:

- `draw_world(...)`
- `draw_title(...)`
- `draw_chart_briefing(...)`
- `draw_level_intro(...)`
- `draw_launch_countdown(...)`
- `draw_startup_splash(...)`
- `draw_brood_transition(...)`
- Hit test methods: `title_hit_test`, `chart_hit_test`, etc.

Scenes remain **identical in control flow**.

---

## 6. The DrawContext abstraction (critical spine)

Every `canvas.create_*` call becomes a DrawContext method. This is the **highest-leverage refactor** and must land before bulk porting.

### 6.1 Core protocol surface

Minimum methods to cover 95% of current draw calls:

| Method | Tk equivalent | Notes |
|--------|---------------|-------|
| `clear()` | `delete("all")` | Pygame: blit background fill each frame OR layer surfaces |
| `polygon(points, fill, outline, width)` | `create_polygon` | Workhorse for lit_draw |
| `line(x0,y0,x1,y1, color, width, cap)` | `create_line` | cap ROUND |
| `rect(x0,y0,x1,y1, fill, outline, width)` | `create_rectangle` | Sky bands, HUD panels |
| `oval(x0,y0,x1,y1, fill, outline, width)` | `create_oval` | Wells, fog glow rings |
| `text(x, y, string, color, font, anchor)` | `create_text` | HUD labels |
| `image(x, y, surface, anchor)` | `create_image` | GIF frames, baked sprites |
| `stipple_rect(...)` | `stipple=` | Emulate with alpha surface blit on Pygame |

### 6.2 Extended helpers (shared, backend-free)

Move to `render/draw_helpers.py`:

- `draw_ground_fog_glow(ctx, x, y, radius, color, pulse)` — already conceptually backend-free; today lives in chase_fx
- `_dash_ring_segments` (planet landing band) — uses `line` only
- `_flat(points)` — unchanged

### 6.3 Migration order for DrawContext

1. Define protocol + TkDrawContext (wrap existing canvas)
2. Change `lit_draw.py` to accept `DrawContext` instead of `tk.Canvas`
3. Change top 5 viz files: `ship_viz`, `asteroid_viz`, `beacon_viz`, `entity_viz`, `world_draw`
4. Change `view_renderers.py` signatures
5. Implement PygameDrawContext with pixel-perfect parity checks on Cove stills
6. Remaining viz files in batches (theme groups)

### 6.4 Color handling

Today: hex strings (`"#08111f"`) everywhere in `palette.py`.

Plan:

- Keep **hex strings in palette** (no mass rename)
- DrawContext backends parse hex → backend color once per call (or cached RGB tuples in `asset_cache.py`)
- Optional: add `palette.rgb(name)` helper for Pygame `(r,g,b)` / `(r,g,b,a)`

---

## 7. Application shell migration

### 7.1 Current Tk shell (`app.py`)

- `tk.Tk()` + single full-size `Canvas`
- `root.after(FRAME_MS, _tick)` game loop
- Key/pointer/wheel bindings → `InputState`
- Scene `update(dt)` → `draw(host)`
- Error overlay on exception (keep equivalent in Pygame)

### 7.2 Target Pygame shell (`pygame_app.py`)

| Concern | Design |
|---------|--------|
| Init | `pygame.init()`, `display.set_mode((960,640), RESIZABLE optional later)` |
| Loop | `while running: dt = clock.tick(60)/1000; handle_events(); scene.update; scene.draw; flip()` |
| Draw target | Single `screen` Surface; optional `playfield_surface` for HUD split |
| Quit | pygame.QUIT + Esc policy matches Tk |
| Error frame | Red banner + traceback to console (same as today) |

### 7.3 Entry points

| Script | Purpose |
|--------|---------|
| `run_game.py` | Default Tk (until cutover) |
| `run_game_pygame.py` | Pygame CE path |
| `GRAVITY_BACKEND=pygame` env var | Optional unified entry via `main.py` dispatcher |

### 7.4 `SceneHost` protocol update

`scenes/base.py`:

- Replace `TkRenderer` import with `GameRenderer` protocol in `render/game_renderer.py`
- Both app classes implement `SceneHost`

---

## 8. Input, timing, and windowing

### 8.1 Keyboard mapping

Current: Tk `keysym` strings → `InputState.normalize_key`.

Pygame plan:

- Map `pygame.key.get_pressed()` + TEXTINPUT for space-equivalent
- Maintain **same normalized key set**: `a`, `d`, `w`, `space`, `shift_l`, etc.
- Map `K_ESCAPE`, `K_RETURN`, `K_r` for scene flow
- Chart/title: number keys `1`–`6` for dev deploy

**Do not change `ControlIntent` or gameplay input consumption.**

### 8.2 Pointer / shop UI

Tk provides pixel coords from bind events.

Pygame:

- `MOUSEBUTTONDOWN/MOTION/WHEEL` → same `(x, y)` in canvas space
- Shop tree drag, holo button hover: unchanged logic in overlay code; only hit geometry stays in screen space

### 8.3 Timing

Keep `TimeKeeper` and `MAX_DT` clamp — swap only the clock source.

### 8.4 Window modes (post-slice)

- Phase 8: optional integer scale 2× for 1920×1280 displays
- Fullscreen toggle (F11) — nice-to-have

---

## 9. Asset and narrative pipeline (GIFs, fonts, audio)

### 9.1 GIF intros (no Tk PhotoImage)

Replace `AnimatedImageSequence` Tk binding with **backend-neutral frame store**:

```
AnimatedImageSequence
  frames: list[BackendImage]  # Protocol: width, height, blit to DrawContext
  delays_ms: list[int]
```

Loading strategy:

1. **Preferred:** Pillow loads GIF → `pygame.image.fromstring` / `surfarray` → `Surface.convert_alpha()`
2. **Fallback:** `pygame.image.load` per frame if exported PNG sequence added later
3. Keep existing assets in `src/gravity_ho_matey/assets/narrative/*.gif`

Optional one-time tool (Phase 4): script to bake GIF → PNG strip folder for faster load (not required for L1).

### 9.2 Fonts

Tk uses `("Courier New", 10, "bold")`.

Pygame:

- Ship **`assets/fonts/CourierPrime-Bold.ttf`** or similar open font (OF license) OR use pygame `SysFont("courier")` with fallback chain
- `AssetCache.get_font(size, bold)` returns memoized `pygame.font.Font`
- Match line heights to keep HUD layout stable (may need 1–2 px nudge constants)

### 9.3 Audio (Phase 6 — hooks in Phase 1)

| Event | SFX priority |
|-------|--------------|
| Thrust loop | High |
| Fire | High |
| Beacon collect | High |
| Gate open / win | High |
| Hull chip / death | High |
| Asteroid crack | Medium |
| Menu click | Medium |
| Sector music beds | Per theme (Cove first) |

Use **free libraries** (OpenGameArt, Kenney, Freesound CC0). No budget.

Architecture:

- `AudioBus.play(name)`, `play_music(theme)`, `set_volume`
- Gameplay emits events; renderer/bus handles playback (no audio in pure sim tests)

### 9.4 No new raster art required

Ships, asteroids, squids remain **procedural lit polygons**. Optional Phase 7: bake to sprite at load for perf — still generated from code.

---

## 10. Hit testing and UI interaction

### 10.1 MenuHitMap (unchanged logic)

`menu_ui.MenuHitMap` stores axis-aligned hit rects `{id: (x0,y0,x1,y1)}`.

Works identically with Pygame pointer events — **no Tk dependency today**.

### 10.2 Hit test owners

| Component | Method |
|-----------|--------|
| TitleScreenOverlay | `hits.hit(x,y)` |
| ChartMapOverlay | `hits.hit(x,y)` |
| HoloShopOverlay | shop click routing via chart/title scenes |
| LevelIntroOverlay | skip / continue regions if any |

Port: ensure overlays still populate `MenuHitMap` during `draw()`, not during event handling.

### 10.3 Focus and modal states

Shop open, chart briefing, title deploy — scene FSM unchanged in `scenes/title.py`, `chart_briefing.py`, `shop_ui.py`.

---

## 11. Render layer migration matrix

Priority tiers for porting after DrawContext exists.

### Tier 0 — Infrastructure

| File | Action |
|------|--------|
| `render/draw_context.py` | **Create** |
| `render/backends/tk_draw.py` | **Create** |
| `render/backends/pygame_draw.py` | **Create** |
| `render/game_renderer.py` | **Create** protocol |
| `render/pygame_renderer.py` | **Create** |
| `render/asset_cache.py` | **Create** |
| `render/tk_renderer.py` | Refactor to use TkDrawContext |

### Tier 1 — L1 play path (Cove)

| File | Cove dependency |
|------|-----------------|
| `lit_draw.py` | Asteroids, stations |
| `lighting.py` | Materials (no change) |
| `light_compose.py` | Well glow |
| `ship_viz.py` | Player ship |
| `asteroid_viz.py` | Rocks |
| `beacon_viz.py` | Objectives |
| `entity_viz.py` | Gate, bolts |
| `world_draw.py` | Wells, heatmap |
| `edge_hints.py` | Off-screen markers |
| `explosion_fx.py` | Combat feedback |
| `weapon_projectile_fx.py` | Bolts |
| `health_bar_viz.py` | Enemies/allies if any |
| `hud_overlay.py` | Play HUD |
| `hud_primitives.py` | Shared HUD chrome |
| `view_renderers.py` | Tactical + chase dispatch |
| `chase_fx.py` | Sky, floor, fog |
| `chase_ground.py` | Horizon |
| `chase_wells.py` | Chase wells |
| `chase_entities.py` | Chase entity placement |
| `chase_helm.py` | Cockpit frame |
| `chase_mirror.py` | Rear mirror |
| `chase_projectile_fx.py` | Chase bolts |
| `chase_chart_bounds.py` | Open bounds toast viz |
| `jewel_viz.py` | Pickups |

### Tier 2 — L1 meta loop UI

| File | Used in L1 loop |
|------|-----------------|
| `title_overlay.py` | Title |
| `menu_ui.py` | Buttons |
| `chart_map_overlay.py` | Briefing (Cove inaugural) |
| `level_intro_overlay.py` | Cove GIF |
| `launch_countdown_overlay.py` | Countdown fallback |
| `startup_splash_overlay.py` | Boot |
| `animated_image.py` | GIF loader refactor |

### Tier 3 — Later levels (theme modules)

| Group | Files |
|-------|-------|
| Solar | solar patrol viz paths in enemy_viz, station_viz |
| Drift | drift enemies, chase FX variants, membrane_viz |
| Rift | rift theme branches in chase_fx, squid_viz |
| Siege | siege stations, waves, escorts |
| Brood Moon | brood_* viz (6 files), planet_mission_viz, squid_boss, egg_pod, brood transition |
| Guard (if active) | guard-specific test paths |

### Tier 4 — Shop / meta

| File | Notes |
|------|-------|
| `holo_shop_overlay.py` | Complex; needed for full campaign shop |
| `shop_tree_view.py` | Logic-only — keep |
| `shop_skill_tree_layout.py` | Layout math — keep |

---

## 12. Scene-by-scene migration order

| Order | Scene | Why this order |
|-------|-------|----------------|
| 1 | `PlayScene` (Cove only) | Core fun proof |
| 2 | `EndScene` | Win/loss feedback |
| 3 | `LaunchCountdownScene` | Minimal overlay before intro |
| 4 | `LevelIntroScene` | GIF pipeline proof |
| 5 | `ChartBriefingScene` | Holo map + first deploy UX |
| 6 | `TitleScene` | Full boot + deploy |
| 7 | `StartupSplashScene` | Optional polish |
| 8 | Brood landing overlay in PlayScene | L6-only branch |

**PlayScene first** is intentional: if Cove feels wrong on Pygame, fix DrawContext before porting shop/chart complexity.

---

## 13. Level 1 vertical slice — full loop specification

This is the **mandatory first milestone** before porting L2–L6.

### 13.1 Loop diagram

```
[Launch Pygame app]
       ↓
[StartupSplashScene] — skip if no asset / press Enter
       ↓
[TitleScene]
  - Deploy Cove (key 1 or menu)
  - Esc quits
       ↓
[ChartBriefingScene] — inaugural Cove briefing OR skip if re-deploy
  - Launch button → intro
       ↓
[LevelIntroScene] — cove.gif OR
[LaunchCountdownScene] — if no intro configured
       ↓
[PlayScene level_id="cove"]
  - Tactical ↔ Chase toggle (existing key)
  - Full beacon + gate win
  - Death + life loss
       ↓
[EndScene] — win/loss
  - Enter → chart or title per existing rules
```

### 13.2 Cove play parity requirements

| System | Must work |
|--------|-----------|
| Gravity wells | Pull + heatmap (tactical) |
| Asteroids | Breakup, bounce, combat |
| Curved projectiles | Gravity-affected bolts |
| Beacons | Collect all → gate opens |
| Finish gate | Win state |
| Camera toggle | Tactical + chase |
| Chase HUD | Helm, mirror, speed streaks |
| Edge hints | Gate/beacon off-screen |
| Chart bounds | N/A for Cove (open bounds off) |
| Campaign | Lives, hull, jewels on Cove run |
| Reactor burst | Shift tap boost |

### 13.3 Explicit L1 deferrals (OK for slice)

| Deferred | Reason |
|----------|--------|
| Shop popup on title/chart | Can use direct deploy key |
| L2–L6 deploy keys | Disabled until ported |
| Brood transition cinematic | L6 only |
| Audio | Phase 6 — but stub `AudioBus` no-op in slice |
| Sprite baking / particles upgrade | Phase 7 |

### 13.4 L1 slice exit criteria

See [Appendix C](#appendix-c--cove-l1-acceptance-checklist) — all items checked + 30-minute playtest without crash + pytest green.

---

## 14. Phased rollout (Phases 0–8)

### Phase 0 — Foundation (2–4 days)

**Objective:** DrawContext + dual backend skeleton without changing player-visible behavior on Tk.

Tasks:

- [ ] Add `pygame-ce` to dev dependencies (document in README; optional extras group)
- [ ] Create DrawContext protocol + TkDrawContext
- [ ] Refactor `lit_draw.py` + 3 viz files to use DrawContext
- [ ] Introduce `GameRenderer` protocol; TkRenderer implements it
- [ ] Generalize `SceneHost` in `scenes/base.py`
- [ ] Create empty `pygame_app.py` that opens window and clears to background color
- [ ] CI: pytest still green on Tk path

**Exit:** Tk path identical; Pygame opens blank window with Esc quit.

---

### Phase 1 — Cove play scene on Pygame (5–8 days)

**Objective:** Play Cove end-to-end in Pygame with tactical + chase.

Tasks:

- [ ] Implement PygameDrawContext (full protocol)
- [ ] Port Tier 1 render files (Cove branches only where theme splits)
- [ ] Implement `PygameRenderer.draw_world` mirroring TkRenderer
- [ ] Wire `PlayScene` to Pygame host
- [ ] Minimal in-game HUD (hud_overlay Tier 1)
- [ ] Camera toggle + chase helm/mirror
- [ ] Win/loss overlay text on playfield
- [ ] Manual playtest: full Cove completion

**Exit:** Appendix C items for play scene pass.

---

### Phase 2 — L1 full loop (4–6 days)

**Objective:** Title → briefing → intro → play → end on Pygame.

Tasks:

- [ ] Port Tier 2 overlays (title, chart, intro, countdown, splash)
- [ ] Refactor `animated_image.py` to backend-neutral surfaces
- [ ] Scene transitions via `pygame_app.set_scene`
- [ ] Pointer hit tests on title/chart
- [ ] `EndScene` on Pygame
- [ ] `run_game_pygame.py` entry script

**Exit:** Full Appendix C checklist.

---

### Phase 3 — Remaining levels render parity (8–12 days)

**Objective:** L2–L6 playable on Pygame with theme branches.

Order: **Solar → Drift → Rift → Siege → Brood Moon** (simplest FX → hardest).

Per level:

- [ ] Theme-specific chase_fx / palette branches verified
- [ ] Enemy viz variants
- [ ] Station/siege/brood modules
- [ ] Level-specific playtest script (15 min each)
- [ ] Fix parity bugs before next level

Brood Moon last (surface, orbital, transition overlay).

**Exit:** Campaign deploy 1–6 from title/chart on Pygame.

---

### Phase 4 — Shop and campaign meta (3–5 days)

**Objective:** Holo shop, skill tree, jewel treasury UI on Pygame.

Tasks:

- [ ] Port `holo_shop_overlay.py`
- [ ] Wheel scroll on shop tree
- [ ] Shop open/close animation
- [ ] Campaign persistence unchanged

**Exit:** Buy skill between sectors; effects apply in play.

---

### Phase 5 — Test suite migration (3–5 days)

**Objective:** Replace Tk canvas smoke tests with Pygame equivalents.

Strategy:

- [ ] `tests/render_support/pygame_surface.py` — headless or offscreen `Surface`
- [ ] `tests/render_support/tk_canvas.py` — keep temporarily
- [ ] Parametrize viz smoke tests: `@backend("tk", "pygame")` OR split files
- [ ] Replace `len(canvas.find_all())` assertions with:
  - Draw call counters on DrawContext (test double), OR
  - Pixel sample smoke (center pixel not background), OR
  - Snapshot PNG compare (optional, brittle — avoid initially)

Target: **488+ tests passing** on Pygame backend.

**Exit:** CI runs pytest with `GRAVITY_TEST_BACKEND=pygame`.

---

### Phase 6 — Audio layer (2–4 days)

**Objective:** First-class SFX + music.

Tasks:

- [ ] `AudioBus` + asset folder `assets/audio/sfx/`, `assets/audio/music/`
- [ ] Wire combat, beacon, gate, UI events
- [ ] Cove music bed loop
- [ ] Volume settings in `settings.py` or runtime config

**Exit:** Play Cove with sound; mute key optional.

---

### Phase 7 — Visual perf and juice (ongoing, 3–7 days initial)

**Objective:** Look/feel better than Tk, not just equal.

Tasks:

- [ ] Layered surfaces: static HUD chrome cached
- [ ] Stop full-screen clear where possible (dirty rects optional)
- [ ] Alpha fog Disables stipple hacks
- [ ] Hit flash, small particle bursts on explosions (pygame draw circles)
- [ ] Optional sprite bake for ship/asteroid at N angles

**Exit:** Stable 60 FPS on Brood surface chase; subjective "feels better" vs Tk recording.

---

### Phase 8 — Packaging and Tk retirement (2–3 days)

**Objective:** Ship Pygame as default.

Tasks:

- [ ] PyInstaller spec or briefcase/pyxel-style bundle doc
- [ ] README update: Pygame default, Tk deprecated
- [ ] `run_game.py` dispatches to Pygame
- [ ] Remove or archive `app.py` Tk shell (or keep `run_game_tk.py` one release)
- [ ] Update DEVGOV journal entry

**Exit:** Fresh clone → `pip install -e ".[pygame]"` → `python run_game.py` → full campaign.

---

## 15. Testing strategy

### 15.1 Test categories

| Category | Count (approx) | Port impact |
|----------|----------------|-------------|
| Pure gameplay/sim | ~350 | **None** |
| Render smoke (canvas item count) | ~25 files | **Rewrite** |
| Integration (build_level + step) | ~80 | **None** |
| GIF/intro load | ~10 | **Update loader mocks** |

### 15.2 Test doubles

**DrawContextSpy** for unit tests:

- Records `{method, args}` list
- Assert beacon draw called N times
- No pygame display needed (headless friendly)

### 15.3 Visual regression (optional)

- Manual: record 20s Cove play GIF from Pygame vs Tk
- Semi-auto: save PNG at frame 300; human diff

Do **not** block migration on pixel-perfect snapshot CI initially.

### 15.4 Playtest scripts

Document in `docs/playtest/PYGAME_PORT_CHECKLIST.md` (create during Phase 2):

- 10-minute Cove speedrun
- Chase cam toggle stress
- Death/restart/life loss
- Win → chart → title

---

## 16. Performance and visual upgrade path

### 16.1 Known Tk pain points to fix in Pygame

| Issue | Pygame remedy |
|-------|---------------|
| `canvas.delete("all")` every frame | Retained playfield surface |
| Thousands of oval fog rings | Alpha gradient texture blit |
| Heatmap cell spam | Same draw logic + surface cache per frame |
| GIF reload / PhotoImage GC | Pre-converted Surfaces at load |

### 16.2 Frame budget targets

| Scene | Target FPS | Notes |
|-------|------------|-------|
| Cove tactical | 60 | Baseline |
| Drift chase | 60 | Many streaks |
| Brood surface chase | 45–60 | Prop caps already exist — enforce |

### 16.3 Memory

- GIF frames: ~6 sectors × ~30 frames × 960×640 RGBA — acceptable on desktop; subsample at load as today.

---

## 17. Packaging, dependencies, and CI

### 17.1 Dependencies

**Production (Pygame path):**

```
pygame-ce>=2.4
```

**Optional:**

```
Pillow>=10  # GIF load quality + resize (already optional in Tk path)
```

**Stdlib-only goal:** Pygame path will **require pygame-ce** — acceptable trade for ship.

### 17.2 pyproject.toml / setup (recommended)

```toml
[project.optional-dependencies]
pygame = ["pygame-ce>=2.4", "Pillow>=10"]
dev = ["pytest", "ruff", ...]
```

### 17.3 CI matrix

| Job | Command |
|-----|---------|
| gameplay | `pytest -k "not viz"` (no display) |
| render pygame | `pytest tests/test_chase_fx.py ...` with `SDL_VIDEODRIVER=dummy` |
| render tk (interim) | optional parallel job until Phase 8 |

### 17.4 Distribution

- **itch.io:** zip with `run_game.exe` + assets
- **GitHub releases:** same
- Document Python 3.11+ Windows/macOS/Linux

---

## 18. Risk register and mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| DrawContext parity gaps (ellipse thickness, dash) | Medium | Implement `_dash_ring_segments` once; oval glow as multi-circle |
| Font metrics shift HUD layout | Medium | Golden-master screenshot Cove HUD; nudge constants |
| GIF load without Pillow | Low | Require Pillow for Pygame path OR pre-bake PNG sequences |
| Headless CI pygame display | Medium | `SDL_VIDEODRIVER=dummy`; DrawContextSpy for unit tests |
| Dual maintenance fatigue | High | Time-box Tk; delete after Phase 8 |
| Scope creep (rewrite gameplay) | High | Lock gameplay PRs during port |
| Brood L6 parity delays ship | Medium | Brood last; L1 slice stands alone |
| Performance regression | Low | Profile Brood chase before/after |
| Agent-generated inconsistent draw API | Medium | DrawContext protocol is single choke point; ruff + review |

---

## 19. Rollback and dual-backend strategy

### During migration (Phase 0–7)

- Tk remains default entry in `run_game.py`
- Pygame via `run_game_pygame.py`
- Shared gameplay code — only render differs

### Cutover (Phase 8)

- Flip default to Pygame
- Keep `run_game_tk.py` for one release tag `v0.x-tk-legacy`

### If Pygame blocked

- DrawContext on Tk means **no throwaway work** — port proceeds incrementally even if Pygame pauses

---

## 20. Timeline estimates (solo + agent)

| Phase | Calendar time | Cumulative |
|-------|---------------|------------|
| 0 Foundation | 2–4 days | ~4 days |
| 1 Cove play | 5–8 days | ~12 days |
| 2 L1 full loop | 4–6 days | ~18 days |
| 3 L2–L6 parity | 8–12 days | ~30 days |
| 4 Shop meta | 3–5 days | ~35 days |
| 5 Tests | 3–5 days | ~40 days |
| 6 Audio | 2–4 days | ~44 days |
| 7 Juice/perf | 3–7 days | ~51 days |
| 8 Package/cutover | 2–3 days | **~6–8 weeks** |

**L1 test loop (Phases 0–2): ~2.5–3 weeks** at current velocity with agent assist.

Aggressive: L1 slice in 10 days if scope ruthlessly held.

---

## 21. Definition of done — full port complete

- [ ] `python run_game.py` uses Pygame CE by default
- [ ] Full campaign L1–L6 deployable from title/chart
- [ ] Tactical + chase on all levels
- [ ] Shop, jewels, lives, drone wingman UI working
- [ ] GIF intros + splash + countdown + brood transition
- [ ] Audio bus with Cove + combat SFX minimum
- [ ] 488+ pytest green on Pygame render backend
- [ ] README updated; Tk documented as removed/legacy
- [ ] One playable build artifact uploaded (itch or Releases)
- [ ] 60-minute full campaign playtest without crash
- [ ] DEVGOV journal entry: migration complete

---

## 22. Anti-patterns — do not do these

1. **Big-bang rewrite** — porting all 55 files before L1 loop runs.
2. **Gameplay “while we're at it” tweaks** — freeze mechanics during port.
3. **Unity/Godot pivot** — loses velocity and tests.
4. **Buying 3D assets** — wrong genre; keep lit 2D.
5. **Shader rabbit hole before audio** — audio is cheaper and louder.
6. **Deleting Tk before L1 slice passes** — removes safety net.
7. **Pixel-perfect snapshot CI on day one** — slows migration.
8. **New level content (L7+)** — finish port first.
9. **Embedding pygame in Tk window** — worst of both worlds; pick one loop.
10. **Skipping DrawContext** — leads to `#ifdef pygame` chaos in every viz file.

---

## Appendix A — Tk-coupled file list

Render modules importing tkinter (migrate in tier order):

```
app.py
render/tk_renderer.py
render/pygame_renderer.py          [to create]
render/lit_draw.py
render/view_renderers.py
render/world_draw.py
render/light_compose.py
render/hud_overlay.py
render/hud_primitives.py
render/menu_ui.py
render/title_overlay.py
render/chart_map_overlay.py
render/holo_shop_overlay.py
render/level_intro_overlay.py
render/launch_countdown_overlay.py
render/startup_splash_overlay.py
render/brood_moon_transition_overlay.py
render/animated_image.py
render/ship_viz.py
render/asteroid_viz.py
render/beacon_viz.py
render/entity_viz.py
render/enemy_viz.py
render/station_viz.py
render/station_lit_draw.py
render/drone_viz.py
render/squid_viz.py
render/squid_boss_viz.py
render/egg_pod_viz.py
render/jewel_viz.py
render/health_bar_viz.py
render/explosion_fx.py
render/weapon_projectile_fx.py
render/chase_fx.py
render/chase_ground.py
render/chase_wells.py
render/chase_entities.py
render/chase_helm.py
render/chase_mirror.py
render/chase_projectile_fx.py
render/chase_chart_bounds.py
render/edge_hints.py
render/planet_mission_viz.py
render/brood_moon_surface_viz.py
render/brood_geology_viz.py
render/brood_flora_viz.py
render/brood_ambient_viz.py
render/membrane_viz.py
scenes/play.py                     [tk import for transition — refactor]
```

---

## Appendix B — Portable file list (do not rewrite)

```
core/*
gameplay/*          (except any future audio event hooks — additive only)
levels/*
narrative/level_intros.py, launch_countdown.py, startup_splash.py
scenes/game_flow.py, play_session.py, shop_ui.py (logic), end.py (logic)
render/camera.py
render/palette.py
render/lighting.py
render/chase_threat.py
render/shop_tree_view.py
render/shop_skill_tree_layout.py
util/timekeeper.py
settings.py
tests/*             (gameplay tests unchanged)
```

---

## Appendix C — Cove L1 acceptance checklist

Use this to sign off Phase 2 (full L1 loop on Pygame).

### Boot and navigation

- [ ] App launches without PYTHONPATH hacks (documented install)
- [ ] Startup splash displays and skips on Enter (if enabled)
- [ ] Title screen renders ship demo + menu chrome
- [ ] Deploy Cove reaches play scene
- [ ] Esc from title quits cleanly
- [ ] Chart briefing renders map + Cove labels (inaugural flow)
- [ ] Launch from chart reaches intro/countdown

### Narrative

- [ ] Cove GIF intro animates frame timing correctly
- [ ] Skip/Enter advances to play (match Tk behavior)
- [ ] Launch countdown 3-2-1 displays if no GIF

### Cove gameplay

- [ ] Ship thrust, rotate, fire respond identically
- [ ] Reactor burst (Shift tap) works once per tap
- [ ] Gravity wells pull ship and curve bolts
- [ ] Asteroids collide, break, damage ship
- [ ] All beacons required before gate opens
- [ ] Gate win triggers WON status + overlay
- [ ] Death triggers life loss + restart (R) + Esc to title
- [ ] Camera toggle tactical ↔ chase with HUD flash
- [ ] Chase: helm frame, mirror, horizon, floor gradient visible
- [ ] Tactical: heatmap reasonable density (no purple slab bugs)
- [ ] Edge hints for gate/beacons when off-screen
- [ ] Jewels drop and increment campaign treasury (if Cove drops jewels)
- [ ] FPS ≥ 55 average on Cove chase (informal overlay or log)

### End state

- [ ] **Cove win → Solar ChartBriefing** (NOT EndScene) with cleared banner
- [ ] Loss with life lost → EndScene with correct copy + retry → countdown → play
- [ ] Game over → EndScene; Enter → title
- [ ] Esc from play → title; campaign jewels/lives preserved where Tk preserves them

### Engineering

- [ ] `pytest` ≥ 488 pass (Tk and/or Pygame backend per Phase)
- [ ] No tkinter import in `pygame_app.py` hot path
- [ ] Gameplay tests unchanged and green
- [ ] Known Phase 2 deferrals documented (shop popup OK to skip)

---

# Part II — L1 full game loop (final planning)

This section is the **implementation-ready** plan for the first Pygame CE milestone: a player can boot the Pygame build, navigate the same pre-play flow as Tk, complete **Smuggler's Cove**, and land in the post-win campaign transition — with no Tk imports on the hot path.

**Relationship to Part I:** Part I Phases 0–2 map to Part II work packages WP-00 through WP-12. Do not start L2–L6 until [Section 37](#37-l1-final-sign-off-gates) gates pass.

---

## 26. L1 scope lock — what “full loop” means

### 26.1 In scope (L1-FULL)

| ID | Requirement |
|----|-------------|
| L1-F-01 | Pygame app entry: `run_game_pygame.py` |
| L1-F-02 | `StartupSplashScene` → `TitleScene` boot path |
| L1-F-03 | Title deploy Cove via UI click, Enter on deploy page, or key `1` |
| L1-F-04 | `ChartBriefingScene` for Cove (inaugural holo map) |
| L1-F-05 | Chart Launch → `LevelIntroScene` (cove.gif) |
| L1-F-06 | Intro finish/skip → `LaunchCountdownScene` (3-2-1) |
| L1-F-07 | Countdown finish/skip → `PlayScene` Cove live |
| L1-F-08 | Full Cove sim: wells, asteroids, beacons, gate, combat, lives |
| L1-F-09 | Tactical + chase camera toggle (`V`) |
| L1-F-10 | Win → auto `ChartBriefingScene` for **Solar** (cleared Cove) — matches Tk today |
| L1-F-11 | Death with life remaining → hull chip + in-place recovery (no EndScene) |
| L1-F-12 | Death with life lost → `EndScene` loss; retry → countdown → play |
| L1-F-13 | Campaign game over → `EndScene`; Enter → title |
| L1-F-14 | Play `R` restart, `Esc` → title |
| L1-F-15 | Chart/title `Esc` / back navigation |
| L1-F-16 | All gameplay pytest green (no sim changes) |
| L1-F-17 | Render smoke tests updated or duplicated for Pygame backend |
| L1-F-18 | All player screens S1–S17 (Section 38) implemented |
| L1-F-19 | GIF load + playback + skip paths (Section 39) |
| L1-F-20 | All five title pages + deploy list (Section 40) |
| L1-F-21 | Inaugural Cove chart + post-win Solar chart (Section 41) |
| L1-F-22 | Master test matrix L1-T-001–065 executed (Section 42) |
| L1-F-23 | QA Playbooks A/B/C logged (Section 43) |

### 26.2 In scope — shop (L1-FULL-B, same milestone)

Title and chart both wire holo shop today. Full loop **includes** shop if time allows in WP-11; otherwise ship L1-FULL-A first (shop buttons show “coming soon” toast) and complete shop before sign-off.

| ID | Requirement |
|----|-------------|
| L1-F-24 | `B` opens/closes shop on title and chart |
| L1-F-25 | Shop tree render + scroll wheel |
| L1-F-26 | Purchase with jewels updates `CampaignState` |

### 26.3 Explicitly out of scope for L1 milestone

| ID | Deferred to Part I Phase 3+ |
|----|----------------------------|
| L1-O-01 | Deploy Solar–Brood from title (keys 2–6 may show “Pygame: Cove only” toast) |
| L1-O-02 | Brood landing cinematic branch in `PlayScene` |
| L1-O-03 | Audio bus (stub no-op OK) |
| L1-O-04 | PyInstaller / itch build |
| L1-O-05 | Visual upgrades beyond Tk parity (particles, sprite bake) |
| L1-O-06 | EndScene win path for final campaign level (Cove win uses chart transition, not EndScene) |
| L1-O-07 | Launch Solar from post-win chart S15 (map preview only; Esc/title OK) |

### 26.4 Parity standard

**Behavioral parity with Tk**, not pixel-perfect parity. HUD text may shift ±2 px with font metrics. Colors, timing, transitions, and game outcomes must match.

---

## 27. Complete scene FSM and transition table

### 27.1 Primary happy path (first-time Cove)

```
StartupSplashScene
  │ skip debounce / end of GIF
  ▼
TitleScene (WELCOME → DEPLOY)
  │ level:cove click OR key 1 OR Enter on deploy
  ▼
ChartBriefingScene (upcoming=cove, cleared=None)
  │ launch hit OR Enter
  ▼
LevelIntroScene (cove.gif)
  │ timer OR skip OR Enter/Space/Esc
  ▼
LaunchCountdownScene (3-2-1, playfield reveal)
  │ timer OR Enter/Space
  ▼
PlayScene (level_id=cove)
  │ GameStatus.WON (all beacons + gate)
  ▼
ChartBriefingScene (upcoming=solar, cleared=cove)  ← NOT EndScene
```

### 27.2 Failure and branch paths

```
PlayScene
  │ SHIP_HIT + life lost
  ▼
EndScene (won=False, game_over=?)
  │ Enter → retry: LaunchCountdownScene(cove)
  │ Esc → TitleScene (fresh campaign default on title — match Tk)

PlayScene
  │ SHIP_HIT + hull chip only
  ▼
PlayScene (in-place recovery, hud_alert flash)

PlayScene
  │ Esc
  ▼
TitleScene(campaign preserved)

PlayScene
  │ R
  ▼
PlayScene (fresh start_play — new session)

ChartBriefingScene
  │ back_title OR Esc (no shop)
  ▼
TitleScene(campaign preserved)

LevelIntroScene
  │ load failure
  ▼
LaunchCountdownScene (fallback — existing behavior)
```

### 27.3 Scene → renderer method map

| Scene | Renderer calls per frame |
|-------|--------------------------|
| `StartupSplashScene` | `draw_startup_splash(frame_image, …)` |
| `TitleScene` | `draw_title(page, campaign, …, shop_view?)` |
| `ChartBriefingScene` | `draw_chart_briefing(world, field, …)` |
| `LevelIntroScene` | `draw_level_intro(level_id, spec, frame_image, …)` |
| `LaunchCountdownScene` | `draw_launch_countdown(session, reveal, digit, …)` |
| `PlayScene` | `draw_world(world, campaign, camera, field, …)` |
| `EndScene` | `draw_end(won, elapsed, reason, …)` |

### 27.4 Hit-test methods required on GameRenderer

| Method | Used by |
|--------|---------|
| `title_hit_test(x, y)` | TitleScene |
| `chart_hit_test(x, y)` | ChartBriefingScene |
| `level_intro_hit_test(x, y)` | LevelIntroScene |
| `end_hit_test(x, y)` | EndScene |

---

## 28. GameRenderer API contract (Pygame parity)

`PygameRenderer` must implement the same public surface as `TkRenderer`. Internal storage: `screen: pygame.Surface`, `AssetCache`, sub-renderers unchanged.

### 28.1 Lifecycle

| Method | Behavior |
|--------|----------|
| `clear()` | Fill screen with `#08111f` or scene-specific bg; do not recreate display |
| `flip()` | Called by app shell after scene draw — **not** on renderer (app owns `display.flip()`) |

### 28.2 Draw methods (complete list for L1)

| Method | Parameters (summary) | Notes |
|--------|------------------------|-------|
| `draw_title` | page, campaign, deploy_focus, hover_id, elapsed, shop_* | Includes demo ship lambda internally on Tk; Pygame uses same callback pattern |
| `draw_chart_briefing` | world, field, campaign, upcoming_level_id, cleared_level_id, elapsed, hover_id, anim, shop_* | Builds preview via `build_level` in scene — renderer read-only |
| `draw_level_intro` | level_id, spec, frame_image, elapsed, playback_seconds, progress, hover_id | `frame_image` becomes `pygame.Surface` |
| `draw_startup_splash` | frame_image, elapsed, playback_seconds, progress, show_skip_hint | Full-screen GIF frame |
| `draw_launch_countdown` | session, reveal, digit, step_index, digits, step_elapsed, step_seconds, total_elapsed, total_seconds | **Composite:** `draw_world` + reveal mask + digit strip |
| `draw_world` | world, campaign, camera, gravity_field, hud_alert, bounds_toast_*, treasury_flash_ttl | Dispatches tactical vs chase |
| `draw_end` | won, elapsed, reason, level_id, campaign, game_over, hover_id | Inline in tk_renderer today — extract to `end_overlay.py` during port |

### 28.3 Asset loader host

Replace `host.renderer.canvas` (Tk master) with `host.renderer.asset_host` or `AssetCache` singleton:

| Current (Tk) | Target (Pygame) |
|--------------|-----------------|
| `AnimatedImageSequence.load(..., master=canvas)` | `AnimatedImageSequence.load(..., cache=asset_cache)` → `list[pygame.Surface]` |
| `PhotoImage` frame | `pygame.Surface` with alpha |
| GC hold `canvas._hold = frame` in tests | Cache strong refs on scene or cache |

### 28.4 DrawContext ownership

Each frame:

1. `PygameRenderer` creates `PygameDrawContext(screen)` at draw start.
2. Passes `ctx` to overlays and view renderers (not raw `screen`).
3. Optional: separate `hud_surface` blitted at fixed y=0 if optimizing later — **not required for L1**.

---

## 29. Scene-by-scene final specification

### 29.1 StartupSplashScene

**Source:** `scenes/startup_splash.py`  
**Logic changes:** None — only loader host.

| Concern | Detail |
|---------|--------|
| Asset | `assets/narrative/startup.gif` via `startup_asset_path()` |
| Skip | After `SKIP_DEBOUNCE_SECONDS`; click / Enter / Space / Esc |
| Failure | Missing asset → immediate `TitleScene` |
| Draw | Full viewport 960×640 frame centered |
| Pygame test | `tests/test_startup_splash.py` — load sequence without Tk root |

### 29.2 TitleScene

**Source:** `scenes/title.py`  
**Logic changes:** None.

| Concern | Detail |
|---------|--------|
| Pages | `TitlePage.WELCOME`, `DEPLOY`, others in `TITLE_PAGE_ORDER` |
| Cove launch | `level:cove` hit, key `1`, Enter on DEPLOY with focus on cove (index 0) |
| Demo ship | Renderer draws animated ship at title — uses `draw_friendly_fighter_ship` or title lambda |
| Shop | Modal overlay; blocks level launch while open |
| Keys 2–6 | L1-FULL: may call `_launch_level` but Pygame build should guard with toast if Solar+ not ported OR allow chart preview only for Cove |
| **Recommendation** | Only `is_level_selectable("cove")` path fully wired; others show dimmed + tooltip “Sector port pending” |

### 29.3 ChartBriefingScene

**Source:** `scenes/chart_briefing.py`  
**Logic changes:** None.

| Concern | Detail |
|---------|--------|
| Preview world | `build_level(upcoming_level_id)` — for Cove inaugural, `cove` layout baked into field |
| Map transform | Strip vs full map based on aspect — Cove uses standard 4800×3200 tactical map |
| Hit IDs | `launch`, `back_title`, `shop_open`, `shop_close`, shop tree ids |
| Launch | → `start_level_intro(cove, campaign)` |
| Cleared banner | When `cleared_level_id=cove` post-win, shows sector cleared copy |
| Cove-specific map content | Wells, asteroids, beacons, gate glyph — no brood/siege entities |

### 29.4 LevelIntroScene

**Source:** `scenes/level_intro.py`  
**Logic changes:** Replace `master=host.renderer.canvas` → `cache=host.renderer.assets`.

| Concern | Detail |
|---------|--------|
| Cove spec | `header_tag="ENEMY SPACE · CAPTAIN'S LOG"`, asset `cove.gif` |
| Playback | GIF duration via `resolve_playback_seconds` |
| Skip hit | `skip_intro` region |
| Advance | → `start_launch_countdown` (not direct play) |
| Overlay | `level_intro_overlay.py` — progress bar, header/footer text |

### 29.5 LaunchCountdownScene

**Source:** `scenes/launch_countdown.py`  
**Logic changes:** None.

| Concern | Detail |
|---------|--------|
| Session | `build_play_session(cove)` on enter — world live but input ignored until play |
| Cove countdown | Default 3-2-1 @ 1.0s per digit (`LaunchCountdownSpec`) |
| Draw stack | (1) Full playfield dim world (2) reveal wipe (3) digit strip |
| Skip | Enter / Space → `PlayScene.from_session` |
| Importance | Proves play renderer before input — visual stress test |

### 29.6 PlayScene (Cove)

**Source:** `scenes/play.py`  
**Logic changes:**

| Change | Reason |
|--------|--------|
| Remove `import tkinter` | Brood cinematic only — guard with `if False` or extract loader |
| Replace `host.renderer.canvas` in `_ensure_transition_sequence` | Use AssetCache; **Cove never hits this path** |
| No other logic changes | Sim, camera, campaign wiring unchanged |

| Concern | Detail |
|---------|--------|
| Session | `play_session.build_play_session("cove", campaign)` |
| Theme | `level_theme == "cove"` (default palette) |
| Open bounds | Cove: **closed** — no chart bounds toast |
| Camera default | Tactical; `V` toggles chase |
| Win | `record_level_cleared("cove")` → chart for solar |
| Restart | `R` → `start_play("cove", campaign)` |
| Draw | `draw_world` only (no brood branch) |

### 29.7 EndScene

**Source:** `scenes/end.py`  
**Logic changes:** None.

| Concern | Detail |
|---------|--------|
| Cove loss | Retry → countdown → play |
| Game over | Enter → title (new campaign on title — match Tk) |
| Cove win | **Not shown** — win routes to chart |
| Hit IDs | `action_retry`, `action_next`, `action_title` |

---

## 30. Cove playfield — content and draw pipeline

### 30.1 Cove world contents (from `build_cove_run_level`)

Document for parity testing — verify all render paths touched:

| Entity | Expected render module |
|--------|------------------------|
| Gravity wells | `world_draw.draw_well`, chase wells |
| Gravity heatmap | `world_draw.draw_gravity_heatmap` |
| Asteroids (tiered) | `asteroid_viz`, lit_draw |
| Beacons | `beacon_viz`, entity markers |
| Finish gate | `entity_viz.draw_gate_portal` |
| Player ship | `ship_viz` |
| Projectiles | `weapon_projectile_fx`, chase variant |
| Explosions | `explosion_fx` |
| Jewels (if dropped) | `jewel_viz` |
| Edge hints | `edge_hints` (gate, beacons) |
| Enemies | Cove may have minimal/none — verify registry |
| Drone wingman | If purchased in shop — optional for L1 |

### 30.2 Tactical draw order (Cove)

Order enforced in `TacticalViewRenderer.draw`:

1. Playfield background rect (`palette.BACKGROUND`)
2. Ambient depth (Cove — not dense starfield)
3. Gravity heatmap
4. Wells (before asteroids for occlusion)
5. Asteroids (viewport culled)
6. Beacons, gate
7. Jewels, explosions, projectiles
8. Ship
9. Allies/enemies if any
10. Edge hints
11. *(HUD chrome drawn by TkRenderer after view renderer)*

### 30.3 Chase draw order (Cove)

Order in `PerspectiveViewRenderer.draw`:

1. `draw_chase_sky`
2. Floor gradient / chase ground
3. Chase wells, entities (depth sorted)
4. Chase projectiles + FX
5. Speed streaks, fog glows
6. Chase helm frame + mirror
7. Ship in perspective
8. Edge hints (chase mode)
9. HUD playfield chrome + status overlay

### 30.4 HUD layers (both modes)

From `TkRenderer.draw_world` tail:

1. `SciFiHudOverlay.draw_playfield_chrome`
2. `SciFiHudOverlay.draw` — lives, hull, jewels, weapons, alerts
3. Win overlay text `"YOU ESCAPED"` when `GameStatus.WON` (brief frame before scene swap)

### 30.5 Cove-specific palette tokens

From `palette.py` — verify no solar/rift/brood branch misfires:

- `BACKGROUND`, `HUD_ACCENT`, `WELL`, `GATE_OPEN`, `CHASE_FOG_*`, `BEACON_*`

---

## 31. Input matrix — every key and pointer per scene

### 31.1 Global

| Input | App shell |
|-------|-----------|
| Quit | Window close → `pygame.QUIT` |
| Alt+Tab | OS default |

### 31.2 StartupSplashScene

| Key / pointer | Action |
|---------------|--------|
| Enter / Space / Esc | Skip (after debounce) |
| Click | Skip (after debounce) |

### 31.3 TitleScene

| Key / pointer | Action |
|---------------|--------|
| Enter | WELCOME→DEPLOY; DEPLOY→launch focused level |
| Esc | *(no op on title today — Pygame: optional quit confirm)* |
| 1 | Launch Cove |
| 2–6 | Launch if selectable (guard in L1 Pygame build) |
| Tab / arrows | Page navigate / deploy focus |
| B | Toggle shop |
| Click | Hit test: tabs, level tiles, shop, goto_deploy |
| Wheel | Shop scroll when open |

### 31.4 ChartBriefingScene

| Key / pointer | Action |
|---------------|--------|
| Enter | Launch intro |
| Esc | Back title OR close shop |
| B | Toggle shop |
| Click | launch, back_title, shop |
| Wheel | Shop scroll |

### 31.5 LevelIntroScene

| Key / pointer | Action |
|---------------|--------|
| Enter / Space / Esc | Skip to countdown |
| Click skip region | Skip |

### 31.6 LaunchCountdownScene

| Key / pointer | Action |
|---------------|--------|
| Enter / Space | Skip to play |

### 31.7 PlayScene

| Key / pointer | Action |
|---------------|--------|
| A/D, arrows | Rotate |
| W / Up | Thrust |
| Shift tap | Reactor burst |
| Space | Fire |
| V | Camera toggle |
| R | Restart level |
| Esc | Title |
| E hold | Interaction (if Cove has interactables — verify) |

### 31.8 EndScene

| Key / pointer | Action |
|---------------|--------|
| Enter | Retry / next chart / title per FSM |
| Esc | Title |
| Click | action_retry, action_next, action_title |

### 31.3 Pygame key normalization

Extend `util/input.py` OR add `util/pygame_input.py`:

| pygame constant | normalize_key output |
|-----------------|----------------------|
| `K_a`, `K_LEFT`, etc. | same as Tk keysym today |
| `K_LSHIFT`, `K_RSHIFT` | `shift_l`, `shift_r` |
| `K_RETURN` | `return` |
| `K_ESCAPE` | `escape` |

Scenes continue to receive `keysym: str` — **no scene edits for key names**.

---

## 32. L1 asset manifest

### 32.1 Narrative GIFs (required)

| File | Scene |
|------|-------|
| `assets/narrative/startup.gif` | Startup (optional if missing) |
| `assets/narrative/cove.gif` | Level intro |

### 32.2 Fonts (recommended)

| File | Use |
|------|-----|
| `assets/fonts/CourierPrime-Bold.ttf` | HUD headers (or sysfont fallback) |
| `assets/fonts/CourierPrime-Regular.ttf` | Body |

Ship open-font OFL — download once, commit to repo.

### 32.3 Audio (stub for L1)

| File | Status |
|------|--------|
| `assets/audio/` | Empty dir + `AudioBus` no-op |

### 32.4 Code-generated art (no files)

Ships, asteroids, wells, HUD chrome — all DrawContext primitives.

---

## 33. Scene code changes (Tk decoupling)

Minimal edits — **scenes stay backend-blind**.

| File | Change |
|------|--------|
| `scenes/base.py` | `SceneHost.renderer: GameRenderer` protocol |
| `scenes/level_intro.py` | `AnimatedImageSequence.load(..., cache=host.renderer.assets)` |
| `scenes/startup_splash.py` | Same loader change |
| `scenes/play.py` | Remove tk import; brood cinematic uses cache; Cove path untouched |
| `render/animated_image.py` | Backend-neutral `SurfaceSequence` + Tk/Pygame loaders |
| `app.py` | Unchanged during L1 |
| `pygame_app.py` | **New** — implements SceneHost with PygameRenderer |

**Rule:** No `import pygame` in `scenes/` except none — pygame stays in `render/backends/` and `pygame_app.py`.

---

## 34. L1 work packages — dependency graph

```
WP-00 DrawContext protocol + TkDrawContext
  └─► WP-01 PygameDrawContext (unit tested)
        └─► WP-02 AssetCache + SurfaceSequence GIF loader
              └─► WP-03 PygameRenderer skeleton + GameRenderer protocol
                    ├─► WP-04 pygame_app shell + input bridge
                    ├─► WP-05 lit_draw + core viz (ship, asteroid, well, beacon, gate)
                    │     └─► WP-06 view_renderers tactical/chase Cove path
                    │           └─► WP-07 hud_overlay + chase helm/mirror/fx
                    │                 └─► WP-08 PlayScene vertical (countdown + play)
                    ├─► WP-09 end_overlay + EndScene draw
                    ├─► WP-10 intro + splash overlays
                    └─► WP-11 title + chart overlays
                          └─► WP-12 Full loop wiring + shop (optional B)
                                └─► WP-13 L1 test pass + sign-off
```

### WP details (acceptance per package)

| WP | Deliverable | Done when |
|----|-------------|-----------|
| **WP-00** | `draw_context.py`, `tk_draw.py`; `lit_draw` migrated | Tk Cove still runs; pytest green |
| **WP-01** | `pygame_draw.py` with polygon/line/oval/text/image | Spy tests assert call list |
| **WP-02** | GIF → list[Surface]; font cache | cove.gif loads headless |
| **WP-03** | `game_renderer.py`, `pygame_renderer.py` stub methods | Blank pygame window |
| **WP-04** | `pygame_app.py`, `run_game_pygame.py`, key map | Esc quits; empty scene |
| **WP-05** | Tier-1 entity viz on PygameDrawContext | Static screenshot: ship+rock+well |
| **WP-06** | `TacticalViewRenderer` + `PerspectiveViewRenderer` take DrawContext | Cove world visible frozen |
| **WP-07** | HUD + chase chrome | Countdown scene full composite |
| **WP-08** | Play + countdown scenes on Pygame | Playable Cove sim |
| **WP-09** | `draw_end` extracted + ported | Loss → end screen |
| **WP-10** | Splash + intro | GIF plays |
| **WP-11** | Title + chart | Deploy Cove from UI |
| **WP-12** | Scene FSM complete | Happy path end-to-end |
| **WP-13** | Tests + checklist | Section 37 gates |

---

## 35. L1 day-by-day implementation schedule

**18 working days** (solo + agent, ~3–4 h focused/day). Adjust if shop (WP-11B) adds 2 days.

| Day | WP | Tasks |
|-----|-----|-------|
| **D1** | WP-00 | DrawContext protocol; TkDrawContext; migrate `lit_draw.py` |
| **D2** | WP-00 | Migrate `ship_viz`, `asteroid_viz`, `beacon_viz`; pytest Tk green |
| **D3** | WP-01 | PygameDrawContext full; headless surface tests |
| **D4** | WP-02–03 | AssetCache, GIF loader, PygameRenderer stub, GameRenderer protocol |
| **D5** | WP-04 | pygame_app event loop, input bridge, SceneHost wired |
| **D6** | WP-05 | well, entity, explosion, projectile viz |
| **D7** | WP-06 | view_renderers Cove branches; gravity heatmap |
| **D8** | WP-07 | chase_fx, helm, mirror, edge_hints; hud_overlay |
| **D9** | WP-08 | draw_world integration; LaunchCountdownScene |
| **D10** | WP-08 | PlayScene live — manual Cove playtest starts |
| **D11** | WP-08 | Camera toggle, win→chart transition, death paths |
| **D12** | WP-09 | EndScene draw + retry flow |
| **D13** | WP-10 | Startup + LevelIntro overlays |
| **D14** | WP-11 | Title overlay + hit tests |
| **D15** | WP-11 | Chart map overlay + hit tests |
| **D16** | WP-12 | Full loop polish; keys 2–6 guard; dev unlock behavior |
| **D17** | WP-11B | Holo shop overlay (if committed to L1-FULL-B) |
| **D18** | WP-13 | Test migration, Appendix C checklist, side-by-side Tk comparison |

**Buffer D19–D20:** Font metric fixes, heatmap perf, chase FPS tuning.

---

## 36. L1 test and parity verification plan

### 36.1 Automated tests (must pass)

| Suite | Action |
|-------|--------|
| All non-render tests | Run unchanged — **zero edits expected** |
| `test_cove_*`, `test_world`, `test_gravity*` | Gate on every WP merge |
| Render smoke | Add `tests/render_support/pygame_ctx.py` |

### 36.2 New tests for L1

| Test file | Purpose |
|-----------|---------|
| `tests/test_draw_context.py` | Spy records polygon/line counts |
| `tests/test_pygame_assets.py` | Load cove.gif → Surfaces headless |
| `tests/test_pygame_renderer_smoke.py` | `build_level("cove")` + one draw frame no throw |
| `tests/test_l1_loop_scenes.py` | Scene FSM unit tests (mock renderer) |

### 36.3 Render smoke migration pattern

Replace:

```text
len(canvas.find_all()) > N
```

With:

```text
DrawContextSpy.call_count("polygon") > N
```

OR pygame surface `get_at(center) != BACKGROUND_RGB` after draw.

### 36.4 Manual parity script (30 min)

Record checklist session in `docs/playtest/PYGAME_L1_SESSION.md`:

1. Boot Pygame → splash skip → title
2. Deploy Cove via click path (not key 1)
3. Chart → launch → watch full GIF → countdown
4. Play tactical: collect all beacons, open gate
5. Confirm solar chart appears (not end screen)
6. Esc → title → key 1 quick deploy → chase cam win
7. Intentional death → end → retry
8. R restart mid-level
9. Compare side-by-side screenshot with Tk at frame: chase mid-cove

### 36.5 Performance check

| Metric | Target |
|--------|--------|
| Cove tactical FPS | ≥ 58 avg |
| Cove chase FPS | ≥ 55 avg |
| Frame time spike on explosion | < 25 ms |

Log via optional `settings.DEBUG_FPS` flag in pygame_app.

---

## 37. L1 final sign-off gates

**All must pass before starting L2 (Solar) port.**

### Gate A — Loop completeness

- [ ] Happy path D1–D18 complete without crash
- [ ] **Playbooks A + B + C** (Section 43) executed and logged
- [ ] All screens S1–S17 reachable (Section 38) except S0
- [ ] Win routes to Solar chart with `cleared_level_id=cove`
- [ ] Loss → EndScene → retry works
- [ ] All Appendix C + Section 42 critical manual tests checked

### Gate B — Engineering

- [ ] `pytest` ≥ 488 pass
- [ ] New pygame smoke tests ≥ 4 pass
- [ ] No `import tkinter` in `pygame_app.py`, `pygame_renderer.py`, `pygame_draw.py`
- [ ] `run_game_pygame.py` documented in README

### Gate C — Parity

- [ ] Same beacon count, gate win, life loss on identical inputs (replay test optional)
- [ ] Camera toggle preserves ship position within 1 px tolerance
- [ ] GIF intro duration within ±0.2 s of Tk

### Gate D — Scope

- [ ] Keys 2–6 behavior documented (blocked or toast)
- [ ] Shop: either L1-FULL-B complete OR documented deferral with issue link
- [ ] Audio stub present; no regression if files missing

### Gate E — Maintainability

- [ ] DrawContext used by all Tier-1 files in Section 11
- [ ] `GameRenderer` protocol typed in `render/game_renderer.py`
- [ ] DEVGOV journal entry for L1 milestone

**Sign-off owner:** Project lead playtest + green CI.

---

## 38. Complete player screen inventory (L1)

Every **distinct screen** the player can see in the L1 Pygame build. Each row must render and transition correctly before L1 sign-off.

| # | Screen ID | Scene | Overlay module | First seen |
|---|-----------|-------|----------------|------------|
| S0 | `FRAME_ERROR` | any (crash) | inline pygame_app | On draw exception |
| S1 | `STARTUP_SPLASH` | StartupSplashScene | `startup_splash_overlay.py` | App boot if `startup.gif` exists |
| S2 | `TITLE_WELCOME` | TitleScene | `title_overlay.py` | After splash or boot |
| S3 | `TITLE_MISSION` | TitleScene | same | Tab MISSION / page next |
| S4 | `TITLE_HELM` | TitleScene | same | Tab CONTROLS |
| S5 | `TITLE_COMBAT` | TitleScene | same | Tab COMBAT |
| S6 | `TITLE_DEPLOY` | TitleScene | same | goto_deploy / Enter |
| S7 | `TITLE_SHOP` | TitleScene | `holo_shop_overlay.py` | Key B (L1-FULL-B) |
| S8 | `CHART_COVE_INITIAL` | ChartBriefingScene | `chart_map_overlay.py` | Deploy Cove (cleared=None) |
| S9 | `CHART_SHOP` | ChartBriefingScene | holo shop layer | Key B on chart |
| S10 | `INTRO_COVE` | LevelIntroScene | `level_intro_overlay.py` | Chart Launch |
| S11 | `COUNTDOWN_COVE` | LaunchCountdownScene | `launch_countdown_overlay.py` | After intro |
| S12 | `PLAY_COVE_TACTICAL` | PlayScene | view_renderers tactical | After countdown |
| S13 | `PLAY_COVE_CHASE` | PlayScene | view_renderers chase | Key V |
| S14 | `PLAY_WIN_FLASH` | PlayScene | inline "YOU ESCAPED" | Gate touch (1 frame+) |
| S15 | `CHART_SOLAR_POST_CLEAR` | ChartBriefingScene | chart_map_overlay | Cove win auto-transition |
| S16 | `END_LOSS` | EndScene | inline in renderer | Life lost |
| S17 | `END_GAME_OVER` | EndScene | inline | Campaign over |

**Pygame boot rule (match Tk):**

```text
if has_startup_splash(): scene = StartupSplashScene()
else:                  scene = TitleScene()
```

Implement identical logic in `pygame_app.py` `__init__`.

### 38.1 Visual elements per screen (spot-check list)

| Screen | Must be visible |
|--------|-----------------|
| S1 | Full-bleed GIF, skip hint after debounce |
| S2–S6 | Starfield, holo command bar, tab strip, demo ship (WELCOME+) |
| S6 | Six sector rows; Cove row clickable; focus highlight on keyboard |
| S8 | Holo map panel, gravity field tint, wells/asteroids/beacons/gate glyphs, side intel, LAUNCH + BACK buttons |
| S10 | Header "ENEMY SPACE · CAPTAIN'S LOG", GIF viewport, progress bar, SKIP INTRO button |
| S11 | Live Cove playfield under reveal mask, 3-2-1 strip, sector label |
| S12–S13 | Playfield chrome, lives/hull/jewels HUD, mode badge TACTICAL / CHASE CAM |
| S15 | Status banner shows cleared Cove; upcoming Solar; map preview Solar layout |

---

## 39. Loading, GIF, and transition timing spec

All **loading** in L1 is synchronous asset decode at scene `on_enter` — no async thread required for milestone. Document expected timing so testers know normal vs broken.

### 39.1 Asset load points

| Trigger | Loads | Blocking? | Failure behavior |
|---------|-------|-----------|------------------|
| App boot S1 | `startup.gif` → Surface list | Yes, on_enter | Skip to TitleScene |
| Chart enter S8 | `build_level(cove)` + GravityField.bake | Yes, __post_init__ | Should not fail |
| Intro enter S10 | `cove.gif` → Surface list | Yes, on_enter | Skip to LaunchCountdownScene |
| Countdown enter S11 | `build_play_session(cove)` | Yes, on_enter | Critical — must not fail silently |
| Play draw | None (session pre-built) | — | — |

**Pygame requirement:** GIF decode via Pillow → Surfaces in `AssetCache`; cache keyed by path so re-entering intro does not re-decode.

### 39.2 GIF playback timing

| Asset | Playback rule | Skip rule |
|-------|---------------|-----------|
| `startup.gif` | `clamp(duration, 2.5s, 5.0s)` per `startup_splash.py` | After `SKIP_DEBOUNCE_SECONDS` (0.35s): click / Enter / Space / Esc |
| `cove.gif` | Full GIF duration OR `LevelIntroSpec.playback_seconds` if set | Enter / Space / Esc / SKIP INTRO click anytime |

**Frame advance:** Same as Tk — per-frame `delay_ms` from GIF metadata; index increments when `_frame_elapsed >= delay`.

### 39.3 Countdown timing (Cove)

| Step | Duration | Cumulative |
|------|----------|------------|
| Digit 3 | 1.0 s | 1.0 s |
| Digit 2 | 1.0 s | 2.0 s |
| Digit 1 | 1.0 s | 3.0 s |
| → Play | — | 3.0 s total |

Skip: Enter / Space at any step → immediate `PlayScene`.

**Reveal animation:** `reveal = total_elapsed / total_seconds` drives playfield wipe (0 = dark, 1 = full bright).

### 39.4 Scene transition table (with timing)

| From | To | Trigger | Campaign state |
|------|-----|---------|----------------|
| S1 | S2 | timer / skip | default new |
| S2 | S6 | goto_deploy | preserved |
| S6 | S8 | level:cove | preserved |
| S8 | S10 | launch | preserved |
| S10 | S11 | timer / skip | preserved |
| S11 | S12 | timer / skip | preserved |
| S12 | S15 | WON | `record_level_cleared(cove)` |
| S12 | S16 | life lost | lives decremented |
| S16 | S11 | retry | preserved |
| S16 | S2 | Esc / title | preserved (match Tk) |
| S12 | S2 | Esc | preserved |
| S8 | S2 | back_title | preserved |

### 39.5 Loading UX (Pygame polish — optional within L1)

| Enhancement | Priority | Notes |
|-------------|----------|-------|
| Show static "DECODING TRANSMISSION…" if GIF load > 200 ms | P2 | Intro only |
| Preload `cove.gif` during chart briefing | P3 | Cuts intro hitch |
| Progress spinner on countdown session build | P3 | Only if build_level slow |

**L1-FULL minimum:** No spinner required — but **no freeze > 1 s without eventual scene** unless asset missing (then fallback).

---

## 40. Title hub — all menu pages and hit regions

Title is **five pages** + optional shop modal. Pygame port must implement **all pages** (content is static text + chrome — low risk).

### 40.1 Page enum (`TitlePage`)

| Page | Tab label | Content summary |
|------|-----------|-----------------|
| WELCOME | WELCOME | Flavor welcome, goto_deploy CTA |
| MISSION | MISSION | Campaign premise / objective copy |
| HELM | CONTROLS | WASD, Space, Shift burst, V cam, R restart |
| COMBAT | COMBAT | Weapons, asteroids, hull chunks |
| DEPLOY | SELECT CHART | Sector list → chart briefing |

### 40.2 Hit regions (MenuHitMap IDs)

| Hit ID | Page | Action |
|--------|------|--------|
| `goto_deploy` | WELCOME | → DEPLOY page |
| `tab:welcome` … `tab:deploy` | all | Switch page |
| `page_prev` / `page_next` | all | Cycle pages |
| `level:cove` … `level:brood_moon` | DEPLOY | Launch chart if selectable |
| `shop_open` / `shop_close` | all | Toggle shop (L1-FULL-B) |

### 40.3 Keyboard navigation (title)

| Key | WELCOME | DEPLOY | Shop open |
|-----|---------|--------|-----------|
| Enter | → DEPLOY | Launch focused sector | Close shop |
| Tab / Right | Next page | — | — |
| Left | Prev page | — | — |
| Up/Down | — | Change deploy_focus | Shop tree nav |
| 1 | Launch Cove | Launch Cove | — |
| B | Toggle shop | Toggle shop | — |

### 40.4 L1 Pygame sector keys 2–6

| Key | L1 behavior (recommended) |
|-----|---------------------------|
| 2–6 | If sector not ported: toast HUD "Sector N — Pygame port pending" + no scene change |
| 2–6 alt | Allow chart preview but block Launch with toast — **not recommended** (confusing) |

### 40.5 Title render dependencies

| Module | Purpose |
|--------|---------|
| `title_overlay.py` | Pages, tabs, deploy list |
| `menu_ui.py` | Buttons, holo corners, fitted text |
| `hud_primitives.py` | Panels, scanlines |
| `ship_viz` / demo lambda | Rotating ship on title |

---

## 41. Chart briefing — inaugural Cove UI spec

First Cove deploy uses **INITIAL BRIEF** mode (`cleared_level_id is None`).

### 41.1 Layout regions (960×640)

| Region | Content |
|--------|---------|
| Command bar | Lives, jewels, hull, weapon track |
| Status banner | "INITIAL BRIEF" + upcoming Cove label |
| Left side panel | Objectives, hazards, controls reminder |
| Center map | Cove gravity field, entities |
| Right side panel | Intel rows, powerup chips |
| Footer | LAUNCH (center), BACK (left), shop CTA |

### 41.2 Map entities required for Cove preview

| Entity | Glyph source |
|--------|--------------|
| Gravity wells | Oval rings |
| Asteroids | `draw_map_asteroid_glyph` |
| Beacons | `draw_beacon_play` |
| Finish gate | `draw_gate_glyph` |
| Ship marker | Player position on preview world |

### 41.3 Hit regions

| Hit ID | Action |
|--------|--------|
| `launch` | → LevelIntroScene |
| `back_title` | → TitleScene |
| `shop_open` / `shop_close` | Shop modal |

### 41.4 Post-win chart (S15) differences

| Field | Value after Cove clear |
|-------|------------------------|
| `upcoming_level_id` | `solar` |
| `cleared_level_id` | `cove` |
| Banner | Shows last sector cleared |
| Map preview | Solar layout (render only — Launch blocked until L2 port OR show "pending" toast) |

**L1 test note:** Reaching S15 proves win transition. **Launch Solar on Pygame** is explicitly **out of L1 scope** — Esc or back to title is sufficient after verifying banner/map.

---

## 42. Master L1 test matrix (automated + manual)

Single table for QA + CI. **ID format:** `L1-T-###`.

### 42.1 Boot and menus

| ID | Type | Steps | Expected |
|----|------|-------|----------|
| L1-T-001 | auto | Import pygame_app | No throw |
| L1-T-002 | auto | Load startup.gif via AssetCache | frame_count ≥ 1 |
| L1-T-003 | auto | Load cove.gif via AssetCache | frame_count ≥ 1 |
| L1-T-004 | manual | Boot without startup.gif | Lands S2 directly |
| L1-T-005 | manual | Boot with startup.gif | S1 → skip → S2 |
| L1-T-006 | manual | Cycle all title tabs S2–S6 | All pages render text |
| L1-T-007 | manual | goto_deploy button | Reaches S6 |
| L1-T-008 | manual | Click level:cove row | Reaches S8 |
| L1-T-009 | manual | Key 1 from title | Reaches S8 |
| L1-T-010 | manual | Chart BACK | Returns S2 with campaign |

### 42.2 Intro, countdown, loading

| ID | Type | Steps | Expected |
|----|------|-------|----------|
| L1-T-020 | manual | LAUNCH from chart | S10 intro loads ≤ 1 s |
| L1-T-021 | manual | Watch full cove.gif | Auto → S11 at end |
| L1-T-022 | manual | SKIP INTRO click | Immediate S11 |
| L1-T-023 | manual | Enter during intro | S11 |
| L1-T-024 | manual | Full 3-2-1 countdown | S12 at ~3 s |
| L1-T-025 | manual | Space skip countdown | Immediate S12 |
| L1-T-026 | auto | build_play_session cove | world.status PLAYING |
| L1-T-027 | manual | Intro missing file | Fallback S11 (no crash) |

### 42.3 Cove gameplay

| ID | Type | Steps | Expected |
|----|------|-------|----------|
| L1-T-040 | auto | build_level cove beacon count | Matches Tk baseline test |
| L1-T-041 | manual | Thrust + fire 30 s | No crash; bolts curve |
| L1-T-042 | manual | Toggle V × 5 | S12 ↔ S13; HUD badge updates |
| L1-T-043 | manual | Collect all beacons | Gate opens |
| L1-T-044 | manual | Enter gate | WON; brief S14 flash |
| L1-T-045 | manual | Win transition | S15 solar chart; cleared=cove |
| L1-T-046 | manual | Asteroid hit (chip left) | Hull alert; play continues |
| L1-T-047 | manual | Fatal hit | S16; retry → S11 → S12 |
| L1-T-048 | manual | R mid-level | Fresh cove session |
| L1-T-049 | manual | Esc from play | S2 |
| L1-T-050 | auto | pytest full suite | ≥ 488 pass |

### 42.4 Render smoke (Pygame backend)

| ID | Type | Steps | Expected |
|----|------|-------|----------|
| L1-T-060 | auto | DrawContextSpy: draw_world cove | polygon calls > 50 |
| L1-T-061 | auto | draw_title DEPLOY | text calls > 10 |
| L1-T-062 | auto | draw_chart_briefing cove | polygon/rect > 40 |
| L1-T-063 | auto | draw_level_intro frame 0 | image blit 1 |
| L1-T-064 | auto | draw_launch_countdown step 0 | composite draw ok |
| L1-T-065 | auto | draw_end loss | hit regions registered |

### 42.5 Shop (L1-FULL-B only)

| ID | Type | Steps | Expected |
|----|------|-------|----------|
| L1-T-080 | manual | B on title | S7 shop opens |
| L1-T-081 | manual | Purchase with DEV jewels | Campaign updated |
| L1-T-082 | manual | B on chart | Shop over map |

---

## 43. QA playbooks — three complete loop scripts

Copy to `docs/playtest/PYGAME_L1_SESSION.md` when testing starts.

### 43.1 Playbook A — Smoke (5 minutes)

**Goal:** Prove Pygame app runs and reaches playable Cove.

1. `python run_game_pygame.py`
2. Mash Enter through splash + title → key `1`
3. Enter on chart → mash Enter through intro + countdown
4. Thrust 5 seconds in tactical
5. Press V — chase visible
6. Esc → quit

**Pass:** No crash; at least S1→S12 seen.

### 43.2 Playbook B — Full L1 loop (25 minutes)

**Goal:** Complete player journey + win transition.

1. Fresh boot; **click-only path** (no number keys): splash skip → WELCOME → goto_deploy → click Cove row
2. Chart: read side panel; click LAUNCH
3. Watch **entire** cove.gif without skipping
4. Watch **entire** 3-2-1 countdown
5. Play Cove tactical to completion (all beacons + gate)
6. Verify **Solar chart** (S15), not EndScene
7. Esc → title
8. Key `1` speed run: skip intro/countdown (Enter spam)
9. Win again in **chase cam** (toggle V at start)
10. Esc title

**Pass:** Two wins; S15 twice; Appendix C checked.

### 43.3 Playbook C — Failure + menu regression (15 minutes)

**Goal:** Death, retry, title pages, chart back.

1. Boot → Cove play
2. Die intentionally → S16
3. Retry → countdown → play
4. Esc → title
5. Visit **every title tab** (S2–S6) — 30 s each
6. Deploy Cove → chart → BACK → title
7. Deploy again → intro → **SKIP INTRO** → play
8. Chip damage (non-lethal) — verify HUD alert string
9. R restart — verify beacon state resets

**Pass:** All transitions correct; no stuck scene.

### 43.4 Side-by-side Tk parity (optional, 10 minutes)

Run Playbook B on **Tk** and **Pygame** in same session:

| Checkpoint | Compare |
|------------|---------|
| S10 frame 0 | GIF centered in viewport |
| S12 mid-game | Beacon count, HUD lives |
| S15 banner | Cleared sector text |

Record pass/fail in session log — pixel diff not required.

### 43.5 Session log template

```markdown
# Pygame L1 session — YYYY-MM-DD
Tester:
Build: commit SHA
Backend: pygame-ce version

| Playbook | Pass? | Notes |
|----------|-------|-------|
| A Smoke | | |
| B Full loop | | |
| C Failure | | |

Failed tests: L1-T-___
Blockers:
```

---

## Document maintenance

When implementation starts:

1. Check off phases in this doc or link to GitHub issues per phase.
2. Log L1 playtest sessions in `docs/playtest/PYGAME_L1_SESSION.md` (create on D10).
3. Update README **Current state** when L1 slice lands.
4. Do **not** fork this plan into multiple docs — extend sections here.
5. Part II Section 37 gates = merge criteria for `pygame-l1` branch → main.

---

*End of Pygame CE Migration Plan (Part I + Part II L1 complete-loop final)*
