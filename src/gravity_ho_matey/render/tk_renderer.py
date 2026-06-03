from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette


class TkRenderer:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas

    def clear(self) -> None:
        self.canvas.delete("all")

    def draw_title(self) -> None:
        self.clear()
        self.canvas.create_rectangle(0, 0, 960, 640, fill=palette.BACKGROUND, outline="")
        self._draw_starfield()
        self.canvas.create_text(480, 150, text="Gravity Ho, Matey!", fill=palette.TEXT, font=("Courier", 34, "bold"))
        self.canvas.create_text(480, 205, text="A pirate gravity race through a cursed cove", fill=palette.MUTED_TEXT, font=("Courier", 15))
        controls = [
            "Collect all beacons, then escape through the finish gate.",
            "A/D or ←/→ rotate     W/↑ thrust     Shift boost",
            "Space fires curved cannon shots     R restarts",
            "Press Enter to launch.",
        ]
        for i, line in enumerate(controls):
            self.canvas.create_text(480, 285 + i * 34, text=line, fill=palette.TEXT if i == 3 else palette.MUTED_TEXT, font=("Courier", 14))
        self._draw_demo_ship(Vec2(480, 475), 0.0, scale=2.4)

    def draw_world(self, world: GameWorld) -> None:
        self.clear()
        self.canvas.create_rectangle(0, 0, world.config.width, world.config.height, fill=palette.BACKGROUND, outline="")
        self._draw_grid(world.config.width, world.config.height)
        self._draw_gate(world)
        for wall in world.walls:
            r = wall.rect
            self.canvas.create_rectangle(r.x, r.y, r.x + r.w, r.y + r.h, fill=palette.WALL, outline=palette.WALL_EDGE, width=2)
        for well in world.wells:
            self._draw_well(well.pos, well.radius, well.label)
        for beacon in world.beacons:
            color = palette.BEACON_COLLECTED if beacon.collected else palette.BEACON
            self.canvas.create_rectangle(beacon.pos.x - 7, beacon.pos.y - 7, beacon.pos.x + 7, beacon.pos.y + 7, fill=color, outline="#dff", width=1)
            if not beacon.collected:
                self.canvas.create_oval(beacon.pos.x - 17, beacon.pos.y - 17, beacon.pos.x + 17, beacon.pos.y + 17, outline=color)
        for projectile in world.projectiles:
            p = projectile.pos
            self.canvas.create_oval(p.x - 4, p.y - 4, p.x + 4, p.y + 4, fill=palette.PROJECTILE, outline="")
            tail = p - projectile.vel.normalized() * 14
            self.canvas.create_line(tail.x, tail.y, p.x, p.y, fill=palette.PROJECTILE)
        self._draw_ship(world.ship.pos, world.ship.angle, world.ship.boost_energy)
        self._draw_hud(world)

    def draw_end(self, won: bool, elapsed: float, reason: str = "") -> None:
        self.clear()
        self.canvas.create_rectangle(0, 0, 960, 640, fill=palette.BACKGROUND, outline="")
        self._draw_starfield()
        title = "Treasure route cleared!" if won else "Shipwrecked."
        subtitle = f"Finished in {elapsed:0.2f}s" if won else (reason or "The cove claims another captain.")
        self.canvas.create_text(480, 220, text=title, fill=palette.TEXT, font=("Courier", 30, "bold"))
        self.canvas.create_text(480, 275, text=subtitle, fill=palette.MUTED_TEXT, font=("Courier", 16))
        self.canvas.create_text(480, 355, text="Enter: sail again     Esc: title", fill=palette.TEXT, font=("Courier", 15))

    def _draw_grid(self, width: int, height: int) -> None:
        for x in range(0, width, 48):
            self.canvas.create_line(x, 0, x, height, fill=palette.SEA_GRID)
        for y in range(0, height, 48):
            self.canvas.create_line(0, y, width, y, fill=palette.SEA_GRID)

    def _draw_starfield(self) -> None:
        for i in range(80):
            x = (i * 83) % 960
            y = (i * 47 + 31) % 640
            self.canvas.create_rectangle(x, y, x + 2, y + 2, fill="#294764", outline="")

    def _draw_ship(self, pos: Vec2, angle: float, boost: float) -> None:
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

    def _draw_well(self, pos: Vec2, radius: float, label: str) -> None:
        for frac in (1.0, 0.66, 0.33):
            r = radius * frac
            self.canvas.create_oval(pos.x - r, pos.y - r, pos.x + r, pos.y + r, outline=palette.WELL)
        self.canvas.create_oval(pos.x - 10, pos.y - 10, pos.x + 10, pos.y + 10, fill=palette.WELL_CORE, outline="")
        if label:
            self.canvas.create_text(pos.x, pos.y - 24, text=label, fill="#caaaff", font=("Courier", 8))

    def _draw_gate(self, world: GameWorld) -> None:
        r = world.finish_gate.rect
        color = palette.GATE_OPEN if world.finish_unlocked else palette.GATE_LOCKED
        self.canvas.create_rectangle(r.x, r.y, r.x + r.w, r.y + r.h, outline=color, width=4)
        text = "OPEN" if world.finish_unlocked else "LOCK"
        self.canvas.create_text(r.x + r.w / 2, r.y + r.h / 2, text=text, fill=color, font=("Courier", 10, "bold"))

    def _draw_hud(self, world: GameWorld) -> None:
        status = f"Beacons: {world.beacons_remaining}   Time: {world.elapsed:0.1f}s   Boost: {int(world.ship.boost_energy * 100)}%"
        self.canvas.create_rectangle(0, 0, world.config.width, 28, fill="#050a12", outline="")
        self.canvas.create_text(14, 14, anchor="w", text=status, fill=palette.TEXT, font=("Courier", 12, "bold"))
        if world.status is GameStatus.WON:
            self.canvas.create_text(480, 320, text="YOU ESCAPED", fill=palette.GATE_OPEN, font=("Courier", 28, "bold"))
