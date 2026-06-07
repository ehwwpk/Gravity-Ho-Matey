"""Field codex — welcome hangar encyclopedia entries and navigation state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodexEntry:
    entry_id: str
    title: str
    tag: str
    threat: str
    preview_kind: str
    theme: str
    blurb: str


CODEX_ENTRIES: tuple[CodexEntry, ...] = (
    CodexEntry(
        "skiff",
        "BRIGAND SKIFF",
        "YOUR RIDE",
        "CREW",
        "skiff",
        "cove",
        "Hot-wired strike hull. Boost hard, sling wells, strip wrecks for fittings that stick the whole run.",
    ),
    CodexEntry(
        "relay",
        "NAV RELAY",
        "ALLY DOCK",
        "SAFE",
        "relay_station",
        "rift",
        "Friendly ring-station — holo bazaar, chart brief, and a turret that shoots your problems, not you.",
    ),
    CodexEntry(
        "hostile_stn",
        "HOSTILE STATION",
        "SIEGE RING",
        "BRUTAL",
        "hostile_station",
        "siege",
        "Orbital fort with tractor jaws and a spawn bay. Crack the ring before it fills the lane with corsairs.",
    ),
    CodexEntry(
        "patrol",
        "PATROL SKIFF",
        "CORSAIR",
        "MEAN",
        "patrol",
        "solar",
        "Automated hunter-killer. Lead-aim guns, beacon greed. Wreck it — jewels and power-ups fall out.",
    ),
    CodexEntry(
        "squid",
        "VOID SQUID",
        "KRAKEN",
        "NASTY",
        "void_squid",
        "drift",
        "Eight arms, zero mercy. Tentacles latch the hull; you bleed a chunk every two seconds till you shake it.",
    ),
    CodexEntry(
        "brood",
        "BROOD-MOTHER",
        "MEGA BOSS",
        "APEX",
        "brood_mother",
        "rift",
        "Rift apex. Soaks turret fire, births squids and pods. Tag her down, then burn for the extract pad.",
    ),
    CodexEntry(
        "drone",
        "ESCORT DRONE",
        "CONTRACT",
        "ALLY",
        "drone",
        "cove",
        "Shop contract wingman. Hugs your six, hoses lead till the barrel glows — then it cools off and whines.",
    ),
    CodexEntry(
        "asteroid",
        "ASTEROID",
        "BELT ROCK",
        "HEAVY",
        "asteroid",
        "drift",
        "Spinning kinetic junk. Sling it through a well, shave it with guns, or wear the impact like a fool.",
    ),
    CodexEntry(
        "well",
        "GRAVITY WELL",
        "SINGULARITY",
        "LETHAL",
        "singularity",
        "solar",
        "Gravity spike on the chart. Orbit the pull tight or cook your reactor on the escape burn.",
    ),
    CodexEntry(
        "beacon",
        "NAV BEACON",
        "CHART MARK",
        "MARK",
        "beacon",
        "cove",
        "Log every beacon on the chart. Finish gate stays welded shut till the set reads green.",
    ),
)


@dataclass(slots=True)
class TitleCodexState:
    """Carousel index, turntable spin, and timed auto-advance."""

    index: int = 0
    yaw: float = 0.0
    last_auto_at: float = 0.0
    manual_until: float = 0.0

    AUTO_INTERVAL: float = 7.0
    MANUAL_PAUSE: float = 18.0

    def entry(self) -> CodexEntry:
        return CODEX_ENTRIES[self.index % len(CODEX_ENTRIES)]

    def tick(self, dt: float, elapsed: float) -> None:
        self.yaw += dt * 1.05
        if elapsed < self.manual_until:
            return
        if elapsed - self.last_auto_at >= self.AUTO_INTERVAL:
            self.step(1, elapsed, manual=False)

    def step(self, delta: int, elapsed: float, *, manual: bool = True) -> None:
        count = len(CODEX_ENTRIES)
        self.index = (self.index + delta) % count
        self.last_auto_at = elapsed
        if manual:
            self.manual_until = elapsed + self.MANUAL_PAUSE

    def reset(self) -> None:
        self.index = 0
        self.yaw = 0.0
        self.last_auto_at = 0.0
        self.manual_until = 0.0
