from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.planet_mission import PlanetBody


@dataclass(frozen=True, slots=True)
class CometBody:
    """Elliptical orbit body — phase frozen while player is on-foot."""

    path_center: Vec2
    orbit_semi_major: float
    orbit_semi_minor: float
    angular_speed: float
    surface_radius: float
    landing_band_inner: float
    landing_band_outer: float
    phase: float = 0.0
    phase_frozen: bool = False

    def position(self) -> Vec2:
        return self.path_center + Vec2(
            math.cos(self.phase) * self.orbit_semi_major,
            math.sin(self.phase) * self.orbit_semi_minor,
        )

    def advance(self, dt: float) -> CometBody:
        if self.phase_frozen:
            return self
        return CometBody(
            path_center=self.path_center,
            orbit_semi_major=self.orbit_semi_major,
            orbit_semi_minor=self.orbit_semi_minor,
            angular_speed=self.angular_speed,
            surface_radius=self.surface_radius,
            landing_band_inner=self.landing_band_inner,
            landing_band_outer=self.landing_band_outer,
            phase=self.phase + self.angular_speed * dt,
            phase_frozen=self.phase_frozen,
        )

    def with_frozen_phase(self, frozen: bool) -> CometBody:
        return CometBody(
            path_center=self.path_center,
            orbit_semi_major=self.orbit_semi_major,
            orbit_semi_minor=self.orbit_semi_minor,
            angular_speed=self.angular_speed,
            surface_radius=self.surface_radius,
            landing_band_inner=self.landing_band_inner,
            landing_band_outer=self.landing_band_outer,
            phase=self.phase,
            phase_frozen=frozen,
        )

    def planet_body(self) -> PlanetBody:
        pos = self.position()
        return PlanetBody(
            center=pos,
            surface_radius=self.surface_radius,
            landing_band_inner=self.landing_band_inner,
            landing_band_outer=self.landing_band_outer,
        )

    def pad_position(self) -> Vec2:
        """Sunlit face pad — trailing side of nucleus."""
        pos = self.position()
        vel_dir = Vec2(
            -math.sin(self.phase) * self.orbit_semi_major,
            math.cos(self.phase) * self.orbit_semi_minor,
        )
        if vel_dir.length_sq() <= 1e-6:
            return pos + Vec2(0.0, self.surface_radius)
        return pos - vel_dir.normalized() * (self.surface_radius + 12.0)
