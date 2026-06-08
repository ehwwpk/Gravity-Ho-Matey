# Space Junk — System Specification

**Gravity Ho, Matey!** · Authoring-grade indestructible metal barriers  
**Status:** **Implemented (v1)** — building block ready; no production level ships junk yet  
**Purpose:** Standardized “scrap metal wall” objects for race courses, chokepoints, and hard-closed map regions in future levels.

---

## Contents

1. [Executive summary](#1-executive-summary)
2. [Design goals & non-goals](#2-design-goals--non-goals)
3. [Player identity](#3-player-identity)
4. [Distinction matrix](#4-distinction-matrix)
5. [Entity model](#5-entity-model)
6. [Shape catalog (prefabs)](#6-shape-catalog-prefabs)
7. [Collision & contact policy](#7-collision--contact-policy)
8. [Combat & weapon interaction](#8-combat--weapon-interaction)
9. [Visual language](#9-visual-language)
10. [Rendering plan](#10-rendering-plan)
11. [Spatial & performance](#11-spatial--performance)
12. [World integration checklist](#12-world-integration-checklist)
13. [Level authoring pipeline](#13-level-authoring-pipeline)
14. [Module & file layout](#14-module--file-layout)
15. [Implementation phases](#15-implementation-phases)
16. [Test plan](#16-test-plan)
17. [Future extensions](#17-future-extensions)
18. [Anti-patterns & decisions log](#18-anti-patterns--decisions-log)
19. [Hostile pass — edge cases & gaps](#19-hostile-pass--edge-cases--gaps)
20. [Implementation blueprint (next coding pass)](#20-implementation-blueprint-next-coding-pass)

---

## 1. Executive summary

**Space Junk** is a new world object family — **not** a variant of `Asteroid`. Pieces are **authored, indestructible, metal-scrap geometry** used to define lanes, walls, bays, and slalom corridors. They block the **player ship**, **all hostile units** (void squids, corsair fighters, patrol skiffs), **player weapons**, and **ally movement** — permanently in v1 (unless a future scripted breach is explicitly added).

| Property | Space Junk | Asteroid |
|----------|------------|----------|
| Material read | Scrap metal / hull / girders | Rock / regolith |
| Destructible | **Never** (v1) | Yes (tiers, breakup) |
| Typical motion | Static (v1); optional kinematic (v2) | Drift, ring orbit, breakup fragments |
| Design role | **Layout / architecture** | **Combat clutter / resources** |
| Count per level | Low–medium (authored) | High (procedural + belts) |

Implementation should mirror existing professional patterns in this repo: dataclass entity, convex polygon collision (same narrow-phase as asteroids), spatial broad-phase, dedicated viz module, level layout builders, pytest coverage **before** any level ships junk in production.

---

## 2. Design goals & non-goals

### Goals

- **Instant read:** Player sees metal scrap wall, not “weird rock.”
- **Authoring first:** Level designers place walls, gaps, and corridors without fighting combat systems.
- **Stable geometry:** Map topology does not change when the player shoots or overheats.
- **Reuse collision stack:** Convex polygons + circle narrow-phase — no new physics engine.
- **Multi-shape kit:** Several prefab silhouettes so repeated levels don’t look copy-pasted.
- **Camera parity:** Readable in tactical **and** chase (silhouette + material, not tint-only).
- **Zero coupling to asteroid combat:** No `hits_remaining`, no `asteroid_combat`, no jewel drops.

### Non-goals (v1)

- Do **not** replace asteroids in existing levels.
- Do **not** add junk to L1–L6 retroactively in the first implementation pass.
- Do **not** share `Asteroid` dataclass or `asteroid_spatial` type — parallel list + grid.
- Do **not** support destructible junk, nested interiors, or non-convex meshes in v1.
- Do **not** implement until this spec is agreed; then implement **end-to-end in one vertical slice** (entity → collision → render → tests → one dev test layout).

---

## 3. Player identity

### One-sentence player rule

> **“Metal doesn’t break — fly around it.”**

### HUD / briefing vocabulary (future)

| Term | Use |
|------|-----|
| **DEBRIS WALL** | Briefing label for junk-bordered zones |
| **SCRAP CORRIDOR** | Slalom / race sections |
| **HULL RING** | Closed bay or quarantine boundary |

### Chase read

- **Silhouette:** straight edges, rivet bands, panel seams — never organic blobs.
- **Material:** cold gray-blue steel, rust accents, specular edge — **no brown regolith**.
- **Scale:** often **larger** than single rocks; reads as “built environment.”

### Tactical read

- Flat fill + edge highlight + optional interior cross-brace lines.
- Holo chart (briefing map): junk shown as **angular hatching**, not holo-asteroid blue facets.

---

## 4. Distinction matrix

| Object | Collides ship | Blocks units (enemies/allies) | Blocks shots | Breaks | Moves | Visual |
|--------|---------------|------------------------------|--------------|--------|-------|--------|
| **Space Junk** | Yes | **Yes — solid** | Yes | No | Static (v1) | Metal panels, girders |
| **Asteroid** | Yes | **No** (units pass through) | Yes | Yes | Often | Rocky polygon |
| **Station** | No* | No | Yes (target) | Yes (mission) | No | Structured hub |
| **Finish gate** | No | No | No | N/A | No | Portal glyph |
| **Chart margin** | No (radiation) | N/A | N/A | N/A | N/A | Invisible |

\*Stations today are primarily targets; junk fills the “solid obstacle” role stations don’t.

**Key learning for players:** Rocks are shootable clutter; **metal debris is a wall** — enemies pile up at gaps too.

---

## 5. Entity model

### Type name

`SpaceJunk` — lives in `gameplay/entities.py` (or `gameplay/space_junk.py` if the struct grows; prefer separate module if prefab logic is non-trivial).

### Core fields (v1)

```python
@dataclass(slots=True)
class SpaceJunk:
    pos: Vec2
    angle: float                    # radians, placement rotation
    prefab_id: str                  # registry key, e.g. "girder_a"
    local_verts: tuple[Vec2, ...]   # convex CCW copy from prefab at spawn — not shared ref
    contact_policy: ContactPolicy   # enum — see §7
    layer: JunkLayer = JunkLayer.STRUCTURAL
    instance_id: int = 0            # monotonic per level load — debug / tests
    # v2 optional:
    # vel: Vec2 = Vec2()
    # angular_vel: float = 0.0
    # scorch_until: float = 0.0
```

### Enums (v1)

```python
class ContactPolicy(Enum):
    CHIP = auto()       # default — same severity as asteroid strike
    BOUNCE = auto()     # reflect velocity, no hull loss (race tracks)

class JunkLayer(Enum):
    STRUCTURAL = auto()   # default — collidable
    # DECOR = auto()      # v2 — visual-only unless collidable flag added
```

`GLANCING` contact (chip only above impact threshold) deferred to §17 — not in v1 enum.

### Instantiation (required API)

Level code never constructs raw verts. Use the factory:

```python
# gameplay/space_junk_prefabs.py
def instantiate_junk(
    prefab_id: str,
    pos: Vec2,
    angle: float = 0.0,
    *,
    contact_policy: ContactPolicy | None = None,
) -> SpaceJunk:
    """Copy prefab verts into a new instance; validate convex at registry load."""
```

**Invariant:** `local_verts` is a **deep copy** from `JunkPrefab` so per-instance cosmetic state (future scorch) never mutates the registry.

### Shared geometry helpers (mirror `Asteroid`)

- `approximate_radius() -> float`
- `world_vertices() -> list[Vec2]`

**Invariant:** `local_verts` must be **convex** and **CCW**. Prefab factory validates at load time.

### World container

```python
# GameWorld
space_junk: list[SpaceJunk] = field(default_factory=list)
junk_spatial: JunkSpatialGrid = field(default_factory=JunkSpatialGrid)
junk_spatial_static: bool = False   # True when list never mutates — skip rebuild
```

Separate from `asteroids` — never merge lists. Default empty list keeps all existing tests and levels unchanged.

### Config (optional per-level)

```python
# WorldConfig additions (when needed)
max_space_junk: int = 128
space_junk_enabled: bool = True
```

---

## 6. Shape catalog (prefabs)

Minimum **six** distinct prefabs for v1 — each unique silhouette, shared metal material.

| ID | Name | Silhouette | Typical use | Approx size (world u) |
|----|------|------------|-------------|------------------------|
| `girder_a` | **I-Girder** | Long narrow rectangle + flange notches | Straight walls, slalom gates | 120 × 28 |
| `hull_plate_a` | **Hull Plate** | Wide trapezoid slab | Bulkheads, diagonal barriers | 90 × 55 |
| `rib_arc_a` | **Station Rib** | Curved convex arc (8–10 verts) | Bays, crescents, salvage rings | radius 70, arc 90° |
| `truss_corner_a` | **Truss Corner** | L-shaped convex hull | Room corners, T-junctions | 80 × 80 leg |
| `container_a` | **Cargo Box** | Rect + rib lines (visual) | Stackable blocks, maze cells | 64 × 48 |
| `pipe_a` | **Dock Pipe** | Rounded capsule convex hull | Tubes, crawl gaps, “underpass” edges | 100 × 36 |

### v1.1 additions (still before first shipping level)

| ID | Name | Use |
|----|------|-----|
| `shrapnel_fan_a` | **Weld Fan** | Jagged but convex wreck fan — graveyard flavor |
| `boom_segment_a` | **Containment Boom** | Long thin barrier — quarantine lanes |
| `docking_claw_a` | **Claw Arm** | Hook silhouette — gate framing (non-lethal) |

### Prefab source of truth

```
src/gravity_ho_matey/gameplay/space_junk_prefabs.py
```

Each prefab exports:

```python
@dataclass(frozen=True)
class JunkPrefab:
    id: str
    local_verts: tuple[Vec2, ...]
    default_contact: ContactPolicy
    tactical_detail: JunkDrawSpec   # rib lines, rivet points
    chase_depth_bias: float         # for lit_draw sorting
```

**Authoring rule:** Designers reference `prefab_id` + `pos` + `angle` only — never hand-edit verts in level files except in prefab module.

### Composite walls (design-time, not runtime boolean ops)

Walls are **many prefab instances**, not CSG:

```
junk_wall_line(start, end, prefab="girder_a", overlap=8)
junk_arc(center, radius, start_deg, end_deg, prefab="rib_arc_a", spacing=...)
junk_box(rect, prefab="container_a", gap=...)       # deliberate gate gap
junk_gate_pair(center, width, prefab="truss_corner_a")  # slalom gate framing
```

Helpers live in `levels/space_junk_placements.py`.

---

## 7. Collision & contact policy

### Narrow-phase

Reuse `circle_intersects_convex_polygon(pos, radius, world_vertices())` from `core/geometry.py`.

### Queries (parallel to asteroids)

| Query | Used by |
|-------|---------|
| Ship hull vs junk | `_check_loss` / ship separation |
| **Unit circle vs junk** | Enemies, allies, boss, drone, nifflerp — **solid separation** (§7.5) |
| Projectile vs junk | `_update_projectiles` |
| Ally pathing queries | Obstacle avoidance broad-phase (same radii family as asteroids) |
| Explosive AoE | **No geometry change** — optional scorch decal only |

### Ship contact order (`_check_loss`)

Match existing well priority; insert junk **before** asteroids:

1. Out of bounds (closed charts only)
2. Gravity **maw** (lethal)
3. **Space junk** (if overlapping — one event)
4. **Asteroid** (if overlapping — only if junk did not already fire this frame)
5. Chart radiation (separate tick)

If junk + asteroid overlap same frame: **junk wins** — reason string references salvage metal, not rock.

### Default contact: `ContactPolicy.CHIP`

- New enum member: **`DamageSource.SPACE_JUNK`** (single name — no alias).
- Register in `DAMAGE_RULES`: `DamageSpec(DamageSeverity.CHIP, 1)` — same as `ASTEROID`.
- `default_reason`: *“Ripped open on salvage plating.”*
- **`scenes/play.py`**: HUD toast branch for `SPACE_JUNK` (mirror asteroid chip messaging).
- **Rubber hull** (`consume_rubber_hull_bounce`): when policy is `CHIP` and charge available → `resolve_junk_bounce` (mirror `resolve_rubber_hull_bounce` in `space_junk.py`); no hull loss, consumes bounce charge.

### `ContactPolicy.BOUNCE`

- No hull damage; push-out + velocity reflect.
- Use for **tutorial slalom** and **time-trial corridors** only — flag in layout, not global default.

### Separation push-out

When overlap detected, apply minimal positional correction along collision normal (same as rubber bounce overlap fix) to prevent tunneling at high speed.

---

### 7.5 Unit solid collision (enemies & allies)

**Requirement:** Void squids, hostile fighters, patrol skiffs, mega squid boss, wing escorts, drone, and nifflerp **cannot pass through** junk geometry. This is **stricter than asteroids** — today enemy `integrate()` ignores rock collision entirely; junk introduces real walls for AI.

#### Covered unit types (v1)

| Unit | `EnemyKind` / type | Collision radius | Notes |
|------|-------------------|------------------|-------|
| Patrol skiff | `PATROL` | `enemy.radius` (~14) | Waypoint pursuit; stacks at wall |
| Void squid | `SQUID` | `enemy.radius` (~18) | Includes cling latch path — see below |
| Corsair fighter | `HOSTILE_FIGHTER` | `enemy.radius` | Relay / siege assault craft |
| Mega squid boss | `MEGA_SQUID` | `boss.radius` (~42) | Large separation pushes |
| Wing escort | `FriendlyFighter` | `ally.radius` | Blocked **and** ram = death (§7.6) |
| Guardian drone | `DroneWingman` | `drone.radius` | Separation + existing obstacle query |
| Nifflerp | `Nifflerp` | buddy hit radius | Separation + existing obstacle query |
| Squid pod (flying) | `SquidPod` | `hit_radius()` | Blocked while `FLYING`; hatching pod anchored |

**Not blocked v1:** Projectiles (handled separately), jewels, explosions, beacons.

#### Shared resolver API (`gameplay/space_junk.py`)

```python
JUNK_SEPARATION_PASSES = 3          # multi-contact in one frame
JUNK_SEPARATION_SLOP = 3.0          # match rubber-hull push-out
JUNK_QUERY_PADDING = 72.0           # match asteroid projectile padding

def junk_hit_at(
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    pos: Vec2,
    radius: float,
) -> SpaceJunk | None: ...

def resolve_circle_against_junk(
    pos: Vec2,
    vel: Vec2,
    radius: float,
    junk: SpaceJunk,
    *,
    reflect_velocity: bool = True,
    restitution: float = 0.55,
) -> tuple[Vec2, Vec2]:
    """Push circle out of convex junk; optionally damp/relect velocity along normal."""

def apply_junk_separation(
    pos: Vec2,
    vel: Vec2,
    radius: float,
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    *,
    reflect_velocity: bool = True,
) -> tuple[Vec2, Vec2]:
    """Up to JUNK_SEPARATION_PASSES iterations — returns corrected pos/vel."""
```

#### World hook (`GameWorld`)

Call **`_resolve_units_against_junk()`** once per frame **after** unit movement integration, **before** projectile tick:

```python
def _resolve_units_against_junk(self) -> None:
    if not self.space_junk:
        return
    for enemy in self.enemies:
        if not enemy.alive:
            continue
        r = enemy.radius  # boss uses mega_squid.radius
        pos, vel = apply_junk_separation(enemy.pos, enemy.vel, r, ...)
        enemy.pos, enemy.vel = pos, vel
    # same for allies, drone, nifflerp, mega_squid, squid_pods (flying)
```

Insert in `GameWorld.update` immediately after `_update_nifflerp` / `_update_boss_and_pods` block and **before** `_update_projectiles`.

#### Squid-specific nuance

| Mode | Behavior |
|------|----------|
| Normal integrate | Post-step `apply_junk_separation` on body |
| **Cling latch** | After latch lerp toward prey, **still** run separation so body cannot be pulled through junk to reach player |
| Tentacle tips (v1) | **Visual-only** may clip wall slightly; body must not. v2 optional: tip circle separation at radius 6 |

#### Patrol waypoint nuance

Patrols do not replan paths around junk v1 — they thrust toward waypoint and **stack/slide** along junk face via separation. This is intentional: junk-walled lanes create chokepoints where skiffs queue at gaps.

#### Asteroid contrast (do not change)

Enemy units **continue to pass through asteroids** in v1. Only junk is solid to units. Do not unify lists.

---

### 7.6 Ally & escort hazard parity

Today `_check_ally_hazards` kills wing escorts on **asteroid** ram. Junk adds **solid separation (§7.5)** plus ram death:

| Actor | Junk contact (v1) |
|-------|-------------------|
| Player ship | CHIP or BOUNCE per `ContactPolicy` |
| Wing escort (`allies`) | **Cannot pass through**; overlap after separation → destroyed (`SHIP_STRUCK` FX) — mirror asteroid ram |
| Drone / Nifflerp | Separation each frame; `_nearby_*` obstacle queries include junk |
| Patrol / squid / corsair | **Cannot pass through** — separation only, no unit death |
| Mega squid boss | **Cannot pass through** — separation only |

### 7.7 Projectiles

- Junk **always** blocks collidable projectiles (`layer=STRUCTURAL`).
- **Hostile shots:** blocked + `JUNK_IMPACT` FX — **must not** call `apply_projectile_hit` / `asteroid_combat` (today hostile shots can destroy asteroids; junk is different).
- **Player / ally / drone / wingman shots:** same block — no friendly “clear path” through junk.
- **`from_ally` projectiles:** blocked on junk (same as rock).

### Enemy AI (v1 limitation)

Patrol aim (`enemy_aim.py`) does **not** raycast cover. Enemies may waste shots into junk and **stack at walls** without pathfinding — **acceptable v1**. Unit pathfinding around junk is §17.

---

## 8. Combat & weapon interaction

### Projectile resolution order (`_update_projectiles`)

Insert junk test **immediately before** the existing asteroid check (after TTL / bounds cull):

```
for each projectile:
  … bounds / ttl …
  if _junk_hit_at(pos, radius):          # NEW — spatial query
      handle_junk_impact(projectile)     # FX + consume; see matrix below
      continue                             # never fall through to asteroid
  if _asteroid_hit_at(pos, radius):       # existing path unchanged
      …
```

**Critical:** Junk intercept prevents hostile fire from “mining” asteroids through junk, and prevents explosive bolts from detonating on rocks behind junk when the junk face is hit first.

### Matrix (v1)

| Attack type | Effect on junk geometry | Projectile |
|-------------|-------------------------|------------|
| Default bullet | Unchanged | Consumed at impact |
| Laser + pierce | Unchanged | **Consumed** — pierce **not** decremented, does not continue |
| Shotgun pellet | Unchanged | Each pellet: spark + consumed |
| Explosive bolt | Unchanged | Detonates at junk face; `apply_explosive_burst` runs at impact point; AoE damages entities in radius **behind** junk if exposed |
| Hostile projectile | Unchanged | Blocked + spark — **no** asteroid combat |
| Ally / drone fire | Unchanged | Blocked + spark |
| Boss energy orb | Unchanged | Blocked + spark (treat as hard cover) |

### New explosion kinds (`gameplay/explosions.py`)

| Kind | Use |
|------|-----|
| `JUNK_IMPACT` | Small gray-orange metal spark — quieter than `ASTEROID_BREAKUP` |
| `JUNK_SCORCH` | v2 cosmetic — darkens rivet line on instance |

Wire `spawn_weapon_hit_fx` (`weapon_combat.py`) to route junk hits to `JUNK_IMPACT` instead of doctrine-colored pierce flashes.

### Explicit exclusions

- Junk not in `apply_explosive_burst` destroy list (geometry never removed).
- Junk not in `apply_projectile_hit` / `asteroid_combat`.
- Junk drops **no jewels**.
- `resolve_projectile_after_hit` bypassed for junk — always hard stop.

---

## 9. Visual language

### Palette (new entries in `render/palette.py` — planned)

| Token | Role | Direction |
|-------|------|-----------|
| `JUNK_HULL` | Base fill | `#4a5568` blue-gray steel |
| `JUNK_HULL_LIT` | Light-facing edge | `#7a8898` |
| `JUNK_HULL_DARK` | Shadow face | `#2a3038` |
| `JUNK_RUST` | Accent seam | `#6a4838` |
| `JUNK_RIVET` | Dot highlights | `#9aa8b8` |
| `JUNK_EDGE` | Outline | `#1a2028` |
| `JUNK_SPARK` | Impact FX | `#ffb080` |

**Forbidden for junk:** `ASTEROID_*`, `CHASE_ASTEROID_*`, brown regolith tones.

### Silhouette rules

1. **Straight edges dominate** — max 1 curved prefab per 6 straight pieces in a wall run.
2. **Rivet / seam lines** parallel to longest edge (tactical + chase).
3. **No craters** — damage reads as scorch smudge only.
4. **Aspect ratio:** girders ≥ 3:1 length:width; plates ≤ 2:1.

### Chase-specific

- Register `"space_junk"` in `render/lighting.py` → `material_for("space_junk", …)` (same string-key pattern as `"asteroid"`, `"ship"` — **not** a separate `MaterialKind` enum).
- Depth bias slightly **behind** ship when lateral — reads as environment, not pickup.
- No regolith speckle pass (asteroid-only).

### Holo chart (briefing)

- New glyph: hatched rectangle / angular bracket — **not** `HOLO_ASTEROID_*` colors.
- Token: `HOLO_JUNK_FILL`, `HOLO_JUNK_HATCH`.

---

## 10. Rendering plan

### Module

`render/space_junk_viz.py`

### Functions (planned API)

```python
def draw_tactical_junk(canvas, junk: SpaceJunk, *, camera, ship_pos, hud_top, scale) -> None
def draw_chase_junk(canvas, junk: SpaceJunk, *, camera, ship_pos, ship_angle, ...) -> None
def draw_holo_junk_glyph(canvas, junk: SpaceJunk, *, map_scale) -> None  # chart briefing
def junk_in_play_view(junk, ship_pos, viewport, ...) -> bool  # cull
```

### Draw order (relative)

1. Wells / floor
2. **Space junk (structural)**
3. Asteroids
4. Entities (ship, enemies, shots)
5. Junk decor (v2)

Hook into **`view_renderers.py`** (tactical + chase projectile loops) and **`world_draw.py`** shared tactical path — same insertion point in both.

### Culling

Mirror asteroid cull distances; junk walls may be **wider** — use `approximate_radius() + margin` for early-out. Long straight walls may need **AABB cull** per instance (future) if draw cost spikes.

---

## 11. Spatial & performance

### `JunkSpatialGrid`

Clone pattern from `asteroid_spatial.py`:

- Same `DEFAULT_CELL_SIZE = 240`
- `rebuild(space_junk: list[SpaceJunk])` each frame (or when list static, rebuild once at level load + flag dirty)
- `query_circle`, `query_interaction_zones` analogs

**Optimization:** If `space_junk` is static for a level, set `world.junk_spatial_static = True` and skip rebuild after first tick.

### Budgets

| Level type | Suggested max instances |
|------------|-------------------------|
| Compact chart | 0–24 |
| Open arena | 24–80 |
| Junk-heavy course (L7+) | 80–128 |

Convex count is cheap; **draw call count** matters more — batch by prefab in viz if needed later.

---

## 12. World integration checklist

When implementing, touch these systems **in one PR** — partial integration causes silent bugs.

| System | Change |
|--------|--------|
| `GameWorld` | `space_junk`, `junk_spatial`, `junk_spatial_static`; `_junk_hit_at`; **`_resolve_units_against_junk()`** (§7.5) |
| `world._update_projectiles` | Junk test **before** asteroid branch (§8) |
| `world._check_loss` | Junk after maw, before asteroid (§7) |
| `world._check_ally_hazards` | `_junk_hit_at` on allies — ram → destroyed (mirror asteroid) |
| `world._nearby_junk` / drone / nifflerp | Junk in obstacle queries (mirror `_nearby_asteroids` radii) |
| `gameplay/space_junk.py` | `instantiate_junk`, `apply_junk_separation`, `resolve_circle_against_junk`, ship bounce |
| `squid_enemy.integrate` | Post-cling separation via world hook (do not fork cling logic in squid file) |
| `gameplay/damage.py` | `DamageSource.SPACE_JUNK`, `DAMAGE_RULES`, `default_reason` |
| `gameplay/explosions.py` | `ExplosionKind.JUNK_IMPACT` preset |
| `gameplay/weapon_combat.py` | `spawn_weapon_hit_fx` junk route; `apply_explosive_burst` unchanged list |
| `scenes/play.py` | HUD toast for `SPACE_JUNK` chip |
| `render/lighting.py` | `material_for("space_junk", …)` tones |
| `render/palette.py` | `JUNK_*`, `HOLO_JUNK_*` |
| `render/space_junk_viz.py` | Tactical + chase draw |
| `render/chart_map_overlay.py` | Holo junk layer on briefing map (levels with junk) |
| `render/view_renderers.py` + `world_draw.py` | Draw junk in both cameras |
| `narrative/chart_briefing_copy.py` | `HAZARDS` row template for junk-heavy levels |
| `levels/level_data.py` | `space_junk=` kwarg on `GameWorld(...)` |
| `threat_snapshot.py` | Optional `JunkThreatSnapshot` for narrow-corridor HUD warn |

### Actual sim tick order (align with `GameWorld.update`)

Do **not** reorder the whole loop — insert junk into existing stages:

```
… brood / invuln / tractor …
_update_asteroids + asteroid_spatial.rebuild
_update_ship
… waves, enemies, allies, drone, nifflerp, boss, pods, stations …
_resolve_units_against_junk()   ← NEW — solid separation all units (§7.5)
_update_projectiles             ← junk hit before asteroid in loop body
refresh_threat_snapshots
… beacons, jewels, squid cling …
_check_ally_hazards             ← junk ram death for escorts still overlapping
… radiation …
_check_loss                     ← ship junk/asteroid chip
```

Junk spatial: rebuild once on level load; set `junk_spatial_static=True`; skip per-frame rebuild unless list mutates (v2 kinematic).

---

## 13. Level authoring pipeline

### File flow

```
levels/<level>_layout.py     # anchor positions, mission zones
levels/space_junk_placements.py   # shared helpers
levels/<level>_junk.py         # optional — junk-only layout for heavy courses
level_data.build_*()         # assembles GameWorld(space_junk=...)
```

### Example (planned syntax)

```python
from gravity_ho_matey.levels.space_junk_placements import junk_wall_line, junk_gate_pair

def build_shoal_corridor_junk() -> list[SpaceJunk]:
    left = junk_wall_line(Vec2(800, 400), Vec2(800, 2200), prefab="girder_a", angle=0.0)
    right = junk_wall_line(Vec2(1200, 400), Vec2(1200, 2200), prefab="girder_a", angle=0.0)
    gate = junk_gate_pair(center=Vec2(1000, 1200), width=140, prefab="truss_corner_a")
    return left + right + gate
```

### Validation (CI)

`tests/test_space_junk_prefabs.py`:

- All prefabs convex (CCW winding check)
- `approximate_radius` > 0
- No duplicate prefab IDs
- Max vert count ≤ 12 (performance guard)

`tests/test_space_junk_placements.py`:

- Helper-generated walls have overlap ≥ 4u between segments (no hull leaks)
- Deliberate gate gaps ≥ `2 * ship.radius + 8` (default ship radius 12 → **min 32u** clear width)
- Level build rejects `len(space_junk) > config.max_space_junk`

### Scope boundary (v1)

| Context | Junk in v1? |
|---------|-------------|
| Open / orbital sectors (L7+) | **Yes** — primary target |
| Brood Moon **surface** (`surface_wrap`) | **No** — uses terrain scrape + flora props; separate system |
| L1–L6 retrofit | **No** |
| Holo chart preview | Yes when level ships junk |

### Dev sandbox level

`levels/junk_sandbox_layout.py` — not in `LEVEL_ORDER`; deploy via test or debug key only. Used to sign off v1 before L7.

---

## 14. Module & file layout

```
src/gravity_ho_matey/
├── gameplay/
│   ├── entities.py              # SpaceJunk dataclass (+ enums) OR re-export
│   ├── space_junk.py              # contact resolution, bounce
│   ├── space_junk_prefabs.py      # PREFAB_REGISTRY, factory
│   ├── space_junk_spatial.py      # JunkSpatialGrid
│   ├── space_junk_spatial.py      # JunkSpatialGrid
│   └── damage.py                  # DamageSource.SPACE_JUNK (+ DAMAGE_RULES)
├── scenes/
│   └── play.py                    # SPACE_JUNK HUD toast
├── levels/
│   ├── space_junk_placements.py   # junk_wall_line, junk_arc, ...
│   └── junk_sandbox_layout.py     # dev only
├── narrative/
│   └── chart_briefing_copy.py     # HAZARDS copy for junk levels
├── render/
│   ├── palette.py                 # JUNK_* colors
│   ├── lighting.py                # material_for("space_junk")
│   ├── space_junk_viz.py          # tactical + chase + holo
│   └── chart_map_overlay.py       # briefing map junk layer
└── tests/
    ├── test_space_junk_prefabs.py
    ├── test_space_junk_collision.py
    ├── test_space_junk_combat.py
    └── test_space_junk_render_smoke.py
```

**Dependency rule:** `space_junk_*` must **not** import `asteroid_combat` or `asteroid_tiers`.

---

## 15. Implementation phases

### Phase 0 — Spec sign-off (current)

- [x] This document
- [x] Hostile review pass (§19)
- [x] Prefab silhouettes agreed (nine in registry)
- [x] Contact default agreed (`CHIP` global default; `BOUNCE` per-piece for courses)

### Phase 1 — Core vertical slice (no shipping level)

1. Entity + prefab registry + convex validation tests  
2. Spatial grid + ship/projectile collision  
3. Damage source + bounce variant  
4. Tactical render only  
5. Sandbox layout + manual fly test  

**Exit:** Ship chips on junk; shots spark; asteroids unchanged; pytest green. **Done.**

### Phase 2 — Presentation parity

1. Chase render + metal material  
2. Holo chart glyph  
3. Impact/scorch FX  
4. AI obstacle avoidance  

**Exit:** Chase silhouette distinct from asteroids in side-by-side screenshot. **Done (v1).**

### Phase 3 — Authoring kit

1. `junk_wall_line`, `junk_arc`, `junk_box` helpers  
2. Layout validation tests  
3. Briefing copy template for junk-heavy levels  

**Exit:** Designer can build a slalom corridor in <30 lines without touching sim code. **Done.**

### Phase 4 — First production use

- Deploy junk in **one new level** (e.g. L7 shoal corridor) — not retroactive L1–L6. **Next.**

---

## 16. Test plan

### Unit

| Test | Assert |
|------|--------|
| Prefab convexity | All verts CCW convex |
| Ship vs junk | Contact registers `SPACE_JUNK` damage |
| Bounce policy | No damage, velocity reflected |
| Projectile | Consumed; no `asteroid_combat` call |
| Laser pierce | Stops at junk |
| Explosive | Junk list length unchanged post-blast |
| Hostile projectile on junk | Blocked; `len(space_junk)` unchanged; no asteroid destroyed |
| Ally wing ram junk | Escort destroyed (same as asteroid ram) |
| Explosive on junk face | Junk count unchanged; enemies behind may still take AoE |
| Spatial | Query returns nearby junk only |
| **`apply_junk_separation`** | Circle pushed out of convex junk; velocity reflected |
| **Patrol vs wall** | Skiff blocked over 60 frames; does not cross junk segment |
| **Squid vs wall** | Body blocked; cling test does not tunnel through girder |
| **Hostile fighter vs wall** | Same as patrol |
| **Unit + asteroid control** | Enemy still passes asteroid when `space_junk=[]` only |
| Existing suite | All L1–L6 tests green with default `space_junk=[]` |

### Integration

| Test | Assert |
|------|--------|
| `GameWorld` tick | Junk static list stable after 500 frames of firing |
| Rubber hull | Bounce off junk consumes charge |
| Drone path | Obstacle query includes junk; separation applied |
| **Siege patrol + junk corridor** | Roster skiff stacks at gap, does not appear inside wall |

### Render smoke

- Instantiate each prefab; draw tactical + chase without Tk error  
- Palette regression: junk draw never references `ASTEROID` tokens  

### Manual QA script

1. Deploy junk sandbox  
2. Fire all weapon doctrines into wall — geometry unchanged  
3. Ram wall — chip; rubber hull — bounce  
4. Toggle chase — read as metal, not rock  
5. Compare screenshot adjacent to Drift asteroid field  
6. Spawn patrol + squid in sandbox against junk wall — neither passes through; both stack at gap  

---

## 17. Future extensions (post-v1)

| Feature | Notes |
|---------|-------|
| **Kinematic junk** | Slow drift (shoal front); `vel` + `integrate_junk`; clears `junk_spatial_static` |
| **Decor layer** | Non-colliding visual scrap |
| **Glancing contact** | Chip only above impact normal threshold |
| **AI cover awareness** | Patrol aim raycast / flank paths |
| **Scripted breach** | Mission opens one gap — explicit animation, still not player guns |
| **Resonant shell** | Timing window — still indestructible; different FX |
| **Brood surface junk** | Wreck props on wrap terrain — may share viz, not v1 sim |
| **Composite prefab** | `prefab_id="wall_segment_4x"` precomposed for perf |
| **Pygame migration** | Same data model; swap `space_junk_viz` backend |

---

## 18. Anti-patterns & decisions log

### Do not

| Anti-pattern | Why |
|--------------|-----|
| `indestructible=True` on `Asteroid` | Couples combat/breakup/spatial caps; breaks player learnings |
| Invisible collision-only junk | Chase/tactical must show walls |
| Brown palette reuse | Fails “scrap metal” read |
| Piercing junk with laser | Collapses cover design |
| 200+ micro scraps per sector | Draw + collision noise; use fewer larger pieces |
| Retrofit Cove with junk in Phase 1 | Pollutes tutorial; use sandbox only |
| Sharing prefab vert tuples across instances | Breaks future per-instance scorch state |
| Hostile shots deleting junk via asteroid path | Must use dedicated junk branch **before** asteroid |
| **Player-only junk collision** | Enemies ghosting through walls breaks chokepoint design |

---

### Decisions locked for v1

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Collision mesh | Convex polygons only | Matches engine; predictable |
| Separate entity type | `SpaceJunk` | Clear ownership, no combat coupling |
| Laser vs junk | Always blocks | Hard cover is the point |
| Default damage | Chip (like rock) | Consistent stakes; bounce opt-in per piece |
| Motion | Static | Simpler; kinematic deferred |
| Prefab count | ≥ 6 | Visual variety without art pipeline |
| **Unit collision** | **Solid for all units** | Junk is architecture; enemies must not ghost through |

---

## 19. Hostile pass — edge cases & gaps

Review against current codebase (`world.py`, `damage.py`, `weapon_combat.py`, ally/drone paths). Items below are **required** for v1 — not optional follow-ups.

### Projectile / combat

| Edge case | Required behavior |
|-----------|-------------------|
| Hostile shot hits junk | Consume + `JUNK_IMPACT`; **do not** damage asteroids behind in same frame unless separate projectile |
| Laser pierce at junk | Hard stop; `pierce_remaining` unchanged |
| Explosive hits junk face | Detonate at impact; junk list unchanged; AoE applies normally |
| Player shotgun on junk | Per-pellet sparks; no junk HP |
| `from_ally` bolt | Blocked on junk (no ally tunneling) |

### Enemy & ally units (solid)

| Edge case | Required behavior |
|-----------|-------------------|
| Patrol skiff into junk wall | Blocked; slides/reflects via `apply_junk_separation` |
| Void squid into junk wall | Body blocked; cling latch cannot tunnel through |
| Hostile fighter into junk | Blocked same as patrol |
| Mega squid boss into junk | Blocked; large radius pushes along face |
| Flying squid pod | Blocked while `PodPhase.FLYING` |
| Wing escort into junk | Separation first; if still overlapping → `_check_ally_hazards` death |
| Unit through asteroid (control) | **Still passes** — only junk is solid |
| High speed tunneling | 3 separation passes + slop prevents frame skip through thin girder |

### Ship / damage

| Edge case | Required behavior |
|-----------|-------------------|
| Invuln frames | `_register_ship_hit` early-out — junk respects invuln |
| Junk + maw same frame | Maw checked first — lethal wins |
| Junk + asteroid overlap | One chip event — junk reason string |
| Rubber hull + junk CHIP | Bounce + consume charge |
| Rubber hull + junk BOUNCE | Bounce only — no charge consumed |
| `BOUNCE` policy corridor | No chip ever on that piece |

### Allies / escorts

| Edge case | Required behavior |
|-----------|-------------------|
| Wing escort rams junk | Escort dies — mirror `_check_ally_hazards` asteroid branch |
| Drone pathing | Include junk in `_nearby_*` obstacle query (same radius family as asteroids) |
| Nifflerp avoidance | Include junk in nifflerp obstacle query radius |

### Rendering / UX

| Edge case | Required behavior |
|-----------|-------------------|
| Chase vs tactical | Both cameras draw junk; metal material distinct from `CHASE_ASTEROID_*` |
| Chart briefing | Junk hatched on holo map — not blue asteroid facets |
| Long wall off-screen | Cull OK; collision still active when ship arrives |

### Level build / data

| Edge case | Required behavior |
|-----------|-------------------|
| Empty junk list | Default — zero meaningful cost beyond empty grid |
| Invalid prefab_id | `instantiate_junk` raises at build time, not mid-play |
| Gap too narrow | CI test fails if clear width < 32u |
| Over `max_space_junk` | Level builder raises |

### Explicitly out of v1 (documented, not bugs)

- Enemy patrol pathfinding around junk walls  
- Ship–junk friction / sliding along wall  
- Junk damaged by station tractor or boss tentacle scrape  
- Destructible junk doors  

---

## 20. Implementation blueprint (next coding pass)

Single PR — **no partial landing**. Order below matches dependency chain for the next implementation message.

### Step 1 — Data & registry

| File | Work |
|------|------|
| `gameplay/entities.py` | `SpaceJunk`, `ContactPolicy`, `JunkLayer` |
| `gameplay/space_junk_prefabs.py` | 6 prefabs, `PREFAB_REGISTRY`, `instantiate_junk()`, convex validation |
| `gameplay/space_junk_spatial.py` | `JunkSpatialGrid` (clone asteroid grid) |
| `tests/test_space_junk_prefabs.py` | Convexity, IDs, vert count |

### Step 2 — Collision core

| File | Work |
|------|------|
| `gameplay/space_junk.py` | `junk_hit_at`, `resolve_circle_against_junk`, `apply_junk_separation`, `resolve_junk_bounce` (ship) |
| `gameplay/damage.py` | `DamageSource.SPACE_JUNK` + rules + reason |
| `tests/test_space_junk_collision.py` | Separation math, multi-pass, ship chip/bounce |

### Step 3 — World sim

| File | Work |
|------|------|
| `gameplay/world.py` | `space_junk` field; `_junk_hit_at`; `_resolve_units_against_junk()`; projectile branch; `_check_loss`; `_check_ally_hazards` junk ram; `_nearby_junk()`; drone/nifflerp queries |
| `gameplay/explosions.py` | `JUNK_IMPACT` |
| `gameplay/weapon_combat.py` | Junk impact FX routing |
| `tests/test_space_junk_combat.py` | Projectiles, hostile, laser, explosive, unit blocking |

### Step 4 — Presentation

| File | Work |
|------|------|
| `render/palette.py` | `JUNK_*`, `HOLO_JUNK_*` |
| `render/lighting.py` | `material_for("space_junk", …)` |
| `render/space_junk_viz.py` | Tactical + chase draw |
| `render/view_renderers.py`, `world_draw.py` | Insert junk draw pass |
| `scenes/play.py` | HUD toast |
| `tests/test_space_junk_render_smoke.py` | Tk draw all prefabs |

### Step 5 — Authoring sandbox

| File | Work |
|------|------|
| `levels/space_junk_placements.py` | `junk_wall_line`, `junk_gate_pair`, gap validation |
| `levels/junk_sandbox_layout.py` | Test corridor + wall |
| `tests/test_space_junk_placements.py` | Overlap + gap width |
| Wire sandbox in test only | `build_junk_sandbox_world()` — **not** in `LEVEL_ORDER` |

### Step 6 — Verify

```bash
python -m pytest tests/test_space_junk_prefabs.py tests/test_space_junk_collision.py tests/test_space_junk_combat.py tests/test_space_junk_placements.py tests/test_space_junk_render_smoke.py -q
python -m pytest tests -q
```

Manual: junk sandbox — player, patrol, squid, corsair all block on wall.

**Do not** add junk to L1–L6 or any shipping level in this pass.

---

## Sign-off

When ready to implement:

1. Confirm prefab list (§6)  
2. Implement Phase 1 in a single focused branch  
3. Sign off sandbox QA (§16)  
4. Only then author junk into a new level  

**No partial merges** (viz-only or collision-only without tests).

---

*Document version: 1.2 · 2026-06-02 · Plan only — includes enemy/allied unit solid collision (§7.5) + implementation blueprint (§20).*
