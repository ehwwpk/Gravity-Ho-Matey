from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2

_ALPHA = 0.5


@dataclass(frozen=True, slots=True)
class RibbonSample:
    pos: Vec2
    tangent: Vec2
    ribbon_id: str
    arc_s: float
    half_width: float


@dataclass(frozen=True, slots=True)
class RibbonSpec:
    id: str
    control_points: tuple[Vec2, ...]
    half_width: float = 105.0
    sample_step: float = 28.0


def _catmull_point(p0: Vec2, p1: Vec2, p2: Vec2, p3: Vec2, t: float) -> Vec2:
    t2 = t * t
    t3 = t2 * t
    return (
        p1 * 2.0
        + (p2 - p0) * t
        + (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * t2
        + (p0 * -1.0 + p1 * 3.0 - p2 * 3.0 + p3) * t3
    ) * 0.5


def _segment_length(p0: Vec2, p1: Vec2, p2: Vec2, p3: Vec2, steps: int = 8) -> float:
    prev = _catmull_point(p0, p1, p2, p3, 0.0)
    total = 0.0
    for i in range(1, steps + 1):
        t = i / steps
        cur = _catmull_point(p0, p1, p2, p3, t)
        total += (cur - prev).length()
        prev = cur
    return total


def sample_ribbon(spec: RibbonSpec) -> tuple[RibbonSample, ...]:
    pts = spec.control_points
    if len(pts) < 4:
        return ()
    padded = (pts[0], *pts, pts[-1])
    samples: list[RibbonSample] = []
    arc = 0.0
    for seg in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[seg - 1], padded[seg], padded[seg + 1], padded[seg + 2]
        seg_len = _segment_length(p0, p1, p2, p3)
        if seg_len < 1e-6:
            continue
        steps = max(2, int(seg_len / spec.sample_step))
        prev = _catmull_point(p0, p1, p2, p3, 0.0)
        for i in range(steps + 1):
            t = i / steps
            pos = _catmull_point(p0, p1, p2, p3, t)
            if i > 0:
                arc += (pos - prev).length()
            if i == 0 and samples:
                prev = pos
                continue
            if i < steps:
                nxt = _catmull_point(p0, p1, p2, p3, min(1.0, t + 1.0 / steps))
                tangent = (nxt - pos).normalized()
            else:
                tangent = (pos - prev).normalized()
            if tangent.length_sq() < 1e-9:
                tangent = Vec2(0.0, -1.0)
            samples.append(
                RibbonSample(
                    pos=pos,
                    tangent=tangent,
                    ribbon_id=spec.id,
                    arc_s=arc,
                    half_width=spec.half_width,
                )
            )
            prev = pos
    return tuple(samples)


def build_all_samples(ribbons: tuple[RibbonSpec, ...]) -> tuple[RibbonSample, ...]:
    out: list[RibbonSample] = []
    for spec in ribbons:
        out.extend(sample_ribbon(spec))
    return tuple(out)


@dataclass(frozen=True, slots=True)
class NearestRibbonHit:
    dist: float
    sample: RibbonSample


def nearest_ribbon(pos: Vec2, samples: tuple[RibbonSample, ...]) -> NearestRibbonHit | None:
    if not samples:
        return None
    best: NearestRibbonHit | None = None
    for sample in samples:
        d = (pos - sample.pos).length()
        if best is None or d < best.dist:
            best = NearestRibbonHit(dist=d, sample=sample)
    return best
