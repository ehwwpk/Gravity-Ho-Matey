from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import WorldConfig
from gravity_ho_matey.settings import CANVAS_HEIGHT, CANVAS_WIDTH

# Chase rig tuned like a low drone: ~10 units behind, ~15 units elevated (racing feel).
CHASE_BACK = 95.0
CHASE_LIFT = 145.0
# Horizontal FOV at the chase projection plane (pinhole: focal = (vw/2) / tan(hfov/2)).
CHASE_HFOV_DEG = 105.0
CHASE_FOCAL = (CANVAS_WIDTH * 0.5) / math.tan(math.radians(CHASE_HFOV_DEG * 0.5))
CHASE_HORIZON_FRAC = 0.26
CHASE_SHIP_ANCHOR_FRAC = 0.76
CHASE_SHIP_SCALE = 1.12
CHASE_SCREEN_HEADING = -math.pi / 2.0

# Forward/back world slide under fixed ship rig (pixels at max speed).
CHASE_VELOCITY_LAG_MAX = 21.0

# Follow-cam: beacons read smaller at depth — boost visuals + pickup forgiveness.
CHASE_BEACON_VISUAL_BOOST = 1.38
CHASE_BEACON_SCALE_FLOOR = 0.52
CHASE_BEACON_CAPTURE_SLACK = 5.0

TACTICAL_CENTER_FOLLOW = 10.0
TACTICAL_SHIP_EDGE_MARGIN = 24.0
TACTICAL_ZOOM_BLEND = 3.2

# Fixed chase playfield top — HUD toasts must not shift the ship rig.
CHASE_PLAY_HUD_TOP = 54.0


class CameraMode(Enum):
    TACTICAL = auto()
    CHASE = auto()

    def next_mode(self) -> CameraMode:
        return CameraMode.CHASE if self is CameraMode.TACTICAL else CameraMode.TACTICAL

    @property
    def hud_label(self) -> str:
        return "TACTICAL" if self is CameraMode.TACTICAL else "CHASE CAM"


@dataclass(frozen=True, slots=True)
class ProjectedPoint:
    x: float
    y: float
    depth: float
    visible: bool


