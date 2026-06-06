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
CHASE_FOCAL = 440.0
CHASE_HORIZON_FRAC = 0.26
CHASE_SHIP_ANCHOR_FRAC = 0.76
CHASE_SHIP_SCALE = 1.12
CHASE_SCREEN_HEADING = -math.pi / 2.0

# Forward/back world slide under fixed ship rig (pixels at max speed).
CHASE_VELOCITY_LAG_MAX = 21.0

# Compact arenas (Cove): zoom in so ship + local hazards read larger on screen.
TACTICAL_ZOOM_COMPACT = 1.32


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
    play_hud_top: float = 0.0
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
        return self.mode

    def tick(self, dt: float) -> None:
        if self.mode_flash_ttl > 0.0:
            self.mode_flash_ttl = max(0.0, self.mode_flash_ttl - dt)

    def set_play_layout(self, hud_top: float) -> None:
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
        self.tactical_scale = tactical_scale_for(config)
        target = self._tactical_center_for(ship_pos, config)
        blend = 1.0 - math.exp(-14.0 * max(dt, 1.0 / 120.0))
        if self._smooth_center.length_sq() <= 1e-9 and self.center.length_sq() <= 1e-9:
            self._smooth_center = target
        else:
            self._smooth_center = Vec2(
                self._smooth_center.x + (target.x - self._smooth_center.x) * blend,
                self._smooth_center.y + (target.y - self._smooth_center.y) * blend,
            )
        self.center = self._smooth_center

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

    def _tactical_center_for(self, ship_pos: Vec2, config: WorldConfig) -> Vec2:
        vw = config.viewport_width
        vh = config.viewport_height
        ww = config.width
        wh = config.height
        scale = self.tactical_scale
        vis_w = vw / scale
        vis_h = vh / scale
        if ww <= vis_w and wh <= vis_h:
            return Vec2()
        max_x = max(0.0, ww - vis_w)
        max_y = max(0.0, wh - vis_h)
        cx = _clamp(ship_pos.x - vis_w * 0.5, 0.0, max_x)
        cy = _clamp(ship_pos.y - vis_h * 0.5, 0.0, max_y)
        return Vec2(cx, cy)

    def world_to_screen(self, world_pos: Vec2, ship_pos: Vec2, ship_angle: float) -> ProjectedPoint:
        if self.mode is CameraMode.TACTICAL:
            return ProjectedPoint(
                x=(world_pos.x - self.center.x) * self.tactical_scale,
                y=(world_pos.y - self.center.y) * self.tactical_scale,
                depth=0.0,
                visible=True,
            )
        return self._project_chase(world_pos, ship_pos, ship_angle)

    def _project_chase(self, world_pos: Vec2, ship_pos: Vec2, ship_angle: float) -> ProjectedPoint:
        """Racing chase: camera behind + above ship; forward stays toward top of screen."""
        forward = Vec2.from_angle(ship_angle)
        right = forward.rotated(math.pi / 2.0)
        cam_pos = ship_pos - forward * self.chase_back
        rel = world_pos - cam_pos
        ahead = rel.dot(forward)
        lateral = rel.dot(right)

        if ahead < self.min_depth:
            return ProjectedPoint(x=0.0, y=0.0, depth=ahead, visible=False)

        scale = self.focal_length / ahead
        lateral_scale = scale * self.chase_thrust_boost
        anchor_x, anchor_y = self.chase_anchor()
        pitch = 0.48 + self.chase_lift / self.focal_length
        screen_x = anchor_x + lateral * lateral_scale
        screen_y = anchor_y + self.velocity_lag_y - (ahead - self.chase_back) * scale * pitch

        margin = 96.0
        visible = (
            -margin <= screen_x <= self.viewport_width + margin
            and self.chase_horizon_y() - margin <= screen_y <= self.viewport_height + margin
        )
        return ProjectedPoint(x=screen_x, y=screen_y, depth=ahead, visible=visible)

    def perspective_scale(self, depth: float) -> float:
        safe = max(depth, self.min_depth)
        return self.focal_length / safe


def tactical_scale_for(config: WorldConfig) -> float:
    if config.width <= config.viewport_width and config.height <= config.viewport_height:
        return TACTICAL_ZOOM_COMPACT
    return 1.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _angle_delta(radians: float) -> float:
    """Shortest signed delta in (-pi, pi]."""
    while radians > math.pi:
        radians -= math.tau
    while radians <= -math.pi:
        radians += math.tau
    return radians
