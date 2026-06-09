from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.comet_fuel_expedition import (
    charter_depot_center,
    foot_regolith_anchors,
    DEPOT_PLATFORM_RADIUS,
    LANDER_BLAST_RADIUS,
)
from gravity_ho_matey.levels.comet_fuel_layout import EXPEDITION_HEIGHT, EXPEDITION_WIDTH, LANDER_PAD
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.edge_hints import draw_edge_hints
from gravity_ho_matey.render.eva_viz import draw_eva_avatar
from gravity_ho_matey.render.expedition_depot_viz import draw_charter_depot
from gravity_ho_matey.render.expedition_interact_viz import draw_expedition_interact_prompts
from gravity_ho_matey.render.expedition_fuel_viz import (
    draw_feeding_site_glow,
    draw_fuel_feed_line,
    draw_fuel_line_trench,
    draw_fuel_valve_station,
    draw_rtb_extraction_beacon,
)
from gravity_ho_matey.render.expedition_surface_viz import draw_comet_contact_ring, draw_expedition_tactical_backdrop
from gravity_ho_matey.render.lighting import LightRig, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon
from gravity_ho_matey.render.squid_viz import draw_squid_enemy_tactical
from gravity_ho_matey.gameplay.expedition_mission import (
    InteractKind,
    expedition_foot_objectives_met,
    expedition_fuel_loaded,
)