@dataclass(slots=True)
class ViewCamera:
    """Presentation-only camera — never mutates gameplay state."""

    mode: CameraMode = CameraMode.TACTICAL
    center: Vec2 = Vec2()
    viewport_width: int = CANVAS_WIDTH
    viewport_height: int = CANVAS_HEIGHT
    chase_back: float = CHASE_BACK
    chase_lift: float = CHASE_LIFT
    focal_length: float = CHASE_FOCAL
    min_depth: float = 22.0
    horizon_frac: float = CHASE_HORIZON_FRAC
    ship_anchor_frac: float = CHASE_SHIP_ANCHOR_FRAC
    mode_flash_ttl: float = 0.0
    bounds_alert_flash_ttl: float = 0.0
    play_hud_top: float = CHASE_PLAY_HUD_TOP
    chase_thrust_boost: float = 1.0
    tactical_scale: float = 1.0
    _smooth_center: Vec2 = Vec2()
    _last_ship_angle: float = 0.0
    turn_rate: float = 0.0
    _chase_heading_ready: bool = False
    velocity_lag_y: float = 0.0

    def cycle_mode(self) -> CameraMode:
        self.mode = self.mode.next_mode()
        self.mode_flash_ttl = 1.4
        self._chase_heading_ready = False
        self.velocity_lag_y = 0.0
        if self.mode is CameraMode.CHASE:
            self.set_play_layout(CHASE_PLAY_HUD_TOP)
        return self.mode

    def snap_tactical_to_ship(self, ship_pos: Vec2, config: WorldConfig) -> None:
        """Hard-align tactical pan/zoom to the ship — scene enter, respawn, mode switch."""
        if self.mode is not CameraMode.TACTICAL:
            return
        self.viewport_width = config.viewport_width
        self.viewport_height = config.viewport_height
        self.tactical_scale = tactical_scale_for(config)
        target = self._tactical_center_for(ship_pos, config)
        self._smooth_center = target
        self.center = target

    def flash_bounds_alert(self) -> None:
        self.bounds_alert_flash_ttl = 0.9

    def tick(self, dt: float) -> None:
        if self.mode_flash_ttl > 0.0:
            self.mode_flash_ttl = max(0.0, self.mode_flash_ttl - dt)
        if self.bounds_alert_flash_ttl > 0.0:
            self.bounds_alert_flash_ttl = max(0.0, self.bounds_alert_flash_ttl - dt)

    def set_play_layout(self, hud_top: float) -> None:
        if self.mode is CameraMode.CHASE:
            self.play_hud_top = CHASE_PLAY_HUD_TOP
            return
        self.play_hud_top = hud_top

    def chase_anchor(self) -> tuple[float, float]:
        """Fixed on-screen rig point — ship stays here; world rotates around forward."""
        play_h = max(1.0, self.viewport_height - self.play_hud_top)
        ax = self.viewport_width * 0.5
        ay = self.play_hud_top + play_h * self.ship_anchor_frac
        return ax, ay

    def chase_horizon_y(self) -> float:
        play_h = max(1.0, self.viewport_height - self.play_hud_top)
        return self.play_hud_top + play_h * self.horizon_frac

    def update_follow(self, ship_pos: Vec2, config: WorldConfig, dt: float) -> None:
        self.viewport_width = config.viewport_width
        self.viewport_height = config.viewport_height

        if self.mode is CameraMode.CHASE:
            # Chase projection is ship-locked; keep tactical pan/zoom frozen while in OG view.
            return

        step = max(dt, 1.0 / 120.0)
        target_scale = tactical_scale_for(config)
        zoom_blend = 1.0 - math.exp(-TACTICAL_ZOOM_BLEND * step)
        self.tactical_scale += (target_scale - self.tactical_scale) * zoom_blend

        target = self._tactical_center_for(ship_pos, config)
        if self._ship_leaves_playfield(ship_pos, self._smooth_center, config):
            self._smooth_center = target
        else:
            blend = 1.0 - math.exp(-TACTICAL_CENTER_FOLLOW * step)
            if self._smooth_center.length_sq() <= 1e-9 and self.center.length_sq() <= 1e-9:
                self._smooth_center = target
            else:
                self._smooth_center = Vec2(
                    self._smooth_center.x + (target.x - self._smooth_center.x) * blend,
                    self._smooth_center.y + (target.y - self._smooth_center.y) * blend,
                )
        self.center = self._smooth_center

    def _ship_leaves_playfield(self, ship_pos: Vec2, center: Vec2, config: WorldConfig) -> bool:
        scale = max(1e-6, self.tactical_scale)
        play_h = self._tactical_play_height(config)
        margin = TACTICAL_SHIP_EDGE_MARGIN
        sx = (ship_pos.x - center.x) * scale
        sy = (ship_pos.y - center.y) * scale
        return (
            sx < margin
            or sx > config.viewport_width - margin
            or sy < margin
            or sy > play_h - margin
        )

    def update_chase_heading(self, ship_angle: float, dt: float) -> None:
        """Track smoothed turn rate for chase banking / HUD (presentation only)."""
        if self.mode is not CameraMode.CHASE:
            self.turn_rate = 0.0
            self._last_ship_angle = ship_angle
            self._chase_heading_ready = False
            return
        if not self._chase_heading_ready:
            self._last_ship_angle = ship_angle
            self._chase_heading_ready = True
            return
        delta = _angle_delta(ship_angle - self._last_ship_angle)
        instant = delta / max(dt, 1.0 / 240.0)
        blend = 1.0 - math.exp(-18.0 * max(dt, 1.0 / 120.0))
        self.turn_rate = self.turn_rate + (instant - self.turn_rate) * blend
        self._last_ship_angle = ship_angle

    def update_chase_velocity(self, vel: Vec2, ship_angle: float, config: WorldConfig, dt: float) -> None:
        """Slide projected world on screen from forward speed — ship rig stays fixed."""
        if self.mode is not CameraMode.CHASE:
            self.velocity_lag_y = 0.0
            return
        forward = Vec2.from_angle(ship_angle)
        norm = max(-1.0, min(1.0, vel.dot(forward) / max(1.0, config.max_ship_speed)))
        target = norm * CHASE_VELOCITY_LAG_MAX
        blend = 1.0 - math.exp(-14.0 * max(dt, 1.0 / 120.0))
        self.velocity_lag_y = self.velocity_lag_y + (target - self.velocity_lag_y) * blend

    def _tactical_play_height(self, config: WorldConfig) -> float:
        return max(1.0, float(config.viewport_height) - self.play_hud_top)

    def _tactical_center_for(self, ship_pos: Vec2, config: WorldConfig) -> Vec2:
        """Ship-centered tactical follow — open sectors never clamp; closed maps clamp to world rect."""
        play_h = self._tactical_play_height(config)
        scale = self.tactical_scale
        vis_w = config.viewport_width / scale
        vis_h = play_h / scale
        cx = ship_pos.x - vis_w * 0.5
        cy = ship_pos.y - vis_h * 0.5
        if config.open_bounds:
            return Vec2(cx, cy)
        max_x = max(0.0, config.width - vis_w)
        max_y = max(0.0, config.height - vis_h)
        return Vec2(
            cx if max_x <= 0.0 else _clamp(cx, 0.0, max_x),
            cy if max_y <= 0.0 else _clamp(cy, 0.0, max_y),
        )

    def world_to_screen(self, world_pos: Vec2, ship_pos: Vec2, ship_angle: float) -> ProjectedPoint:
        if self.mode is CameraMode.TACTICAL:
            return ProjectedPoint(
                x=(world_pos.x - self.center.x) * self.tactical_scale,
                y=(world_pos.y - self.center.y) * self.tactical_scale,
                depth=0.0,
                visible=True,
            )
        return self._project_chase(world_pos, ship_pos, ship_angle)

    def world_to_chase_screen(
        self,
        world_pos: Vec2,
        ship_pos: Vec2,
        ship_angle: float,
        *,
        min_ahead: float | None = None,
        screen_margin: float | None = None,
    ) -> ProjectedPoint:
        """Chase projection with optional extended frustum (asteroids, distant gates)."""
        return self._project_chase(
            world_pos,
            ship_pos,
            ship_angle,
            min_ahead=min_ahead if min_ahead is not None else self.min_depth,
            screen_margin=screen_margin if screen_margin is not None else 96.0,
        )

    def _project_chase(
        self,
        world_pos: Vec2,
        ship_pos: Vec2,
        ship_angle: float,
        *,
        min_ahead: float | None = None,
        screen_margin: float | None = None,
    ) -> ProjectedPoint:
        """Racing chase: camera behind + above ship; forward stays toward top of screen."""
        forward = Vec2.from_angle(ship_angle)
        right = forward.rotated(math.pi / 2.0)
        cam_pos = ship_pos - forward * self.chase_back
        rel = world_pos - cam_pos
        ahead = rel.dot(forward)
        lateral = rel.dot(right)

        depth_floor = min_ahead if min_ahead is not None else self.min_depth
        if ahead < depth_floor:
            return ProjectedPoint(x=0.0, y=0.0, depth=ahead, visible=False)

        scale = self.focal_length / ahead
        lateral_scale = scale * self.chase_thrust_boost
        anchor_x, anchor_y = self.chase_anchor()
        pitch = 0.48 + self.chase_lift / self.focal_length
        screen_x = anchor_x + lateral * lateral_scale
        screen_y = anchor_y + self.velocity_lag_y - (ahead - self.chase_back) * scale * pitch

        margin = screen_margin if screen_margin is not None else 96.0
        visible = (
            -margin <= screen_x <= self.viewport_width + margin
            and self.chase_horizon_y() - margin <= screen_y <= self.viewport_height + margin
        )
        return ProjectedPoint(x=screen_x, y=screen_y, depth=ahead, visible=visible)

    def chase_threat_screen(
        self,
        world_pos: Vec2,
        ship_pos: Vec2,
        ship_angle: float,
        threat_range: float,
    ) -> ProjectedPoint:
        """Extended chase frustum for in-range combat threats off-screen."""
        return self.world_to_chase_screen(
            world_pos,
            ship_pos,
            ship_angle,
            min_ahead=-threat_range * 0.5,
            screen_margin=threat_range * 0.45,
        )

    def perspective_scale(self, depth: float) -> float:
        safe = max(depth, self.min_depth)
        return self.focal_length / safe


def tactical_scale_for(config: WorldConfig) -> float:
    _ = config
    return 1.0


def chase_horizontal_fov_deg(*, viewport_width: float, focal_length: float) -> float:
    """Horizontal FOV implied by chase lateral projection at a reference depth plane."""
    half = math.atan((viewport_width * 0.5) / max(1.0, focal_length))
    return math.degrees(half * 2.0)


def chase_focal_for_hfov(viewport_width: float, hfov_deg: float) -> float:
    half = math.radians(hfov_deg) * 0.5
    return (viewport_width * 0.5) / math.tan(half)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _angle_delta(radians: float) -> float:
    """Shortest signed delta in (-pi, pi]."""
    while radians > math.pi:
        radians -= math.tau
    while radians <= -math.pi:
        radians += math.tau
    return radians
