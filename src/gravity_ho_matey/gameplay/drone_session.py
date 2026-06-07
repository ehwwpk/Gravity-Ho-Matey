from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.drone_wingman import DroneWingman
from gravity_ho_matey.gameplay.world import GameWorld


def deploy_drone_wingman(world: GameWorld, campaign: CampaignState) -> None:
    """Spawn carried drone at level start — pending purchase or surviving HP."""
    if world.drone_wingman is not None:
        return
    if campaign.drone_wingman_pending:
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship)
        campaign.drone_wingman_hp = world.drone_wingman.hits_remaining
        campaign.drone_wingman_pending = False
        return
    if campaign.drone_wingman_hp > 0:
        world.drone_wingman = DroneWingman.spawn_behind_player(
            world.ship,
            hits_remaining=campaign.drone_wingman_hp,
        )


def sync_drone_wingman_to_campaign(world: GameWorld, campaign: CampaignState) -> None:
    drone = world.drone_wingman
    if drone is None or not drone.alive:
        campaign.drone_wingman_hp = 0
        world.drone_wingman = None
    else:
        campaign.drone_wingman_hp = drone.hits_remaining
