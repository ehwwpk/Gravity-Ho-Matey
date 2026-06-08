from __future__ import annotations

from enum import Enum, auto


class PowerUpKind(Enum):
    THRUST_BOOST = auto()
    RAPID_FIRE = auto()
    BOOST_TAP = auto()
    RUBBER_HULL = auto()
    DRONE_WINGMAN = auto()
    NIFFLERP = auto()
    HULL_REINFORCE = auto()
    DRONE_REPAIR = auto()
    DRONE_ARMOR = auto()
    WEAPON_LASER = auto()
    WEAPON_SHOTGUN = auto()
    WEAPON_EXPLOSIVE = auto()
    WEAPON_ADV_LASER = auto()
    WEAPON_ADV_SHOTGUN = auto()
    WEAPON_ADV_EXPLOSIVE = auto()


POWERUP_LABELS: dict[PowerUpKind, str] = {
    PowerUpKind.THRUST_BOOST: "Plunder Thrusters — +6% acceleration per tier",
    PowerUpKind.RAPID_FIRE: "Gatling Rigging — modest fire-rate boost (one install)",
    PowerUpKind.BOOST_TAP: "Shift Boost Coil — +8% shift-burst per tier",
    PowerUpKind.RUBBER_HULL: "Rubber Hull — 10 asteroid bounces, no chip damage",
    PowerUpKind.DRONE_WINGMAN: "Guardian Drone — escorts next sector, 5 HP, overheats",
    PowerUpKind.NIFFLERP: "Nifflerp — jewel retriever, 3 HP, no guns, extreme agility",
    PowerUpKind.HULL_REINFORCE: "Bulkhead Plating — +2 hull chunks per life (max 3 buys)",
    PowerUpKind.DRONE_REPAIR: "Drone Field Kit — restore escort to full HP",
    PowerUpKind.DRONE_ARMOR: "Drone Armor Kit — escort max HP 8 (was 5)",
    PowerUpKind.WEAPON_LASER: "Phase Lance — piercing bursts pass through hostiles",
    PowerUpKind.WEAPON_SHOTGUN: "Scatter Cannon — twin bolts with slight spread",
    PowerUpKind.WEAPON_EXPLOSIVE: "Nova Shell — slow slugs, wide blast radius",
    PowerUpKind.WEAPON_ADV_LASER: "Prismatic Overcharge — deeper pierce, faster beam",
    PowerUpKind.WEAPON_ADV_SHOTGUN: "Triple Tap — 3 bolts: twin spread + center slug",
    PowerUpKind.WEAPON_ADV_EXPLOSIVE: "Supernova Shell — faster rocket, wider blast",
}

POWERUP_HUD_TAGS: dict[PowerUpKind, str] = {
    PowerUpKind.THRUST_BOOST: "THRUST",
    PowerUpKind.RAPID_FIRE: "GATLING",
    PowerUpKind.BOOST_TAP: "SHIFT",
    PowerUpKind.RUBBER_HULL: "RUBBER",
    PowerUpKind.DRONE_WINGMAN: "DRONE",
    PowerUpKind.NIFFLERP: "NIFFLR",
    PowerUpKind.HULL_REINFORCE: "BULKHD",
    PowerUpKind.DRONE_REPAIR: "DR-FIX",
    PowerUpKind.DRONE_ARMOR: "DR-ARM",
    PowerUpKind.WEAPON_LASER: "LANCE",
    PowerUpKind.WEAPON_SHOTGUN: "SCATTER",
    PowerUpKind.WEAPON_EXPLOSIVE: "NOVA",
    PowerUpKind.WEAPON_ADV_LASER: "LANCE+",
    PowerUpKind.WEAPON_ADV_SHOTGUN: "TRIPLE",
    PowerUpKind.WEAPON_ADV_EXPLOSIVE: "SUPER",
}
