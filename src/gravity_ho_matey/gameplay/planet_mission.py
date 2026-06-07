from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2


@dataclass(frozen=True, slots=True)
class PlanetBody:
    """Reusable planet/moon spec for orbital approach → surface transition missions."""

    center: Vec2
    surface_radius: float
    landing_band_inner: float
    landing_band_outer: float

    @classmethod
    def from_surface_radius(
        cls,
        center: Vec2,
        surface_radius: float,
        *,
        inner_slack: float = 48.0,
        outer_slack: float = 200.0,
    ) -> PlanetBody:
        """Landing band wraps the full planetary limb — any approach angle works."""
        return cls(
            center=center,
            surface_radius=surface_radius,
            landing_band_inner=max(32.0, surface_radius - inner_slack),
            landing_band_outer=surface_radius + outer_slack,
        )


def in_planet_landing_band(ship_pos: Vec2, body: PlanetBody) -> bool:
    dist = (ship_pos - body.center).length()
    return body.landing_band_inner <= dist <= body.landing_band_outer


def limb_point_toward(ship_pos: Vec2, body: PlanetBody) -> Vec2:
    """Nearest point on the planet limb from the ship — for edge hints / UI."""
    offset = ship_pos - body.center
    if offset.length_sq() <= 1e-6:
        return body.center + Vec2(body.surface_radius, 0.0)
    return body.center + offset.normalized() * body.surface_radius


def landing_band_mid_radius(body: PlanetBody) -> float:
    return (body.landing_band_inner + body.landing_band_outer) * 0.5


# --- Planet mission framework hooks (L6 Brood Moon is first consumer) ---
#
# Planetside design lock (L6+ surface phases):
#   - Tactical side-scroll camera only (chase disabled on surface_wrap worlds).
#   - Toroidal X wrap via WorldConfig.surface_wrap + planetside_flight profile.
#   - Faster cruise + stronger Shift boost (burst, overspeed, REACTOR_BURST FX).
#   - Edge hints: wrap-aware rim arrows for beacons (◈), egg pods (EG), boss (BM).
#
# PlanetBody              — orbital limb + landing annulus geometry
# SurfacePropTable        — levels.brood_moon_props.BROOD_SURFACE_PROPS
# OrbitalHazardPolicy     — ORBITAL_DEBRIS_EXCLUDE_* in brood_moon_layout
# PhaseRenderHooks        — planet_mission_viz (orbital band tactical/chase),
#                           brood_moon_surface_viz (surface band tactical/chase)
#
# Future land-on-X levels implement props + materials and reuse this controller pattern.
