# Levels 6–20+ Forward Mega Brainstorm

**Gravity Ho, Matey!** — single creative backlog for post–Sector 5 content (Cove → Siege Line). Brainstorm only; no implementation commitments. Nothing is off limits.

---

## Contents

1. [Foundation palette (Sectors 1–5)](#foundation-palette-sectors-15)
2. [Campaign acts & emotional design](#campaign-acts--emotional-design)
3. [Tone, voice & sector map](#tone-voice--sector-map)
4. [Levels 6–10 (primary pitches)](#levels-610-primary-pitches)
5. [Level alternates (6B–10D)](#level-alternates-6b10d)
6. [Levels 11–20](#levels-1120)
7. [Units: human, horror, neutral, friendly, stations](#units-human-horror-neutral-friendly-stations)
8. [Celestial objects & hazards](#celestial-objects--hazards)
9. [EVA (out-of-ship)](#eva-out-of-ship)
10. [Chase / follow-on camera](#chase--follow-on-camera)
11. [Skill deck, economy & builds](#skill-deck-economy--builds)
12. [Quests, narrative & endings](#quests-narrative--endings)
13. [Factions, bosses & mission combinatorics](#factions-bosses--mission-combinatorics)
14. [Captain, crew & rivals](#captain-crew--rivals)
15. [Multiplayer & async](#multiplayer--async)
16. [Accessibility, audio, modding, seasonal](#accessibility-audio-modding-seasonal)
17. [Technical enablers & production order](#technical-enablers--production-order)
18. [Anti-patterns](#anti-patterns)
19. [Wild ideas bin](#wild-ideas-bin)
20. [Vision statements](#vision-statements)

---

## Foundation palette (Sectors 1–5)

| Layer | Established |
|-------|-------------|
| **Arc** | Smuggler training → solar choke → open drift horror → relay defense → two-fleet siege |
| **Human line** | Patrol skiffs, roster wingmen, friendly fighters, hostile/friendly stations |
| **Horror line** | Void squids, coil rings, tentacle reach, corsair strike on Relay Hold |
| **Environment** | Black holes (maw + footprint), asteroid tiers/breakup, ring/shower drift, radiation (optional) |
| **Mission types** | Beacon gate race, open survival/extract, timed waves, kill quota + station assault |
| **Meta** | 3 lives, hull chunks, jewel treasury, radial skill deck, weapon doctrine + advanced branch |
| **Views** | Tactical (route planning) + Chase (follow-cam, cockpit HUD, rear mirror) |

Everything below **extends** this palette rather than replacing it.

---

## Campaign acts & emotional design

### Narrative through-line

| Act | Levels | Story | What the player’s body should do |
|-----|--------|-------|----------------------------------|
| **I — Apprentice** | 1–5 | Gravity is the real enemy; the void has hunters | Plan route → commit → panic → recover → gate euphoria |
| **II — Operator** | 6–8 | Rift lane opened; squids migrated up; factions fracture | Read the room → choose violence or theft → live with heat |
| **III — Pilgrim** | 9–10 | Megastructure / orphan hole / comet cathedral | Surf momentum → accept you can’t fight gravity → moral exit |
| **IV — Legend** | 11–15 | Mastery, mirror levels, NG+ | Flex skill → optional cruelty or mercy |
| **V — Aftermath** | 16–20 | Consequences, not escalation | Recontextualize Act I—“*that’s* what Cove was teaching” |

**Design rules for 6+:**
- Every sector: at least one moment where **not thrusting** (let the well work) is correct.
- Act II: at least one moment where **not shooting** is correct.
- Act III: at least one moment where **not winning cleanly** is correct.

Endgame reflects **campaign doctrine**—how you played the skill deck (pirate, diplomat, horror sympathizer, etc.).

---

## Tone, voice & sector map

### Pirate swagger vs space horror

Arcade pirate energy colliding with genuine void dread—neither wins permanently.

```
Cove ████████░░  Drift ░░████████  Rift ░░░░██████  Siege ██████░░░░
Salvage ██████░░░░  Shoal ░░░░░░████  Charter █████░░░░░  Comet ░░░░██████  Court ░░██████░░
```

- **Horror never jokes** — squids = sonar + static only; radio jokes *nervously*
- **Pirate never undercuts bosses** — letterbox + silence during Brood phases
- **Loot stays vulgar** — TREASURY ★, salvage = theft not crafting
- **Corporate = sterile villain voice** — charter legalese vs crew slang

**Radio voices (cheap):** wingman tries to sound pirate (“Aye— acknowledged”); corporate = legal threats; neutrals = tired workers (“That core’s *spoken for*, captain.”)

### Sector map (place, not list)

After Level 5, chart briefing shows **geography**, not “Level 6 unlocks.”

```
                    [ COMET RAIL ]──────► (9 Perihelion)
                          │
    (3 Drift) ◄─── [ THE DRIFT ] ───► (7 Shoal)
         │              │                    │
         │         [ RIFT LANE ]              │
         │              │                    │
    (1 Cove)      (4 Relay Hold)        (8 Charter Belt)
         │              │                    │
    [ INNER EXPANSE ]───┴─── [ SALVAGE VERGE ] (6)
                              │
                    (5 Siege)─┴─► (10 Accretion Court)
```

- **Optional fork** after 6: Shoal (7) *or* Charter (8) first → different rep, both gate to 9
- **Failed sectors** scar the map in NG+ (burnt relay icon, etc.)

---

## Levels 6–10 (primary pitches)

### Level 6 — **The Salvage Verge** (`salvage`)

**Fantasy:** Graveyard orbit around a dead mining station. Scavengers fight over hulls; squids nest in wreck shadows.

**Layout:** Crescent arena—dense debris arc + open lane. Low global gravity; **micro-wells** on stolen reactor cores.

**Win:** Heist 3 cores from neutral barges + exit on timer **OR** escort crippled friendly tug through scrap ring.

**Pressure:** Neutral scavenger skiffs—heat rises on near-miss fire; reinforcements if provoked.

**Enemies:** Scavenger skiffs, nest squids, **Salvage Crawler** mini-boss (tractor + debris throw).

**Meta:** Skill deck **Salvage Contracts**—bonus jewels if no neutral kills.

**Chase beat:** Wreck silhouettes past wing struts; flickering salvage lamps.

---

### Level 7 — **Tide of the Mantle** (`shoal`)

**Fantasy:** Squids **herd** asteroids toward human lanes—open ocean in space.

**Layout:** Drift-scale arena; three migrating shoals (rings + squid escorts). Weak, numerous wells—surf the gaps.

**Win:** Destroy 3 **Squid Lures** **OR** survive as bait until friendly depth-charge frigate arrives.

**Enemies:** Mantle Stingers, arch squids, one doomed human patrol on radio.

**Mechanic:** **Biolum panic**—squid kills briefly invert chase fog (subtle, optional accessibility off).

**Chase beat:** Shoal wall fills horizon like a wave.

---

### Level 8 — **The Neutral Belt Charter** (`charter`)

**Fantasy:** Three-way standoff—brigands, corporate, free miners. Neutral trade hub center.

**Layout:** Tri-lobe map; **no-fire bubble** at hub (optional objective fail, not instant loss).

**Win:** Deliver signed cache to your gate while corporate intercepts. Optional mid-mission hub shop (spend jewels).

**Enemies:** Enforcer skiffs (shield arc), miner Rockhounds (tethered turrets), squids drawn to gunfire.

**Friendly:** Negotiator drone (marks safe corridors). **Notary drone**—stay within 200u during fights.

**Meta:** **DIPLOMACY** skill branch—lower neutral aggro, better prices, worse DPS.

**Chase beat:** Corporate spotlight sweep from hub.

---

### Level 9 — **Perihelion Run** (`comet`)

**Fantasy:** Megacomet screaming orbit around orphan black hole—ride the tail into periapsis slingshot.

**Layout:** Arena **scrolls/rotates** with comet frame. Outgassing jets + capture radius at periapsis.

**Win:** Hit 3 crust beacons, peel off before capture.

**Celestial:** Nucleus body, ice vent thrust bonus, tail debris shower, accretion disk as chase floor read.

**Enemies:** Tail-riding squids, **Hole Cultist** kamikaze skiffs.

**Optional:** One beacon needs **micro-EVA** (see EVA section).

**Chase beat:** Nucleus eclipses sun; tail particles rush; rear mirror shows hole gaining.

---

### Level 10 — **The Accretion Court** (`court`)

**Fantasy:** Megaring around supermassive well—stations, fleets, squid cathedral, civilian pods.

**Layout:** Ring hub + **4 arms** (station visual language at megascale). Gravity ramps toward hub.

**Win (multi-phase):**
1. Arm A — break hostile station gun (Siege)
2. Arm B — hold relay vs squid surge (Rift)
3. Arm C — beacon race through shoal (Drift)
4. Arm D — **choice:** save civilians / destroy Brood core / steal data / burn the lane

**Boss:** **Brood-Mother Ascendant**—segment squid + station hybrid; phase grammar, not HP sponge.

**Chase beat:** Ring rotation syncs with bank angle.

---

## Level alternates (6B–10D)

Swap if primary pitch doesn’t land:

| Slot | Alt | Name | Hook |
|------|-----|------|------|
| 6 | B | Graveyard Waltz | Counter-rotating debris rings—relative velocity lesson |
| 6 | C | Hulk Lottery | Random derelict each run holds macguffin |
| 6 | D | Claims Court | Win by *recording* theft on camera drone—neutrals are witnesses |
| 7 | B | Kraken Weather | Squid storm visibility cycles |
| 7 | C | The Nursery | Seal pods before hatch—pacifist horror |
| 7 | D | Echo Shoal | Hollow asteroids—shots pass until resonance timing |
| 8 | B | Blockade Breakfast | Timer = civilian hunger not hull |
| 8 | C | The Auction | Buy your own exit gate mid-fight |
| 8 | D | Double Agent | Paint IFF corporate once per run |
| 9 | B | Tail First | Start at nucleus, flee as it cracks |
| 9 | C | Guest Star | Brief wingman-drone playable segment |
| 9 | D | No Hole | “Hole” is lensing—horror is human |
| 10 | B | The Vote | Control broadcast towers, not guns |
| 10 | C | Pyrrhic Crown | Each arm cleared buffs final boss |
| 10 | D | Split Party | Co-op wingman path at court scale |

---

## Levels 11–20

### Act IV (11–15) — NG+ / episode 2

| # | Name | Pitch |
|---|------|-------|
| 11 | **Moonfall Refinery** | Mini-moon low-G pad; refuel while orbital fight continues |
| 12 | **Ghost Fleet** | AI-only enemies; no cockpit glow; quiet chase |
| 13 | **Redshift Convoy** | Escort 10 civilians through shifting wells |
| 14 | **The Quiet Hole** | No weapons—stealth/thrust puzzle; sensor rings |
| 15 | **Return to Cove** | Corrupted Cove geometry; secret gate |

### Act V (16–20) — after the crown

| # | Name | Pitch |
|---|------|-------|
| 16 | **Exodus Trail** | Saved civilians convoy—persistent NPC IDs |
| 17 | **The Drift Remembers** | Squids mimic *your* weapon doctrine colors |
| 18 | **Corporate Collapse** | Rogue enforcers; loot black sites |
| 19 | **The Garden Ring** | Squids as gardeners—not evil, alien |
| 20 | **Ho, Matey.** | Title phrase = place name; epilogue cove inside megastructure |

---

## Units: human, horror, neutral, friendly, stations

### Design questions (every new unit)

1. What does it teach about **gravity**?
2. What’s the **chase silhouette** at high speed?
3. What happens if the player **ignores** it?

### Human line

| Unit | Role |
|------|------|
| Enforcer | Shield arc—flank to kill |
| Torpedo skiff | Gravity-curving torpedo |
| Mine layer | Dormant mines wake on thrust |
| Carrier tender | Spawns 2-seater drones |
| Cultist kamikaze | Feeds the hole |
| Ghost drone | AI-only, minimal silhouette |
| Boarding clipper | Grapples station/drone |
| Executive shuttle | Non-combat—kidnap/ransom objective |

**Lifecycle:** Enforcer → Boarding clipper → Executive shuttle.

### Horror line (squid lifecycle)

| Stage | Behavior |
|-------|----------|
| Spore | Particle; attracted to thrust noise |
| Mantle Stinger | Swarm chip; steals reactor charge |
| Mantle | Coil ring elite (current) |
| Arch Squid | Pull + spawn stingers |
| Lure beacon | Objective—attracts shoals |
| Deep Angler | Ambush via rear mirror heat |
| Brood segment | Boss part; regen if siblings live |

### Neutral line

| Unit | Role |
|------|------|
| Scavenger skiff | Yellow IFF; heat on provocation |
| Miner rockhound | Claim turret on asteroid |
| Trade lugger | Mobile mid-mission shop |
| Refugee pod | Collateral fail |
| Survey probe | Scan cone raises attention |

**Neutral rules:** never spawn in crosshair cone; IFF yellow → orange → red; witness kills → bounty *next* sector; neutrals can kill squids (but loot jewels).

### Friendly line

| Unit | Role |
|------|------|
| Wingman drone | Doctrine-sync tracers (shop) |
| Repair tender | Heal aura |
| Miner ally | Breaks rocks for jewels; fragile |
| Frigate (AI) | Level 7 arrival fantasy |
| Negotiator probe | Shows neutral aggro radius |
| Decoy barge | Taunt—one-shot purchase |
| Shield escort | Bubble stacks with rubber hull |

**Command:** hold key **ping focus**—allies prioritize; no full RTS.

### Stations & structures

| Unit | Notes |
|------|-------|
| Relay (friendly) | Rift—add repair between waves |
| Hostile gun hub | Siege—add shield satellite |
| Neutral trade hub | Charter |
| Squid cathedral | Bio-station spawns horror |
| Comet beacon pillar | Navigation on comet levels |

---

## Celestial objects & hazards

| Object | Gameplay |
|--------|----------|
| Comet nucleus | Large solid; optional land cap |
| Mini-moon | Low-G pad; orbital motion |
| Binary moonlets | Chaotic micro-G for EVA |
| Ice fragment / vent | Thrust boost or vision obscure |
| Glass asteroid | Transparent until cracked |
| Magnetite cluster | Pulls metallic shots |
| Derelict hull / satellite | Cover; T2 EVA interior |
| Reactor core pickup | Heavy mass curves shots while carried |
| Gas giant edge | Drag band |
| Accretion stream | Rotating damage zones |
| Megaring segment | Shifting lanes |
| Gravity lens / echo well | HUD lies until learned |
| Tidal bulge | Periodic gravity pulse |
| Frozen scream | Lore-only ice bodies |

**Flagship moon fantasy:** one landable moon per campaign if Salvage Contracts taken—6×6 jetpack grid, coffee/data/horror egg POI; orbital fight continues above.

---

## EVA (out-of-ship)

**Rule:** T0 + T1 ≤ ~8% campaign time; ship is home.

| Tier | Duration | Example |
|------|----------|---------|
| **T0 Grapple snap** | ~2 sec | Cut tentacle QTE |
| **T1 Micro-EVA** | 15–30 sec | Comet beacon, moon coffee, gantry repair |
| **T2 Away mission** | 2–3 min optional, once NG+ | Derelict interior—gravity pulls toward nearest well |

**T1 UX:** 4×4–8×8 grid; jetpack puffs; cutter/welder/scanner; hatch proximity returns to chase.

**T2:** Side-scroll micro room; one wall squid; reward = unique deck node.

**Chase during EVA:** tactical shows ship; chase shows tiny figure on hull wire.

---

## Chase / follow-on camera

**Goal:** arcade flight-sim credibility in Tkinter—speed + danger + readability, never empty tunnel or soup.

### Roadmap (visual)

1. Layered parallax sky (3 speeds)
2. Locked horizon / no rig jitter from HUD
3. Bank-on-turn capped 8–12°, tied to turn rate
4. Subtle speed FOV
5. Unified contact shadows on floor gradient
6. Fake DOF on far sprites
7. Doctrine-specific tracers (incl. advanced tier)
8. Hull-chunk cockpit crack decals
9. Mach ticks + rear mirror compression on boost

### UX

- One **danger clock** (edge hints + rear mirror merged)
- Optional soft target lock
- 200ms V-toggle blend
- Boss letterbox 2px
- LOD + heatmap caps (wells)

### Three lenses

| Lens | Borrow |
|------|--------|
| **Racing** | Slingshot ghost lines, drift style meter, gate photo freeze |
| **Horror** | Low-hull cockpit occlusion, mandatory mirror 7+, purple glass smears |
| **Diegetic** | Coin-tray treasury, analog threat gauge, doctrine sticker on glass |

### Audio (when added)

Engine whine ∝ thrust; wet squid motion; neutral IFF ping; gate chime; silence before periapsis.

---

## Skill deck, economy & builds

### New branches (Act II+)

| Branch | Examples |
|--------|----------|
| Tactics | Threat HUD+, mirror zoom, well footprint preview |
| Diplomacy | Lower aggro, bribe, worse DPS |
| Salvage | Jewel magnet, core carry penalty, break bonus |
| Horror ward | Tentacle resist, biolum filter |
| Escort++ | Wingman heal, ally cap, decoy call |

### Advanced tier examples

- Lance+ → split beam after pierce
- Triple Tap+ → explosive center slug only
- Supernova+ → cluster impact
- Drone → ace wingman tracers
- Rubber → reactive plating (one free bounce kill/sector)

### Controversy nodes

Mutiny insurance; corporate shell company (rep flip); brood sample (squids passive, humans hostile).

### Build identities

| Build | Feel |
|-------|------|
| Glass Lance | Sniper rhythm |
| Shotgun Surgeon | Close chaos |
| Nova Farmer | AoE score |
| Diplomat | Escort master |
| Horror Sympathizer | Squids ignore you |
| Tank Brigand | Bulkhead ×3 forgiving |

### Anti-builds (hard mode endings)

Pacifist charter (no doctrine); broke captain (zero jewels 6–10); squid friend (never kill—seal/lure only).

### Jewel economy as story

| Source | Narrative read |
|--------|----------------|
| Beacons | Legitimate piracy |
| Asteroid break | Miners hate you |
| Kills | Corporate hate you |
| Neutral theft | Heat + scavenger memory |
| Civilian save | Ending stat, few jewels |
| Periapsis bonus | Leaderboard brag |

**Mid-campaign:** corporate **amnesty**—jewels → rep at bad rate. **No grind wall** for 9–10.

---

## Quests, narrative & endings

### Main spine (post-5)

1. Who opened the Rift lane? (fragments 6–10)
2. Brood intelligence reacts to weapon doctrine
3. Charter sets rep
4. Accretion Court verdict

### Five competing truths (black boxes contradict)

Corporate mining; Brood from below; *you* in prior NG+ run; miner accident; natural lane—factions invented story.

### Quest layers

**Layer 1 — Contract cards:** one main + two side + optional curse (*Hands Clean*, *Loud Doctrine*, *Dead Reckoning*).

**Layer 2 — Sagas:** Black Box (5 boxes); Wingman’s Debt; Coffee Moon.

**Layer 3 — Flags:** `relay_saved`, `charter_signed`, `brood_scanned`, `comet_ridden`, etc. → one dialogue line + ending slide each.

### Side templates

Bounty, salvage timer, silence run, escort chain, horror scan.

### Lore delivery

Radio squelch; chart **RUMOR** tab; black box VOIP—**no codex menu**.

### Endings matrix

Rows = Arm D choice (save / destroy brood / steal data / burn lane).  
Columns = identity (pirate king / corporate dog / void saint / ghost).

NG+ uses ending slide as next briefing background.

---

## Factions, bosses & mission combinatorics

### Reputation (−100 to +100)

Corporate · Free miners · Void cult (high = squids calmer, humans angrier).

Affects spawns, shop, endings, wingman barks.

### Boss roster

| Boss | Slot | Hook |
|------|------|------|
| Salvage Crawler | 6 | Tractor + debris |
| Shoal Oracle | 7 | Lures + ring summons |
| Charter Arbiter | 8 | Shields + crowd panic |
| Perihelion Leviathan | 9 | Comet-riding phases |
| Brood-Mother Ascendant | 10 | Hybrid segments |
| Quiet Captain | 11+ | Mirrors your doctrine FX |

### Mission axes (mix & match)

Space shape · win condition · enemy line · ally presence · economy · special (EVA, no-fire, stealth).

---

## Captain, crew & rivals

### Captain archetype (one label, not a class)

Smuggler · Privateer · Mediator · Void-touched → nudges shop + endings.

### Crew (audio/HUD; silencable)

Engineer (well quips), Gunner (flank calls), Cook (moon coffee buff).

### Rivals

**Red Keel** route ghost · **Charter Arbiter** duel · **Quiet Captain** ghost boss.

---

## Multiplayer & async

| Mode | Notes |
|------|-------|
| Ghost route | JSON replay; holo racing line |
| Contract board | Async salvage tags + jewel tip |
| Duel chart | Same seed gate race |
| Fleet memory | Community “relay saved %” flag |

Stdlib-first—no MMO requirement.

---

## Accessibility, audio, modding, seasonal

**Accessibility:** tactical auto-fit zoom; shape IFF (squid blob / human chevron / neutral diamond); motion reduce bank + biolum invert off; single objective compass.

**Music acts:** 1 synth arcade · 2 industrial tension · 3 choir dread · 4 pirate legend + accordion joke.

**Modding:** compose from WorldConfig flags, spawn tables, layouts, win plugins, briefing text—community “Charter inverted” packs.

**Seasonal (offline):** Perihelion week, Charter month, Drift anniversary, Bulkhead sale.

---

## Technical enablers & production order

| System | Unlocks |
|--------|---------|
| Rep + IFF stages | 6, 8, endings |
| Witness / heat | 6, morality |
| Comet frame | 9, 11 |
| Multi-phase missions | 10, 16 |
| EVA micro-grid | 9, 11 |
| Contract cards | Replay |
| Sector holo map | 7 vs 8 branch |
| Ghost route recorder | Chase + async |
| Living flags | Endings, Act V |

### Suggested production (identity-first)

1. Sector holo map + branch briefing  
2. Neutral IFF + heat  
3. Chase racing line + contact shadows  
4. Contract cards  
5. Level 6 Salvage  
6. Living world flags  
7. Level 7 *or* 8 (player choice)  
8. Comet frame  
9. Level 10 Court  
10. Act V if replay strong  

*(Horizontal chase polish benefits all levels in parallel with step 3.)*

---

## Anti-patterns

1. Bullet sponge bosses without phases  
2. Neutral instant-fail on splash damage  
3. EVA becoming half the game  
4. New weapon type every level  
5. Chase that needs post-processing to read  
6. Jewel grind wall before 9–10  
7. Lore codex menu  
8. Friendly AI that rams player  
9. Level 6 as “another siege”  
10. Horror comedy / squid jokes  

---

## Wild ideas bin

Gravity duel boss (slingshot accuracy not DPS) · ship-too-big barge level · reverse IFF until doctrine shot · pet space crab · pet squid wingman hates · drunk thrust consumable · solar flare EMP level · secret 6th doctrine railgun · brigand union strike · accretion surf time trial · hole sings morse ARG · wanted poster from palette · gravity surf score multiplier · reverse level (gate inward) · co-op hot-seat drone · captain’s quarters title room · time-reversed shot ghosts · alliance with squids ending · black hole marriage joke ending · language barrier corporate subtitles · asteroid pet rock · captain log typed death screen · megastructure elevator strip · community seasonal comet leaderboard · executive kidnapping ransom · glass fleet · well whisper UI glitch · land on moon brew coffee restore 1 chunk · pyrrhic crown alt · the 6th doctrine heresy · your face on holo warrant  

---

## Vision statements

**Levels 6–10:**  
> Salvage the dead fleet, survive the squid tide, broker a fragile charter, ride the comet into the hole, and choose who owns the Accretion Court—while the skill deck remembers whether you were pirate, diplomat, or horror.

**Acts II–III:**  
> Act II is when the void becomes a neighborhood—thieves, believers, things that hunt in gravity. Act III asks whether you’ll be its landlord, its meal, or its ghost.

---

*Brainstorm only—not a commitment schedule. Revisit after Siege polish and chase cam pass.*
