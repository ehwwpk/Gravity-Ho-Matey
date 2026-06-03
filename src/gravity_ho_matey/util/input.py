from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.gameplay.world import ControlIntent


@dataclass(slots=True)
class InputState:
    pressed: set[str] = field(default_factory=set)

    def set_key(self, keysym: str, is_pressed: bool) -> None:
        key = normalize_key(keysym)
        if is_pressed:
            self.pressed.add(key)
        else:
            self.pressed.discard(key)

    def down(self, *keys: str) -> bool:
        return any(normalize_key(key) in self.pressed for key in keys)

    def to_control_intent(self) -> ControlIntent:
        return ControlIntent(
            rotate_left=self.down("a", "left"),
            rotate_right=self.down("d", "right"),
            thrust=self.down("w", "up"),
            boost=self.down("shift_l", "shift_r", "shift"),
            fire=self.down("space"),
        )


def normalize_key(keysym: str) -> str:
    return keysym.strip().lower()
