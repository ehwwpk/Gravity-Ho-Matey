from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import EvaAvatar, Projectile
from gravity_ho_matey.gameplay.expedition_foot_config import (
    ACCEL,
    DECEL,
    FOOT_HUD_DEFAULT,
    INTERACT_MOVE_SCALE,
    MAX_SPRINT,
    MAX_WALK,
    SIDEARM_COOLDOWN,
    SIDEARM_RANGE,
    SIDEARM_SPEED,
    SIDEARM_TTL,
    SPRINT_COOLDOWN,
    SPRINT_DURATION,
    TURN_RATE,
)
from gravity_ho_matey.gameplay.expedition_mission import (
    ExpeditionInteractNode,
    ExpeditionState,
    InteractKind,
    expedition_foot_objectives_met,
    expedition_fuel_loaded,
    nearest_interact_node,
)
from gravity_ho_matey.gameplay.squid_behavior import SquidBehaviorMode
from gravity_ho_matey.gameplay.expedition_squid_ai import alert_squid_on_damage, chain_alert_nearby, tick_expedition_squid
from gravity_ho_matey.gameplay.control_intent import ControlIntent
from gravity_ho_matey.gameplay.squid_enemy import SQUID_CLING_DAMAGE_INTERVAL
from gravity_ho_matey.levels.comet_fuel_layout import EXPEDITION_HEIGHT, EXPEDITION_WIDTH

_FOOT_HUD_DEFAULT = FOOT_HUD_DEFAULT


def _refresh_foot_hud_prompt(exp: ExpeditionState) -> None:
    if expedition_fuel_loaded(exp):
        exp.hud_prompt = "FUEL SECURED — RTB AT LANDER · HOLD E"
    else:
        exp.hud_prompt = _FOOT_HUD_DEFAULT


def tick_expedition_foot(
    world,
    exp: ExpeditionState,
    dt: float,
    intent: ControlIntent,
    *,
    interaction_hold: bool,
    aim_world: Vec2 | None,
) -> None:
    avatar = world.avatar
    if avatar is None:
        return

    sprinting = intent.sprint and avatar.sprint_cooldown <= 0.0 and not avatar.carrying_fuel
    if sprinting:
        avatar.sprint_timer = max(0.0, avatar.sprint_timer - dt)
        if avatar.sprint_timer <= 0.0:
            avatar.sprint_cooldown = SPRINT_COOLDOWN
    else:
        avatar.sprint_timer = SPRINT_DURATION
        if avatar.sprint_cooldown > 0.0:
            avatar.sprint_cooldown = max(0.0, avatar.sprint_cooldown - dt)

    turn = 0.0
    if intent.rotate_left:
        turn -= 1.0
    if intent.rotate_right:
        turn += 1.0
    if turn != 0.0:
        avatar.face_angle += turn * TURN_RATE * dt

    forward = 0.0
    if intent.thrust:
        forward += 1.0
    if intent.reverse:
        forward -= 1.0

    if aim_world is not None:
        avatar.aim_angle = math.atan2(aim_world.y - avatar.pos.y, aim_world.x - avatar.pos.x)
    else:
        avatar.aim_angle = avatar.face_angle

    max_speed = MAX_SPRINT if sprinting and avatar.sprint_cooldown <= 0.0 else MAX_WALK
    if avatar.carrying_fuel:
        max_speed = MAX_WALK * 0.88
    if interaction_hold and exp.active_interact_id:
        max_speed *= INTERACT_MOVE_SCALE

    if abs(forward) > 1e-6:
        desired = Vec2.from_angle(avatar.face_angle) * (forward * max_speed)
    else:
        desired = Vec2()
    blend = ACCEL if desired.length_sq() > avatar.vel.length_sq() else DECEL
    avatar.vel = avatar.vel + (desired - avatar.vel) * min(1.0, blend * dt)
    avatar.pos = avatar.pos + avatar.vel * dt
    avatar.pos = Vec2(
        max(40.0, min(float(EXPEDITION_WIDTH) - 40.0, avatar.pos.x)),
        max(40.0, min(float(EXPEDITION_HEIGHT) - 40.0, avatar.pos.y)),
    )

    if avatar.fire_cooldown > 0.0:
        avatar.fire_cooldown = max(0.0, avatar.fire_cooldown - dt)
    if intent.fire and avatar.fire_cooldown <= 0.0:
        direction = Vec2.from_angle(avatar.aim_angle)
        muzzle = avatar.pos + direction * (avatar.radius + 6.0)
        world.projectiles.append(
            Projectile(
                pos=muzzle,
                vel=direction * SIDEARM_SPEED,
                ttl=SIDEARM_TTL,
                radius=3.0,
                hostile=False,
            )
        )
        avatar.fire_cooldown = SIDEARM_COOLDOWN
        avatar.recoil_timer = 0.08

    if avatar.recoil_timer > 0.0:
        avatar.recoil_timer = max(0.0, avatar.recoil_timer - dt)
    if avatar.invuln_remaining > 0.0:
        avatar.invuln_remaining = max(0.0, avatar.invuln_remaining - dt)

    _tick_interact(world, exp, avatar, dt, interaction_hold=interaction_hold)
    _tick_foot_projectiles(world, exp, dt)
    _tick_foot_squids(world, exp, avatar, dt)


