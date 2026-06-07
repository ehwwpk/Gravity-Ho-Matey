from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.chart_bounds import ChartBoundsToast, ship_in_chart
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.session import capture_level_spawn, ensure_active_life_hull
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay


@dataclass(slots=True)
class PlaySession:
    """Frozen play bootstrap — shared by launch countdown and live play."""

    level_id: str
    campaign: CampaignState
    world: GameWorld
    camera: ViewCamera
    gravity_field: GravityField
    hud_alert: str = ""
    hud_alert_ttl: float = 0.0
    bounds_toast_kind: ChartBoundsToast | None = None
    bounds_toast_ttl: float = 0.0
    ship_was_in_chart: bool | None = None
    treasury_flash_ttl: float = 0.0


def build_play_session(level_id: str, campaign: CampaignState) -> PlaySession:
    ensure_active_life_hull(campaign)
    world = build_level(level_id)
    capture_level_spawn(world)
    camera = ViewCamera()
    gravity_field = GravityField.bake(
        world.wells,
        world_width=world.config.width,
        world_height=world.config.height,
        cols=32,
        rows=max(32, int(32 * world.config.height / max(1, world.config.width))),
        gravity_scale=world.config.gravity_scale,
    )
    session = PlaySession(
        level_id=level_id,
        campaign=campaign,
        world=world,
        camera=camera,
        gravity_field=gravity_field,
    )
    if world.config.open_bounds:
        session.ship_was_in_chart = ship_in_chart(world.ship.pos, world.config)
    else:
        session.ship_was_in_chart = True
    world.refresh_threat_snapshots()
    camera.set_play_layout(SciFiHudOverlay.PANEL_H)
    camera.snap_tactical_to_ship(world.ship.pos, world.config)
    return session
