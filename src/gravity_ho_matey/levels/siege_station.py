from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.levels.siege_layout import SiegeLayout


def siege_hostile_station(layout: SiegeLayout) -> SpaceStation:
    anchor = layout.station_anchor
    return SpaceStation(
        pos=Vec2(anchor.x, anchor.y),
        anchor=anchor,
        faction=StationFaction.HOSTILE,
        facing_angle=3.14159,
    )
