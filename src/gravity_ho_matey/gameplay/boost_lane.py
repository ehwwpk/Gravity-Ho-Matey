from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.membrane_ribbons import nearest_ribbon
from gravity_ho_matey.levels.membrane_layout import MembraneLayout

RUNOFF_EXTRA = 280.0


class LaneState(Enum):
    ON_RIBBON = auto()
    RUNOFF = auto()
    VOID = auto()


@dataclass(frozen=True, slots=True)
class LaneProbe:
    state: LaneState
    dist: float
    tangent: Vec2
    ribbon_id: str
    half_width: float


def probe_lane(pos: Vec2, layout: MembraneLayout) -> LaneProbe:
    hit = nearest_ribbon(pos, layout.samples)
    if hit is None:
        return LaneProbe(LaneState.VOID, 9999.0, Vec2(0.0, -1.0), "", 0.0)
    half_w = hit.sample.half_width
    if hit.dist <= half_w:
        state = LaneState.ON_RIBBON
    elif hit.dist <= half_w + RUNOFF_EXTRA:
        state = LaneState.RUNOFF
    else:
        state = LaneState.VOID
    return LaneProbe(
        state=state,
        dist=hit.dist,
        tangent=hit.sample.tangent,
        ribbon_id=hit.sample.ribbon_id,
        half_width=half_w,
    )
