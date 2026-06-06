from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.edge_hints import draw_edge_hints
from gravity_ho_matey.render.entity_viz import draw_beacon_marker, draw_gate_portal, draw_tactical_wall
from gravity_ho_matey.render.explosion_fx import draw_explosions
from gravity_ho_matey.render.world_draw import (
    WELL_RING_VISUAL_SCALE,
    draw_gravity_floor_grid,
    draw_gravity_heatmap,
    draw_ship,
    draw_well,
)


class TacticalViewRenderer:
    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        camera: ViewCamera,
        field: GravityField,
        *,
        hud_top: int,
    ) -> None:
        vw = camera.viewport_width
        vh = camera.viewport_height
        solar = world.config.level_theme == "solar"
        ship_pos = world.ship.pos
        bg = palette.SOLAR_BG if solar else palette.BACKGROUND
        canvas.create_rectangle(0, hud_top, vw, vh, fill=bg, outline="")
        if solar:
            self._starfield(canvas, vw, vh, hud_top, dense=True)
        else:
            self._grid(canvas, vw, vh, hud_top, camera)
        draw_gravity_heatmap(canvas, field, camera, y_offset=hud_top, alpha_step=1, world=world)
        draw_gravity_floor_grid(
            canvas, field, camera, ship_pos, world.ship.angle, y_offset=hud_top, step=1, world=world,
        )
        for wall in world.walls:
            draw_tactical_wall(
                canvas,
                wall,
                camera,
                hud_top=hud_top,
                solar=solar,
                world_width=world.config.width,
                world_height=world.config.height,
            )
        for well in world.wells:
            p = camera.world_to_screen(well.pos, ship_pos, world.ship.angle)
            draw_well(
                canvas,
                Vec2(p.x, p.y + hud_top),
                well.radius,
                well.label,
                well.kind,
                scale=camera.tactical_scale * WELL_RING_VISUAL_SCALE,
            )
        gate = world.finish_gate.rect
        gate_center = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        gp = camera.world_to_screen(gate_center, ship_pos, world.ship.angle)
        draw_gate_portal(
            canvas,
            Vec2(gp.x, gp.y),
            size=max(gate.w, gate.h),
            unlocked=world.finish_unlocked,
            solar=solar,
            hud_top=hud_top,
        )
        for beacon in world.beacons:
            p = camera.world_to_screen(beacon.pos, ship_pos, world.ship.angle)
            draw_beacon_marker(canvas, Vec2(p.x, p.y), beacon, hud_top=hud_top)
        for pickup in world.pickups:
            self._pickup(canvas, pickup.pos, pickup.kind, camera, ship_pos, hud_top)
        for enemy in world.enemies:
            if enemy.alive:
                self._enemy(canvas, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, hud_top)
        for projectile in world.projectiles:
            self._projectile(canvas, projectile.pos, projectile.vel, camera, ship_pos, hud_top)
        ship_screen = camera.world_to_screen(world.ship.pos, ship_pos, world.ship.angle)
        draw_ship(
            canvas,
            Vec2(ship_screen.x, ship_screen.y + hud_top),
            world.ship.angle,
            world.ship.boost_energy,
            invuln=world.invuln_remaining,
            elapsed=world.elapsed,
            scale=1.08 * camera.tactical_scale / 1.1,
        )
        draw_edge_hints(canvas, world, camera, hud_top=hud_top)
        draw_explosions(
            canvas,
            world.explosions.active,
            project=lambda p: camera.world_to_screen(p, ship_pos, world.ship.angle),
            offset=(0.0, float(hud_top)),
        )

    def _pickup(self, canvas: tk.Canvas, pos: Vec2, kind: PowerUpKind, camera: ViewCamera, ship_pos: Vec2, hud_top: int) -> None:
        p = camera.world_to_screen(pos, ship_pos, 0.0)
        color = {
            PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
            PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
            PowerUpKind.STABILIZER: palette.PICKUP_STABILIZER,
        }.get(kind, palette.BEACON)
        x, y = p.x, p.y + hud_top
        canvas.create_polygon(x, y - 12, x + 10, y, x, y + 12, x - 10, y, fill=color, outline="#fff")

    def _enemy(self, canvas: tk.Canvas, pos: Vec2, radius: float, facing: float, camera: ViewCamera, ship_pos: Vec2, hud_top: int) -> None:
        p = camera.world_to_screen(pos, ship_pos, 0.0)
        x, y = p.x, p.y + hud_top
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=2)
        spike = Vec2(x, y) + Vec2.from_angle(facing) * (radius + 5)
        canvas.create_line(x, y, spike.x, spike.y, fill=palette.ENEMY_EDGE, width=2)

    def _projectile(self, canvas: tk.Canvas, pos: Vec2, vel: Vec2, camera: ViewCamera, ship_pos: Vec2, hud_top: int) -> None:
        p = camera.world_to_screen(pos, ship_pos, 0.0)
        x, y = p.x, p.y + hud_top
        canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=palette.PROJECTILE, outline="")
        if vel.length_sq() > 1.0:
            tail = Vec2(x, y) - vel.normalized() * 14
            canvas.create_line(tail.x, tail.y, x, y, fill=palette.PROJECTILE)

    def _grid(self, canvas: tk.Canvas, width: int, height: int, y_offset: int, camera: ViewCamera) -> None:
        step = int(48 / max(1.0, camera.tactical_scale * 0.85))
        step = max(32, step)
        for x in range(0, width + step, step):
            canvas.create_line(x, y_offset, x, height, fill=palette.SEA_GRID)
        for y in range(y_offset, height + step, step):
            canvas.create_line(0, y, width, y, fill=palette.SEA_GRID)

    def _starfield(self, canvas: tk.Canvas, width: int, height: int, y_offset: int, dense: bool) -> None:
        count = 140 if dense else 80
        for i in range(count):
            x = (i * 83 + 17) % width
            y = y_offset + (i * 47 + 31) % max(1, height - y_offset)
            size = 3 if dense and i % 5 == 0 else 2
            tone = "#3a5570" if dense and i % 7 == 0 else "#294764"
            canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")


