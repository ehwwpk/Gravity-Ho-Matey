from __future__ import annotations

from collections import Counter

from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_HUD_TAGS, PowerUpKind

PowerUpStacks = Counter[PowerUpKind]


def powerup_hud_tag(kind: PowerUpKind, count: int) -> str:
    tag = POWERUP_HUD_TAGS[kind]
    return f"{tag}×{count}" if count > 1 else tag


def active_powerup_kinds(stacks: PowerUpStacks) -> set[PowerUpKind]:
    return {kind for kind, count in stacks.items() if count > 0}
