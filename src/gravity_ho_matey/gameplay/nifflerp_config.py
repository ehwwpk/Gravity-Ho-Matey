from __future__ import annotations

# Holo bazaar — jewel-retriever contract (non-combat escort).
NIFFLERP_SHOP_PRICE = 18
NIFFLERP_HITS_MAX = 3

# Flight — fastest craft in the game; dodge-first, never shoots (+35% cruise/boost).
NIFFLERP_THRUST = 546.0
NIFFLERP_MAX_SPEED = 268.0
NIFFLERP_BOOST_SPEED = 375.0
NIFFLERP_TURN_RATE = 14.2
NIFFLERP_RADIUS = 6.5
NIFFLERP_SPAWN_TRAIL = 28.0
NIFFLERP_SPAWN_LATERAL = 34.0

# Boost — shift burst on any real threat; cheaper + longer so it can spam escapes.
NIFFLERP_BOOST_ENERGY_COST = 0.22
NIFFLERP_BOOST_REGEN = 0.26
NIFFLERP_BOOST_FLASH_SECONDS = 0.42
NIFFLERP_BOOST_TRIGGER_URGENCY = 0.22
NIFFLERP_ENEMY_BOOST_TRIGGER = 0.10

# Jewel sweep — large local radius around the captain, not full-map fetch.
NIFFLERP_SEEK_RADIUS = 520.0
NIFFLERP_JEWEL_GRAB_RANGE = 12.0
NIFFLERP_JEWEL_MAGNET_RANGE = 180.0
# Abort jewel runs when hostiles get this close while chasing loot.
NIFFLERP_JEWEL_ABORT_ENEMY_URGENCY = 0.42

# Hazard awareness — wide net, hard shove away from hostiles (squids worst).
NIFFLERP_ASTEROID_QUERY_RADIUS = 560.0
NIFFLERP_ASTEROID_AVOID_RADIUS = 230.0
NIFFLERP_ASTEROID_PANIC_GAP = 72.0
NIFFLERP_ASTEROID_AVOID_THRUST = 760.0
NIFFLERP_ENEMY_AVOID_RADIUS = 380.0
NIFFLERP_SQUID_AVOID_RADIUS = 460.0
NIFFLERP_SQUID_PANIC_RADIUS = 290.0
NIFFLERP_SQUID_AVOID_THRUST = 1180.0
NIFFLERP_ENEMY_AVOID_THRUST = 920.0
NIFFLERP_PROJECTILE_DODGE_RADIUS = 240.0
NIFFLERP_PROJECTILE_DODGE_THRUST = 860.0
NIFFLERP_WELL_ESCAPE_SCALE = 2.85
NIFFLERP_HIT_INVULN = 0.42
# Pure flee mode — drop loot chase, boost toward captain + away from threat.
NIFFLERP_FLEE_ENEMY_URGENCY = 0.30

# Play mode — figure-8 and loop-de-loops when no jewels to chase.
NIFFLERP_PLAY_ORBIT = 78.0
