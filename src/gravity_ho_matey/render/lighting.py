from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode

_KEY_COVE = Vec2(-0.65, -0.75).normalized()
_KEY_SOLAR = Vec2(-0.55, -0.80).normalized()
_KEY_RIFT = Vec2(-0.48, -0.82).normalized()


@dataclass(frozen=True, slots=True)
class LightRig:
    """Screen-space lighting rig — shared tactical + chase entity drawing."""

    theme: str
    view: str
    key_dir: Vec2
    ambient: float
    rim_strength: float

    @staticmethod
    def for_play(*, theme: str, camera_mode: CameraMode) -> LightRig:
        solar = theme == "solar"
        rift = theme == "rift"
        key = _KEY_SOLAR if solar else _KEY_RIFT if rift else _KEY_COVE
        view = "chase" if camera_mode is CameraMode.CHASE else "tactical"
        rim = 0.55 if view == "chase" else 0.45
        if solar:
            rim += 0.05
        elif rift:
            rim += 0.08
        ambient = 0.28 if solar else 0.38 if rift else 0.35
        return LightRig(
            theme=theme,
            view=view,
            key_dir=key,
            ambient=ambient,
            rim_strength=min(0.72, rim),
        )


@dataclass(frozen=True, slots=True)
class MaterialTones:
    highlight: str
    mid: str
    shadow: str
    deep: str
    rim: str
    crater_pit: str
    crater_rim_hi: str


