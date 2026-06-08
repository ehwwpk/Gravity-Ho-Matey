from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.light_compose import LightLayerBuilder
from gravity_ho_matey.render.edge_hints import draw_edge_hints
from gravity_ho_matey.render.asteroid_viz import (
    ORBITAL_ASTEROID_THREAT_RADIUS,
    asteroid_in_play_view,
    draw_tactical_asteroid,
)
from gravity_ho_matey.render.entity_viz import draw_beacon_marker, draw_gate_portal
from gravity_ho_matey.render.explosion_fx import draw_explosions
from gravity_ho_matey.render.health_bar_viz import draw_health_bar, hp_fraction
from gravity_ho_matey.render.world_draw import (
    WELL_RING_VISUAL_SCALE,
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
        powerup_stacks: PowerUpStacks | None = None,
    ) -> None:
        vw = camera.viewport_width
        vh = camera.viewport_height
        solar = world.config.level_theme == "solar"
        rift = world.config.level_theme == "rift"
        siege = world.config.level_theme == "siege"
        brood = world.config.level_theme == "brood_moon"
        ship_pos = world.ship.pos
        rig = LightRig.for_play(theme=world.config.level_theme, camera_mode=camera.mode)
        bg = (
            palette.SOLAR_BG
            if solar
            else palette.RIFT_BG
            if rift
            else palette.SIEGE_BG
            if siege
            else palette.BROOD_MOON_BG
            if brood
            else palette.BACKGROUND
        )
        canvas.create_rectangle(0, hud_top, vw, vh, fill=bg, outline="")
        from gravity_ho_matey.render.starfield_viz import draw_tactical_starfield

        draw_tactical_starfield(
            canvas,
            width=vw,
            height=vh,
            y_offset=hud_top,
            theme=world.config.level_theme,
            elapsed=world.elapsed,
            dense=True,
        )
        brood_surface = brood and world.brood_moon is not None and world.brood_moon.on_surface
        if not brood_surface:
            draw_gravity_heatmap(
                canvas,
                field,
                camera,
                y_offset=hud_top,
                alpha_step=4,
                ship_pos=ship_pos,
                world=world,
            )
        if brood_surface:
            from gravity_ho_matey.render.brood_moon_surface_viz import draw_brood_tactical_surface_band
            from gravity_ho_matey.render.brood_geology_viz import draw_brood_geology_tactical
            from gravity_ho_matey.render.brood_flora_viz import draw_brood_flora_tactical
            from gravity_ho_matey.render.brood_fauna_viz import draw_brood_fauna_tactical
            from gravity_ho_matey.render.brood_ambient_viz import draw_brood_ambient_tactical

            draw_brood_tactical_surface_band(
                canvas,
                camera,
                world,
                hud_top=float(hud_top),
                ship_pos=ship_pos,
                ship_angle=world.ship.angle,
                rig=rig,
            )
            draw_brood_geology_tactical(
                canvas, camera, world, hud_top=float(hud_top),
                ship_pos=ship_pos, ship_angle=world.ship.angle, rig=rig,
            )
            draw_brood_flora_tactical(
                canvas, camera, world, hud_top=float(hud_top),
                ship_pos=ship_pos, ship_angle=world.ship.angle, rig=rig,
            )
            draw_brood_fauna_tactical(
                canvas, camera, world, hud_top=float(hud_top),
                ship_pos=ship_pos, ship_angle=world.ship.angle, rig=rig,
            )
            draw_brood_ambient_tactical(
                canvas, camera, world, hud_top=float(hud_top),
                ship_pos=ship_pos, ship_angle=world.ship.angle, rig=rig,
            )
        brood_orbital = (
            brood
            and world.brood_moon is not None
            and not world.brood_moon.on_surface
        )
        threat_radius = ORBITAL_ASTEROID_THREAT_RADIUS if brood_orbital else 0.0
        scree_material = "brood_regolith" if brood else "asteroid"
        if brood_orbital:
            for well in world.wells:
                p = camera.world_to_screen(well.pos, ship_pos, world.ship.angle)
                draw_well(
                    canvas,
                    Vec2(p.x, p.y + hud_top),
                    well.radius,
                    well.label,
                    well.kind,
                    scale=camera.tactical_scale * WELL_RING_VISUAL_SCALE,
                    rig=rig,
                    elapsed=world.elapsed,
                )
        for asteroid in world.asteroids:
            if not asteroid_in_play_view(
                asteroid,
                ship_pos,
                viewport_width=float(vw),
                viewport_height=float(vh - hud_top),
                threat_radius=threat_radius,
            ):
                continue
            draw_tactical_asteroid(
                canvas,
                asteroid,
                camera,
                hud_top=hud_top,
                rig=rig,
                ship_pos=ship_pos,
                ship_angle=world.ship.angle,
                material_kind=scree_material,
            )
        if not brood_orbital:
            for well in world.wells:
                p = camera.world_to_screen(well.pos, ship_pos, world.ship.angle)
                draw_well(
                    canvas,
                    Vec2(p.x, p.y + hud_top),
                    well.radius,
                    well.label,
                    well.kind,
                    scale=camera.tactical_scale * WELL_RING_VISUAL_SCALE,
                    rig=rig,
                    elapsed=world.elapsed,
                )
        gate = world.finish_gate.rect
        gate_center = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        gp = camera.world_to_screen(gate_center, ship_pos, world.ship.angle)
        if rift:
            from gravity_ho_matey.render.rift_pad_viz import draw_rift_extract_pad

            draw_rift_extract_pad(
                canvas,
                gp.x,
                gp.y + hud_top,
                unlocked=world.finish_unlocked,
                elapsed=world.elapsed,
            )
        else:
            draw_gate_portal(
                canvas,
                Vec2(gp.x, gp.y),
                size=max(gate.w, gate.h),
                unlocked=world.finish_unlocked,
                solar=solar,
                hud_top=hud_top,
                elapsed=world.elapsed,
            )
        for beacon in world.beacons:
            p = camera.world_to_screen(beacon.pos, ship_pos, world.ship.angle)
            draw_beacon_marker(
                canvas,
                Vec2(p.x, p.y),
                beacon,
                hud_top=hud_top,
                rig=rig,
                elapsed=world.elapsed,
            )
        for jewel in world.jewels:
            self._jewel(canvas, jewel.pos, camera, ship_pos, hud_top, elapsed=world.elapsed)
        for station in world.friendly_stations:
            if station.alive:
                from gravity_ho_matey.render.station_viz import draw_space_station_tactical

                draw_space_station_tactical(
                    canvas,
                    station,
                    camera,
                    ship_pos=ship_pos,
                    ship_angle=world.ship.angle,
                    hud_top=hud_top,
                    rig=rig,
                    elapsed=world.elapsed,
                )
        if world.space_station is not None and world.space_station.alive:
            from gravity_ho_matey.render.station_viz import draw_space_station_tactical

            draw_space_station_tactical(
                canvas,
                world.space_station,
                camera,
                ship_pos=ship_pos,
                ship_angle=world.ship.angle,
                hud_top=hud_top,
                rig=rig,
                elapsed=world.elapsed,
                tractor=world.tractor_beam,
            )
        for enemy in world.enemies:
            if enemy.alive:
                self._draw_tactical_enemy(
                    canvas,
                    enemy,
                    camera,
                    ship_pos,
                    world.ship.radius,
                    hud_top,
                    elapsed=world.elapsed,
                    rig=rig,
                )
        if rift and world.mega_squid is not None and world.mega_squid.alive:
            from gravity_ho_matey.render.squid_boss_viz import draw_mega_squid_tactical, draw_squid_pods_tactical

            draw_mega_squid_tactical(
                canvas,
                world.mega_squid,
                camera,
                ship_pos=ship_pos,
                ship_angle=world.ship.angle,
                ship_radius=world.ship.radius,
                hud_top=float(hud_top),
                rig=rig,
                elapsed=world.elapsed,
                scrape_flash=world.boss_scrape_flash,
            )
            draw_squid_pods_tactical(
                canvas,
                world.squid_pods,
                camera,
                ship_pos=ship_pos,
                ship_angle=world.ship.angle,
                hud_top=float(hud_top),
                elapsed=world.elapsed,
            )
        if brood and world.mega_squid is not None and world.mega_squid.alive:
            from gravity_ho_matey.render.squid_boss_viz import draw_mega_squid_tactical

            draw_mega_squid_tactical(
                canvas,
                world.mega_squid,
                camera,
                ship_pos=ship_pos,
                ship_angle=world.ship.angle,
                ship_radius=world.ship.radius,
                hud_top=float(hud_top),
                rig=rig,
                elapsed=world.elapsed,
                scrape_flash=world.boss_scrape_flash,
            )
        if brood and world.egg_pods:
            from gravity_ho_matey.render.egg_pod_viz import draw_egg_pods_tactical

            def _pod_screen(pos):
                p = camera.world_to_screen(pos, ship_pos, world.ship.angle)
                return p.x, p.y + hud_top

            draw_egg_pods_tactical(
                canvas,
                world.egg_pods,
                to_screen=_pod_screen,
                rig=rig,
                elapsed=world.elapsed,
            )
        if brood and world.brood_moon is not None and world.brood_moon.layout is not None:
            from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase

            bm = world.brood_moon
            if bm.phase is BroodPhase.ORBITAL:
                from gravity_ho_matey.render.planet_mission_viz import draw_planet_landing_band_tactical

                draw_planet_landing_band_tactical(
                    canvas,
                    bm.layout.planet,
                    camera=camera,
                    ship_pos=ship_pos,
                    ship_angle=world.ship.angle,
                    hud_top=float(hud_top),
                    accent=palette.BROOD_MOON_HUD_ACCENT,
                    dim=palette.HUD_DIM,
                    elapsed=world.elapsed,
                )
        for projectile in world.projectiles:
            self._projectile(canvas, projectile, camera, ship_pos, hud_top, elapsed=world.elapsed)
        from gravity_ho_matey.render.ship_viz import draw_friendly_fighter_ship

        ally_scale = 0.78 * camera.tactical_scale / 1.1
        for ally in world.allies:
            if not ally.alive:
                continue
            ap = camera.world_to_screen(ally.pos, ship_pos, world.ship.angle)
            draw_friendly_fighter_ship(
                canvas,
                Vec2(ap.x, ap.y + hud_top),
                ally.facing_angle,
                scale=ally_scale,
                rig=rig,
            )
            ally_hp = hp_fraction(ally)
            if ally_hp is not None:
                bar_y = ap.y + hud_top - 18.0 * ally_scale
                draw_health_bar(
                    canvas,
                    ap.x,
                    bar_y,
                    14.0 * ally_scale,
                    ally_hp,
                    outline="#68e0c0",
                    fill="#40d0a8",
                    low_fill=palette.HUD_WARN,
                )
        if world.drone_wingman is not None and world.drone_wingman.alive:
            from gravity_ho_matey.render.drone_viz import draw_drone_wingman_tactical

            drone = world.drone_wingman
            dp = camera.world_to_screen(drone.pos, ship_pos, world.ship.angle)
            draw_drone_wingman_tactical(
                canvas,
                Vec2(dp.x, dp.y + hud_top),
                drone.facing_angle,
                scale=ally_scale * 0.92,
                drone=drone,
                rig=rig,
            )
            drone_hp = hp_fraction(drone)
            if drone_hp is not None:
                bar_y = dp.y + hud_top - 18.0 * ally_scale
                draw_health_bar(
                    canvas,
                    dp.x,
                    bar_y,
                    14.0 * ally_scale,
                    drone_hp,
                    outline=palette.DRONE_TRIM,
                    fill=palette.DRONE_CORE,
                    low_fill=palette.HUD_WARN,
                )
        ship_screen = camera.world_to_screen(world.ship.pos, ship_pos, world.ship.angle)
        from gravity_ho_matey.gameplay.planetside_flight import is_planetside, ship_draw_jolt_angle

        draw_angle = world.ship.angle + ship_draw_jolt_angle(world.ship.boost_jolt, world.elapsed)
        planetside = is_planetside(world.config)
        draw_ship(
            canvas,
            Vec2(ship_screen.x, ship_screen.y + hud_top),
            draw_angle,
            world.ship.boost_energy,
            boost_burst=world.ship.boost_flash,
            planetside_boost=planetside and world.ship.boost_flash > 0.0,
            invuln=world.invuln_remaining,
            elapsed=world.elapsed,
            scale=1.08 * camera.tactical_scale / 1.1,
            rig=rig,
            powerup_stacks=powerup_stacks,
        )
        from gravity_ho_matey.render.chase_helm import draw_tactical_flight_instruments

        draw_tactical_flight_instruments(
            canvas,
            world,
            viewport_width=vw,
            viewport_height=vh,
            ship_angle=world.ship.angle,
        )
        draw_edge_hints(canvas, world, camera, hud_top=hud_top)
        draw_explosions(
            canvas,
            world.explosions.active,
            project=lambda p: camera.world_to_screen(p, ship_pos, world.ship.angle),
            offset=(0.0, float(hud_top)),
        )

    def _jewel(
        self,
        canvas: tk.Canvas,
        pos: Vec2,
        camera: ViewCamera,
        ship_pos: Vec2,
        hud_top: int,
        *,
        elapsed: float = 0.0,
    ) -> None:
        from gravity_ho_matey.render.jewel_viz import draw_jewel_world

        p = camera.world_to_screen(pos, ship_pos, 0.0)
        draw_jewel_world(canvas, Vec2(p.x, p.y), hud_top=hud_top, elapsed=elapsed)

    def _draw_tactical_enemy(
        self, canvas, enemy, camera, ship_pos, ship_radius, hud_top, *, elapsed: float = 0.0, rig: LightRig | None = None
    ) -> None:
        p = camera.world_to_screen(enemy.pos, ship_pos, 0.0)
        x, y = p.x, p.y + hud_top
        if enemy.kind is EnemyKind.SQUID:
            assert isinstance(enemy, SquidEnemy)
            from gravity_ho_matey.render.squid_viz import draw_squid_enemy_tactical

            if rig is not None:
                draw_squid_enemy_tactical(
                    canvas,
                    enemy,
                    camera=camera,
                    ship_pos=ship_pos,
                    ship_radius=ship_radius,
                    hud_top=hud_top,
                    rig=rig,
                    elapsed=elapsed,
                )
            return
        from gravity_ho_matey.gameplay.enemies import PatrolEnemy
        from gravity_ho_matey.render.enemy_viz import draw_patrol_enemy_tactical

        if isinstance(enemy, PatrolEnemy) and rig is not None:
            draw_patrol_enemy_tactical(
                canvas,
                enemy,
                camera=camera,
                ship_pos=ship_pos,
                hud_top=hud_top,
                rig=rig,
                elapsed=elapsed,
            )
            return
        self._enemy(canvas, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, hud_top)

    def _enemy(self, canvas: tk.Canvas, pos: Vec2, radius: float, facing: float, camera: ViewCamera, ship_pos: Vec2, hud_top: int) -> None:
        p = camera.world_to_screen(pos, ship_pos, 0.0)
        x, y = p.x, p.y + hud_top
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=2)
        spike = Vec2(x, y) + Vec2.from_angle(facing) * (radius + 5)
        canvas.create_line(x, y, spike.x, spike.y, fill=palette.ENEMY_EDGE, width=2)

    def _projectile(
        self,
        canvas: tk.Canvas,
        projectile,
        camera: ViewCamera,
        ship_pos: Vec2,
        hud_top: int,
        *,
        elapsed: float = 0.0,
    ) -> None:
        from gravity_ho_matey.render.weapon_projectile_fx import draw_tactical_projectile

        draw_tactical_projectile(
            canvas,
            projectile,
            camera=camera,
            ship_pos=ship_pos,
            hud_top=hud_top,
            elapsed=elapsed,
        )

    def _ambient_depth(self, canvas: tk.Canvas, width: int, height: int, y_offset: int) -> None:
        """Soft star specks — no line grid (reads cleaner than a dev overlay)."""
        specks = (
            (72, 118, "#0e1a2e"),
            (188, 96, "#0c1828"),
            (412, 142, "#101f34"),
            (638, 88, "#0d1b2f"),
            (824, 156, "#0f1d31"),
            (156, 298, "#111e33"),
            (502, 244, "#0e1a2c"),
            (748, 312, "#101f35"),
            (318, 402, "#0d192b"),
            (892, 428, "#0f1e32"),
            (44, 512, "#101d30"),
            (566, 548, "#0e1b2d"),
        )
        for x, y, color in specks:
            if y_offset <= y < height:
                canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill=color, outline="")


