"""Player-facing holo chart briefing — objectives and context refreshers per sector."""

from __future__ import annotations

# Each row is (section_label, line). Empty label = continuation under prior section.
BriefingRow = tuple[str, str]

JUNK_CORRIDOR_HAZARDS: BriefingRow = ("HAZARDS", "Indestructible scrap walls — fly the gaps.")

# Standard section labels — same structure game-wide; renderer groups by label.
LEVEL_BRIEFING: dict[str, tuple[BriefingRow, ...]] = {
    "cove": (
        ("OBJECTIVE", "Collect nav beacons across the cove."),
        ("", "Four on chart — three required."),
        ("WIN", "Exit gate unlocks after 3 beacons."),
        ("HAZARDS", "Gravity wells and drifting rocks."),
        ("TIP", "Shift burst to sling past wells."),
    ),
    "solar": (
        ("OBJECTIVE", "Collect all 3 nav beacons."),
        ("", "Patrol skiffs guard the lanes."),
        ("WIN", "South exit opens after all beacons."),
        ("HAZARDS", "Singularity maw, patrol fire, rocks."),
        ("TIP", "Map pans with you — tall sector."),
    ),
    "drift": (
        ("OBJECTIVE", "Push north through debris belts."),
        ("", "Void squids hunt the lanes."),
        ("WIN", "North exit gate is always open."),
        ("HAZARDS", "Titan wells and squid hull cling."),
        ("TIP", "Boost to shake squids off."),
    ),
    "rift": (
        ("OBJECTIVE", "Survive 3 waves at the relay."),
        ("", "Patrol, squids, then corsair strike."),
        ("WIN", "Clear all hostiles, extract south."),
        ("ALLIES", "Fighters spawn from relay bays."),
        ("HAZARDS", "Titan black holes and crossfire."),
        ("TIP", "Hold E at relay between waves to patch hull."),
    ),
    "siege": (
        ("OBJECTIVE", "Eliminate 12 hostile patrol skiffs."),
        ("", "Roster counter tracks kills left."),
        ("WIN", "Exit opens when roster is clear."),
        ("OPTIONAL", "Crack hostile station to free the lane."),
        ("ALLIES", "12 wing escorts fight with you."),
        ("HAZARDS", "Tractor beam and reinforcements."),
    ),
    "brood_moon": (
        ("ORBITAL", "Approach moon limb, hold E to land."),
        ("SURFACE", "Tag 3 beacons and rupture 6 egg pods."),
        ("", "Eight pods on field — alarms call squids."),
        ("WIN", "Circumnav to seal, hold E to ascend."),
        ("", "Return orbital and enter quarantine dock."),
        ("OPTIONAL", "Brood-Mother hunt for extra jewels."),
        ("", "Liftoff blocked if too close while she lives."),
        ("HAZARDS", "Nursery fauna on a wrap-around surface."),
    ),
    "comet_fuel": (
        ("ORBITAL", "Orbit volatile comet, hold E to dock."),
        ("EXPEDITION", "Clear squids feeding on busted fuel lines."),
        ("", "Hold E at depot valves to load fuel."),
        ("WIN", "RTB lander, undock, deliver fuel at charter depot."),
        ("", "Enter gate after fuel delivery."),
        ("HAZARDS", "Escape flight through debris and squids."),
    ),
}

# Right panel — two short reminders only (same keys every level).
LEVEL_INTEL: dict[str, tuple[BriefingRow, ...]] = {
    "cove": (
        ("CONTROLS", "Arrows/W thrust/Space fire/Shift boost."),
        ("REMEMBER", "One beacon may be skipped — need 3 of 4."),
    ),
    "solar": (
        ("CONTROLS", "Same flight — watch chart radiation timer."),
        ("REMEMBER", "All three beacons required before exit."),
    ),
    "drift": (
        ("CONTROLS", "Slingshot wells; boost breaks squid cling."),
        ("REMEMBER", "No beacon checklist — gate is open now."),
    ),
    "rift": (
        ("CONTROLS", "Hold near relay; RTB when HUD says extract."),
        ("REMEMBER", "Clear every wave before extract opens."),
    ),
    "siege": (
        ("CONTROLS", "Escorts follow; crack station to free lane."),
        ("REMEMBER", "Twelve kills on the roster unlocks exit."),
    ),
    "brood_moon": (
        ("CONTROLS", "Hold E to land and to ascend when ready."),
        ("REMEMBER", "Seal lap after surface objectives."),
    ),
    "comet_fuel": (
        ("CONTROLS", "Hold E for dock, fuel load, extract, delivery."),
        ("REMEMBER", "Feeding squids ignore you until alerted."),
    ),
}

# Drop these briefing sections first when vertical space is tight.
BRIEFING_LOW_PRIORITY: frozenset[str] = frozenset({"TIP", "HAZARDS", "OPTIONAL", "ALLIES", "CONTEXT"})

# Draw order for grouped briefing sections (same every level).
BRIEFING_SECTION_ORDER: tuple[str, ...] = (
    "OBJECTIVE",
    "ORBITAL",
    "SURFACE",
    "WIN",
    "ALLIES",
    "OPTIONAL",
    "HAZARDS",
    "TIP",
    "CONTEXT",
)
