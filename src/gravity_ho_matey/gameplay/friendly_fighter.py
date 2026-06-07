from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.ally_kinds import AllyKind
from gravity_ho_matey.gameplay.boost_lane import LaneProbe, LaneState
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.lane_physics import LaneModifiers, apply_lane_centering
from gravity_ho_matey.gameplay.entities import GravityWell, Projectile
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss

# Escort baseline — faster than prior pass, still below player top-end.
_DEFAULT_THRUST = 252.0
_DEFAULT_MAX_SPEED = 106.0
_CATCH_UP_SPEED = 128.0
_DEFAULT_TURN_RATE = 4.95
_DEFAULT_FIRE_INTERVAL = 4.4
_DEFAULT_SHOT_SPEED = 214.0
_DEFAULT_ENGAGE_RANGE = 520.0
_BOSS_ENGAGE_BONUS = 140.0
_SQUID_TARGET_BIAS = 48.0

ALLY_HIGHWAY_CRUISE_RATIO = 0.90
ALLY_HIGHWAY_CATCHUP_RATIO = 0.96
_DEFAULT_MIN_RANGE = 85.0
_DEFAULT_AIM_LEAD = 0.58
_DEFAULT_AIM_SPREAD = 0.068


@dataclass(frozen=True, slots=True)
class ThreatTarget:
    pos: Vec2
    vel: Vec2
    radius: float
    is_boss: bool = False
    is_asteroid: bool = False
    is_squid: bool = False
    danger_radius: float = 0.0