class PerspectiveViewRenderer:
    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        camera: ViewCamera,
        field: GravityField,
        *,
        hud_top: int,
        powerup_stacks: PowerUpStacks | None = None,
    ) -> None:
        from gravity_ho_matey.render.camera import (
            CHASE_BEACON_SCALE_FLOOR,
            CHASE_BEACON_VISUAL_BOOST,
            CHASE_SHIP_SCALE,
        )
        from gravity_ho_matey.render.chase_entities import (
            draw_chase_beacon,
            draw_chase_enemy,
            draw_chase_gate,
            draw_chase_jewel,
            draw_chase_squid,
        )
        from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
        from gravity_ho_matey.render.chase_projectile_fx import draw_chase_projectile
        from gravity_ho_matey.render.chase_fx import (
            draw_boost_pressure,
            draw_chase_boost_jolt,
            draw_chase_floor_gradient,
            draw_chase_sky,
            draw_engine_bloom,
            draw_speed_streaks,
            draw_speed_vignette,
        )
        from gravity_ho_matey.render.chase_ground import draw_chase_gravity_heatmap
        from gravity_ho_matey.render.asteroid_viz import collect_chase_asteroid_sprites, draw_chase_asteroids
        from gravity_ho_matey.render.chase_helm import draw_xwing_cockpit_hud
        from gravity_ho_matey.render.camera import CHASE_SCREEN_HEADING
        from gravity_ho_matey.render.chase_wells import draw_chase_well

        vw = camera.viewport_width
        vh = camera.viewport_height
        camera.set_play_layout(hud_top)
        solar = world.config.level_theme == "solar"
        rift = world.config.level_theme == "rift"
        brood = world.config.level_theme == "brood_moon"
        ship_pos = world.ship.pos
        ship_angle = world.ship.angle
        elapsed = world.elapsed
        rig = LightRig.for_play(theme=world.config.level_theme, camera_mode=camera.mode)
        thrusting = world.ship.boost_flash > 0.0
        chase_intensity = camera.chase_intensity()

        bg = (
            palette.RIFT_BG
            if rift
            else palette.SIEGE_BG
            if world.config.level_theme == "siege"
            else palette.BROOD_MOON_BG
            if brood
            else palette.BACKGROUND
        )
        canvas.create_rectangle(0, 0, vw, vh, fill=bg, outline="")

        draw_chase_sky(canvas, camera, world)

        brood_on_surface = brood and world.brood_moon is not None and world.brood_moon.on_surface
        brood_orbital_chase = (
            brood
            and world.brood_moon is not None
            and not world.brood_moon.on_surface
        )
        if not brood_on_surface and not brood_orbital_chase:
            draw_chase_floor_gradient(canvas, camera)
        if rift:
            from gravity_ho_matey.render.chase_fx import draw_rift_chase_floor_wash

            draw_rift_chase_floor_wash(canvas, camera)
        elif world.config.level_theme == "siege":
            from gravity_ho_matey.render.chase_fx import draw_siege_chase_floor_wash

            draw_siege_chase_floor_wash(canvas, camera)
        elif brood_on_surface:
            from gravity_ho_matey.render.brood_moon_surface_viz import (
                draw_brood_chase_floor_wash,
                draw_brood_chase_surface_band,
            )

            draw_brood_chase_floor_wash(canvas, camera, world)
            draw_brood_chase_surface_band(
                canvas, camera, world, ship_pos=ship_pos, ship_angle=ship_angle,
            )
            from gravity_ho_matey.render.brood_geology_viz import draw_brood_geology_chase
            from gravity_ho_matey.render.brood_flora_viz import draw_brood_flora_chase
            from gravity_ho_matey.render.brood_fauna_viz import draw_brood_fauna_chase
            from gravity_ho_matey.render.brood_ambient_viz import draw_brood_ambient_chase

            draw_brood_geology_chase(canvas, camera, world, ship_pos=ship_pos, ship_angle=ship_angle, rig=rig)
            draw_brood_flora_chase(canvas, camera, world, ship_pos=ship_pos, ship_angle=ship_angle, rig=rig)
            draw_brood_fauna_chase(canvas, camera, world, ship_pos=ship_pos, ship_angle=ship_angle, rig=rig)
            draw_brood_ambient_chase(canvas, camera, world, ship_pos=ship_pos, ship_angle=ship_angle)
        elif brood_orbital_chase:
            from gravity_ho_matey.render.chase_fx import draw_brood_orbital_chase_floor_wash

            draw_brood_orbital_chase_floor_wash(canvas, camera)
            if world.brood_moon is not None and world.brood_moon.layout is not None:
                from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase
                from gravity_ho_matey.render.planet_mission_viz import draw_planet_landing_band_chase

                if world.brood_moon.phase is BroodPhase.ORBITAL:
                    draw_planet_landing_band_chase(
                        canvas,
                        world.brood_moon.layout.planet,
                        camera=camera,
                        ship_pos=ship_pos,
                        ship_angle=ship_angle,
                        accent=palette.BROOD_MOON_HUD_ACCENT,
                        dim=palette.HUD_DIM,
                        elapsed=elapsed,
                    )
        if not brood_on_surface:
            heat_step = 8 if brood_orbital_chase else (4 if field.rows >= 64 else 2)
            draw_chase_gravity_heatmap(
                canvas, field, camera, ship_pos, ship_angle, step=heat_step, _world=world,
            )
        from gravity_ho_matey.render.chase_chart_bounds import draw_chase_chart_edge_hints

        draw_chase_chart_edge_hints(
            canvas,
            config=world.config,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            camera=camera,
        )

        light_layer = LightLayerBuilder(rig, elapsed=elapsed)
        from gravity_ho_matey.render.chase_wells import chase_well_drawable, chase_well_glow_radius

        for well in world.wells:
            drawable, anchor, depth = chase_well_drawable(camera, well, ship_pos, ship_angle)
            if drawable:
                wscale = max(0.25, camera.perspective_scale(depth) / camera.focal_length)
                glow_r = chase_well_glow_radius(camera, well, ship_pos, ship_angle, scale=wscale)
                light_layer.add_well(
                    well,
                    anchor,
                    scale=wscale,
                    depth=depth,
                    screen_glow_radius=glow_r,
                )
        for beacon in world.beacons:
            if beacon.collected:
                continue
            bp = camera.world_to_screen(beacon.pos, ship_pos, ship_angle)
            if bp.visible:
                bscale = max(
                    CHASE_BEACON_SCALE_FLOOR,
                    camera.perspective_scale(bp.depth) / camera.focal_length * CHASE_BEACON_VISUAL_BOOST,
                )
                light_layer.add_beacon(Vec2(bp.x, bp.y), scale=bscale, depth=bp.depth, collected=beacon.collected)
        light_layer.draw_onto_canvas(canvas, horizon_y=camera.chase_horizon_y())

        chase_threat_r = ORBITAL_ASTEROID_THREAT_RADIUS if brood_orbital_chase or brood_on_surface else 0.0
        chase_scree_material = "brood_regolith" if brood_on_surface else "asteroid"
        asteroid_sprites = collect_chase_asteroid_sprites(
            world.asteroids,
            camera,
            ship_pos,
            ship_angle,
            threat_radius=chase_threat_r,
        )
        draw_chase_asteroids(
            canvas,
            asteroid_sprites,
            rig=rig,
            ship_angle=ship_angle,
            material_kind=chase_scree_material,
        )

        sprites: list[tuple[float, str, object]] = []
        from gravity_ho_matey.render.chase_wells import chase_well_drawable

        for well in world.wells:
            drawable, anchor, depth = chase_well_drawable(camera, well, ship_pos, ship_angle)
            if drawable:
                scale = max(0.25, camera.perspective_scale(depth) / camera.focal_length)
                sprites.append((depth, "well", (anchor, well, scale, depth)))
        gate = world.finish_gate.rect
        gate_center = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        gp = camera.world_to_screen(gate_center, ship_pos, ship_angle)
        if gp.visible:
            gate_size = max(gate.w, gate.h)
            sprites.append((gp.depth, "gate", (Vec2(gp.x, gp.y), world.finish_unlocked, gate_size, gp.depth)))
        for beacon in world.beacons:
            p = camera.world_to_screen(beacon.pos, ship_pos, ship_angle)
            if p.visible:
                b_scale = max(
                    CHASE_BEACON_SCALE_FLOOR,
                    camera.perspective_scale(p.depth) / camera.focal_length * CHASE_BEACON_VISUAL_BOOST,
                )
                sprites.append((p.depth, "beacon", (Vec2(p.x, p.y), beacon, b_scale)))
        for jewel in world.jewels:
            p = camera.world_to_screen(jewel.pos, ship_pos, ship_angle)
            if p.visible:
                j_scale = max(0.5, camera.perspective_scale(p.depth) / camera.focal_length)
                sprites.append((p.depth, "jewel", (Vec2(p.x, p.y), world.elapsed, j_scale)))
        if brood and world.egg_pods:
            for pod in world.egg_pods:
                if not pod.alive:
                    continue
                p = camera.world_to_screen(pod.pos, ship_pos, ship_angle)
                if p.visible:
                    scale = max(0.35, camera.perspective_scale(p.depth) / camera.focal_length)
                    sprites.append((p.depth, "egg_pod", (Vec2(p.x, p.y), pod, scale, p.depth)))
        from gravity_ho_matey.gameplay.friendly_fighter_config import PATROL_ENGAGE_RANGE

        brood_combat_read = brood_on_surface or brood_orbital_chase

        def _chase_entity_projection(pos: Vec2, threat_range: float = 0.0):
            if brood_combat_read and threat_range > 0.0:
                return camera.chase_threat_screen(pos, ship_pos, ship_angle, threat_range)
            return camera.world_to_screen(pos, ship_pos, ship_angle)

        for enemy in world.enemies:
            if not enemy.alive:
                continue
            engage = getattr(enemy, "engage_range", PATROL_ENGAGE_RANGE)
            dist = (enemy.pos - ship_pos).length()
            if brood_combat_read and dist > engage + 80.0:
                continue
            threat = engage if brood_combat_read else 0.0
            p = _chase_entity_projection(enemy.pos, threat)
            if p.visible or (brood_combat_read and dist <= engage):
                scale = max(0.35, camera.perspective_scale(max(p.depth, camera.min_depth)) / camera.focal_length)
                sprites.append((max(p.depth, camera.min_depth), "enemy", (Vec2(p.x, p.y), enemy, scale)))
        for ally in world.allies:
            if ally.alive:
                p = camera.world_to_screen(ally.pos, ship_pos, ship_angle)
                if p.visible:
                    scale = max(0.30, camera.perspective_scale(p.depth) / camera.focal_length * 0.78)
                    sprites.append((p.depth, "ally", (Vec2(p.x, p.y), ally, scale)))
        if world.drone_wingman is not None and world.drone_wingman.alive:
            p = camera.world_to_screen(world.drone_wingman.pos, ship_pos, ship_angle)
            if p.visible:
                scale = max(0.32, camera.perspective_scale(p.depth) / camera.focal_length * 0.82)
                sprites.append((p.depth, "drone", (Vec2(p.x, p.y), world.drone_wingman, scale)))
        if world.mega_squid is not None and world.mega_squid.alive:
            from gravity_ho_matey.render.squid_boss_viz import chase_boss_projected

            projected = chase_boss_projected(camera, world.mega_squid, ship_pos, ship_angle)
            if projected is not None:
                pos, scale, depth = projected
                sprites.append((depth, "boss", (pos, world.mega_squid, scale)))
        if world.space_station is not None and world.space_station.alive:
            p = camera.world_to_screen(world.space_station.pos, ship_pos, ship_angle)
            if p.visible:
                scale = max(0.42, camera.perspective_scale(p.depth) / camera.focal_length)
                sprites.append((p.depth, "station", (Vec2(p.x, p.y), world.space_station, scale)))
        for station in world.friendly_stations:
            if not station.alive:
                continue
            p = camera.world_to_screen(station.pos, ship_pos, ship_angle)
            if p.visible:
                scale = max(0.42, camera.perspective_scale(p.depth) / camera.focal_length)
                sprites.append((p.depth, "station", (Vec2(p.x, p.y), station, scale)))
        for projectile in world.projectiles:
            dist = (projectile.pos - ship_pos).length()
            threat = 520.0 if brood_combat_read and projectile.hostile else 0.0
            if brood_combat_read and projectile.hostile and dist > threat + 120.0:
                continue
            p = _chase_entity_projection(projectile.pos, threat)
            if p.visible or (brood_combat_read and projectile.hostile and dist <= threat):
                sprites.append((max(p.depth, camera.min_depth), "projectile", (Vec2(p.x, p.y), projectile)))
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
                    rig=rig,
                )
            elif kind == "gate":
                pos, unlocked, gate_size, depth = payload
                g_scale = max(0.35, camera.perspective_scale(depth) / camera.focal_length)
                if rift:
                    from gravity_ho_matey.render.rift_pad_viz import draw_rift_extract_pad

                    draw_rift_extract_pad(
                        canvas,
                        pos.x,
                        pos.y,
                        unlocked=unlocked,
                        elapsed=elapsed,
                    )
                else:
                    draw_chase_gate(
                        canvas,
                        pos,
                        unlocked=unlocked,
                        solar=solar,
                        gate_size=gate_size,
                        depth_scale=g_scale,
                        elapsed=elapsed,
                    )
            elif kind == "beacon":
                pos, beacon, b_scale = payload
                draw_chase_beacon(
                    canvas,
                    pos,
                    beacon,
                    elapsed=elapsed,
                    depth_scale=b_scale,
                    rig=rig,
                )
            elif kind == "jewel":
                pos, elapsed_j, j_scale = payload
                draw_chase_jewel(canvas, pos, elapsed=elapsed_j, depth_scale=j_scale)
            elif kind == "egg_pod":
                from gravity_ho_matey.render.egg_pod_viz import draw_egg_pod_chase

                pos, pod, scale, depth = payload
                draw_egg_pod_chase(
                    canvas,
                    pod,
                    pos=pos,
                    scale=scale,
                    depth=depth,
                    rig=rig,
                )
            elif kind == "boss":
                from gravity_ho_matey.render.squid_boss_viz import draw_mega_squid_chase

                pos, boss, scale = payload
                draw_mega_squid_chase(
                    canvas,
                    boss,
                    camera,
                    ship_pos=ship_pos,
                    ship_angle=ship_angle,
                    ship_radius=world.ship.radius,
                    elapsed=elapsed,
                    scrape_flash=world.boss_scrape_flash,
                    rig=rig,
                )
            elif kind == "station":
                from gravity_ho_matey.render.station_viz import draw_space_station_chase

                pos, station, scale = payload
                draw_space_station_chase(
                    canvas,
                    station,
                    camera,
                    ship_pos=ship_pos,
                    ship_angle=ship_angle,
                    elapsed=elapsed,
                    rig=rig,
                )
            elif kind == "ally":
                from gravity_ho_matey.render.ship_viz import draw_friendly_fighter_ship

                pos, ally, scale = payload
                draw_friendly_fighter_ship(
                    canvas,
                    pos,
                    ally.facing_angle,
                    scale=scale * CHASE_SHIP_SCALE,
                    rig=rig,
                )
                ally_hp = hp_fraction(ally)
                if ally_hp is not None:
                    r = min(ally.radius * scale * CHASE_SHIP_SCALE, 22.0)
                    draw_health_bar(
                        canvas,
                        pos.x,
                        pos.y - r - 8,
                        r * 1.3,
                        ally_hp,
                        outline="#68e0c0",
                        fill="#40d0a8",
                        low_fill=palette.HUD_WARN,
                    )
            elif kind == "drone":
                from gravity_ho_matey.render.drone_viz import draw_drone_wingman_chase

                pos, drone, scale = payload
                draw_drone_wingman_chase(
                    canvas,
                    pos,
                    drone.facing_angle,
                    scale=scale * CHASE_SHIP_SCALE,
                    drone=drone,
                )
                drone_hp = hp_fraction(drone)
                if drone_hp is not None:
                    r = min(drone.radius * scale * CHASE_SHIP_SCALE, 22.0)
                    draw_health_bar(
                        canvas,
                        pos.x,
                        pos.y - r - 8,
                        r * 1.3,
                        drone_hp,
                        outline=palette.DRONE_TRIM,
                        fill=palette.DRONE_CORE,
                        low_fill=palette.HUD_WARN,
                    )
            elif kind == "enemy":
                pos, enemy, scale = payload
                if enemy.kind is EnemyKind.SQUID and isinstance(enemy, SquidEnemy):
                    tip_screen: list[tuple[float, float]] = []
                    for tip in enemy.tentacle_tips():
                        tp = camera.world_to_screen(tip, ship_pos, ship_angle)
                        if tp.visible:
                            tip_screen.append((tp.x, tp.y))
                    draw_chase_squid(
                        canvas,
                        pos,
                        enemy=enemy,
                        scale=scale,
                        ship_world=ship_pos,
                        ship_radius=world.ship.radius,
                        tip_screen=tuple(tip_screen) if tip_screen else None,
                        rig=rig,
                        elapsed=elapsed,
                    )
                    squid_hp = hp_fraction(enemy)
                    if squid_hp is not None:
                        r = min(enemy.radius * scale, 32.0)
                        draw_health_bar(
                            canvas,
                            pos.x,
                            pos.y - r - 10,
                            r * 1.2,
                            squid_hp,
                            outline="#c058ff",
                            fill="#ff4080",
                            low_fill=palette.BOSS_SCRAPE_WARN,
                        )
                else:
                    draw_chase_enemy(
                        canvas,
                        pos,
                        enemy=enemy,
                        camera=camera,
                        ship_pos=ship_pos,
                        ship_angle=ship_angle,
                        scale=scale,
                        rig=rig,
                        elapsed=elapsed,
                    )
            elif kind == "projectile":
                pos, projectile = payload
                draw_chase_projectile(
                    canvas,
                    pos,
                    projectile,
                    camera=camera,
                    ship_pos=ship_pos,
                    ship_angle=ship_angle,
                    elapsed=elapsed,
                    extended_tail=brood_combat_read and projectile.hostile,
                )

        if rift and world.squid_pods:
            from gravity_ho_matey.render.squid_boss_viz import draw_squid_pods_chase

            draw_squid_pods_chase(
                canvas,
                world.squid_pods,
                camera,
                ship_pos=ship_pos,
                ship_angle=ship_angle,
                elapsed=elapsed,
            )

        anchor_x, anchor_y = camera.chase_anchor()
        display_angle = CHASE_SCREEN_HEADING + camera.bank_display
        if not thrusting and world.ship.vel.length() > 55.0:
            draw_speed_streaks(
                canvas,
                camera,
                world,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                display_angle=display_angle,
                ship_scale=CHASE_SHIP_SCALE,
            )
        draw_speed_vignette(canvas, camera, world.ship.vel.length(), intensity=chase_intensity)
        draw_boost_pressure(canvas, camera, thrusting=thrusting, intensity=chase_intensity)
        if thrusting:
            draw_chase_boost_jolt(
                canvas,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                display_angle=display_angle,
                world=world,
                camera=camera,
                intensity=chase_intensity,
                elapsed=elapsed,
                ship_scale=CHASE_SHIP_SCALE,
            )
        else:
            draw_engine_bloom(
                canvas,
                anchor_x,
                anchor_y,
                display_angle=display_angle,
                boost_energy=world.ship.boost_energy,
                thrusting=False,
                speed=world.ship.vel.length(),
                intensity=chase_intensity,
                ship_scale=CHASE_SHIP_SCALE,
            )
        draw_ship(
            canvas,
            Vec2(anchor_x, anchor_y),
            display_angle,
            world.ship.boost_energy,
            boost_burst=world.ship.boost_flash,
            chase_boost=thrusting,
            invuln=world.invuln_remaining,
            elapsed=elapsed,
            scale=CHASE_SHIP_SCALE,
            rig=rig,
            powerup_stacks=powerup_stacks,
        )
        draw_xwing_cockpit_hud(
            canvas,
            world,
            camera,
            field,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            hud_top=hud_top,
        )
        draw_edge_hints(canvas, world, camera, hud_top=hud_top)
        draw_explosions(canvas, world.explosions.active, project=lambda p: camera.world_to_screen(p, ship_pos, ship_angle))
