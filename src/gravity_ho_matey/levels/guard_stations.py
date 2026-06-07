from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.spawn_director import SpawnDirector
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.levels.guard_layout import GuardLayout


def relay_friendly_stations(layout: GuardLayout) -> list[SpaceStation]:
    anchor = layout.station_anchor
    return [
        SpaceStation(
            pos=Vec2(anchor.x, anchor.y),
            anchor=anchor,
            faction=StationFaction.FRIENDLY,
            station_label="RELAY",
            facing_angle=0.0,
            spawn_interval=19.5,
            can_spawn=True,
            director=SpawnDirector(max_alive=2, global_cooldown=3.5),
            next_wing_id=100,
        ),
    ]
