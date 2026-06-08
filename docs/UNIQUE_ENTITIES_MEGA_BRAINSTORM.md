# Unique Entities Mega Brainstorm

**Gravity Ho, Matey!** — wild, silly, out-there planning for **Holo Bazaar expansions**, **field objects**, **friendlies**, **hostiles**, and **mega-structures** (building-scale, not “another skiff with +1 gun”).

Brainstorm only. Cross-ref: [LEVELS_6_10_MEGA_BRAINSTORM.md](LEVELS_6_10_MEGA_BRAINSTORM.md) for campaign acts, sector map, and unit lifecycle tables already sketched there. **This doc goes weirder** and focuses on *feel* — things that read as places and personalities, not stat stickers.

---

## Contents

1. [Design lens](#design-lens)
2. [Holo Bazaar — new shop branches](#holo-bazaar--new-shop-branches)
3. [One-shot & contract consumables](#one-shot--contract-consumables)
4. [Field objects & pickups](#field-objects--pickups)
5. [Friendly units & allies](#friendly-units--allies)
6. [Hostile units & hunters](#hostile-units--hunters)
7. [Neutral & weird IFF](#neutral--weird-iff)
8. [Mega-structures & buildings](#mega-structures--buildings)
9. [Bio-horror architecture](#bio-horror-architecture)
10. [Corporate & charter megafabs](#corporate--charter-megafabs)
11. [Gravity-native gimmicks](#gravity-native-gimmicks)
12. [Silly / carnival tier](#silly--carnival-tier)
13. [Combo synergies (build fantasies)](#combo-synergies-build-fantasies)
14. [Spawn & shop placement rules](#spawn--shop-placement-rules)
15. [Anti-patterns (for this doc)](#anti-patterns-for-this-doc)
16. [Wild bin — one-liners](#wild-bin--one-liners)

---

## Design lens

Every entry should pass **at least two** of:

| Question | Good answer sounds like… |
|----------|---------------------------|
| What does **gravity** do to it? | “It falls *up* on even sectors.” / “Its shots orbit before arriving.” |
| What’s the **chase silhouette**? | “You see the crown before you know what it is.” |
| What if the player **ignores** it? | “The lane closes.” / “It remembers.” / “It gets bored and leaves you a gift.” |
| What’s **funny** without undercutting horror? | Pirate bravado about something genuinely awful. |
| Is it a **place** or a **person**? | Prefer places that *behave* like persons. |

**Tone blend:** arcade pirate loot vulgarity + void horror that never jokes + corporate sterile villain paperwork.

**Implementation tags used below:**

- `[SHOP]` — Holo Bazaar / merchant tree node  
- `[FIELD]` — spawned in-sector, single use or carry  
- `[UNIT]` — mobile actor with AI  
- `[STRUCT]` — building-scale, often immobile, may have interior logic  
- `[WONDER]` — unique per sector, mission-shaping  

---

## Holo Bazaar — new shop branches

Current tree: doctrine · drive · hull · escort. Proposed **new radial spokes** (not all at once):

### Spoke: **Superstition & salvage law**

| Item | Tag | Short description |
|------|-----|-------------------|
| **Knotted Red Wire** | `[SHOP]` | First hull chunk lost each sector is “borrowed” and returns after gate — wire visibly frays on HUD. |
| **Notarized Apology** | `[SHOP]` | One witness-kill forgiven; corporate radio plays your fake confession on next neutral contact. |
| **Salvage Lien Stamp** | `[SHOP]` | +jewels from wrecks, but exit gate delays 3s while “paperwork animates” on HUD. |
| **Three-Dated Coin** | `[SHOP]` | Reroll one shop offer per sector; coin flips in treasury tray (diegetic UI). |
| **Reverse Heirloom** | `[SHOP]` | Start sector with −1 jewel; if you finish untouched, +5. Family shame as mechanics. |

### Spoke: **Void ethnography** (horror sympathy — not friendship)

| Item | Tag | Short description |
|------|-----|-------------------|
| **Squid-Appeasement Horn** | `[SHOP]` | Blow once: shoal breaks off chase — but next sector spawns one **Arch** watching from rim. |
| **Bioluminescent Decoy Gut** | `[SHOP]` | Deployable lure; attracts spores **and** patrols. Messy solutions only. |
| **Brood Taboo Mark** | `[SHOP]` | Squids ignore you 8s after boost — HUD shows forbidden symbol on boost meter. |
| **Molt Offering Crate** | `[SHOP]` | Drop jewels in lane; void squids fight each other over them for 12s. |
| **Echo Recorder** | `[SHOP]` | Replay last 5s of tentacle audio on demand — reveals Angler position in chase mirror. |

### Spoke: **Reactor crimes**

| Item | Tag | Short description |
|------|-----|-------------------|
| **Stolen Cooling Choir** | `[SHOP]` | Boost overheats slower; chase audio adds harmonic whine enemies can “hear.” |
| **Illegal Mass Injector** | `[SHOP]` | Ship temporarily +mass: slingshot harder, drift worse, shots droop beautifully. |
| **Borrowed Reactor Ghost** | `[SHOP]` | One free boost with zero meter cost — leaves a cold spot on chart you must avoid 30s. |
| **Catalytic Spite** | `[SHOP]` | Destroying mines boosts you. Encourages being petty. |
| **Half-Life Coffee** | `[SHOP]` | HUD sharpens 20s; tactical zoom breathes faster; one chunk cannot be lost during buzz. |

### Spoke: **Dockyard weird**

| Item | Tag | Short description |
|------|-----|-------------------|
| **Parasite Tow Cable** | `[SHOP]` | Drags a captured mine behind you; detonates on command (also on panic boost). |
| **Glass Anchor** | `[SHOP]` | Drop anchor in open chart: you orbit it for 4s invuln while it screams (glass stress sfx). |
| **Foldable Bulkhead** | `[SHOP]` | One frontal ram per sector becomes 0 damage + stagger. Bulkhead dents stay on ship sprite. |
| **Second-Hand Canopy** | `[SHOP]` | Chase view gains optional “roof” tint — reduces squid smear panic, adds glare on beacons. |
| **Unregistered Limb** | `[SHOP]` | Extra gun port fires **backward** only; amazing for mirror checks, terrible for dignity. |

### Spoke: **Contracts & crew drama**

| Item | Tag | Short description |
|------|-----|-------------------|
| **Wingman Lottery Ticket** | `[SHOP]` | Drone spawns with random personality: coward / show-off / lawyer. |
| **Gunner’s Grudge** | `[SHOP]` | +damage to last thing that chipped you; resets if you flee. |
| **Cook’s Thermos Upgrade** | `[SHOP]` | Moon-landing sectors: thermos POI gives random buff from list of three lies. |
| **Union Steward Badge** | `[SHOP]` | Friendly stations repair 1 chunk once — then send invoice (jewel cost next bazaar). |
| **Quiet Captain’s Map** | `[SHOP]` | Shows one “wrong” ghost route that is secretly optimal if you trust it. |

---

## One-shot & contract consumables

Bazaar buys that **live in cargo** until fired in-sector (not passive stacks):

| Name | Tag | Short description |
|------|-----|-------------------|
| **Chart Grease** | `[FIELD]` | Slip through radiation edge once without banking exposure. Leaves slick trail squids love. |
| **Bribe Capsule** | `[FIELD]` | Neutral heat −2 stages instantly; spawns “audit skiff” later anyway. |
| **Panic Ballast** | `[FIELD]` | Dump mass: huge snap turn, lose jewels overboard as physical pickups you can re-collect. |
| **Litigation Flare** | `[FIELD]` | Marks you “legal target” — patrols focus you, but witness kills don’t count. |
| **Comet Nail** | `[FIELD]` | Pin one asteroid; creates micro-well for 15s. Nail glows in chase like a streetlight. |
| **Portable Hole (Licensed)** | `[FIELD]` | Place temporary black hole footprint — **small**, expires, corporate logo on rim. |
| **Recall Beacon** | `[FIELD]` | Teleport to last collected beacon; beacon un-collects (puzzle reset). |
| **Hull Confetti** | `[FIELD]` | Sacrifice 1 chunk to blast radial shrapnel — rubber hull users get rainbow sparks (embarrassing). |
| **Translator Mold** | `[FIELD]` | Squid HUD icons show “intent” for 10s (hunger / mating / boredom). Still kill them. |
| **Not-a-Bomb** | `[FIELD]` | Arms on timer; can be dropped as mine OR traded to neutral lugger for jewels. |

---

## Field objects & pickups

Static or slow objects that **change routing** (not generic loot crates):

| Name | Tag | Short description |
|------|-----|-------------------|
| **Whispering Buoy** | `[FIELD]` | Repeats your last boost timing — echo teaches optimal slingshot rhythm. |
| **Debt Asteroid** | `[FIELD]` | Mining it grants jewels; adds invisible “weight” until you pay at next bazaar. |
| **Mirror Shard Field** | `[FIELD]` | Rear mirror shows **future** 0.5s ahead in this patch only. Disorienting. |
| **Frozen Payroll** | `[FIELD]` | Ice block with corpses + credits; thaw with thrust waste heat. |
| **Orphan Gate Fragment** | `[FIELD]` | Broken gate piece; fly through to “pre-unlock” vision of exit — psychological pull. |
| **Coral of Old Radios** | `[FIELD]` | Tuning dial rotates gravity slightly in bubble. Pirate stations of yore. |
| **Judgment Lens** | `[FIELD]` | Singularity with courtroom overlay; entering triggers “verdict” (buff or chunk). |
| **Sleeping Tug** | `[FIELD]` | Derelict with lights off; wake it → friendly escort OR angry AI if you loot first. |
| **Jewel Nest (Fake)** | `[FIELD]` | Looks like pickup cluster; actually spore cluster. Learn once, laugh once. |
| **Gratitude Mine** | `[FIELD]` | If you don’t shoot it for 30s, it opens and drops rubber hull charge. |

---

## Friendly units & allies

Not “escort that shoots” — **roles with opinions**:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Towbar Sisterhood Tug** | `[UNIT]` | Pulls you out of maw radius if you hold ping — complains about your thrust hygiene. |
| **Notary Frigate** | `[UNIT]` | Circles neutrals; prevents heat spikes unless **you** fire first. Useless in Drift, godlike in Charter. |
| **Salvage Choir Barge** | `[UNIT]` | Sings on comms; marks wreck jewels through walls while singing. |
| **Well Shepherd** | `[UNIT]` | Keeps a micro-well “calm” so you can sling predictably; leaves when you boost too much. |
| **Mirror Tender** | `[UNIT]` | Flies behind you; chase mirror always ON but shows tender’s face occasionally (jump scare). |
| **Coffee Nun Pod** | `[UNIT]` | Immobile until defended; grants thermos buff if alive at exit. |
| **Retired Enforcer** | `[UNIT]` | Slow tank; draws patrol aggro; refuses to enter squid zones (“I’ve seen things”). |
| **Kid’s Science Fair Probe** | `[UNIT]` | Draws perfect slingshot ghost lines — wrong color, right math. |
| **Lawful Good Mine** | `[UNIT]` | Mobile mine that only hits hostiles; steps in front of you heroically. |
| **Ghost Wingman (Not Yours)** | `[UNIT]` | Copies your last sector inputs with 2s delay; helps or blocks depending on rep. |

---

## Hostile units & hunters

Weird hunters that **change how you fly**, not just DPS:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Subpoena Skiff** | `[UNIT]` | No guns; proximity increases “legal drag” — thrust capped until you break line-of-sight to a relay. |
| **Mortgage Torpedo** | `[UNIT]` | Slow orbiting warhead; interest rate rises the longer it tracks; pay jewels to dismiss. |
| **Acoustic Lighthouse** | `[UNIT]` | Paints thrust noise; wakes mine layers across map. Chase view gets rhythmic strobe. |
| **Grief Counselor Flagship** | `[UNIT]` | Broadcasts fake wingman all-clear; actual threat icon hidden 5s. |
| **Orthodox Ram** | `[UNIT]` | Charges only when you boost; respects rubber hull less each hit. |
| **Cartographer Leech** | `[UNIT]` | Steals minimap/edge hints; sells them back as dropped pickup behind you. |
| **Phase Bailiff** | `[UNIT]` | Exists only in chase cam; must be shot via mirror timing. Tactical shows empty space. |
| **Jealous Comet** | `[UNIT]` | Steals your slingshot exit velocity; you exit slower if it’s watching the same well. |
| **HR Drone Swarm** | `[UNIT]` | Each kill spawns apology form pickup blocking shots until collected. |
| **Disciplinary Eclipse** | `[UNIT]` | Giant shadow disc; inside shadow, IFF lies. Outside, truth. |

---

## Neutral & weird IFF

Yellow IFF with **social mechanics**:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Fence Lugger** | `[UNIT]` | Buys stolen jewels; spawns if you over-loot witnesses. |
| **Funeral Procession** | `[UNIT]` | Slow chain of pods; any splash damage → permanent rep stain + ghost radio. |
| **Prospector Family** | `[UNIT]` | Claims asteroids; if you mine “their” rock, kid skiff chases you with slingshot only. |
| **Insurance Adjuster Ring** | `[STRUCT]` | Neutral station; inspects damage after fight — bill or buff. |
| **Pilgrim String** | `[UNIT]` | Linked ships; cutting one link makes others pray (harmless) or scream (attracts squids). |
| **Tax Season Buoy Line** | `[FIELD]` | Crossing charges jewels unless you’ve bought Notarized Apology. |
| **Sleepwalking Fleet** | `[UNIT]` | Drifts on fixed path; wake with thrust noise near them. |
| **Celebrity Chef Shuttle** | `[UNIT]` | Non-combat; if escorted, next bazaar food spoke unlocked. |

---

## Mega-structures & buildings

**Building-feel** = multi-part silhouette, interior logic, sector landmark. Bigger than ring stations.

### Scale guide

| Tier | Size feel | Examples |
|------|-----------|----------|
| **S** | Current relay / siege ring | Already in game |
| **M** | 2–3× ring; multi-ring | Charter court, salvage cathedral |
| **L** | Map-spanning; lane splitter | Accretion viaduct, comet spine |
| **XL** | Sector *is* the structure | Orphan hole orphanage, living megaring |

### M-tier structures

| Name | Tag | Short description |
|------|-----|-------------------|
| **Charter Compliance Cathedral** | `[STRUCT]` | Glass nave + rotating audit spire; flying inside = legal safe, flying above = fines as lasers. |
| **Salvage Verge Basilica** | `[STRUCT]` | Broken dome; interior micro-G “rain” falls toward pulpit reactor. Heist objective in altar. |
| **Shoal Listening Dome** | `[STRUCT]` | Half-submerged; squids press against glass — breach event if you shoot glass. |
| **Double Ring Notary** | `[STRUCT]` | Two counter-rotating rings; timing windows to pass inner dock for shop discount. |
| **Broken Elevator Strip** | `[STRUCT]` | Vertical megastructure segment; lift pods move on schedule — ride for speed, dodge for dignity. |
| **Quarantine Drydock** | `[STRUCT]` | Brood Moon scale; capture bays open/close on alarm — steal ship-sized loot or free something awful. |
| **Jury Rigged Dyson Scrap** | `[STRUCT]` | Partial shell; shadows create cold lanes; pirates nest in light gaps. |
| **The Hungry Drydock** | `[STRUCT]` | Dock clamps grab passing rocks **and** ships that idle too long. |

### L-tier wonders

| Name | Tag | Short description |
|------|-----|-------------------|
| **Accretion Viaduct** | `[WONDER]` | Bridge over disk shadow; time dilation band — boost meter drains slow, enemies fast. |
| **Comet Spine Highway** | `[WONDER]` | Land on spine; drive along it while orbital fight continues below (T1 EVA + chase split-screen fantasy). |
| **Gravity Organ** | `[WONDER]` | Pipe organ of wells; playing it (shooting pipes) retunes sector gravity for 60s. |
| **Silent Auction Hub** | `[WONDER]` | Neutrals bid on your cargo in real time; highest bidder sends hunters. |
| **The Repossession Grid** | `[WONDER]` | Laser lattice; if in debt (shop item), grid activates until paid. |

### XL-tier (one per campaign act, optional)

| Name | Tag | Short description |
|------|-----|-------------------|
| **Orphan Hole Orphanage** | `[WONDER]` | Kid pods orbit singularity; moral exit requires slingshot **without** dropping cargo. |
| **Living Megaring (Crinoid)** | `[WONDER]` | Entire sector is creature; “stations” are mouthparts; exit is sneeze. |
| **The Ledger Inverted** | `[WONDER]` | Corporate megastructure inside-out; all damage is financial until you invert again. |
| **Brood Moon Nursery Stack** | `[WONDER]` | Already partially in game — expand with cathedral anchor, egg cathedrals, seal lap as circumnav of **structure** not just distance. |

---

## Bio-horror architecture

Squid theology as **architecture**, not just units:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Spore Bell Tower** | `[STRUCT]` | Rings when you boost; wakes shoals progressively higher pitch. |
| **Milk Vein Aqueduct** | `[STRUCT]` | Bio-pipe crossing map; flying through heals hull but marks you “tasty.” |
| **Calamari Confessional** | `[STRUCT]` | Booth; trade 1 chunk for squid rep — they ignore you until you shoot again. |
| **Nursery Organ Pipe** | `[STRUCT]` | Vertical tubes; egg pods visible inside; rupture from outside vs inside different loot. |
| **Titan Ribcage Gate** | `[STRUCT]` | Rib arches form exit; ribs close if brood still alive. |
| **Synapse Bridge** | `[STRUCT]` | Neural bridge between two moons; pulses push ship sideways on beat. |

---

## Corporate & charter megafabs

Sterile villain paperwork at scale:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Compliance Sunflower** | `[STRUCT]` | Petals = sensor arrays; center = safe dock; petals track you if illegal cargo. |
| **Arbitration Coliseum** | `[STRUCT]` | Duel pit; Red Keel rival OR drone mirror fight; crowd neutrals bet. |
| **Mandatory Retreat Spa** | `[STRUCT]` | Heals all chunks slowly; traps you in tractor pleasant music until fee paid. |
| **Executive Escape Ark** | `[STRUCT]` | Moves toward exit; if reaches gate before you, sector fails “with apology.” |
| **Brand Orbital Billboard** | `[STRUCT]` | Blocks line of sight to real hazards with cheerful ads; shooting ads increases heat. |
| **Subsidiary Stack** | `[STRUCT]` | Nested stations; destroying outer reveals inner with different faction each layer. |

---

## Gravity-native gimmicks

Entities that only make sense because **wells are the game**:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Lagrange Funeral Platform** | `[STRUCT]` | Stable point between two wells; sniper nest that falls upward on schedule. |
| **Tidal Printer** | `[STRUCT]` | Prints mines when moons align; pattern learnable like a clock face. |
| **Well Marriage Chapel** | `[STRUCT]` | Two wells “bond”; breaking bond releases shockwave — risk/reward heist. |
| **Retrograde Chapel Bell** | `[FIELD]` | Object orbiting retrograde; catching it reverses your boost meter fill direction briefly. |
| **Gravity Debt Collector** | `[UNIT]` | Pull strength scales with jewels carried; pay at structure to debuff. |
| **Slingshot Notary Public** | `[FIELD]` | Ghost line only appears **after** you commit — confirms if commit was legal. |

---

## Silly / carnival tier

Keep horror sacred — silly targets **pirates, corps, physics**:

| Name | Tag | Short description |
|------|-----|-------------------|
| **Coconut Well** | `[FIELD]` | Well that sounds like coconut; actually maw. Lesson in trust. |
| **Pirate Accent Filter** | `[SHOP]` | All radio text gains pirate filter; wingman unintelligible but confident. |
| **Inflatable Frigate** | `[FIELD]` | Decoy XL silhouette; pops on first hit — embarrasses hostiles into pause. |
| **Disco Tractor** | `[UNIT]` | Hostile station variant; pulls you to beat; mirror shows disco ball. |
| **Mandatory Fun Zone** | `[STRUCT]` | Corporate; mini-games as traps (ring course = mine course). |
| **Seagull Drone** | `[UNIT]` | Steals single jewel; chase mirror shows bird shadow. Drift only. |
| **Haunted Boost Meter** | `[SHOP]` | Meter face shows emotions; “sad” when full — no mechanical change, pure vibe. |
| **Bag of Holding (Holey)** | `[SHOP]` | +cargo for consumables; 10% jewels fall out on boost randomly. |
| **Reverse Chase Cam** | `[SHOP]` | Chase shows where you’ve been, not where you go — mirror mandatory joke. |
| **The Compliment Mine** | `[FIELD]` | Explodes into compliments; zero damage; confuses witness system. |

---

## Combo synergies (build fantasies)

Shop + field + structure interactions worth designing toward:

| Build name | Pieces | Fantasy |
|------------|--------|---------|
| **Salvage Lawyer** | Notarized Apology + Notary Frigate + Insurance Adjuster | Never “wrong,” always late |
| **Squid Diplomat** | Appeasement Horn + Calamari Confessional + Molt Crate | Control shoals like weather |
| **Mass Poet** | Illegal Mass Injector + Comet Nail + Well Marriage | Slingshot haiku — one perfect line per sector |
| **Mirror Cultist** | Phase Bailiff hunting you + Mirror Tender ally + Echo Recorder | Fight in rear-view only |
| **Petty King** | Catalytic Spite + Complaint Mine + HR Drone Swarm | Win by being annoying |
| **Coffee Runner** | Half-Life Coffee + Coffee Nun + Thermos upgrade | Speed narrative for moon sectors |
| **Repo Man** | Debt Asteroid + Repossession Grid + Mortgage Torpedo | Roguelike but accounting |

---

## Spawn & shop placement rules

| Rule | Why |
|------|-----|
| **Silly never in boss phase** | Disco tractor ok in siege approach, not Brood phase 3 |
| **XL wonder once per act** | Memory, not clutter |
| **Shop weird unlocked by witness** | Bribe items appear after first neutral incident |
| **Structures cast chase shadow** | M/L tiers must read in mirror / horizon |
| **Bio buildings respawn geometry** | Milk Vein heals but shifts position next visit NG+ |
| **Corporate spawns rep-gated** | Charter spoke items only if heat ever hit orange |
| **Consumables max 3 carried** | Prevents bazooka inventory |
| **One-shot items don’t stack with copy of self** | Knotted Red Wire ×1 only |

---

## Anti-patterns (for this doc)

Reject ideas that are:

1. **+10% damage / +5% speed** without a story or HUD face  
2. **Another turret station** with different palette only  
3. **Friendly that rams player** (see main anti-patterns doc)  
4. **Instant fail neutral** because silly object touched them  
5. **Pop culture reference as entire joke** — we want *original* weird  
6. **EVA required** to interact with shop item  
7. **Horror that winks** — squids don’t know they’re in a game  
8. **Building with no gravity opinion** — if it doesn’t curve shots or routes, it’s wallpaper  

---

## Wild bin — one-liners

Dump for future sorting:

- Station that only opens when you **stop shooting** for 20s  
- Enemy that is **only visible in tactical**, invisible in chase (inverse Phase Bailiff)  
- Shop item: **“Borrowed Exit”** — gate works once, then doesn’t exist next sector  
- Structure: **Clockwork Kuiper Belt** — asteroids on gears, teeth bite lane  
- Friendly: **Therapist Tug** — reduces panic HUD shake, increases guilt subtitles  
- Hostile: **Apology Submarine** — torpedoes say sorry on impact  
- Field: **Well in a Box** — Schrödinger maw until observed in mirror  
- Shop: **Extended Warranty** — drone revives once, sends surveys forever  
- Structure: **Vertical Farm of Guns** — crops are turrets, harvest by shooting stalks  
- Neutral: **Intergalactic Food Critic** — rates your boost style; bad review = bounty  
- Unit: **The Accountant’s Pet Rock** — follows you, absorbs one hit, depreciates  
- Wonder: **Inverted Lighthouse** — darkness beams outward, safe in beam  
- `[SHOP]` **Glitch Hull** — random chunk becomes “?” — resolves buff or pratfall at exit  
- Structure: **Pocket Cathedral** — bigger inside; tactical zoom lies about size  
- Enemy: **Motivational Speaker Mine** — explodes into applause, pushes you toward maw  
- Friendly: **Retired Boss** — Brood-Mother NPC if spared once; sits on rim, eats patrols  
- Field: **Gravity Scratch-Off** — reveal prize by slingshot through scratch layer  
- Shop: **Installment Plan Boost** — boost now, lose future sector shop access  
- Structure: **The Departure Lounge** — waiting chairs orbit gate; sitting heals, aging raises difficulty  

---

## Vision statement (this doc)

**The best new “item” is a place that hates you politely.**

Shops sell **contracts with personality**. Fields sell **stories that curve**. Buildings sell **silhouettes you remember in chase**. Hostiles sell **new reasons to boost**. Friendlies sell **arguments**.

If it could appear in any space game with a rename — **cut it or twist it until it couldn’t**.

---

*Last updated: planning session — pairs with LEVELS_6_10 mega brainstorm; implementation order TBD.*