class ExpeditionViewRenderer:
    def draw(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        camera,
        *,
        hud_top: int,
    ) -> None:
        exp = world.expedition
        rig = LightRig.for_play(theme=world.config.level_theme, camera_mode=camera.mode)
        avatar = world.avatar
        follow = avatar.pos if avatar is not None else Vec2(world.config.width * 0.5, world.config.height * 0.5)
        draw_expedition_tactical_backdrop(
            canvas,
            camera,
            hud_top=float(hud_top),
            follow=follow,
            rig=rig,
            elapsed=world.elapsed,
            map_height=float(EXPEDITION_HEIGHT),
            map_width=float(EXPEDITION_WIDTH),
            depot_center=charter_depot_center(),
            depot_platform_radius=DEPOT_PLATFORM_RADIUS,
            lander_pad=LANDER_PAD,
            lander_blast_radius=LANDER_BLAST_RADIUS,
        )
        regolith = material_for("comet_regolith", theme=rig.theme, view=rig.view)
        for seed, cx, cy, r in foot_regolith_anchors():
            p = camera.world_to_screen(Vec2(cx, cy), follow, 0.0)
            pts = [
                (
                    p.x + math.cos(a) * r * camera.tactical_scale * 0.52,
                    p.y + hud_top + math.sin(a) * r * camera.tactical_scale * 0.42,
                )
                for a in [i * 0.85 + seed * 0.07 for i in range(9)]
            ]
            draw_illustrated_polygon(
                canvas,
                pts,
                rig=rig,
                material=regolith,
                seed=seed,
                radius_hint=r * camera.tactical_scale * 0.5,
                crater_count=4,
            )
        if exp is not None:
            for line in exp.feed_lines:
                draw_fuel_line_trench(
                    canvas,
                    line,
                    camera=camera,
                    follow=follow,
                    hud_top=float(hud_top),
                    rig=rig,
                )
            draw_charter_depot(
                canvas,
                charter_depot_center(),
                camera=camera,
                follow=follow,
                hud_top=float(hud_top),
                rig=rig,
                elapsed=world.elapsed,
            )
            for node in exp.interact_nodes:
                if node.kind is InteractKind.FUEL_VALVE:
                    draw_fuel_valve_station(
                        canvas,
                        node.pos,
                        camera=camera,
                        follow=follow,
                        hud_top=float(hud_top),
                        rig=rig,
                        elapsed=world.elapsed,
                        loaded=node.id in exp.completed_interact_ids,
                        active=exp.active_interact_id == node.id,
                    )
                elif node.kind is InteractKind.EXTRACT_PAD and expedition_fuel_loaded(exp):
                    draw_rtb_extraction_beacon(
                        canvas,
                        node.pos,
                        camera=camera,
                        follow=follow,
                        hud_top=float(hud_top),
                        elapsed=world.elapsed,
                        scale_hint=camera.tactical_scale,
                        ready=expedition_foot_objectives_met(exp),
                        blocked=False,
                    )
            for line in exp.feed_lines:
                draw_fuel_feed_line(
                    canvas,
                    line,
                    camera=camera,
                    follow=follow,
                    hud_top=float(hud_top),
                    rig=rig,
                    elapsed=world.elapsed,
                )
                draw_feeding_site_glow(
                    canvas,
                    line.end,
                    camera=camera,
                    follow=follow,
                    hud_top=float(hud_top),
                    elapsed=world.elapsed,
                    scale_hint=camera.tactical_scale,
                )
            self._draw_lander_pad(canvas, camera, follow, hud_top, world.elapsed, exp)
            draw_comet_contact_ring(
                canvas,
                world.ship.pos,
                28.0,
                camera=camera,
                follow=follow,
                hud_top=float(hud_top),
                rig=rig,
                scale=1.6,
            )
            self._draw_parked_ship(canvas, world, camera, follow, hud_top, rig, world.elapsed)
            self._draw_interact_markers(canvas, exp, camera, follow, hud_top, world.elapsed)
            if avatar is not None:
                draw_expedition_interact_prompts(
                    canvas,
                    exp,
                    avatar.pos,
                    camera=camera,
                    follow=follow,
                    hud_top=float(hud_top),
                    elapsed=world.elapsed,
                )
        for enemy in world.enemies:
            if enemy.alive:
                draw_comet_contact_ring(
                    canvas,
                    enemy.pos,
                    enemy.radius * 0.85,
                    camera=camera,
                    follow=follow,
                    hud_top=float(hud_top),
                    rig=rig,
                )
                draw_squid_enemy_tactical(
                    canvas,
                    enemy,
                    camera=camera,
                    ship_pos=follow,
                    ship_radius=16.0,
                    hud_top=float(hud_top),
                    rig=rig,
                    elapsed=world.elapsed,
                )
        for projectile in world.projectiles:
            pp = camera.world_to_screen(projectile.pos, follow, 0.0)
            canvas.create_oval(
                pp.x - 3,
                pp.y + hud_top - 3,
                pp.x + 3,
                pp.y + hud_top + 3,
                fill=palette.PICKUP_RAPID,
                outline="",
            )
        if avatar is not None:
            interacting = bool(exp and exp.active_interact_id)
            draw_comet_contact_ring(
                canvas,
                avatar.pos,
                avatar.radius,
                camera=camera,
                follow=follow,
                hud_top=float(hud_top),
                rig=rig,
            )
            draw_eva_avatar(
                canvas,
                avatar,
                camera=camera,
                ship_pos=follow,
                hud_top=float(hud_top),
                rig=rig,
                elapsed=world.elapsed,
                interacting=interacting,
            )
        draw_edge_hints(canvas, world, camera, hud_top=float(hud_top))

    def _draw_parked_ship(
        self,
        canvas: tk.Canvas,
        world: GameWorld,
        camera,
        follow: Vec2,
        hud_top: int,
        rig: LightRig,
        elapsed: float,
    ) -> None:
        """Landed charter vessel at the pad — larger read than EVA."""
        exp = world.expedition
        if exp is None:
            return
        p = camera.world_to_screen(world.ship.pos, follow, 0.0)
        from gravity_ho_matey.render.world_draw import draw_ship

        draw_ship(
            canvas,
            Vec2(p.x, p.y + hud_top),
            world.ship.angle,
            world.ship.boost_energy,
            scale=camera.tactical_scale * 1.35,
            rig=rig,
            elapsed=elapsed,
        )

    def _draw_lander_pad(
        self,
        canvas: tk.Canvas,
        camera,
        follow: Vec2,
        hud_top: int,
        elapsed: float,
        exp,
    ) -> None:
        """Navigation beacons on the landing disc (blast flat drawn in surface backdrop)."""
        p = camera.world_to_screen(LANDER_PAD, follow, 0.0)
        cx, cy = p.x, p.y + hud_top
        scale = camera.tactical_scale
        pulse = 0.5 + 0.5 * math.sin(elapsed * 2.0)
        r = 68.0 * scale
        rtb_ready = expedition_fuel_loaded(exp)
        outline = palette.GATE_OPEN if rtb_ready else palette.COMET_HUD_ACCENT
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=2, dash=(6, 5))
        inner = r * (0.55 + pulse * 0.08)
        canvas.create_oval(cx - inner, cy - inner, cx + inner, cy + inner, outline=palette.COMET_VEIN, width=1)
        for i in range(4):
            ang = i * math.pi / 2 + elapsed * 0.2
            lx = cx + math.cos(ang) * r * 0.75
            ly = cy + math.sin(ang) * r * 0.75
            canvas.create_rectangle(lx - 4, ly - 4, lx + 4, ly + 4, fill=outline, outline="")
        label = "RTB" if rtb_ready else "LANDER"
        label_color = palette.GATE_OPEN if rtb_ready else palette.COMET_HUD_ACCENT
        canvas.create_text(cx, cy - r - 10 * scale, text=label, fill=label_color, font=("Consolas", max(8, int(9 * scale))))

    def _draw_interact_markers(
        self,
        canvas: tk.Canvas,
        exp,
        camera,
        follow: Vec2,
        hud_top: int,
        elapsed: float,
    ) -> None:
        pulse = 0.5 + 0.5 * math.sin(elapsed * 4.0)
        for node in exp.interact_nodes:
            if node.one_shot and node.id in exp.completed_interact_ids:
                continue
            if node.kind is InteractKind.EXTRACT_PAD:
                continue
            if node.kind is InteractKind.FUEL_VALVE:
                color = palette.COMET_HUD_ACCENT
            elif node.kind is InteractKind.EXTRACT_PAD:
                color = palette.GATE_OPEN
            else:
                color = palette.HUD_DIM
            p = camera.world_to_screen(node.pos, follow, 0.0)
            r = (node.radius * 0.35 + pulse * 4.0) * camera.tactical_scale
            canvas.create_oval(
                p.x - r,
                p.y + hud_top - r,
                p.x + r,
                p.y + hud_top + r,
                outline=color,
                width=2,
                dash=(4, 4) if node.kind is InteractKind.EXTRACT_PAD else (),
            )
