from __future__ import annotations

from dataclasses import dataclass

# Brief HUD pulse when a new wave starts (waves 2+ only — wave 1 is already obvious).
WAVE_NUDGE_SECONDS = 1.0
# Soft "something's coming" hint — no countdown, no modal chrome.
INBOUND_HINT_SECONDS = 6.0


@dataclass(frozen=True, slots=True)
class WaveMissionCopy:
    headline: str
    subtitle: str


_WAVE_COPY: dict[int, WaveMissionCopy] = {
    1: WaveMissionCopy("WAVE 1", "patrol contact"),
    2: WaveMissionCopy("WAVE 2", "void squids"),
    3: WaveMissionCopy("WAVE 3", "brood mother"),
}


def wave_mission_copy(wave: int) -> WaveMissionCopy:
    return _WAVE_COPY.get(wave, WaveMissionCopy(f"WAVE {wave}", "hostile contact"))


@dataclass(slots=True)
class WaveMissionPresentation:
    """Gentle HUD wave hints for protection missions — never blocks play."""

    wave_times: tuple[float, float, float] = (0.0, 20.0, 40.0)
    total_waves: int = 3
    waves_spawned: int = 0
    nudge_wave: int = 0
    nudge_ttl: float = 0.0
    inbound_wave: int = 0
    inbound_seconds: float = 0.0

    @property
    def all_waves_fired(self) -> bool:
        return self.waves_spawned >= self.total_waves

    @property
    def current_wave(self) -> int:
        return min(self.total_waves, max(1, self.waves_spawned))

    def tick(self, elapsed: float, dt: float) -> None:
        if self.nudge_ttl > 0.0:
            self.nudge_ttl = max(0.0, self.nudge_ttl - dt)
            if self.nudge_ttl <= 0.0:
                self.nudge_wave = 0

        self.inbound_wave = 0
        self.inbound_seconds = 0.0
        if self.waves_spawned >= self.total_waves:
            return
        next_index = self.waves_spawned
        next_time = self.wave_times[next_index]
        remaining = next_time - elapsed
        if next_index == 0 and self.waves_spawned == 0 and remaining <= 0.0:
            return
        if 0.0 < remaining <= INBOUND_HINT_SECONDS:
            self.inbound_wave = next_index + 1
            self.inbound_seconds = remaining

    def poll_spawn(self, elapsed: float) -> int | None:
        if self.waves_spawned >= self.total_waves:
            return None
        next_wave = self.waves_spawned + 1
        if elapsed < self.wave_times[self.waves_spawned]:
            return None
        self.waves_spawned = next_wave
        self._trigger_nudge(next_wave)
        return next_wave

    def _trigger_nudge(self, wave: int) -> None:
        if wave <= 1:
            self.nudge_wave = 0
            self.nudge_ttl = 0.0
        else:
            self.nudge_wave = wave
            self.nudge_ttl = WAVE_NUDGE_SECONDS
        self.inbound_wave = 0
        self.inbound_seconds = 0.0

    def nudge_copy(self) -> WaveMissionCopy | None:
        if self.nudge_wave <= 0 or self.nudge_ttl <= 0.0:
            return None
        return wave_mission_copy(self.nudge_wave)

    def inbound_copy(self) -> WaveMissionCopy | None:
        if self.inbound_wave <= 0 or self.inbound_seconds <= 0.0:
            return None
        return wave_mission_copy(self.inbound_wave)

    # Back-compat aliases for any external readers
    @property
    def flash_wave(self) -> int:
        return self.nudge_wave

    @property
    def flash_ttl(self) -> float:
        return self.nudge_ttl

    def flash_copy(self) -> WaveMissionCopy | None:
        return self.nudge_copy()