def material_for(kind: str, *, theme: str, view: str = "tactical") -> MaterialTones:
    solar = theme == "solar"
    if kind == "asteroid":
        if view == "chase":
            if solar:
                return MaterialTones(
                    highlight=palette.CHASE_ASTEROID_HIGHLIGHT,
                    mid=palette.CHASE_ASTEROID_FACE,
                    shadow=palette.CHASE_ASTEROID_SIDE,
                    deep=palette.CHASE_ASTEROID_SIDE_DARK,
                    rim=palette.CHASE_ASTEROID_RIM,
                    crater_pit=palette.ASTEROID_CRATER,
                    crater_rim_hi=palette.CHASE_ASTEROID_REGOLITH,
                )
            return MaterialTones(
                highlight="#8298a8",
                mid="#556068",
                shadow="#3a4248",
                deep="#222830",
                rim="#484f58",
                crater_pit=palette.ASTEROID_CRATER,
                crater_rim_hi="#6a7888",
            )
        if solar:
            return MaterialTones(
                highlight=palette.CHASE_ASTEROID_HIGHLIGHT,
                mid=palette.CHASE_ASTEROID_FACE,
                shadow=palette.CHASE_ASTEROID_SIDE,
                deep=palette.CHASE_ASTEROID_SIDE_DARK,
                rim=palette.CHASE_ASTEROID_RIM,
                crater_pit=palette.ASTEROID_CRATER,
                crater_rim_hi=palette.CHASE_ASTEROID_REGOLITH,
            )
        return MaterialTones(
            highlight="#6a90b0",
            mid=palette.HOLO_ASTEROID_TOP,
            shadow=palette.HOLO_ASTEROID_SIDE,
            deep=palette.HOLO_ASTEROID_SIDE_DARK,
            rim=palette.HOLO_ASTEROID_EDGE,
            crater_pit=palette.ASTEROID_CRATER,
            crater_rim_hi=palette.HOLO_ASTEROID_REGOLITH,
        )
    if kind == "well_black_hole":
        return MaterialTones(
            highlight=palette.BLACK_HOLE_RING,
            mid="#2a1048",
            shadow=palette.BLACK_HOLE,
            deep=palette.BLACK_HOLE_CORE,
            rim=palette.BLACK_HOLE_RING,
            crater_pit=palette.BLACK_HOLE_CORE,
            crater_rim_hi="#8b50cc",
        )
    if kind == "well_planet":
        return MaterialTones(
            highlight="#ffe8a8",
            mid=palette.PLANET_CORE,
            shadow="#c89848",
            deep="#8a6830",
            rim=palette.PLANET_WELL,
            crater_pit="#6a5020",
            crater_rim_hi="#fff0c0",
        )
    if kind == "well_cove":
        return MaterialTones(
            highlight="#d0a8ff",
            mid=palette.WELL_CORE,
            shadow=palette.WELL,
            deep="#4a2080",
            rim=palette.WELL,
            crater_pit="#3a1868",
            crater_rim_hi="#e0c0ff",
        )
    if kind == "ship":
        if solar:
            return MaterialTones(
                highlight="#fff0c8",
                mid="#e0c070",
                shadow="#a08038",
                deep="#584828",
                rim="#b8e4ff",
                crater_pit="#284858",
                crater_rim_hi=palette.SHIP_TRIM,
            )
        return MaterialTones(
            highlight="#fff6dc",
            mid=palette.SHIP,
            shadow="#b89848",
            deep="#5a4828",
            rim="#9ad0e8",
            crater_pit="#2a5068",
            crater_rim_hi=palette.SHIP_TRIM,
        )
    if kind == "beacon":
        return MaterialTones(
            highlight="#c8fff4",
            mid=palette.BEACON,
            shadow="#1a8870",
            deep="#0a4838",
            rim="#dff",
            crater_pit="#063828",
            crater_rim_hi="#e8fff8",
        )
    if kind == "rift_ribbon":
        if view == "chase":
            return MaterialTones(
                highlight=palette.RIFT_RIBBON_STRIPE,
                mid=lerp_hex(palette.RIFT_RIBBON_CORE, palette.CHASE_ASTEROID_REGOLITH, 0.32),
                shadow=lerp_hex(palette.RIFT_RIBBON_EDGE, palette.CHASE_ASTEROID_SIDE, 0.38),
                deep=lerp_hex(palette.RIFT_ROAD_BED, palette.CHASE_ASTEROID_SIDE_DARK, 0.55),
                rim=palette.RIFT_RIBBON_RAIL,
                crater_pit=palette.ASTEROID_CRATER,
                crater_rim_hi=lerp_hex(palette.RIFT_ROAD_REGOLITH, palette.CHASE_ASTEROID_REGOLITH, 0.5),
            )
        return MaterialTones(
            highlight=palette.RIFT_RIBBON_STRIPE,
            mid=lerp_hex(palette.RIFT_RIBBON_CORE, palette.HOLO_ASTEROID_TOP, 0.28),
            shadow=lerp_hex(palette.RIFT_RIBBON_EDGE, palette.HOLO_ASTEROID_SIDE, 0.35),
            deep=lerp_hex(palette.RIFT_ROAD_BED, palette.HOLO_ASTEROID_SIDE_DARK, 0.45),
            rim=palette.RIFT_RIBBON_RAIL,
            crater_pit=palette.ASTEROID_CRATER,
            crater_rim_hi=lerp_hex(palette.RIFT_ROAD_REGOLITH, palette.HOLO_ASTEROID_REGOLITH, 0.55),
        )
    if kind == "boost_pad":
        return MaterialTones(
            highlight=palette.RIFT_PAD_FLASH,
            mid=palette.RIFT_PAD_MK_YELLOW,
            shadow=lerp_hex(palette.RIFT_PAD_MK_ORANGE, "#604020", 0.35),
            deep="#302018",
            rim="#fff0d0",
            crater_pit="#281808",
            crater_rim_hi=palette.RIFT_PAD_ZIGZAG,
        )
    if kind == "squid":
        return MaterialTones(
            highlight="#c878e8",
            mid="#7038a0",
            shadow="#381850",
            deep="#180828",
            rim="#a048d0",
            crater_pit="#100818",
            crater_rim_hi="#e0a0ff",
        )
    if kind == "mega_squid":
        return MaterialTones(
            highlight="#e0a0ff",
            mid="#8040c0",
            shadow="#401858",
            deep="#180828",
            rim="#c058ff",
            crater_pit="#100818",
            crater_rim_hi="#ffa0e0",
        )
    if kind == "space_station":
        return MaterialTones(
            highlight=palette.STATION_HOSTILE_GLOW,
            mid=palette.STATION_HOSTILE_HULL,
            shadow="#301810",
            deep="#100808",
            rim=palette.STATION_HOSTILE_RING,
            crater_pit="#180808",
            crater_rim_hi=palette.STATION_HOSTILE_GLOW,
        )
    if kind == "friendly_ship":
        return MaterialTones(
            highlight=palette.FRIENDLY_SHIP_TRIM,
            mid=palette.FRIENDLY_SHIP,
            shadow=palette.FRIENDLY_SHIP_SHADOW,
            deep="#143038",
            rim=palette.RIFT_HUD_ACCENT,
            crater_pit="#0a2028",
            crater_rim_hi=palette.FRIENDLY_SHIP_TRIM,
        )
    return material_for("asteroid", theme=theme)