class PerspectiveViewRenderer:
    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        camera: ViewCamera,
        field: GravityField,
        *,
        hud_top: int,
    ) -> None:
        from gravity_ho_matey.render.camera import CHASE_SHIP_SCALE
        from gravity_ho_matey.render.chase_entities import (
            draw_chase_beacon,
            draw_chase_enemy,
            draw_chase_gate,
            draw_chase_pickup,
            draw_chase_projectile,
        )
        from gravity_ho_matey.render.chase_fx import (
            draw_chase_floor_gradient,
            draw_chase_sky,
            draw_engine_bloom,
            draw_speed_vignette,
        )
        from gravity_ho_matey.render.chase_ground import draw_chase_gravity_heatmap
        from gravity_ho_matey.render.chase_walls import collect_wall_rails, draw_wall_rails
        from gravity_ho_matey.render.chase_helm import bank_angle_for_chase, draw_xwing_cockpit_hud
        from gravity_ho_matey.render.chase_threat import wall_rail_urgency
        from gravity_ho_matey.render.chase_wells import draw_chase_well

        vw = camera.viewport_width
        vh = camera.viewport_height
        camera.set_play_layout(hud_top)
        solar = world.config.level_theme == "solar"
        ship_pos = world.ship.pos
        ship_angle = world.ship.angle
        elapsed = world.elapsed
        thrusting = world.ship.boost_energy < 0.98 and world.ship.vel.length() > 20.0
        camera.chase_thrust_boost = 1.1 if thrusting else 1.0

        canvas.create_rectangle(0, 0, vw, vh, fill=palette.BACKGROUND, outline="")

        draw_chase_sky(canvas, camera, world)

        draw_chase_floor_gradient(canvas, camera)
        draw_chase_gravity_heatmap(canvas, field, camera, world, ship_pos, ship_angle, step=2)

        wall_rails = collect_wall_rails(
            world.walls,
            camera,
            ship_pos,
            ship_angle,
            world.config.width,
            world.config.height,
        )
        draw_wall_rails(canvas, wall_rails, solar=solar, urgency=wall_rail_urgency(world))

        sprites: list[tuple[float, str, object]] = []
        for well in world.wells:
            p = camera.world_to_screen(well.pos, ship_pos, ship_angle)
            if p.visible:
                scale = max(0.25, camera.perspective_scale(p.depth) / camera.focal_length)
                sprites.append((p.depth, "well", (Vec2(p.x, p.y), well, scale, p.depth)))
        gate = world.finish_gate.rect
        gate_center = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        gp = camera.world_to_screen(gate_center, ship_pos, ship_angle)
        if gp.visible:
            sprites.append((gp.depth, "gate", (Vec2(gp.x, gp.y), world.finish_unlocked)))
        for beacon in world.beacons:
            p = camera.world_to_screen(beacon.pos, ship_pos, ship_angle)
            if p.visible:
                sprites.append((p.depth, "beacon", (Vec2(p.x, p.y), beacon)))
        for pickup in world.pickups:
            p = camera.world_to_screen(pickup.pos, ship_pos, ship_angle)
            if p.visible:
                sprites.append((p.depth, "pickup", (Vec2(p.x, p.y), pickup.kind)))
        for enemy in world.enemies:
            if enemy.alive:
                p = camera.world_to_screen(enemy.pos, ship_pos, ship_angle)
                if p.visible:
                    scale = max(0.35, camera.perspective_scale(p.depth) / camera.focal_length)
                    sprites.append((p.depth, "enemy", (Vec2(p.x, p.y), enemy, scale)))
        for projectile in world.projectiles:
            p = camera.world_to_screen(projectile.pos, ship_pos, ship_angle)
            if p.visible:
                sprites.append((p.depth, "projectile", (Vec2(p.x, p.y), projectile)))
        sprites.sort(key=lambda item: item[0])
        for _, kind, payload in sprites:
            if kind == "well":
                pos, well, scale, depth = payload
                draw_chase_well(
                    canvas,
                    pos,
                    well,
                    scale=scale,
                    elapsed=elapsed,
                    depth=depth,
                    camera=camera,
                    ship_pos=ship_pos,
                    ship_angle=ship_angle,
                    default_maw=world.config.well_maw_radius,
                )
            elif kind == "gate":
                pos, unlocked = payload
                draw_chase_gate(canvas, pos, unlocked=unlocked, solar=solar)
            elif kind == "beacon":
                pos, beacon = payload
                draw_chase_beacon(canvas, pos, beacon, elapsed=elapsed)
            elif kind == "pickup":
                pos, kind_enum = payload
                draw_chase_pickup(canvas, pos, kind_enum)
            elif kind == "enemy":
                pos, enemy, scale = payload
                draw_chase_enemy(canvas, pos, radius=enemy.radius, facing=enemy.facing_angle, scale=scale)
            elif kind == "projectile":
                pos, projectile = payload
                draw_chase_projectile(canvas, pos, projectile.vel)

        anchor_x, anchor_y = camera.chase_anchor()
        draw_speed_vignette(canvas, camera, world.ship.vel.length())
        draw_engine_bloom(canvas, anchor_x, anchor_y, boost_energy=world.ship.boost_energy, thrusting=thrusting)
        display_angle = bank_angle_for_chase(world.ship.vel, ship_angle, turn_rate=camera.turn_rate)
        draw_ship(
            canvas,
            Vec2(anchor_x, anchor_y),
            display_angle,
            world.ship.boost_energy,
            invuln=world.invuln_remaining,
            elapsed=elapsed,
            scale=CHASE_SHIP_SCALE,
        )
        draw_xwing_cockpit_hud(
            canvas,
            world,
            camera,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            hud_top=hud_top,
        )
        draw_edge_hints(canvas, world, camera, hud_top=hud_top)
        draw_explosions(canvas, world.explosions.active, project=lambda p: camera.world_to_screen(p, ship_pos, ship_angle))
