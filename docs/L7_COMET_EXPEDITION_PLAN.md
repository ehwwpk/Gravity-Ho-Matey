# L7 — Comet Fuel Expedition · Planning Document

**Status:** Design / architecture plan (no implementation yet)  
**Level slot:** **7** — after `brood_moon` (L6) in campaign order  
**Working id:** `comet_fuel` (rename OK before ship)  
**Codename:** *Volatile Charter*

---

## Executive summary

L7 introduces the **Expedition Framework** — a standardized dock → on-foot → extract → undock loop reused across future levels. For L7 specifically, the player orbits a **slowly revolving comet**, lands at a **derelict fuel station** overrun by **space squids**, clears the site as a **humanoid EVA captain** (top-down), loads **volatile fuel**, returns to the parked ship, undocks, and completes a short **escape flight** to the finish gate.

L7 is the **extended-tier** reference implementation: a large authored site with a **mostly required** objective chain. A future level can use the **same engine** at **open tier** — bigger map, more optional objectives — without a second codebase.

**One sentence:** Same game, same campaign — you fly to a comet, get out of the ship, do boots-on-rock work, get back in, and fly out; L7 proves the pipeline; later levels scale the map and freedom up, not down.

---

## Contents

1. [Campaign & narrative placement](#1-campaign--narrative-placement)
2. [Unified expedition framework](#2-unified-expedition-framework)
3. [L7 mission flow (full run)](#3-l7-mission-flow-full-run)
4. [Comet in orbital flight space](#4-comet-in-orbital-flight-space)
5. [Comet RPG world (on-foot)](#5-comet-rpg-world-on-foot)
6. [Humanoid avatar (EVA captain)](#6-humanoid-avatar-eva-captain)
6A. [EVA visual art bible · motion · weapon](#6a-eva-visual-art-bible--motion--weapon)
7. [Objectives & completion rules (L7)](#7-objectives--completion-rules-l7)
8. [Visual & FX quality bar](#8-visual--fx-quality-bar)
8A. [Fuel station & comet surface art bible](#8a-fuel-station--comet-surface-art-bible)
9. [Architecture · repo mapping](#9-architecture--repo-mapping)
10. [Rendering & camera](#10-rendering--camera)
11. [Combat, enemies, hazards](#11-combat-enemies-hazards)
11A. [Squid feeding behavior · standardization](#11a-squid-feeding-behavior--standardization)
12. [HUD, audio, narrative](#12-hud-audio-narrative)
13. [Future open-tier extension](#13-future-open-tier-extension)
14. [Implementation phases](#14-implementation-phases)
15. [Design locks & risks](#15-design-locks--risks)
16. [References](#16-references)
17. [Zoom-out review · cautions & obvious flaws](#17-zoom-out-review--cautions--obvious-flaws)
18. [External research synthesis (games & patterns)](#18-external-research-synthesis-games--patterns)
19. [Full repo trace · upstream → downstream](#19-full-repo-trace--upstream--downstream)
20. [Implementation contracts (coding standard)](#20-implementation-contracts-coding-standard)
21. [Open decisions register](#21-open-decisions-register)
22. [Cross-cutting concerns matrix](#22-cross-cutting-concerns-matrix)
23. [Implementation readiness · next build pass](#23-implementation-readiness--next-build-pass)
24. [Final pass · hold-E grammar & build strategy](#24-final-pass--hold-e-grammar--build-strategy)

---

## 1. Campaign & narrative placement

| Item | Plan |
|------|------|
| **Unlock** | Clear L6 (`brood_moon` / Siege Line successor chain TBD — L7 locks after Brood Moon) |
| **Label** | `7 — Volatile Charter` (working) |
| **Arc pitch** | Corporate fuel charter on a passing comet — station’s gone dark, squids in the tanks, you need one clean load to make the next jump |
| **Tone** | Pirate pragmatism + void horror (squids in industrial pipes) + corporate paperwork voice on radio |
| **Relation to L6** | L6 = ship-on-surface, side-scroll nursery run. L7 = **humanoid on rock**, top-down EVA. Different fantasy; shared **phase-transition** pattern only |

Register in (when building):

- `levels/level_registry.py` — `LEVEL_ORDER`, `LEVEL_BUILDERS`, `LEVEL_LABELS`
- `narrative/chart_briefing_copy.py` — `LEVEL_BRIEFING`, `LEVEL_INTEL`
- `narrative/level_intros.py`, `launch_countdown.py`
- `render/title_info_pages.py` — `_CAMPAIGN_ARC`, `_LEVEL_LOCK`

---

## 2. Unified expedition framework

### 2.1 Play modes (game-wide standard)

| Mode | Camera | Avatar | When |
|------|--------|--------|------|
| **FLIGHT** | Tactical / Chase (existing) | Ship | Orbital approach, post-undock escape |
| **CINEMATIC** | Transition overlay / short strip | Ship → EVA handoff | Dock & undock |
| **EXPEDITION** | Top-down on foot | Humanoid (EVA captain) | On comet surface / station pad |

**Design lock:** Exactly one sim controller active per frame — flight sim **or** expedition sim, never both. Ship state is **frozen** (parked) during expedition.

### 2.2 Expedition tiers (content scale, not code forks)

| Tier | Map | Objectives | L7? | Future example |
|------|-----|------------|-----|----------------|
| **extended** | Large authored site, 3–5 zones | Most steps **required** | ✅ L7 | — |
| **open** | Larger than extended, branches, caves | Few **required**, many **optional** | — | L9+ hero comet |

Same `ExpeditionSite` schema; tier controls layout size and objective flags only.

### 2.3 Standard phase machine

Mirror proven L6 `BroodPhase` pattern (`gameplay/brood_moon_mission.py`, `brood_moon_controller.py`):

```
ExpeditionPhase (proposed)
  ORBITAL          — fly in arena; comet on path; approach landing band
  DOCK_CINEMATIC   — ship down, EVA out (unskippable first visit)
  ON_FOOT          — top-down humanoid gameplay
  UNDOCK_CINEMATIC — fuel loaded, ship up
  ESCAPE_FLIGHT    — short flight leg to finish gate (or ORBITAL_RETURN if multi-leg)
  COMPLETE         — win state
```

Transitions reuse L6 grammar — **hold E everywhere** for dock, foot work, and extract (see §24):

- **Hold E** in landing band (`LANDING_CHARGE_SECONDS` ~1.0s)
- **Hold E** at interact nodes — fuel load, grab, seal/fix (per-type charge, §24)
- **Hold E** at lander when required objectives met (`EXTRACT_CHARGE_SECONDS` ~1.0s)
- Cinematic length ~4–5s (`CINEMATIC_DEFAULT_SECONDS` from brood layout)

### 2.4 Objective types (shared enum)

| Type | L7 use | Future open tier |
|------|--------|------------------|
| `CLEAR_HOSTILES` | Clear squids from fuel station | Optional nest clears |
| `COLLECT_CARGO` | Load volatile fuel canisters | Optional ore veins |
| `REACH_ZONE` | Enter station inner ring | Optional cave |
| `INTERACT` | Open depot valve / hack charter lock | Lore terminals |
| `EXTRACT` | Return to lander (always required gate) | Same |

Each objective: `{ id, type, required: bool, zone, reward? }`.

**Undock rule (global):** all `required: true` objectives complete → extract enabled.

### 2.5 Flight payoff (not a minigame)

Expedition cargo must echo in flight:

- **L7 required:** volatile fuel → reactor stable for escape segment (no soft-lock; failure = slower / hotter ship, not hard block)
- **Optional (future):** bonus fuel → treasury multiplier, overheat headroom, chase FOV ease

---

## 3. L7 mission flow (full run)

### Act I — Orbital flight (~4–6 min)

1. Spawn in comet approach arena (size TBD ~4800×3200, similar to brood orbital).
2. Tutorial ping: comet icon on tactical map, slow orbital path.
3. Navigate debris field (asteroid tier SMALL/MEDIUM — existing combat).
4. Enter comet **landing band** → HUD: `HOLD E · DOCK AT CHARTER PAD`.
5. Optional: skim close for intel toast — “squid bio-signatures at depot.”

### Act II — Dock cinematic (~4–5 s)

- Reuse `BroodMoonTransitionOverlay` pattern / narrative GIF slot (`assets/narrative/comet_fuel_dock.gif` placeholder).
- Ship settles on pad; camera cuts to top-down; humanoid exits lander.

### Act III — Expedition (~8–12 min) · extended tier

| Step | Zone | Player verb |
|------|------|-------------|
| 1 | **Lander pad** (south) | Orient, read objective rail |
| 2 | **Pad approach** | Navigate stray squids; several **feeding on busted fuel lines** (safe to approach if quiet) |
| 3 | **Regolith trenches** | Follow **surface fuel mains** toward depot; 4–6 squids on feed lines |
| 4 | **Fuel station exterior** | Clear remaining hostiles (`CLEAR_HOSTILES`) — nests on pipes |
| 5 | **Station interior / depot ring** | Interact valves, collect fuel (`COLLECT_CARGO` ×3 or meter fill) |
| 6 | **Return path** | Carry fuel to lander (encumbered — no sprint) |
| 7 | **Lander** | Hold E extract (`EXTRACT`) |

### Act IV — Undock cinematic (~4–5 s)

- Fuel hoses retract; ship lifts; top-down → tactical/chase flight.

### Act V — Escape flight (~2–4 min)

- Comet **outgassing** hazard (visual + mild drag / heat — not new mechanic, reuse weapon heat or chart radiation pattern).
- Fly to finish gate; win.

**Total target:** ~18–22 min first clear; ~12–15 min repeat.

---

## 4. Comet in orbital flight space

### 4.1 Body definition

Reuse `PlanetBody` limb/band math (`gameplay/planet_mission.py`) but for a **small body**:

```text
CometBody (conceptual)
  path_center: Vec2           # arena anchor for orbit ellipse
  orbit_semi_major: float     # ~680 WU
  orbit_semi_minor: float     # ~420 WU
  angular_speed: float        # ~0.045 rad/s (full orbit ~2.5 min)
  surface_radius: float       # ~180 WU (small vs Brood Moon 520)
  landing_band_inner/outer    # shell for hold-to-dock
  phase_at_spawn: float       # seeded per run
```

**Visual:** Comet nucleus = cluster of `draw_illustrated_polygon` chunks (see §8) + translucent coma particle wash (reuse `chase_fx` fog / starfield parallax).

### 4.2 Orbital motion rules

| Rule | Rationale |
|------|-----------|
| Comet position = `center + ellipse(phase)` each flight tick | Readable moving target |
| **Freeze `phase` on dock** | Player must not miss pad because comet drifted during EVA |
| Debris asteroids **avoid** landing band (Brood `ORBITAL_DEBRIS_EXCLUDE_*` pattern) | Fair approach |
| Tactical map shows comet glyph + orbit trail (dotted arc) | Orientation |
| Chase shows comet as lit nucleus + tail streak along velocity vector | Chase silhouette rule from design lens |

### 4.3 Landing approach

- Same UX as Brood orbital: `in_landing_band(ship, comet_body)` + charge meter.
- Pad is on **sunlit face** — approach from comet’s trailing side for drama.
- Failed approach (scrape nucleus) = chip damage, bounce off — not instant fail.

### 4.4 After undock

- Unfreeze phase OR jump comet to escape trajectory (design choice at implement — prefer **continue orbit** with outgassing VFX on sunlit face).
- Finish gate placed **down-track** from comet path so player flies **away from nucleus plume**.

---

## 5. Comet RPG world (on-foot)

### 5.1 Map topology · L7 extended layout

Local expedition map ( **not** 4000×3200 flight coords — separate local origin):

```text
Dimensions (working): 2400 × 1800 WU
Origin: lander pad at (1200, 1500)

Zones:
  A  Lander Pad          — safe bubble, extract point, ship silhouette (parked)
  B  Regolith Slope       — scree rocks, 2–3 squid skirmish spawns
  C  Station Perimeter    — fuel station mesh, pipes, fence, CLEAR_HOSTILES
  D  Depot Ring           — fuel tanks, interact nodes, COLLECT_CARGO
  E  (blocked) Ice Rift   — visual tease for future open tier; collapsed in L7
```

**No toroidal wrap** on expedition map (contrast L6 `surface_wrap`). Boundaries = soft kill zones (outgassing / void edge) with warning HUD.

### 5.2 “Comet RPG world” simulation (L7 scope)

| System | L7 behavior |
|--------|-------------|
| **Gravity** | Low-G: short jump arc or floaty step; uniform down ~12 m/s² equivalent |
| **Collision** | Static polygons (rocks, station hull); grid or polygon nav |
| **Mining / fuel** | Not free-form — **hold E** at interact nodes (progress bar per §24) |
| **Exploration** | Linear-with-pockets; side alcoves for jewels/health, not mandatory |
| **Persistence** | None within run; cleared squids stay dead |
| **Time pressure** | Soft — radio lines at 8 min / 12 min; no hard fail timer in L7 v1 |

### 5.3 Fuel station as hero set-piece

Reuse **station mesh pipeline** (`render/station_mesh.py`, `station_lit_draw.py`, `station_viz.py`):

- Faction: `NEUTRAL` → `HOSTILE` tint when squids infest.
- Scale: ~2× skiff pad station — readable in top-down.
- Layers: pad ring, depot tanks, pipe greebles, rim bloom, HP bar for “depot integrity” (optional).
- Squid nests: bio-growth meshes on pipes (brood chitin/membrane materials).

### 5.4 Terrain · comet regolith

Build static “mega-asteroid” tiles:

- Base chunks: `asteroid_shape` convex verts at large scale + `draw_illustrated_polygon` with **crater_count 3–6** (≥ asteroid quality).
- Ice veins: brood-style `draw_brood_vein_glow_line` in cyan/violet (volatile ice).
- Loose pebbles: pebble `Asteroid` entities **frozen** (vel=0) as props — same viz as combat rocks.

**Quality bar:** Any single rock on the comet surface should use the same faceted lighting path as tactical asteroids (`render/asteroid_viz.py` → `lit_draw.draw_illustrated_polygon`). Station and lander **exceed** rock detail via greeble layers.

---

## 6. Humanoid avatar (EVA captain)

### 6.1 Fantasy

The ship is parked; the **EVA captain** is the playable entity. Not a separate character meta — **you**, in suit, doing the job. Helmet visor reflects key light; pirate patch optional on shoulder.

### 6.2 Controls (expedition mode)

| Input | Action |
|-------|--------|
| WASD / arrows | Move (360° with accel/decel — §6A) |
| Mouse / aim keys | Fire sidearm direction |
| **E (hold)** | **All interactions** — fuel load, grab canister, seal vent, charter log, extract at lander (§24) |
| Shift | Sprint (disabled while carrying fuel) |
| Tab / V | **Disabled** — no chase/tactical swap on-foot |
| B | Shop closed on-foot |

Reuse `ControlIntent` + existing `interaction_hold` from `PlayScene` (`host.input_state.down("e")`) — same wire as brood dock and relay repair.

### 6.3 Stats & damage

| Stat | Proposal |
|------|----------|
| **EVA suit HP** | 3 chunks mirror ship — or single 100 HP bar (prefer **3 chunks** for campaign consistency) |
| **Death** | Respawn at lander, squid respawn in zone optional (prefer **no respawn of cleared zone**) |
| **Campaign lives** | EVA death costs hull chunk → same `CampaignState` pipeline as ship |
| **Sidearm** | Limited DPS — expedition is not bullet hell; squids are melee/leap |

### 6.4 Visual · humanoid ship-replacement

New module family: `render/eva_viz.py` (name TBD)

- **Top-down silhouette:** lit faceted suit body (mini ship grammar — `LightRig` + 2–3 polygon layers).
- **Facing:** rotate toward move or aim vector; thruster puff on sprint.
- **Helmet gleam:** 1px highlight arc synced to `rig.key_dir`.
- **Scale:** ~14–18 px radius at 1.0 expedition scale — readable vs squid enemies.
- **Shadow:** `draw_brood_ground_shadow` ellipse under feet (reuse brood fauna shadow).

**Do not** reuse ship sprite scaled down — reads wrong. Humanoid must be authored for top-down.

### 6.5 Parked ship

During expedition, draw lander + ship at pad:

- Frozen `Ship` state stored in `ExpeditionState.parked_ship` (pos, angle, hull).
- Lander ramp light pulses when extract ready.
- No ship physics tick while on-foot.

---

## 6A. EVA visual art bible · motion · weapon

This section is the **authoritative art + motion spec** for the humanoid player. Implementation must use the same lit pipeline as ship and asteroids — not flat sprites.

### 6A.1 Silhouette & identity (top-down read)

The EVA captain reads at a glance as **“person in suit”**, not a shrunk ship. Design targets:

| Read at 18 px radius | Shape language |
|----------------------|----------------|
| **Head** | Rounded helmet dome, offset **+Y** (screen-down) from torso center — instant humanoid cue |
| **Shoulders** | Wider than hips; slight asymmetry (patch on right shoulder) |
| **Backpack** | Rectangular O₂ pack behind torso; **amber gauge stripe** (matches volatile fuel accent) |
| **Boots** | Slightly flared feet ellipses when moving |
| **Facing** | Visor arc on helmet points toward **aim vector** (not always move vector) |

**Fantasy lock:** Pirate EVA — scuffed suit, one gold earring dot on helmet rim (1 px), corporate charter patch on left shoulder (cyan rectangle). Not cartoon; same gritty faceted tone as fighter hull.

### 6A.2 Lit mesh structure (`render/eva_viz.py`)

Author **local-space polygons** exactly like `_FIGHTER_HULL_LOCAL` in `ship_viz.py`:

```text
_EVA_HELMET_LOCAL     — 8-pt dome + visor cut-in
_EVA_TORSO_LOCAL      — 10-pt faceted chest + abdomen
_EVA_BACKPACK_LOCAL   — 6-pt pack (drawn after torso, keyed to rig)
_EVA_BOOT_L/R_LOCAL   — 4-pt each, only visible when |vel| > threshold
```

**Draw order per frame:**

1. `draw_brood_ground_shadow` (theme-aware — comet regolith deep when `theme=="comet"`)
2. Backpack layer — `draw_illustrated_polygon` with `material_for("eva_pack", theme="comet")`
3. Torso — `draw_illustrated_polygon` with `material_for("eva_suit", theme="comet")`
4. Helmet — separate poly; visor band = `lerp_hex(material.highlight, palette.COMET_ICE_HI, 0.55)` arc
5. Helmet gleam — 1 px line along key-lit rim (same rule as ship panel highlights)
6. Sprint thruster puff — `draw_ground_fog_glow` at backpack when sprinting
7. Sidearm — drawn attached to aim-side hip (see §6A.5)

**New materials** in `lighting.py` → `material_for`:

| kind | Palette direction |
|------|-------------------|
| `eva_suit` | Mid `#4a5868`, highlight `#8aa0b8`, shadow `#2a3440`, rim `#c0d8e8` |
| `eva_pack` | Darker mid, **amber rim stripe** `#ffb040` on gauge face |
| `eva_visor` | Ice cyan `#a8f0ff` @ 70% key response |
| `void_pistol` | Gunmetal like ship fittings; muzzle `palette.PICKUP_RAPID` tint |

**LightRig:** Add `_KEY_COMET = Vec2(-0.56, -0.79).normalized()`; expedition foot always uses `CameraMode.TACTICAL` rig with `view="expedition"` (or reuse tactical with comet theme).

### 6A.3 Motion flow · animation states

Smooth flow = **acceleration-limited velocity** + **visual state machine** synced to physics. No instant direction snaps.

#### Physics ( `gameplay/expedition_foot.py` )

| Parameter | Value | Feel |
|-----------|-------|------|
| `max_walk_speed` | 165 WU/s | Deliberate EVA stride |
| `max_sprint_speed` | 248 WU/s | Short burst; 2.5 s active / 4 s cooldown |
| `accel` | 920 WU/s² | Responsive but not twitch-shooter |
| `decel` | 1100 WU/s² | Clean stop on key release |
| `turn_rate` | 11 rad/s (aim), 8 rad/s (move-only) | Helmet lags body slightly when strafing |
| `foot_friction` | 0.88 per frame @ 60 Hz | Low-G scuff, not ice skating |

**Low-G flavor:** Optional 0.12 s “commit” on direction change — blend old vel 15% into new for floaty feel without breaking combat reads.

#### Visual states (`EvaAnimState`)

```python
class EvaAnimState(Enum):
    IDLE = auto()       # subtle helmet bob sin(elapsed * 2.2) * 1.2 px
    WALK = auto()       # boot flare alternate L/R every 0.28 s
    SPRINT = auto()     # backpack thruster puff + shadow stretch 1.15×
    FIRE = auto()       # torso recoil 2 px opposite aim for 0.08 s
    HIT = auto()        # white rim flash on suit + knockback tint
    INTERACT = auto()   # one-hand reach toward interact node
```

**Footfall FX:** On WALK/SPRINT, every 0.26 s spawn `FootfallPuff` — 2-frame `draw_ground_fog_glow` regolith dust (seed from pos hash). Same particle grammar as asteroid impact dust, smaller radius.

**Camera follow:** Smooth center on avatar with `EXPEDITION_FOLLOW_LERP = 0.14` (slightly tighter than brood surface) — player always sees 1.5 body lengths ahead along move vector for readability.

### 6A.4 Interaction & carry motion

When `load_fuel` active and avatar carries canister:

- **Backpack secondary tank** mesh visible (small illustrated poly on pack)
- Walk speed × 0.88 (no sprint while carrying — design lock D8 revised: **encumbered = no sprint**)
- Interact at depot: `INTERACT` anim state + valve steam FX (§8A)

### 6A.5 Sidearm · “Void Cutlass” pistol

Expedition weapon is a **compact top-down pistol**, not ship cannons. Reuses projectile pipeline for consistency.

| Property | Spec |
|----------|------|
| Name (HUD) | `VOID CUTLASS` |
| Fire rate | 3.5 shots/s |
| Damage | 1 hit per squid body shot (3 hits kill — same as flight `SQUID_HITS_MAX`) |
| Range | 520 WU before fade |
| Projectile | Small lit poly bolt — `draw_simplified_polygon` in flight, `draw_illustrated_polygon` on impact spark |
| Aim | Manual — mouse position or right-stick equivalent; avatar `facing_angle` = aim angle |
| Heat | **No** ship heat system on-foot; infinite ammo (pressure is enemy count + positioning) |
| Muzzle flash | 2-frame `ExplosionKind.PROJECTILE_IMPACT` scaled 0.4 at muzzle local offset |
| Audio hook | Short pneumatic hiss (when audio lands) |

**Visual attachment:** Pistol local mesh rotates with aim; drawn **after** torso so it overlaps hip. Two-tone: grip = `eva_suit` shadow, barrel = `void_pistol`.

**Design lock:** Sidearm DPS tuned so a **feeding squid** dies in ~1.2 s if player commits — rewarding stealth approach on feeders before they alert.

### 6A.6 Quality checklist · EVA

- [ ] Every suit layer uses `LightRig` + `MaterialTones` — zero flat `create_oval` fills for body
- [ ] Helmet visor reflects `rig.key_dir` (highlight arc moves with global light)
- [ ] Ground shadow offset along key light (reuse `draw_brood_ground_shadow` with comet fill)
- [ ] Sprint + footfall FX visible on regolith; silent on station metal pad
- [ ] Sidearm muzzle flash + projectile use lit draw
- [ ] Scale test: avatar readable vs squid at 640 WU detect range on 1920×1080

---

## 7. Objectives & completion rules (L7)

### Required chain (extended tier)

| # | ID | Type | required | Success |
|---|-----|------|----------|---------|
| 1 | `clear_depot` | `CLEAR_HOSTILES` | true | All expedition squids dead (**16** authored spawns; HUD tracks remaining) |
| 2 | `load_fuel` | `COLLECT_CARGO` | true | Fuel meter 100% — **3× hold E** at depot valves (1.2 s each) |
| 3 | `extract` | `EXTRACT` | true | Hold E at lander after 1+2 |

### Optional (L7 v1 — 0–2 max)

| ID | Type | Reward |
|----|------|--------|
| `salvage_charter_log` | `INTERACT` | Codex + 1 jewel |
| `seal_vent` | `INTERACT` | −heat on escape flight |

### HUD objective rail

Reuse rift/brood HUD grammar (`render/hud_overlay.py`):

```text
EXPEDITION · VOLATILE CHARTER
★ CLEAR DEPOT     09 / 16 hostiles
★ LOAD FUEL       66%
○ CHARTER LOG     — optional
RTB · lander pad south
```

**Squid HUD note:** Feeding squids count toward total but show **dimmed** rim tag `FD` when off-screen (optional) — player learns feeders are on lines, not roaming.

Off-screen squids use existing `offscreen_hostile_hints.py` rim chevrons — **no connector lines**.

---

## 8. Visual & FX quality bar

### 8.1 Non-negotiable standard

> **Every expedition surface entity uses `LightRig` + `MaterialTones` + faceted lit draw — same pipeline as asteroids, stations, brood geology.**

Reference implementations in repo:

| Asset class | Reference module | Minimum bar |
|-------------|------------------|-------------|
| Rock / ice | `asteroid_viz.py`, `lit_draw.py` | `draw_illustrated_polygon`, seeded craters, rim highlight |
| Station | `station_viz.py`, `station_lit_draw.py` | Layer polys, greebles, rim bloom, faction glow |
| Bio / squid nests | `brood_fauna_viz.py`, `squid_viz.py` | Membrane tones, vein glow lines |
| Floor / coma | `brood_moon_surface_viz.py`, `chase_fx.py` | Parallax bands, fog glow (not full-screen wash) |
| Transitions | `brood_moon_transition_overlay.py` | Scanlines, holo corners, accent palette |

### 8.2 Comet theme palette (new)

Add `level_theme="comet"` to `palette.py` + `LightRig.for_play`:

| Role | Direction |
|------|-----------|
| Background | Deep blue-black `#040810` |
| Ice highlight | Cyan-white `#a8f0ff` |
| Regolith mid | Blue-gray `#5a6878` (≥ asteroid contrast) |
| Volatile accent | Amber `#ffb040` (fuel hazard) |
| Coma tail | Violet translucent `#6840a0` @ 25% alpha |
| HUD accent | `#48c8f0` (distinct from rift teal, brood mauve) |

### 8.3 FX checklist · L7

- [ ] Comet coma particle drift (parallax, not physics-heavy)
- [ ] Outgassing plume on escape (directional streaks, heat shimmer on HUD)
- [ ] Fuel interact: valve steam + `REACTOR_BURST`-adjacent sparkle (reuse explosion kinds)
- [ ] Squid death: existing squid FX scaled for top-down
- [ ] EVA footfall dust puff on regolith (2-frame, seeded)
- [ ] EVA sprint backpack thruster puff
- [ ] Void Cutlass muzzle flash + lit projectile trail
- [ ] 6× fuel feed line burst + flow pulse
- [ ] Squid feeding tentacle amber glow (`draw_squid_feeding_fx`)
- [ ] Squid ALERT mantle brighten telegraph
- [ ] Dock / undock: landing strut dust + brief screen vignette
- [ ] Station rim pulse when fuel loading

### 8.4 Performance guardrails

- Expedition map static geometry **baked** — no per-frame regen like gravity heatmap full arena.
- Fauna/prop cap similar to brood: `EXPEDITION_PROP_DRAW_MAX ~ 32` off-screen cull.
- Frozen pebble props: no spatial sim unless player bumps (optional static only).

---

## 8A. Fuel station & comet surface art bible

The **Charter Fuel House** is the hero set-piece — equal visual weight to a siege station in flight view, adapted for **top-down expedition camera**.

### 8A.1 Site layout · “Fuel House on the comet”

```text
                    [ Depot Ring — tanks + valve interact ]
                              |
         ═════════════════════╪═════════════════════  ← station perimeter fence mesh
                              |
              ┌───────────────┴───────────────┐
              │   CHARTER FUEL HOUSE HUB    │  ← multi-layer station mesh, ~380 WU diameter
              │   (lit hub + 4 tank silos)  │
              └───────────────┬───────────────┘
                              |
    ──── fuel main A ────┬────┴────┬──── fuel main B ────  ← busted surface lines (hero props)
                       │         │
                  [feed]     [feed]   ← squids anchored here at spawn
                              |
                    regolith slope → lander pad (south)
```

**Zones B–D** connected by **visible fuel infrastructure** — player reads the map by following amber-lit pipes, not minimap arrows alone.

### 8A.2 Fuel station mesh (top-down)

Reuse station pipeline; new **`ExpeditionStationMesh`** in `levels/comet_fuel_props.py`:

| Layer | Source API | L7 content |
|-------|------------|------------|
| **Pad ring** | `draw_station_layer_polygons` | Hex charter pad; scorch marks; dock clamp ghosts |
| **Hub** | `mesh_for_station` variant | Central fuel house — 2× skiff pad scale |
| **Tank silos** | 4× cylindrical illustrated polys | Volatile amber rim glow when fuel inside |
| **Pipe arms** | `draw_station_greeble_mid/front` | 6–8 pipe runs into regolith |
| **Fence** | Low poly barrier ring | Breached sections where squids entered |
| **Rim bloom** | `draw_station_rim_bloom` | Amber + cyan dual tone (fuel + ice) |
| **Bio infestation** | `draw_brood_membrane_ring` + vein lines | Squid nests on 3 pipe junctions |

**Faction tint:** Start `NEUTRAL`; when squids present, `HOSTILE` sub-tint on damaged sections only — not whole station red (reads as damage, not evil station).

**Quality bar:** Hub alone ≥ **12 illustrated polygons** + greebles; any single tank ≥ asteroid `crater_count=2` faceting.

### 8A.3 Busted fuel lines · surface feed props

New prop type: **`FuelFeedLine`** (gameplay + render)

```python
@dataclass(frozen=True, slots=True)
class FuelFeedLine:
    id: str
    start: Vec2          # depot pipe exit or trench break
    end: Vec2            # regolith crack mouth
    burst_width: float   # visual only
    flow_rate: float     # 0..1 anim pulse
    alive: bool = True   # False when sealed (optional objective)
```

**Visual (`render/expedition_fuel_viz.py`):**

1. **Trench mesh** — depressed regolith strip: two parallel `draw_illustrated_polygon` berms with `material_for("comet_regolith")`
2. **Pipe segment** — `draw_illustrated_polygon` pipe hull crossing trench
3. **Burst crack** at `end` — jagged 5–7 pt poly; **amber volatile glow** from crack (`draw_ground_fog_glow` + `draw_brood_vein_glow_line` recolored to `#ffb040` / `#ff6020`)
4. **Flow pulse** — sin(elapsed × 3.2) modulates glow radius; fuel **particles** drift upward 8–14 px (2–3 px ovals, not physics-heavy)
5. **Feed anchor** — point 12 WU from crack along line direction; squids snap here in FEEDING state

**L7 authored lines:** **6 feed lines** — 2 near lander approach, 2 on slope, 2 at depot perimeter. ~**10 of 16 squids** spawn in FEEDING on a line; rest PATROL/ROAM near station.

### 8A.4 Comet regolith · environment tiles

| Element | Technique | Reference |
|---------|-----------|-----------|
| **Mega-rocks** | Seeded convex verts + `draw_illustrated_polygon`, crater_count 3–6 | `asteroid_viz.py` |
| **Ice veins** | `draw_brood_vein_glow_line` with comet cyan palette | `brood_geology_viz.py` |
| **Trenches** | Paired berms + dark trench floor poly (deep material) | New |
| **Pebbles** | Frozen `Asteroid` props, SMALL tier | Existing entity |
| **Sky** | Void `#040810` + sparse starfield parallax (slow) | `starfield_viz.py` |
| **Boundary haze** | Outgassing edge — violet fog band at map rim | `chase_fx.py` |

**Draw order in `ExpeditionViewRenderer`:**

```text
sky → regolith base tiles → ice veins → fuel trenches/lines → rocks/pebbles
→ station mesh → bio nests → feed FX → enemies → avatar → gun FX → HUD
```

### 8A.5 Lighting & “shader” equivalents

This project’s “shaders” = **`LightRig` + faceted normals + rim bloom + fog glow**. No new GPU path.

| Effect | Implementation |
|--------|----------------|
| Faceted rock/station faces | `draw_illustrated_polygon` shade bands |
| Volatile fuel emissive | `draw_ground_fog_glow` + `lerp_hex(material.rim, "#ffb040", pulse)` |
| Ice glint | Key-facing edge lines when `normal_dot_key > 0.22 * rim_strength` |
| Squid biolum on pipes | `draw_brood_vein_glow_line` + `SQUID_WRAP_GLOW` under tentacles |
| EVA visor catch | Helmet arc highlight synced to `rig.key_dir` |
| Station depth | Layer nudge from `station_lit_draw.layer_nudge` — hub above pipes |

Add to `LightRig.for_play` when `theme == "comet"`: ambient **0.34**, rim **0.50** — slightly darker than drift for void contrast; fuel props provide local warm fill.

### 8A.6 Environment FX checklist

- [ ] 6 fuel feed lines with burst cracks + flow pulse
- [ ] Charter hub ≥ siege-station polygon budget
- [ ] 3 bio-nest pipe junctions with membrane rings
- [ ] Ice veins connect zone B → C (wayfinding)
- [ ] Depot valve interact: steam + amber sparkle on `COLLECT_CARGO`
- [ ] Lander pad: ship silhouette + ramp light pulse when extract ready
- [ ] Outgassing map edge: slow HP drain VFX + HUD warning

---

## 9. Architecture · repo mapping

### 9.1 Dependency direction (unchanged)

```text
levels/comet_*     → gameplay/expedition_* , core
render/expedition_* → gameplay , render/lit_draw , render/lighting
scenes/play.py     → expedition phase tick hook (mirror brood)
```

Gameplay never imports Tkinter. Expedition tick lives in gameplay; draw in render.

### 9.2 New modules (proposed)

| Module | Role | Mirrors |
|--------|------|---------|
| `gameplay/expedition_mission.py` | `ExpeditionPhase`, `ExpeditionState`, objective structs | `brood_moon_mission.py` |
| `gameplay/expedition_controller.py` | Phase tick, layout swap, dock/undock | `brood_moon_controller.py` |
| `gameplay/expedition_foot.py` | Humanoid movement, interact, combat | new (planetside_flight is ship-only) |
| `gameplay/comet_body.py` | Orbit path, landing band, phase freeze | extends `planet_mission.py` |
| `levels/comet_fuel_layout.py` | Orbital arena + comet path constants | `brood_moon_layout.py` |
| `levels/comet_fuel_expedition.py` | On-foot spawn, zones, squid placements | `brood_moon_surface.py` |
| `levels/comet_fuel_props.py` | Static mesh tables for rocks/station | `brood_moon_props.py` |
| `levels/level_data.py` | `build_comet_fuel_level()` | `build_brood_moon_level()` |
| `levels/level_profiles.py` | `comet_orbital_config`, `expedition_foot_config` | brood orbital/surface configs |
| `render/expedition_view_renderer.py` | Top-down draw pipeline | new (not TacticalViewRenderer) |
| `render/comet_orbital_viz.py` | Comet nucleus + tail in flight views | `planet_mission_viz.py` |
| `render/comet_surface_viz.py` | Regolith band, ice veins | `brood_moon_surface_viz.py` |
| `render/eva_viz.py` | Humanoid avatar | new |
| `render/expedition_fuel_viz.py` | Fuel lines, burst cracks, flow FX | new |
| `render/expedition_station_viz.py` | Fuel station top-down (may wrap station_viz) | `station_viz.py` |
| `gameplay/squid_behavior.py` | `SquidBehaviorMode`, feed point types | new |
| `gameplay/expedition_squid_ai.py` | `tick_expedition_squid` foot driver | new |

### 9.3 WorldConfig flags (proposed)

```python
# WorldConfig additions
expedition_mission: bool = False      # level uses expedition framework
expedition_foot: bool = False         # currently in on-foot mode (like surface_wrap marker)
comet_mission: bool = False           # orbital comet path active
```

`is_expedition_foot(config)` parallel to `is_planetside(config)`.

**Design lock:** Expedition foot = **top-down only** (like planetside = **no chase**). Document in module header like `planetside_flight.py`.

### 9.4 GameWorld ownership

```text
GameWorld
  expedition: ExpeditionState | None     # parallel to brood_moon: BroodMoonState
  avatar: EvaAvatar | None               # active during ON_FOOT; None in flight
  # ship frozen in expedition.parked_ship snapshot
```

`tick_expedition(world, dt, intent)` called from `GameWorld.update` when `expedition_mission` — same hook point as `tick_brood_moon`.

### 9.5 Layout swap contract

Mirror `apply_orbital_layout` / `apply_surface_layout`:

```text
apply_comet_orbital_layout(world, layout)
apply_expedition_foot_layout(world, layout)
```

Each swap:

- Rebakes `world.config` via level profile
- Replaces entities (asteroids, enemies, static props)
- Clears projectiles / explosions
- Rebuilds spatial indices
- Returns `True` when gravity field rebake needed (flight only)

---

## 10. Rendering & camera

### 10.1 Flight phases (Acts I & V)

Use existing `TacticalViewRenderer` + `PerspectiveViewRenderer`:

- Draw comet via `comet_orbital_viz` (nucleus chunks + tail)
- Draw landing band on tactical (reuse `draw_planet_landing_band_tactical` pattern)
- Chase: comet as distant lit blob + tail streak

### 10.2 Expedition phase (Act III)

New **`ExpeditionViewRenderer.draw(canvas, world, camera, ...)`**:

| Layer order | Content |
|-------------|---------|
| BG | Comet sky void + faint stars |
| Floor | Regolith tiles, ice veins |
| Props | Frozen pebbles, rocks |
| Station | Fuel station mesh (lit) |
| Enemies | Squids / skitters (top-down sprites) |
| Avatar | EVA captain |
| FX | Interact particles, gun flashes |
| HUD chrome | Shared `SciFiHudOverlay` expedition panel |

**Camera:** Fixed top-down follow avatar — center on `avatar.pos`, smooth blend (`TACTICAL_CENTER_FOLLOW`-style constants, new `EXPEDITION_FOLLOW`).

**No** gravity heatmap full-field on-foot (optional tiny local hazard glow near outgassing rift only).

### 10.3 TkRenderer routing

```text
if world.config.expedition_foot:
    expedition_renderer.draw(...)
elif camera.mode is TACTICAL:
    tactical.draw(...)
else:
    perspective.draw(...)
```

---

## 11. Combat, enemies, hazards

### 11.1 L7 enemy roster · spread map population

**Design lock:** L7 is **squid-forward** — many enemies spread across the map, not a handful in one room. Feeding squids create **optional stealth lanes**; patrol squids enforce pressure.

| Enemy | Count | Spawn zones | Behavior |
|-------|-------|-------------|----------|
| **Feeding squid** | **10** | On `FuelFeedLine` anchors | FEEDING — no dash until alerted |
| **Patrol squid** | **4** | Station perimeter + depot ring | Standard seek/lunge |
| **Roaming squid** | **2** | Slope between pad and depot | Wider detect; punishes sprint noise (future) — v1: normal AI |
| **Total** | **16** | Zones B–D | All count toward `clear_depot` |

**No skitters in L7 v1** — focus art budget on squid variants at foot scale. Skitters reserved for open tier.

| Variant | Viz | Scale vs flight |
|---------|-----|-----------------|
| Standard foot squid | `draw_squid_enemy_expedition` (new wrapper) | `radius=14`, `tentacle_reach=72`, tentacle count 8 |
| Feeding squid | Same + `draw_squid_feeding_fx` | Tentacles locked toward feed crack |
| Nest pod (static) | Brood membrane on pipe | Spawns 0 in L7 — visual only |

AI driver: **`tick_expedition_squid`** in `gameplay/expedition_squid_ai.py` — **not** raw `SquidEnemy.integrate` with ship prey. See §11A.

### 11.2 Hazard

| Hazard | Effect |
|--------|--------|
| Outgassing edge | Slow HP drain + pushback at map boundary |
| Volatile puddle | Contact heat (visual only in L7 v1 OK) |
| Collapse rift (zone E) | Blocked — tease for open tier |

### 11.3 Combat tuning

- TTK per squid: 3 sidearm body hits (reuse `SQUID_HITS_MAX`)
- Station clear count: **16 hostiles** (HUD `09/16` style)
- Feeding squid: **0.5× detect_range** while FEEDING — approach from behind line for advantage
- Alerted squid: full detect + **dash lunge** (see §11A)
- Avatar i-frames 0.4s after hit (match ship invuln grammar)
- Cling damage on foot: 1 hull chunk / 2.0 s if tentacles reach avatar (same interval as ship)

---

## 11A. Squid feeding behavior · standardization

This is **new gameplay code** — flight squids always hunt ship prey. Expedition squids need a **behavior mode layer** that is reusable for future open-tier levels (squids on ore veins, bio on water lines, etc.).

### 11A.1 Why this needs its own module

| Risk if bolted onto `SquidEnemy.integrate` | Consequence |
|--------------------------------------------|-------------|
| Feeding squids still receive `prey_pos=avatar` every frame | They dash at player while “feeding” — breaks design |
| Flight + foot share one integrate path | Regression on drift/rift/siege squids |
| No explicit alert transition | Player cannot learn feed → alert → engage loop |

**Decision (lock):** Add **`gameplay/squid_behavior.py`** with mode enum + driver; foot uses **`ExpeditionSquid`** wrapper or extended fields on spawn. Flight levels **unchanged** — default mode = `HUNT`.

### 11A.2 Behavior mode enum (framework standard)

```python
class SquidBehaviorMode(Enum):
    HUNT = auto()       # Flight default — existing integrate logic
    FEEDING = auto()    # Anchored to FeedPoint; no prey chase
    ALERT = auto()      # Brief 0.6 s orient toward threat; tentacles unhook
    ENGAGE = auto()     # Foot hunt — seek avatar, lunge, cling
    RETREAT = auto()    # Optional future — flee to nest when low HP
```

**Expedition-only modes:** FEEDING, ALERT, ENGAGE. HUNT = flight. RETREAT deferred.

### 11A.3 Feed point contract

```python
@dataclass(frozen=True, slots=True)
class SquidFeedPoint:
    id: str
    pos: Vec2                    # anchor on fuel line
    line_id: str                 # links to FuelFeedLine
    facing_angle: float          # mouth toward crack
    feed_radius: float = 28.0    # snap tolerance
```

Squid in FEEDING stores `feed_point_id: str | None` and `behavior_mode: SquidBehaviorMode`.

### 11A.4 FEEDING state rules (must-hold)

While `behavior_mode == FEEDING`:

| Rule | Implementation |
|------|----------------|
| **No dash toward avatar/ship** | Skip radial `approach_thrust` toward prey in integrate |
| **Position anchored** | Soft spring to `feed_point.pos` ± 8 WU wobble |
| **Tentacles target crack** | `update_tentacles_foot(..., feed_target=line.end)` — tips reach toward burst crack, not avatar |
| **Reduced awareness** | `detect_range_effective = detect_range * 0.5` |
| **No cling damage** | `clinging` forced false until ENGAGE |
| **Facing** | `facing_angle` blends toward feed crack direction |
| **Vulnerable** | Body hits still apply — rewarding sneak kills |

**Visual:** `draw_squid_feeding_fx` — extra amber glow on tentacle tips touching fuel flow; mantle pulsing slower (sin × 2.0 vs 4.0 engage).

### 11A.5 Alert & interrupt transitions

```text
FEEDING ──(trigger)──► ALERT ──(0.6 s)──► ENGAGE
   │                        │
   └──(kill)──────────────► dead
```

| Trigger | Threshold |
|---------|-----------|
| **Proximity alert** | Avatar within `detect_range * 0.5` for > 0.35 s continuous |
| **Damage alert** | Any body hit → instant ALERT |
| **Line sealed** | Optional `seal_vent` objective → feeders on that line → ALERT all |
| **Sibling alert** | Another squid on same line enters ENGAGE → chain ALERT within 480 WU (radio “panic”) |

**ALERT phase:** Squid unhooks tentacles (0.4 s blend), mantle brightens (`alarm=True` in viz), **no movement** toward player yet — gives player readable telegraph before dash.

**ENGAGE phase:** Call foot-adapted hunt:

- `prey_pos = avatar.pos`, `prey_radius = avatar.radius`
- Reuse orbit/lunge/cling math from `SquidEnemy.integrate` but **no gravity wells** (`wells=[]`)
- `max_speed` foot scale: 185 WU/s (slightly slower than flight 208 — fairness in corridors)

### 11A.6 Foot integrate API (contract)

```python
def tick_expedition_squid(
    squid: SquidEnemy,
    *,
    mode: SquidBehaviorMode,
    feed_point: SquidFeedPoint | None,
    feed_line: FuelFeedLine | None,
    avatar_pos: Vec2,
    avatar_radius: float,
    dt: float,
) -> SquidBehaviorMode:
    """Returns possibly-updated mode after tick."""
```

**Do not** call `world._squid_prey_for` on expedition foot — avatar is sole prey when ENGAGE.

Flight path remains:

```python
squid.integrate(dt, ship.pos, ship.vel, wells, ..., prey_radius=ship.radius)
```

### 11A.7 Standardization for future levels

| Concept | Reuse |
|---------|-------|
| `SquidBehaviorMode` | Any expedition map |
| `SquidFeedPoint` | Rename to `SquidAnchorPoint` for ore/bio feeds |
| `FuelFeedLine` | Generalize to `ExpeditionResourceLine` (fuel, water, spore) |
| `tick_expedition_squid` | Same driver; data-driven feed points from level layout |
| Viz `draw_squid_feeding_fx` | Parameterized accent color per resource type |

### 11A.8 Render additions (`render/squid_viz.py`)

New functions (foot only):

| Function | Role |
|----------|------|
| `draw_squid_enemy_expedition` | Top-down scale; `theme="comet"` glow |
| `draw_squid_feeding_fx` | Amber tip glow + fuel drip particles |
| `update_tentacles_foot_feeding` | Tips lerp to `feed_line.end` |

Reuse existing: `draw_squid_mantle`, `draw_squid_tentacles_enhanced`, `draw_squid_body_lit`, `draw_squid_coil_ring` — pass `engaging=(mode==ENGAGE)`.

### 11A.9 Tests (required before ship)

| Test | Assert |
|------|--------|
| `test_squid_feeding_no_dash` | FEEDING squid at feed point; avatar 200 WU away; velocity toward avatar < 10 WU/s for 2 s |
| `test_squid_proximity_alert` | Avatar enters detect bubble → mode ALERT then ENGAGE |
| `test_squid_damage_instant_alert` | One shot while FEEDING → ENGAGE within 1 tick |
| `test_squid_feeding_tentacles` | Tips closer to feed crack than avatar when FEEDING |
| `test_clear_depot_objective` | 16 spawns; kill all → objective complete |

### 11A.10 Cautions (critical)

1. **Never pass avatar as prey while FEEDING** — even for tentacle update; use feed crack coords.
2. **Flight regression** — run `tests/test_squid*.py` + drift level after any `SquidEnemy` edit; prefer new foot functions over editing integrate core.
3. **Off-screen hints** — feeding squids still hostile for objective count; show rim chevron when ENGAGE only (optional: suppress FEEDING hints until alert — design choice **suppress until ALERT** for stealth readability).
4. **Chain alert** — cap at 3 squids per event to avoid whole-map aggro from one shot.

---

## 12. HUD, audio, narrative

### 12.1 HUD strings

| Phase | Header |
|-------|--------|
| Orbital | `COMET APPROACH · HOLD E TO DOCK` |
| Expedition | `EXPEDITION · VOLATILE CHARTER` |
| Escape | `OUTGASSING · RTB GATE` |

Reuse holo panel fonts from `SciFiHudOverlay` — expedition uses comet accent.

### 12.2 Radio / briefing

- Chart briefing: comet orbit diagram on holo map (`ChartMapOverlay` — comet elliptical path glyph)
- Launch countdown: custom 3-2-1 copy for L7
- Level intro: one GIF or static holo (`assets/narrative/comet_fuel.gif`)

### 12.3 Audio direction (when audio lands)

- Foot: muffled helmet, suit servo
- Station: clank reverb, squid wet clicks
- Comet: low wind, ice creak

---

## 13. Future open-tier extension

Same codebase; **data + layout** scale up:

| Dimension | L7 extended | Future open |
|-----------|-------------|-------------|
| Map W×H | 2400×1800 | 4000×3200+ |
| Zones | 4 + 1 blocked | 6–8 + caves |
| Required objs | 3 | 1–2 |
| Optional objs | 0–2 | 6–10 |
| Time on-foot | 8–12 min | 15–25 min |
| Extraction | All required done | Minimum cargo only |

**Zone E (Ice Rift)** opens in open tier — second district, optional boss nest.

Expedition framework does **not** need fork — only `ExpeditionSite.tier = "open"` and larger prop tables.

---

## 14. Implementation phases

Recommended build order (each phase shippable behind dev flag):

| Phase | Deliverable | Validates |
|-------|-------------|-----------|
| **P0** | `ExpeditionPhase` stub + dev teleport ON_FOOT empty map | Phase swap |
| **P1** | EVA move + camera + greybox rocks (illustrated polys) | Feel |
| **P2** | Comet orbit in flight + dock band + cinematic placeholder | Full Act I |
| **P3** | Fuel station mesh + 6 feed lines + 16 squids (feeding AI) + sidearm | Combat + feed loop |
| **P4** | Fuel collect + extract + undock + parked ship | Loop closed |
| **P5** | Escape flight + win gate + campaign register | L7 playable |
| **P6** | FX pass, palette, briefing/intro, polish | Ship quality |
| **P7** | Tests: phase transitions, objective gates, layout swap | Regression |

Update `docs/ARCHITECTURE.md` when P0 lands with expedition section.

---

## 15. Design locks & risks

### Locks (do not drift without review)

1. **Expedition = top-down humanoid** — not ship-on-surface (that stays L6 planetside).
2. **No chase camera on-foot** — same lock as `planetside_flight.py`.
3. **No dashed connector lines** on expedition rim hints — entity chevrons only.
4. **Comet phase freezes** while docked.
5. **One controller per frame** — flight or foot, never both simming.
6. **Lit polygon standard** for all rock/station surfaces.

### Risks

| Risk | Mitigation |
|------|------------|
| Scope explosion (full RPG) | L7 = extended tier only; optional objs ≤2 |
| Genre whiplash | Keep expedition ≤40% of total L7 time |
| Duplicating brood surface code | Share phase machine + transitions; **do not** reuse toroidal ship surface |
| Humanoid viz weak | Budget time in P1; suit silhouette is gate before station art |
| Moving comet frustration | Freeze on dock; generous landing band |

---

## 16. References

### In-repo patterns to extend

| Path | Use |
|------|-----|
| `gameplay/brood_moon_mission.py` | Phase enum, cinematic state |
| `gameplay/brood_moon_controller.py` | Layout swap, hold-to-dock |
| `gameplay/planet_mission.py` | Landing band geometry |
| `gameplay/planetside_flight.py` | “Special phase” design lock doc style |
| `render/asteroid_viz.py` | Rock quality bar |
| `render/station_viz.py` | Fuel station hero asset |
| `render/offscreen_hostile_hints.py` | Expedition rim markers |
| `docs/ARCHITECTURE.md` | Scene/world/campaign model |

### External design precedents

| Reference | Lesson |
|-----------|--------|
| Metroid Prime Morph Ball | Mode swap is verb unlock; cinematic sells transition |
| Starbound ship ↔ surface | Unified inventory/progression across instances |
| FTL boarding | Nested tactical layer, same session |
| Tenet of the Spark | Context-gated switching beats free switching |
| Comet Rogue / Harvester | Top-down mining loop + dock grammar |

---

## 17. Zoom-out review · cautions & obvious flaws

### Full-picture framing

Gravity Ho, Matey! is a **flight-first arcade campaign** with nested mission phases (L4 waves, L6 brood orbital/surface). L7 adds a **third nested grammar**: humanoid top-down on a comet. The game remains one Tk canvas, one `GameWorld`, one campaign — but **three different player verbs** across the series (fly ship, fly ship on surface strip, walk EVA).

The expedition framework must **standardize transitions and objectives**, not homogenize level feel. L7 extended tier is the **smallest proof** that boots-on-rock works before any future open-tier mega-map.

### Obvious design flaws to avoid early

| Flaw | Why it hurts | Guard |
|------|--------------|-------|
| **Reusing L6 surface sim for L7** | Side-scroll ship ≠ top-down humanoid; wrong camera, wrap, boost | New `expedition_foot` sim; do not set `surface_wrap` for L7 |
| **`brood_moon_mission` boolean sprawl** | Third flag (`expedition_mission`) + fourth (`expedition_foot`) without phase API → `if` hell in `view_renderers` | Phase enum + `world.expedition.phase`; single `is_expedition_foot(config)` |
| **Ship sim running during on-foot** | Projectiles, boost, chart radiation tick while “outside ship” | Early-return path in `GameWorld.update` (mirror brood cinematic) |
| **Chase cam on EVA** | Chase projection assumes forward flight; breaks reads (L6 fixed via `_enforce_brood_surface_camera`) | `_enforce_expedition_camera`: force tactical/top-down; block `V` or toast |
| **Local comet map in flight coords** | 2400×1800 foot map embedded in 4800 orbital space → float jitter, camera bugs | **Separate local origin** on layout swap; store `parked_ship` snapshot |
| **Moving comet during EVA** | Pad drifts away from lander extract | **Freeze comet phase** on dock (non-negotiable) |
| **Genericizing brood in v1** | Refactoring L6 while building L7 doubles regression surface | **Parallel modules** first; extract shared `phase_mission` utils in P2 if duplication > ~80 lines |
| **Open-tier scope in L7** | 6 optional objectives + caves = second game | L7 ships with **0–2 optional** max; open tier is a **future level** |
| **Minigame damage silo** | EVA HP separate from campaign → player confusion | Route foot damage through `CampaignState.apply_damage` with new `DamageSource.EVA` |
| **Ingress line déjà vu** | Connector lines on foot map | Rim chevrons only (`offscreen_hostile_hints`) |

### Extra caution · things easy to underestimate

1. **`view_renderers.py` branching** — Already theme × phase heavy (brood orbital/surface/chase). L7 adds another renderer path. **Do not** add `if comet` blocks inside every brood block; route at `TkRenderer` / `PlayScene.draw` top.

2. **Gravity field rebake** — Brood returns `True` from `tick_brood_moon` on layout swap; `PlayScene` rebakes and snaps camera. Expedition foot map may have **zero wells** — still rebake to empty/low field or skip heatmap draw explicitly.

3. **Cinematic early return** — `world.update` returns immediately during brood cinematic (no ship/enemy tick). Expedition must identical; otherwise ship drifts during dock GIF.

4. **Win gate logic** — `finish_unlocked` is brood-specific (`ORBITAL_RETURN` + seal). L7 needs explicit `ExpeditionPhase.ESCAPE_FLIGHT` + fuel cargo check — **do not** overload brood properties.

5. **Tests that assume 6 levels** — `next_level_id("brood_moon")` is `None` today; adding L7 breaks tests intentionally. Run full pytest after registry change.

6. **Chart briefing preview** — `ChartBriefingScene` builds preview world via `build_level`. Expedition orbital must look correct in holo map **before** play (comet path glyph).

7. **Companion entities** — Drone wingman / Nifflerp sync in `PlayScene.update`. Policy needed: **hidden/disabled on-foot** or follow in orbit only.

8. **Weapon heat / shop** — Mid-level shop (`B`) on foot could trivialize sidearm. Lock shop to flight phases only unless designed.

### Zoom-out success criteria

L7 is successful if:

- A player can describe the level as **“fly → land → clear station → load fuel → leave → escape”** without feeling they played a different game.
- Future open-tier level requires **only** new layout + objective JSON-like data, not new renderers.
- Brood Moon regression tests stay green without modifying L6 behavior.

---

## 18. External research synthesis (games & patterns)

### Reference games mapped to L7 decisions

| Game / project | Relevant mechanic | Take for GH Matey | Reject |
|----------------|-------------------|-------------------|--------|
| **Metroid Prime** | Morph Ball camera swap; unskippable transition | Sell mode change with cinematic; third-person/top-down as “verb room” | First-person humanoid complexity |
| **Starbound** | Beam down/up; separate world instances; shared inventory | Cargo/fuel returns to ship; campaign treasury unchanged | Full planet proc sim |
| **FTL** | Boarding as same-session tactical layer | One HUD shell; pause-friendly real-time on foot | Crew management UI |
| **Harvester (GDQuest OSS)** | Fly → dock (E) → mine → return; FSM states | Hold-E dock grammar; state machine per mode | Separate Godot project structure |
| **Comet Rogue** | Top-down asteroid; time pressure; destructible terrain | Escalation if player lingers (soft radio); illustrated rocks | Full proc destructible voxels |
| **Hyper Light Drifter** | Top-down combat readability; landmarks; optional exploration | Strong silhouettes; station as landmark; fairness via telegraph | Non-linear open world for L7 |
| **Dark Souls / HLD** | Gated paths reduce overwhelm | L7 linear required chain; future open tier uses blocked doors/rifts | Opaque progression |
| **Tenet of the Spark** | Context-gated layer switching | Dock only in band; expedition only after cinematic | Free-switch three worlds |

### Pattern: finite state machine (implementation aim)

Adopt **explicit phase FSM** (GDQuest FSM pattern): one active phase owns tick + input + draw delegation.

```text
PlayScene
  └─ delegates to active phase handler:
       FlightPhaseHandler      (ORBITAL, ESCAPE_FLIGHT)
       CinematicPhaseHandler   (DOCK, UNDOCK)
       ExpeditionPhaseHandler  (ON_FOOT)
```

Brood already * behaves* like FSM but is embedded in `tick_brood_moon`. L7 should **document** the FSM in `expedition_mission.py` and avoid scattering phase checks across 20 files.

### Pattern: dual coordinate spaces (floating origin lite)

Industry practice for nested bodies: **do not** simulate on-foot in orbital world coordinates at comet position. Use:

- **Orbital space:** comet body at `comet_pos(phase)`
- **Foot space:** local map 0…W, 0…H; lander at fixed pad coords
- **Undock:** restore orbital ship at pad docking point on comet

This avoids precision issues noted in large-coordinate floating-origin discussions and keeps camera follow simple.

### Pattern: objective graph (future-proof)

```text
ExpeditionObjectiveGraph
  nodes: ObjectiveNode(id, type, required, prerequisites[])
  evaluate(): blocked | active | complete
  can_extract(): all required complete
```

L7 graph is a **line** (clear → load → extract). Future open tier adds optional nodes with `required: false` and no extract gate.

---

## 19. Full repo trace · upstream → downstream

### 19.1 Player journey (runtime spine)

```text
TitleScene (deploy L7)
  → ChartBriefingScene (build_level preview, holo map)
  → LaunchCountdownScene (PlaySession frozen)
  → PlayScene
       loop: input → world.update → camera → draw
       win → record_level_cleared → ChartBriefing (L8…) or EndScene
```

Every expedition feature must survive this spine **without forking** `start_play` / `build_play_session`.

### 19.2 Files that MUST change for L7 (by layer)

#### Levels & registry

| File | Change |
|------|--------|
| `levels/level_registry.py` | Add `comet_fuel` to `LEVEL_ORDER`, `LEVEL_BUILDERS`, `LEVEL_LABELS`; `next_level_id("brood_moon")` → `"comet_fuel"` |
| `levels/level_data.py` | `build_comet_fuel_level()` |
| `levels/level_profiles.py` | `comet_orbital_config()`, `expedition_foot_config()` |
| `levels/comet_fuel_layout.py` | **NEW** — orbital arena, comet path, finish gate |
| `levels/comet_fuel_expedition.py` | **NEW** — foot spawns, squids, fuel nodes, station anchor |
| `levels/comet_fuel_props.py` | **NEW** — static rock/station prop tables |
| `levels/comet_fuel_asteroids.py` | **NEW** — orbital debris (mirror `brood_moon_asteroids.py`) |

#### Gameplay core

| File | Change |
|------|--------|
| `gameplay/entities.py` | `WorldConfig`: `expedition_mission`, `expedition_foot`; optional `EvaAvatar` dataclass |
| `gameplay/world.py` | `expedition: ExpeditionState \| None`; `avatar`; tick branch; `finish_unlocked` branch; **early return** cinematic + on-foot rules |
| `gameplay/expedition_mission.py` | **NEW** — phases, objectives, state |
| `gameplay/expedition_controller.py` | **NEW** — `tick_expedition`, `apply_orbital_layout`, `apply_foot_layout` |
| `gameplay/expedition_foot.py` | **NEW** — movement, interact, foot combat |
| `gameplay/comet_body.py` | **NEW** — orbit path, landing band, phase freeze |
| `gameplay/planet_mission.py` | Extend header docs; optional shared `ApproachBody` alias |
| `gameplay/hud_objectives.py` | Expedition objective counters |
| `gameplay/damage.py` | `DamageSource.EVA` + death reasons |
| `gameplay/session.py` | Verify campaign wiring works with foot damage |
| `gameplay/chart_bounds.py` | Possibly disable radiation on foot (`expedition_foot`) |

#### Scenes

| File | Change |
|------|--------|
| `scenes/play.py` | `_enforce_expedition_camera`; cinematic skip (Space); draw branch for expedition cinematic; camera follow **avatar** on foot |
| `scenes/play_session.py` | No change if `build_level` suffices |
| `scenes/chart_briefing.py` | Preview must show comet glyph (via world content) |
| `scenes/end.py` / `game_flow.py` | Unchanged pattern |

#### Render

| File | Change |
|------|--------|
| `render/tk_renderer.py` | Route `expedition_foot` → `ExpeditionViewRenderer`; expedition transition overlay |
| `render/view_renderers.py` | Comet orbital viz hooks in flight renderers (minimal `if theme==comet`) |
| `render/expedition_view_renderer.py` | **NEW** |
| `render/comet_orbital_viz.py` | **NEW** |
| `render/comet_surface_viz.py` | **NEW** |
| `render/eva_viz.py` | **NEW** |
| `render/expedition_station_viz.py` | **NEW** (top-down station) |
| `render/expedition_transition_overlay.py` | **NEW** or generalize `brood_moon_transition_overlay.py` |
| `render/hud_overlay.py` | Expedition header, hold meters, objective rail |
| `render/chart_map_overlay.py` | Comet orbit + expedition intel rows |
| `render/edge_hints.py` | Expedition foot hints (reuse `offscreen_hostile_hints`) |
| `render/lighting.py` | `theme == "comet"` materials: regolith, ice, fuel, suit |
| `render/palette.py` | Comet palette tokens |
| `render/starfield_viz.py` | Comet star tint |
| `render/chase_fx.py` | Coma wash optional in chase |
| `render/camera.py` | `snap_tactical_to_avatar`; expedition follow center |
| `render/planet_mission_viz.py` | Reuse landing band draw for comet approach |

#### Narrative & title

| File | Change |
|------|--------|
| `narrative/chart_briefing_copy.py` | L7 `LEVEL_BRIEFING`, `LEVEL_INTEL` |
| `narrative/level_intros.py` | L7 intro spec |
| `narrative/launch_countdown.py` | L7 countdown copy |
| `render/title_info_pages.py` | `_CAMPAIGN_ARC`, `_LEVEL_LOCK` |
| `render/title_overlay.py` | Deploy blurb |
| `assets/narrative/` | `comet_fuel_dock.gif`, `comet_fuel_undock.gif`, intro art |

#### Tests (new + update)

| File | Change |
|------|--------|
| `tests/test_comet_fuel_level.py` | **NEW** — registry, dock, foot swap, objectives, win |
| `tests/test_expedition_controller.py` | **NEW** — phase transitions |
| `tests/test_brood_moon_level.py` | Update `next_level_id("brood_moon")` expectation |
| `tests/test_levels.py` | Registry parity |
| `tests/test_chart_briefing_copy.py` | L7 copy keys |
| `tests/test_hud_objectives.py` | Expedition counters |
| `tests/test_offscreen_hostile_hints.py` | Foot mode camera cases |
| `docs/ARCHITECTURE.md` | Expedition section |

### 19.3 Read-only dependencies (patterns to study, not necessarily edit)

| File | Why read |
|------|----------|
| `gameplay/brood_moon_controller.py` | Layout swap template |
| `gameplay/brood_moon_mission.py` | Phase + cinematic |
| `gameplay/planetside_flight.py` | Special-phase design lock |
| `gameplay/weapon_combat.py` | Foot gun may share projectile pipeline |
| `gameplay/wave_mission.py` | Not used L7 — avoid coupling |
| `render/lit_draw.py` | All surface art |
| `render/asteroid_viz.py` | Rock quality |
| `render/station_viz.py` / `station_mesh.py` | Fuel station |
| `render/squid_viz.py` | Foot-scale squids |
| `util/input.py` | `ControlIntent` mapping |

### 19.4 `GameWorld.update` tick order (critical integration point)

Current order (simplified):

```text
brood tick (may early-return if cinematic)
→ invuln → asteroids → ship → waves → enemies → … → finish → loss
```

**Required expedition order:**

```text
expedition tick (may early-return if cinematic OR on_foot with foot-only sim)
→ if ON_FOOT: avatar tick, foot enemies, foot projectiles, objectives, extract check; SKIP ship/waves/chart_radiation
→ if ORBITAL/ESCAPE FLIGHT: existing flight tick + comet phase advance
→ finish_unlocked evaluation includes fuel + phase
```

**Brood coexistence:** L7 world has `expedition` not `brood_moon` — no dual mission on one level.

### 19.5 `PlayScene.draw` branch (mirror brood)

Current:

```text
if brood.in_cinematic → draw_brood_transition (early return)
else → draw_world
```

Required:

```text
if expedition.in_cinematic → draw_expedition_transition (early return)
elif expedition.on_foot → draw_expedition_world (avatar camera)
else → draw_world (flight)
```

### 19.6 Standardization for future levels (framework deliverables)

| Deliverable | Consumer |
|-------------|----------|
| `ExpeditionPhase` enum | All dock/foot levels |
| `ExpeditionSite` dataclass (layout ref, tier, objectives) | Level authors |
| `apply_expedition_foot_layout(world, site)` | Controller |
| `ExpeditionViewRenderer` | All foot phases |
| `objective_counters_for_world` extension | HUD |
| `is_expedition_foot(config)` | Camera, input, damage |
| Registry validation | `_validate_registry()` + briefing copy completeness test |

Future **open tier** only adds: larger `comet_fuel_expedition`-style layout + more optional objectives — not new phase types.

---

## 20. Implementation contracts (coding standard)

These are **must-hold contracts** for PR review — not suggestions.

### 20.1 Phase contract

```python
class ExpeditionPhase(Enum):
    ORBITAL = auto()
    DOCK_CINEMATIC = auto()
    ON_FOOT = auto()
    UNDOCK_CINEMATIC = auto()
    ESCAPE_FLIGHT = auto()
```

| Transition | Precondition | Side effects |
|------------|--------------|--------------|
| ORBITAL → DOCK_CINEMATIC | In landing band; hold charged | Snapshot `parked_ship`; freeze comet phase |
| DOCK_CINEMATIC → ON_FOOT | cinematic elapsed | `apply_foot_layout`; spawn avatar at pad |
| ON_FOOT → UNDOCK_CINEMATIC | required objectives met; hold at lander | Attach cargo to expedition state |
| UNDOCK_CINEMATIC → ESCAPE_FLIGHT | cinematic elapsed | `apply_orbital_layout(return=True)`; restore ship |
| ESCAPE_FLIGHT → WIN | gate entered + fuel aboard | `GameStatus.WON` |

### 20.2 Layout swap contract

Every `apply_*_layout` must:

1. Replace `world.config` via `level_profiles` factory  
2. Set/clear entity lists explicitly (no stale enemies)  
3. `projectiles.clear()`, `explosions.active.clear()`  
4. Rebuild `asteroid_spatial` if asteroids exist  
5. `refresh_threat_snapshots()`  
6. Return whether gravity rebake needed  

### 20.3 Simulation ownership contract

| Phase | Simulates | Does NOT simulate |
|-------|-----------|-------------------|
| ORBITAL / ESCAPE | Ship, flight enemies, asteroids, wells | Avatar |
| ON_FOOT | Avatar, foot enemies, interact nodes | Ship thrust, wave director, chart radiation |
| CINEMATIC | Timer only | Everything else |

Enforced by early `return` from `GameWorld.update` when `expedition.in_cinematic` or by gating subsystems with `is_expedition_foot(config)`.

### 20.4 Damage contract

| Source | Applies to | Campaign |
|--------|------------|----------|
| Foot enemy | Avatar / EVA suit | `apply_damage` → hull chunks |
| Foot hazard (outgassing) | Avatar | same |
| Flight after undock | Ship | unchanged |

Respawn on foot: at lander with i-frames; **do not** call `recover_ship_in_place` (ship is parked).

### 20.5 Render contract

- All foot entities use `LightRig.for_play(theme="comet", view="tactical")` or `"expedition"` view flag if added to `LightRig.for_play`.
- Rocks on foot map: **`draw_illustrated_polygon`** minimum; pebbles may use `draw_simplified_polygon`.
- Station: **`draw_station_layer_polygons`** or top-down wrapper — no raw `create_rectangle` hull.
- Off-screen enemies: **`append_offscreen_hostile_hints`** only — no lane lines.

### 20.6 Objective contract

```python
@dataclass(frozen=True)
class ExpeditionObjective:
    id: str
    type: ObjectiveType
    required: bool
    zone_id: str
    label: str
```

L7 instance:

```python
OBJECTIVES = (
    ExpeditionObjective("clear_depot", CLEAR_HOSTILES, True, "station", "Clear depot"),
    ExpeditionObjective("load_fuel", COLLECT_CARGO, True, "depot", "Load fuel"),
)
# EXTRACT is system objective, not optional
```

Future open tier adds entries with `required=False` — same struct.

### 20.7 Registry contract

Adding L7 must update in **one commit**:

- `LEVEL_ORDER`, `LEVEL_BUILDERS`, `LEVEL_LABELS`
- `LEVEL_BRIEFING`, `LEVEL_INTEL`, `LEVEL_INTROS`, launch countdown
- `_CAMPAIGN_ARC`, `_LEVEL_LOCK`, title deploy blurbs
- `progress.py` unlock chain (implicit via order)
- Tests listed in §19.2

---

## 21. Open decisions register

Decisions that **must be locked before P3** (foot combat + station):

| ID | Question | Options | Recommendation | Blocker if open |
|----|----------|---------|----------------|-----------------|
| D1 | Level id string | `comet_fuel`, `volatile_charter`, `comet_hold` | `comet_fuel` | Registry |
| D2 | EVA damage model | Shared hull chunks vs separate suit meter | **Shared hull chunks** (campaign consistency) | HUD + damage |
| D3 | Foot fire input | Auto-aim nearest vs manual aim | **Manual aim** (mouse/dir keys) — matches ship skill | `expedition_foot.py` |
| D4 | Comet theme string | `comet` vs reuse `drift` palette | **`comet`** new theme | palette/lighting |
| D5 | Chase cam during orbital flight | Allowed vs tactical-only level | **Allowed orbital/escape**; blocked on-foot | `play.py` |
| D6 | Drone/Nifflerp on foot | Hide vs orbit ship | **Hide / inactive** on-foot | ally tick |
| D7 | Shop on foot | Block vs allow | **Block** (`B` no-op + toast) | input |
| D9 | Squid count | 5 vs 8 vs 16 | **16 authored** (10 feeding + 6 patrol/roam) | layout + AI |
| D8 | Fuel carry encumbrance | Slow sprint vs no penalty | **No sprint while carrying** | movement tuning |
| D10 | Win condition | Fuel + reach gate vs gate only after undock | **Undock with fuel + fly to gate** | `finish_unlocked` |
| D11 | Transition overlay | Generalize brood overlay vs duplicate | **Generalize** to `MissionTransitionOverlay` accepting stem + state | render |
| D12 | Cinematic skip | Space to skip like brood | **Yes** after first clear; optional first-run unskippable | play input |
| D13 | Post-brood unlock | L7 requires L6 clear | **Yes** — `_LEVEL_LOCK["comet_fuel"] = "Clear Brood Moon"` | title |
| D14 | Expedition local map size | 2400×1800 vs 3200×2400 | **2400×1800** L7; open tier larger later | layout art |
| D15 | Foot projectile pipeline | Reuse `Projectile` vs foot-only hitscan | **Reuse `Projectile`** with `foot_scale` flag | combat code |

| D16 | Off-screen hint for feeders | Show always vs when alerted | **Suppress until ALERT** | edge_hints |
| D17 | Squid behavior module | Extend integrate vs new driver | **New `squid_behavior.py` + foot driver** | AI architecture |

### Decisions explicitly deferred (post-L7)

- Open-tier optional objective rewards table  
- Comet map persistence between visits  
- Procedural foot terrain  
- Multi-comet levels  
- Co-op / multiplayer foot  

---

## 22. Cross-cutting concerns matrix

| Concern | Flight orbital | Dock cinematic | On-foot | Escape flight | Future open tier |
|---------|----------------|----------------|---------|---------------|------------------|
| **Camera** | Tactical/Chase | Overlay | Top-down follow avatar | Tactical/Chase | + minimap fog |
| **Input** | Ship intent | Skip only | EVA intent | Ship intent | Same |
| **HUD** | COMET APPROACH | Transition | EXPEDITION objectives | OUTGASSING | + optional list |
| **Damage** | Ship | None | EVA | Ship | Same |
| **Enemies** | Asteroids / drift | None | Squids | None / environmental | + optional nests |
| **Companions** | Drone/Nifflerp active | Frozen | **Inactive** | Active | Policy TBD |
| **Gravity heatmap** | Wells + bake | Off | Off or flat | Wells | Same |
| **Chart radiation** | Off (open arena) | Off | **Off** | Off | Same |
| **Edge hints** | Beacons/gate | None | Off-screen hostiles | Gate | + optional POIs |
| **Objectives** | Reach band | None | Clear/load | Reach gate | Many optional |
| **Treasury/jewels** | Flight pickups | None | Foot pickups OK | Flight | Same |
| **Tests** | `test_comet_fuel_level` orbital | cinematic skip | foot objectives | win chain | extend optional |
| **Narrative** | Briefing/intel | dock GIF | radio squawk | escape | lore terminals |

### Theme × renderer matrix (avoid combinatorial explosion)

Do **not** add `brood && comet && foot` triple branches. Target structure:

```text
draw_play():
  if expedition_foot: expedition_renderer
  elif standard flight: tactical | perspective (existing)
  
draw_flight_extras(theme):
  match theme:
    brood_moon: brood orbital/surface bands
    comet: comet_orbital_viz
    default: pass
```

### Validation gates per implementation phase

| Phase | Gate test |
|-------|-----------|
| P0 | Phase enum transitions in unit test without Tk |
| P1 | Avatar moves; camera follows; greybox rock uses `draw_illustrated_polygon` |
| P2 | Dock band + cinematic skip + layout swap rebakes gravity |
| P3 | Clear 5 squids → objective complete |
| P4 | Fuel load → extract enabled → undock restores ship pos on comet |
| P5 | Full win; registry chain; briefing copy exists |
| P6 | Visual review: station ≥ asteroid detail |
| P7 | Full pytest green; brood tests unchanged except `next_level_id` |

---

## 23. Implementation readiness · next build pass

This section is the **handoff checklist** for the full L7 coding pass. Execute in order; each block should commit-test before the next.

### 23.1 Locked design summary (do not re-litigate in code pass)

| Topic | Lock |
|-------|------|
| Avatar | Top-down EVA captain, lit polygons, §6A |
| Weapon | Void Cutlass sidearm, manual aim, 3 hits/squid |
| Squids | 16 total; 10 feeding on 6 fuel lines; behavior FSM §11A |
| Station | Charter Fuel House, top-down station mesh + feed trenches §8A |
| Visual bar | `LightRig` + `draw_illustrated_polygon` everywhere — no flat placeholders in ship build |
| Framework | Parallel expedition modules; do not refactor brood in v1 |

### 23.2 Build order · recommended message splits

**Can L7 ship in one implementation message?**  
**Playable vertical slice — yes.** Full quality (orbital comet, illustrated station, 16 squids feeding, narrative, all tests) in a single pass — **no**; diff would be ~40 files, hard to review, high regression risk.

**Should squid mechanics land before the L7 core?**  
**Not in isolation.** Feeding AI needs avatar position, feed points, and the foot tick loop. Building `squid_behavior.py` alone with unit tests is fine, but it must plug into **Wave A foot sandbox** in the same pass — otherwise integration rework is likely.

#### Recommended staging (3 messages)

| Message | Scope | Outcome |
|---------|-------|---------|
| **M1 — Foot combat slice** | Wave A + Wave C (squid AI, feed lines, sidearm, greybox EVA) + dev entry to ON_FOOT | Walk, shoot, feeding squids, clear objective — **no orbital yet** |
| **M2 — Full loop** | Wave B + Wave D (comet orbit, dock/undock, fuel hold-E, extract, win gate, registry) | Campaign-playable L7, greybox art OK |
| **M3 — Ship quality** | Wave E (station mesh, fuel viz, palette, briefing, HUD polish, full pytest) | Matches asteroid/ship visual bar |

If you insist on **one message**, target **M1+M2 only** — playable end-to-end with placeholder art; polish deferred.

#### File creation sequence (within M1)

**Wave A — skeleton (P0–P1)** · *M1*

1. `gameplay/expedition_mission.py` — phases, state, objectives
2. `gameplay/entities.py` — `EvaAvatar`, `WorldConfig` flags
3. `gameplay/expedition_foot.py` — movement, aim, fire
4. `gameplay/expedition_controller.py` — layout swap stubs
5. `levels/comet_fuel_layout.py` + `level_profiles.py` profiles
6. `levels/level_data.py` — `build_comet_fuel_level()`
7. `levels/level_registry.py` — register L7
8. `render/eva_viz.py` — greybox lit avatar
9. `render/expedition_view_renderer.py` — draw loop
10. `render/palette.py` + `lighting.py` — comet theme + eva materials
11. `scenes/play.py` — expedition camera + draw route
12. `gameplay/world.py` — expedition tick hook, early return
13. `tests/test_comet_fuel_level.py` — registry + foot move smoke

**Wave B — orbital + dock (P2)** · *M2*

14. `gameplay/comet_body.py`
15. `render/comet_orbital_viz.py`
16. `render/expedition_transition_overlay.py` (generalize brood)
17. Dock band + cinematic in controller
18. Tests: dock transition, cinematic skip

**Wave C — environment + squids (P3)** · *M1* (squid AI + feed lines before full station art)

19. `levels/comet_fuel_props.py` — station mesh, rocks
20. `levels/comet_fuel_expedition.py` — spawns, zones, 6 feed lines, 16 squids
21. `gameplay/squid_behavior.py`
22. `gameplay/expedition_squid_ai.py`
23. `render/expedition_fuel_viz.py`
24. `render/expedition_station_viz.py`
25. `render/comet_surface_viz.py`
26. Extend `render/squid_viz.py` — expedition + feeding FX
27. `tests/test_expedition_squid_ai.py` — feeding no-dash, alert chain

**Wave D — objectives + loop (P4–P5)** · *M2*

28. Fuel collect interact nodes
29. Extract / undock / parked ship restore
30. `finish_unlocked` + escape flight
31. Narrative: briefing, intro, title arc, `_LEVEL_LOCK`
32. Full win path test

**Wave E — polish (P6–P7)** · *M3*

33. FX pass §8.3 + §8A.6
34. HUD expedition rail + off-screen hints (alert-only feeders)
35. Full pytest + brood regression

### 23.3 New datatypes checklist

| Type | Module |
|------|--------|
| `ExpeditionPhase`, `ExpeditionState` | `expedition_mission.py` |
| `EvaAvatar`, `EvaAnimState` | `entities.py` / `expedition_foot.py` |
| `FuelFeedLine`, `SquidFeedPoint` | `comet_fuel_expedition.py` or `expedition_props.py` |
| `SquidBehaviorMode` | `squid_behavior.py` |
| `ExpeditionObjective` | `expedition_mission.py` |

### 23.4 Standardization deliverables (framework)

These APIs must exist and be documented in module headers for future open-tier levels:

- `is_expedition_foot(config) -> bool`
- `apply_expedition_foot_layout(world, site) -> bool` (rebake flag)
- `tick_expedition(world, dt, intent) -> bool`
- `tick_expedition_squid(...)` — foot AI driver
- `ExpeditionViewRenderer.draw(...)` — foot render pipeline
- `objective_counters_for_world` extension for expedition
- `ExpeditionSite` tier field (`extended` | `open`)

### 23.5 Acceptance criteria · L7 shippable

- [ ] Campaign: clear brood → L7 unlocks on title
- [ ] Full run: orbit → dock → clear 16 squids → **hold E ×3** load fuel → hold E extract → undock → gate win
- [ ] ≥10 squids visibly feeding on fuel lines at spawn; no dash until alert
- [ ] EVA + station + rocks use illustrated lit draw — visual review passes asteroid bar
- [ ] Brood Moon unchanged except `next_level_id("brood_moon") == "comet_fuel"`
- [ ] All tests green including §11A.9 feeding tests

---

## 24. Final pass · hold-E grammar & build strategy

### 24.1 Hold E — unified interaction standard (design lock)

**One key for all “work” verbs** — matches brood dock, relay repair, and player expectation. No separate F for fuel or R for repair on L7.

`PlayScene` already passes `interaction_hold = input_state.down("e")` into `world.update`. Expedition reuses this — **no new key bindings**.

#### Interaction table · L7

| Context | Phase | Hold duration | HUD label | Completes |
|---------|-------|---------------|-----------|-----------|
| Comet landing band | ORBITAL | 1.0 s (`LANDING_CHARGE_SECONDS`) | `HOLD E · DOCK` | → DOCK_CINEMATIC |
| Depot valve / fuel pump | ON_FOOT | **1.2 s** (`FUEL_LOAD_CHARGE_SECONDS`) | `HOLD E · LOAD FUEL` | +33% fuel meter per node (3 nodes) |
| Busted line clamp (optional) | ON_FOOT | 0.9 s (`SEAL_CHARGE_SECONDS`) | `HOLD E · SEAL LINE` | Optional `seal_vent` objective |
| Charter log terminal | ON_FOOT | 0.7 s (`INTERACT_CHARGE_SECONDS`) | `HOLD E · DOWNLOAD LOG` | Optional codex |
| Lander extract | ON_FOOT | 1.0 s (`EXTRACT_CHARGE_SECONDS`) | `HOLD E · RTB` | → UNDOCK_CINEMATIC (requires clear + fuel) |

#### Interaction node contract

```python
@dataclass(frozen=True, slots=True)
class ExpeditionInteractNode:
    id: str
    pos: Vec2
    radius: float = 48.0
    kind: InteractKind  # FUEL_VALVE, CHARTER_LOG, SEAL_LINE, EXTRACT_PAD
    charge_seconds: float
    objective_id: str | None  # links to objective graph
    one_shot: bool = True
```

**Tick logic** (`expedition_foot.py`):

1. Find nearest node within `radius` where prerequisites met.
2. If `interaction_hold` and not firing: increment `node_charge`; avatar → `EvaAnimState.INTERACT`.
3. On charge complete: fire callback (add fuel, complete optional, start extract).
4. Release E early: charge decays at 2× rate (brood landing charge grammar).

**While holding E:** movement speed × 0.35; cannot sprint; can cancel by moving out of radius.

**Fuel load flow (locked):**

```text
Player at depot valve → HOLD E 1.2s → canister attaches to pack (visual) OR meter +33%
Repeat at 2nd and 3rd valve → load_fuel complete
Walk to lander → HOLD E 1.0s extract (only if clear_depot + load_fuel done)
```

No auto-pickup — always hold E at authored nodes.

### 24.2 Final detail gaps closed

| Gap | Resolution |
|-----|------------|
| Dev entry without orbital | M1: `build_comet_fuel_level(dev_foot=True)` spawns directly ON_FOOT at pad for iteration |
| `EXTRACT_CHARGE_SECONDS` | Add to `comet_fuel_layout.py` mirroring brood `LIFTOFF_CHARGE_SECONDS` |
| Feeding squid off-screen hints | Suppress until ALERT (D16) |
| Interact HUD | Reuse brood hold meter arc in `hud_overlay.py` — new `draw_expedition_interact_meter` |
| Damage while interacting | Taking hit cancels charge; does not reset completed nodes |
| Fuel carry | After each load, encumbered until extract — no sprint (D8 locked) |
| Comet briefing preview | M2 gate — holo map shows comet ellipse even if foot art greybox |
| Constants file | All charge seconds in `levels/comet_fuel_layout.py` (single source) |

### 24.3 Constants · copy into layout module

```python
LANDING_CHARGE_SECONDS = 1.0
EXTRACT_CHARGE_SECONDS = 1.0
FUEL_LOAD_CHARGE_SECONDS = 1.2
SEAL_CHARGE_SECONDS = 0.9
INTERACT_CHARGE_SECONDS = 0.7
CINEMATIC_DEFAULT_SECONDS = 4.5
FUEL_NODES_REQUIRED = 3
EXPEDITION_SQUID_COUNT = 16
EXPEDITION_FEEDING_SQUID_COUNT = 10
FUEL_FEED_LINE_COUNT = 6
```

### 24.4 What “done” means per message

**M1 done when:** Dev-spawn on foot map; walk + aim + shoot; 6 feed lines visible (greybox); 16 squids with feeding/alert/engage; clear_depot objective fires; hold E loads fuel at 3 valves.

**M2 done when:** Full campaign entry; orbit comet; dock cinematic; foot loop; undock; escape gate win; L7 in registry + unlock chain.

**M3 done when:** Illustrated station/rocks/EVA; feeding FX; briefing copy; full pytest green.

### 24.5 Squid-before-core verdict

| Approach | Verdict |
|----------|---------|
| Squid AI only, no foot sim | ❌ Too disconnected; rework at integrate |
| Foot sandbox + squid AI together (M1) | ✅ Best first slice; tests prove feeding contract |
| Full end-to-end one message, greybox OK | ⚠️ Possible (M1+M2); tight but feasible |
| Full end-to-end one message, ship-quality art | ❌ Not feasible without quality collapse |

**Next message recommendation:** If one message → **M1+M2** (playable full loop, greybox visuals). If two messages → **M1 then M2**. Squid mechanics ship **inside** M1 foot tick, not as a standalone pre-pass.

---

*Document owner: design session 2026-06-02. Revise when L7 id/name locks or first prototype changes phase names.*
