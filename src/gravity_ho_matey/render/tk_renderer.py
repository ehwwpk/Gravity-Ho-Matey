from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_LABELS, PowerUpKind
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay


class TkRenderer:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self._hud = SciFiHudOverlay()

    def clear(self) -> None:
        self.canvas.delete("all")

    def draw_title(self) -> None:
        self.clear()
        self.canvas.create_rectangle(0, 0, 960, 640, fill=palette.BACKGROUND, outline="")
        self._draw_starfield()
        self.canvas.create_text(480, 150, text="Gravity Ho, Matey!", fill=palette.TEXT, font=("Courier", 34, "bold"))
        self.canvas.create_text(480, 205, text="Pirate gravity races through cursed coves and cursed star charts", fill=palette.MUTED_TEXT, font=("Courier", 14))
        solar_unlocked = is_level_selectable("solar")
        level_two_line = (
            "2 — Singularity Crossing (unlocked)"
            if solar_unlocked
            else "2 — Singularity Crossing (locked — clear Cove first)"
        )
        controls = [
            "Collect all beacons, then escape through the finish gate.",
            "A/D or ←/→ rotate     W/↑ thrust     Shift boost     R restarts level",
            "Space fires curved cannon shots — sink patrol skiffs for power-ups.",
            "3 lives per campaign — 3 hull chunks per life. Power-ups carry across levels.",
            "Planet wells and the singularity are lethal. Reef scrapes cost 1 chunk.",
            f"1 — Full campaign (Cove)     {level_two_line}",
            "Enter starts the campaign at Cove.",
        ]
        for i, line in enumerate(controls):
            accent = i >= 3
            self.canvas.create_text(
                480,
                270 + i * 30,
                text=line,
                fill=palette.TEXT if accent else palette.MUTED_TEXT,
                font=("Courier", 13 if accent else 14),
            )
        self._draw_demo_ship(Vec2(480, 455), 0.0, scale=2.4)

    def draw_world(self, world: GameWorld, campaign: CampaignState, *, hud_alert: str = "") -> None:
        self.clear()
        solar = world.config.level_theme == "solar"
        bg = palette.SOLAR_BG if solar else palette.BACKGROUND
        hud_top = SciFiHudOverlay.PANEL_H + (22 if hud_alert else 0)
        self.canvas.create_rectangle(0, 0, world.config.width, world.config.height, fill=bg, outline="")
        if solar:
            self._draw_starfield(dense=True, y_offset=hud_top)
        else:
            self._draw_grid(world.config.width, world.config.height, y_offset=hud_top)
        self._draw_gate(world, solar)
        for wall in world.walls:
            r = wall.rect
            fill = palette.ASTEROID if solar else palette.WALL
            edge = palette.ASTEROID_EDGE if solar else palette.WALL_EDGE
            self.canvas.create_rectangle(r.x, r.y, r.x + r.w, r.y + r.h, fill=fill, outline=edge, width=2)
        for well in world.wells:
            self._draw_well(well.pos, well.radius, well.label, well.kind)
        for beacon in world.beacons:
            color = palette.BEACON_COLLECTED if beacon.collected else palette.BEACON
            self.canvas.create_rectangle(beacon.pos.x - 7, beacon.pos.y - 7, beacon.pos.x + 7, beacon.pos.y + 7, fill=color, outline="#dff", width=1)
            if not beacon.collected:
                self.canvas.create_oval(beacon.pos.x - 17, beacon.pos.y - 17, beacon.pos.x + 17, beacon.pos.y + 17, outline=color)
        for pickup in world.pickups:
            self._draw_pickup(pickup.pos, pickup.kind)
        for enemy in world.enemies:
            if enemy.alive:
                self._draw_enemy(enemy.pos, enemy.radius, enemy.facing_angle)
        for projectile in world.projectiles:
            p = projectile.pos
            self.canvas.create_oval(p.x - 4, p.y - 4, p.x + 4, p.y + 4, fill=palette.PROJECTILE, outline="")
            tail = p - projectile.vel.normalized() * 14
            self.canvas.create_line(tail.x, tail.y, p.x, p.y, fill=palette.PROJECTILE)
        self._draw_ship(world.ship.pos, world.ship.angle, world.ship.boost_energy, world.invuln_remaining, world.elapsed)
        self._hud.draw(self.canvas, world, campaign, hud_alert=hud_alert)
        if world.status is GameStatus.WON:
            self.canvas.create_text(480, 320, text="YOU ESCAPED", fill=palette.GATE_OPEN, font=("Courier", 28, "bold"))

    def draw_end(
        self,
        won: bool,
        elapsed: float,
        reason: str,
        level_id: str,
        campaign: CampaignState,
        game_over: bool = False,
    ) -> None:
        from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, LEVEL_ORDER, next_level_id

        self.clear()
        self.canvas.create_rectangle(0, 0, 960, 640, fill=palette.BACKGROUND, outline="")
        self._draw_starfield()
        if game_over:
            title = "Campaign over."
            subtitle = reason or "All three lives spent."
            prompt = "Enter: return to title     Esc: title"
        elif won:
            upcoming = next_level_id(level_id)
            if upcoming is not None:
                title = "Treasure route cleared!" if level_id == "cove" else "Star chart cleared!"
                subtitle = f"Finished in {elapsed:0.2f}s — next: {LEVEL_LABELS[upcoming]}"
                level_num = LEVEL_ORDER.index(upcoming) + 1
                prompt = f"Enter: continue to level {level_num}     Esc: title"
            else:
                title = "Campaign complete!"
                subtitle = f"Singularity crossed in {elapsed:0.2f}s. Both charts cleared."
                prompt = "Enter: return to title     Esc: title"
        else:
            title = "Shipwrecked."
            subtitle = (
                f"{reason or 'The void claims another captain.'}   "
                f"Lives left: {campaign.lives}   Hull: {campaign.hull_chunks}/{CHUNKS_PER_LIFE}"
            )
            prompt = "Enter: try again     Esc: title"
        self.canvas.create_text(480, 220, text=title, fill=palette.TEXT, font=("Courier", 30, "bold"))
        self.canvas.create_text(480, 275, text=subtitle, fill=palette.MUTED_TEXT, font=("Courier", 16))
        self.canvas.create_text(480, 355, text=prompt, fill=palette.TEXT, font=("Courier", 15))
        if campaign.powerups:
            perks = "Carried loot: " + ", ".join(POWERUP_LABELS[kind] for kind in sorted(campaign.powerups, key=lambda k: k.name))
            self.canvas.create_text(480, 410, text=perks, fill=palette.MUTED_TEXT, font=("Courier", 12))

    def _draw_grid(self, width: int, height: int, y_offset: int = 0) -> None:
        for x in range(0, width, 48):
            self.canvas.create_line(x, y_offset, x, height, fill=palette.SEA_GRID)
        for y in range(y_offset, height, 48):
            self.canvas.create_line(0, y, width, y, fill=palette.SEA_GRID)

    def _draw_starfield(self, dense: bool = False, y_offset: int = 0) -> None:
        count = 140 if dense else 80
        for i in range(count):
            x = (i * 83 + 17) % 960
            y = y_offset + (i * 47 + 31) % max(1, 640 - y_offset)
            size = 3 if dense and i % 5 == 0 else 2
            tone = "#3a5570" if dense and i % 7 == 0 else "#294764"
            self.canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")

    def _draw_ship(self, pos: Vec2, angle: float, boost: float, invuln: float = 0.0, elapsed: float = 0.0) -> None:
        if invuln > 0.0 and int(elapsed * 14) % 2 == 0:
            ring_r = 22
            self.canvas.create_oval(
                pos.x - ring_r,
                pos.y - ring_r,
                pos.x + ring_r,
                pos.y + ring_r,
                outline=palette.HUD_ACCENT,
                width=2,
            )
        nose = pos + Vec2.from_angle(angle) * 18
        left = pos + Vec2.from_angle(angle + 2.45) * 13
        right = pos + Vec2.from_angle(angle - 2.45) * 13
        self.canvas.create_polygon(nose.x, nose.y, left.x, left.y, right.x, right.y, fill=palette.SHIP, outline="#fff0b5", width=2)
        mast = pos - Vec2.from_angle(angle) * 4
        sail_tip = mast + Vec2.from_angle(angle + 1.55) * 9
        self.canvas.create_line(mast.x, mast.y, sail_tip.x, sail_tip.y, fill=palette.SHIP_TRIM, width=3)
        if boost < 0.98:
            flame = pos - Vec2.from_angle(angle) * 20
            self.canvas.create_line(pos.x, pos.y, flame.x, flame.y, fill="#ff7a4a", width=3)

    def _draw_demo_ship(self, pos: Vec2, angle: float, scale: float) -> None:
        nose = pos + Vec2.from_angle(angle) * (18 * scale)
        left = pos + Vec2.from_angle(angle + 2.45) * (13 * scale)
        right = pos + Vec2.from_angle(angle - 2.45) * (13 * scale)
        self.canvas.create_polygon(nose.x, nose.y, left.x, left.y, right.x, right.y, fill=palette.SHIP, outline="#fff0b5", width=3)

    def _draw_well(self, pos: Vec2, radius: float, label: str, kind: str = "well") -> None:
        if kind == "black_hole":
            for frac in (1.0, 0.72, 0.44):
                r = radius * frac
                self.canvas.create_oval(pos.x - r, pos.y - r, pos.x + r, pos.y + r, outline=palette.BLACK_HOLE_RING, width=2)
            self.canvas.create_oval(pos.x - 22, pos.y - 22, pos.x + 22, pos.y + 22, fill=palette.BLACK_HOLE_CORE, outline=palette.BLACK_HOLE, width=2)
            label_color = "#c58cff"
        elif kind == "planet":
            self.canvas.create_oval(pos.x - radius, pos.y - radius, pos.x + radius, pos.y + radius, outline=palette.PLANET_WELL, width=2)
            self.canvas.create_oval(pos.x - radius * 0.55, pos.y - radius * 0.55, pos.x + radius * 0.55, pos.y + radius * 0.55, fill=palette.PLANET_CORE, outline="")
            label_color = palette.PLANET_LABEL
        else:
            for frac in (1.0, 0.66, 0.33):
                r = radius * frac
                self.canvas.create_oval(pos.x - r, pos.y - r, pos.x + r, pos.y + r, outline=palette.WELL)
            self.canvas.create_oval(pos.x - 10, pos.y - 10, pos.x + 10, pos.y + 10, fill=palette.WELL_CORE, outline="")
            label_color = "#caaaff"
        if label:
            self.canvas.create_text(pos.x, pos.y - radius - 10, text=label, fill=label_color, font=("Courier", 8))

    def _draw_gate(self, world: GameWorld, solar: bool = False) -> None:
        r = world.finish_gate.rect
        color = palette.GATE_OPEN if world.finish_unlocked else palette.GATE_LOCKED
        self.canvas.create_rectangle(r.x, r.y, r.x + r.w, r.y + r.h, outline=color, width=4)
        if solar:
            text = "WORMHOLE" if world.finish_unlocked else "SEALED"
        else:
            text = "OPEN" if world.finish_unlocked else "LOCK"
        self.canvas.create_text(r.x + r.w / 2, r.y + r.h / 2, text=text, fill=color, font=("Courier", 9, "bold"))

    def _draw_enemy(self, pos: Vec2, radius: float, facing_angle: float) -> None:
        self.canvas.create_oval(pos.x - radius, pos.y - radius, pos.x + radius, pos.y + radius, fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=2)
        spike = pos + Vec2.from_angle(facing_angle) * (radius + 5)
        self.canvas.create_line(pos.x, pos.y, spike.x, spike.y, fill=palette.ENEMY_EDGE, width=2)

    def _draw_pickup(self, pos: Vec2, kind: PowerUpKind) -> None:
        color = {
            PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
            PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
            PowerUpKind.STABILIZER: palette.PICKUP_STABILIZER,
        }.get(kind, palette.BEACON)
        self.canvas.create_polygon(
            pos.x,
            pos.y - 12,
            pos.x + 10,
            pos.y,
            pos.x,
            pos.y + 12,
            pos.x - 10,
            pos.y,
            fill=color,
            outline="#fff",
        )