def _tick_interact(world, exp: ExpeditionState, avatar: EvaAvatar, dt: float, *, interaction_hold: bool) -> None:
    node = nearest_interact_node(exp, avatar.pos)
    if node is None or not interaction_hold:
        exp.interact_charge = max(0.0, exp.interact_charge - dt * 2.0)
        exp.active_interact_id = ""
        _refresh_foot_hud_prompt(exp)
        return
    if node.kind is InteractKind.EXTRACT_PAD and not expedition_foot_objectives_met(exp):
        exp.active_interact_id = node.id
        exp.interact_charge = max(0.0, exp.interact_charge - dt * 3.0)
        exp.hud_prompt = "LOAD FUEL AT CHARTER DEPOT FIRST"
        return
    exp.active_interact_id = node.id
    exp.interact_charge = min(node.charge_seconds, exp.interact_charge + dt)
    if exp.interact_charge >= node.charge_seconds:
        _complete_interact(world, exp, node)
        exp.interact_charge = 0.0
        exp.active_interact_id = ""


def _complete_interact(world, exp: ExpeditionState, node: ExpeditionInteractNode) -> None:
    if node.kind is InteractKind.FUEL_VALVE and node.id not in exp.completed_interact_ids:
        exp.completed_interact_ids.add(node.id)
        exp.fuel_nodes_loaded += 1
        avatar = world.avatar
        if avatar is not None:
            avatar.carrying_fuel = True
        if expedition_fuel_loaded(exp):
            exp.hud_prompt = "FUEL SECURED — RTB AT LANDER · HOLD E"
    elif node.kind is InteractKind.EXTRACT_PAD:
        if expedition_foot_objectives_met(exp):
            exp.extract_pending = True
            exp.hud_prompt = "RTB — UNDOCKING…"
            avatar = world.avatar
            if avatar is not None:
                avatar.carrying_fuel = False


def _tick_foot_projectiles(world, exp: ExpeditionState, dt: float) -> None:
    kept: list[Projectile] = []
    for projectile in world.projectiles:
        projectile.pos = projectile.pos + projectile.vel * dt
        projectile.ttl -= dt
        if projectile.ttl <= 0.0:
            continue
        if (projectile.pos - (world.avatar.pos if world.avatar else Vec2())).length() > SIDEARM_RANGE + 80.0:
            continue
        hit = False
        for i, enemy in enumerate(world.enemies):
            if not enemy.alive:
                continue
            if enemy.body_hit_by_projectile(projectile.pos, projectile.radius):
                if enemy.apply_shot():
                    enemy.alive = False
                    exp.hostiles_remaining = max(0, exp.hostiles_remaining - 1)
                else:
                    if i < len(exp.squid_entries):
                        alert_squid_on_damage(exp.squid_entries[i])
                        chain_alert_nearby(exp.squid_entries, world.enemies, enemy.pos)
                hit = True
                break
        if not hit:
            kept.append(projectile)
    world.projectiles.clear()
    world.projectiles.extend(kept)


def _squid_threatens_avatar(squid, entry, avatar: EvaAvatar) -> bool:
    if entry.mode not in (SquidBehaviorMode.ALERT.name, SquidBehaviorMode.ENGAGE.name):
        return False
    touch_radius = avatar.radius + 14.0
    if squid.any_tentacle_on_hull(avatar.pos, touch_radius):
        return True
    return squid.is_clinging(avatar.pos, avatar.radius + 4.0)


def _tick_foot_squids(world, exp: ExpeditionState, avatar: EvaAvatar, dt: float) -> None:
    clinging = False
    for entry, squid in zip(exp.squid_entries, world.enemies, strict=False):
        if not squid.alive:
            continue
        tick_expedition_squid(
            squid,
            entry,
            feed_points=exp.feed_points,
            avatar_pos=avatar.pos,
            avatar_radius=avatar.radius,
            dt=dt,
        )
        if _squid_threatens_avatar(squid, entry, avatar):
            clinging = True

    if clinging and avatar.invuln_remaining <= 0.0:
        exp.eva_cling_timer += dt
        if exp.eva_cling_timer >= SQUID_CLING_DAMAGE_INTERVAL:
            exp.eva_cling_timer = 0.0
            exp.interact_charge = 0.0
            exp.active_interact_id = ""
            world._register_eva_hit()
            if world.avatar is not None:
                world.avatar.invuln_remaining = 0.45
    else:
        exp.eva_cling_timer = 0.0

    exp.hostiles_remaining = sum(1 for enemy in world.enemies if enemy.alive)
