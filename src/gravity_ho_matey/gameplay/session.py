from __future__ import annotations

import math
from collections.abc import Callable

from gravity_ho_matey.gameplay.chart_bounds import nudge_ship_into_chart
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.drone_session import deploy_drone_wingman
from gravity_ho_matey.gameplay.nifflerp_session import deploy_nifflerp
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.ship_modifiers import apply_powerups_to_ship
from gravity_ho_matey.gameplay.weapon_heat import reset_player_weapon_heat
from gravity_ho_matey.gameplay.world import GameWorld

INVULN_SECONDS = 1.0

JewelHudCallback = Callable[[int], None]


def capture_level_spawn(world: GameWorld) -> None:
    world.spawn_pos = Vec2(world.ship.pos.x, world.ship.pos.y)
    world.spawn_angle = world.ship.angle


def ensure_active_life_hull(campaign: CampaignState) -> None:
    """Refill hull when starting a fresh life; keep partial hull between levels."""
    if campaign.lives > 0 and campaign.hull_chunks <= 0:
        campaign.hull_chunks = campaign.max_hull_chunks_per_life


def wire_world_for_campaign(
    world: GameWorld,
    campaign: CampaignState,
    *,
    on_jewels_collected_hud: JewelHudCallback | None = None,
) -> None:
    """Apply carried campaign bonuses and route jewel collection back to campaign."""
    apply_powerups_to_ship(world.ship, campaign.powerup_stacks)

    def on_jewels_collected(amount: int) -> None:
        campaign.add_jewels(amount)
        if on_jewels_collected_hud is not None:
            on_jewels_collected_hud(amount)

    world.on_jewels_collected = on_jewels_collected
    world.consume_rubber_hull_bounce = campaign.try_consume_rubber_hull_bounce
    world.player_weapon_track = campaign.weapon_track
    world.player_weapon_advanced = campaign.weapon_advanced
    deploy_drone_wingman(world, campaign)
    deploy_nifflerp(world, campaign)


def chip_damage_recovers_in_place(*, life_lost: bool) -> bool:
    """True when a chip hit should keep the ship where it was struck."""
    return not life_lost


def recover_eva_in_place(world: GameWorld) -> None:
    """Chip damage on foot — respawn EVA at lander pad with brief invuln."""
    from gravity_ho_matey.gameplay.expedition_mission import is_expedition_foot
    from gravity_ho_matey.levels.comet_fuel_layout import LANDER_PAD

    if not is_expedition_foot(world.config) or world.avatar is None:
        recover_ship_in_place(world)
        return
    avatar = world.avatar
    avatar.pos = Vec2(LANDER_PAD.x, LANDER_PAD.y + 28.0)
    avatar.vel = Vec2()
    avatar.face_angle = -math.pi / 2
    avatar.aim_angle = -math.pi / 2
    avatar.invuln_remaining = INVULN_SECONDS
    world.invuln_remaining = INVULN_SECONDS
    world.last_damage = None
    world.status = GameStatus.RUNNING
    exp = world.expedition
    if exp is not None:
        exp.interact_charge = 0.0
        exp.active_interact_id = ""


def recover_ship_in_place(world: GameWorld) -> None:
    """Chip damage without level respawn — stay on course with brief invuln."""
    if world.config.open_bounds:
        world.ship.pos = nudge_ship_into_chart(world.ship.pos, world.config)
    world.ship.vel = Vec2()
    world.ship.boost_flash = 0.0
    world.ship.boost_jolt = 0.0
    world.invuln_remaining = INVULN_SECONDS
    world.last_damage = None
    world.status = GameStatus.RUNNING


def respawn_ship_at_spawn(world: GameWorld) -> None:
    """Teleport ship to level spawn with invuln. Caller should reset chase camera presentation."""
    world.ship.pos = Vec2(world.spawn_pos.x, world.spawn_pos.y)
    world.ship.vel = Vec2()
    world.ship.angle = world.spawn_angle
    world.ship.cooldown = 0.0
    reset_player_weapon_heat(world.ship)
    world.ship.boost_flash = 0.0
    world.ship.boost_jolt = 0.0
    world.invuln_remaining = INVULN_SECONDS
    world.last_damage = None
    world.status = GameStatus.RUNNING