@dataclass(slots=True)
class FriendlyFighter:
    """Allied escort — follows the player and engages nearby hostiles."""

    wing_id: int
    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    angle: float = 0.0
    facing_angle: float = 0.0
    alive: bool = True
    radius: float = 10.0
    hits_remaining: int = 2
    hits_max: int = 2
    fire_cooldown: float = 0.0
    boost_flash: float = 0.0
    thrust: float = _DEFAULT_THRUST
    max_speed: float = _DEFAULT_MAX_SPEED
    catch_up_speed: float = _CATCH_UP_SPEED
    turn_rate: float = _DEFAULT_TURN_RATE
    fire_interval: float = _DEFAULT_FIRE_INTERVAL
    shot_speed: float = _DEFAULT_SHOT_SPEED
    engage_range: float = _DEFAULT_ENGAGE_RANGE
    min_range: float = _DEFAULT_MIN_RANGE
    aim_lead_factor: float = _DEFAULT_AIM_LEAD
    aim_spread_rad: float = _DEFAULT_AIM_SPREAD
    formation_lateral: float = 88.0
    formation_trail: float = 58.0
    catch_up_radius: float = 400.0

    @property
    def kind(self) -> AllyKind:
        return AllyKind.FRIENDLY_FIGHTER

    def formation_offset(self, player_angle: float) -> Vec2:
        forward = Vec2.from_angle(player_angle)
        right = forward.rotated(math.pi / 2.0)
        lateral = self.formation_lateral if self.wing_id == 0 else -self.formation_lateral * 1.12
        trail = self.formation_trail + (18.0 if self.wing_id == 1 else 0.0)
        return right * lateral - forward * trail

    def formation_target(self, player_pos: Vec2, player_angle: float) -> Vec2:
        return player_pos + self.formation_offset(player_angle)

    def pick_threat(
        self,
        enemies: list,
        boss: MegaSquidBoss | None,
    ) -> ThreatTarget | None:
        if boss is not None and boss.alive:
            boss_dist = (boss.pos - self.pos).length() - boss.radius * 0.35
            if boss_dist <= self.engage_range + _BOSS_ENGAGE_BONUS:
                return ThreatTarget(
                    pos=Vec2(boss.pos.x, boss.pos.y),
                    vel=Vec2(boss.vel.x, boss.vel.y),
                    radius=boss.radius,
                    is_boss=True,
                )

        best: ThreatTarget | None = None
        best_score = self.engage_range + 1.0
        for enemy in enemies:
            if not enemy.alive:
                continue
            dist = (enemy.pos - self.pos).length()
            if dist > self.engage_range:
                continue
            kind = getattr(enemy, "kind", None)
            bias = _SQUID_TARGET_BIAS if kind is EnemyKind.SQUID else 0.0
            score = dist - bias
            if score >= best_score:
                continue
            vel = getattr(enemy, "vel", Vec2())
            is_squid = kind is EnemyKind.SQUID
            danger = getattr(enemy, "tentacle_span", lambda: enemy.radius)() if is_squid else enemy.radius
            best = ThreatTarget(
                pos=Vec2(enemy.pos.x, enemy.pos.y),
                vel=vel,
                radius=enemy.radius,
                is_squid=is_squid,
                danger_radius=danger,
            )
            best_score = score
        return best

    def integrate(
        self,
        dt: float,
        *,
        player_pos: Vec2,
        player_vel: Vec2,
        player_angle: float,
        wells: list[GravityWell],
        gravity_scale: float,
        drag: float,
        well_maw_radius: float,
        threat: ThreatTarget | None,
        lane_probe: LaneProbe | None = None,
        lane_mods: LaneModifiers | None = None,
        thrust_mult: float = 1.0,
        pad_overspeed_cap: float = 1.0,
    ) -> None:
        if not self.alive:
            return

        form_target = self.formation_target(player_pos, player_angle)
        to_form = form_target - self.pos
        form_dist = to_form.length()

        if threat is not None and (threat.pos - self.pos).length() <= self.engage_range * 0.92:
            to_combat = threat.pos - self.pos
            desired_heading = math.atan2(to_combat.y, to_combat.x)
            move_goal = form_target * 0.35 + threat.pos * 0.65
            to_move = move_goal - self.pos
        else:
            desired_heading = math.atan2(to_form.y, to_form.x) if form_dist > 1e-6 else self.angle
            to_move = to_form

        heading_delta = _angle_delta(desired_heading - self.angle)
        max_turn = self.turn_rate * dt
        if heading_delta > max_turn:
            self.angle += max_turn
        elif heading_delta < -max_turn:
            self.angle -= max_turn
        else:
            self.angle = desired_heading
        self.facing_angle = self.angle

        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale
        accel += hazard_escape_acceleration_at(
            self.pos,
            wells,
            gravity_scale=gravity_scale,
            default_maw_radius=well_maw_radius,
        )
        on_highway = (
            lane_probe is not None
            and lane_mods is not None
            and lane_probe.state is LaneState.ON_RIBBON
        )
        if on_highway and lane_mods is not None:
            cruise_cap = lane_mods.max_speed * ALLY_HIGHWAY_CRUISE_RATIO
            catch_cap = lane_mods.max_speed * ALLY_HIGHWAY_CATCHUP_RATIO
        else:
            cruise_cap = self.max_speed
            catch_cap = self.catch_up_speed

        speed_cap = catch_cap if form_dist > self.catch_up_radius else cruise_cap
        if self.boost_flash > 0.0 and on_highway and lane_mods is not None:
            speed_cap = max(speed_cap, lane_mods.max_speed * pad_overspeed_cap * ALLY_HIGHWAY_CATCHUP_RATIO)

        catch_thrust = 1.26 if form_dist > self.catch_up_radius else 1.0
        if to_move.length_sq() > 64.0:
            player_match = min(1.12, 0.35 + player_vel.length() / max(1.0, speed_cap))
            accel += Vec2.from_angle(self.angle) * (self.thrust * thrust_mult * catch_thrust * player_match)

        if on_highway and lane_mods is not None and lane_probe is not None:
            accel = apply_lane_centering(accel, lane_probe, lane_mods)

        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(speed_cap)
        self.pos = self.pos + self.vel * dt

    def tick_combat(self, dt: float) -> None:
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

    def try_fire(self, threat: ThreatTarget | None) -> Projectile | None:
        if not self.alive or self.fire_cooldown > 0.0 or threat is None:
            return None
        to_target = threat.pos - self.pos
        dist = to_target.length()
        if dist < self.min_range or dist > self.engage_range:
            return None

        aim_dir = lead_aim_direction(
            self.pos,
            threat.pos,
            threat.vel * self.aim_lead_factor,
            self.shot_speed,
            refine_passes=2,
        )
        if aim_dir is None:
            return None

        spread = (random.random() * 2.0 - 1.0) * self.aim_spread_rad
        aim_dir = aim_dir.rotated(spread)
        self.fire_cooldown = self.fire_interval
        self.facing_angle = math.atan2(aim_dir.y, aim_dir.x)
        muzzle = self.pos + aim_dir * (self.radius + 6.0)
        inherit = self.vel * 0.10 if self.vel.length_sq() > 1.0 else Vec2()
        return Projectile(
            pos=muzzle,
            vel=aim_dir * self.shot_speed + inherit,
            ttl=2.0,
            radius=3.5,
            hostile=False,
            from_ally=True,
        )

    def apply_shot(self) -> bool:
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        return False

    def body_hit_by_projectile(self, projectile_pos: Vec2, projectile_radius: float) -> bool:
        return (projectile_pos - self.pos).length() <= self.radius + projectile_radius


def _angle_delta(angle: float) -> float:
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    return angle
