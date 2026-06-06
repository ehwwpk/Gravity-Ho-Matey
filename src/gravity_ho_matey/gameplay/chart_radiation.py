from __future__ import annotations

from gravity_ho_matey.gameplay.chart_bounds import CHART_RADIATION_EXPOSURE_LIMIT, ship_in_chart
from gravity_ho_matey.gameplay.entities import GameStatus


def advance_chart_radiation_exposure(world, dt: float) -> bool:
    """Track cumulative OOB time on open charts. True when exposure limit is reached."""
    if not world.config.open_bounds:
        return False
    if world.status is not GameStatus.RUNNING:
        return False
    if world.invuln_remaining > 0.0:
        return False
    if ship_in_chart(world.ship.pos, world.config):
        return False

    world.chart_radiation_exposure += dt
    if world.chart_radiation_exposure < CHART_RADIATION_EXPOSURE_LIMIT:
        return False

    world.chart_radiation_exposure = 0.0
    return True