def shade_band(normal_dot_key: float) -> int:
    """Map lighting response to 0=highlight .. 3=deep."""
    if normal_dot_key > 0.35:
        return 0
    if normal_dot_key > 0.05:
        return 1
    if normal_dot_key > -0.28:
        return 2
    return 3


def tone_for_band(material: MaterialTones, band: int) -> str:
    if band <= 0:
        return material.highlight
    if band == 1:
        return material.mid
    if band == 2:
        return material.shadow
    return material.deep


def poly_centroid(pts: list[tuple[float, float]]) -> tuple[float, float]:
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    return cx, cy


def face_normal_outward(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    cx: float,
    cy: float,
) -> tuple[float, float]:
    """Outward normal for CCW edge a→b on polygon centered near (cx, cy)."""
    mx = (ax + bx) * 0.5
    my = (ay + by) * 0.5
    ex, ey = bx - ax, by - ay
    nx, ny = ey, -ex
    nl = math.hypot(nx, ny)
    if nl <= 1e-6:
        return 0.0, -1.0
    nx /= nl
    ny /= nl
    if (mx - cx) * nx + (my - cy) * ny < 0.0:
        nx, ny = -nx, -ny
    return nx, ny


def normal_dot_key(nx: float, ny: float, rig: LightRig) -> float:
    return nx * rig.key_dir.x + ny * rig.key_dir.y


def arc_tone_for_point(
    px: float,
    py: float,
    center_x: float,
    center_y: float,
    rig: LightRig,
    material: MaterialTones,
) -> str:
    dx = px - center_x
    dy = py - center_y
    dist = math.hypot(dx, dy)
    if dist <= 1e-6:
        return material.deep
    nd = normal_dot_key(dx / dist, dy / dist, rig)
    return tone_for_band(material, shade_band(nd))


def lerp_hex(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = _hex_rgb(a)
    br, bg, bb = _hex_rgb(b)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bl = int(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def depth_faded_material(material: MaterialTones, fade: float) -> MaterialTones:
    """Atmospheric falloff for chase depth — keeps silhouettes readable."""
    t = max(0.0, min(1.0, fade))
    if t <= 0.01:
        return material
    sink = material.deep
    return MaterialTones(
        highlight=lerp_hex(material.highlight, sink, t * 0.55),
        mid=lerp_hex(material.mid, sink, t * 0.65),
        shadow=lerp_hex(material.shadow, sink, t * 0.75),
        deep=lerp_hex(material.deep, sink, t * 0.85),
        rim=lerp_hex(material.rim, sink, t * 0.45),
        crater_pit=lerp_hex(material.crater_pit, sink, t * 0.5),
        crater_rim_hi=lerp_hex(material.crater_rim_hi, sink, t * 0.4),
    )


def chase_depth_fade(depth: float, *, near: float = 120.0, far: float = 720.0) -> float:
    if depth <= near:
        return 0.0
    if depth >= far:
        return 0.72
    return 0.72 * (depth - near) / (far - near)


def gravity_tone_with_sink(base: str, *, sink_strength: float) -> str:
    if sink_strength <= 0.01:
        return base
    return lerp_hex(base, "#0a0610", min(1.0, sink_strength))


def _hex_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    if len(c) != 6:
        return 0, 0, 0
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def well_material_kind(well_kind: str) -> str:
    if well_kind == "black_hole":
        return "well_black_hole"
    if well_kind == "planet":
        return "well_planet"
    return "well_cove"
