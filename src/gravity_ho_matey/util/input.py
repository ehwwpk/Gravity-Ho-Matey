from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.gameplay.world import ControlIntent


@dataclass(slots=True)
class InputState:
    pressed: set[str] = field(default_factory=set)
    _shift_was_down: bool = field(default=False, repr=False)

    def set_key(self, keysym: str, is_pressed: bool) -> None:
        key = normalize_key(keysym)
        if is_pressed:
            self.pressed.add(key)
        else:
            self.pressed.discard(key)
            if key in ("shift_l", "shift_r", "shift"):
                self._shift_was_down = False

    def down(self, *keys: str) -> bool:
        return any(normalize_key(key) in self.pressed for key in keys)

    def to_control_intent(self) -> ControlIntent:
        shift_down = self.down("shift_l", "shift_r", "shift")
        boost_tap = shift_down and not self._shift_was_down
        self._shift_was_down = shift_down
        return ControlIntent(
            rotate_left=self.down("a", "left"),
            rotate_right=self.down("d", "right"),
            thrust=self.down("w", "up"),
            boost_tap=boost_tap,
            fire=self.down("space"),
        )


def normalize_key(keysym: str) -> str:
    return keysym.strip().lower()
