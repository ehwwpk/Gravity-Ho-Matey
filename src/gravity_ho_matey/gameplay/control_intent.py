from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ControlIntent:
    rotate_left: bool = False
    rotate_right: bool = False
    thrust: bool = False
    reverse: bool = False
    boost_tap: bool = False
    sprint: bool = False
    fire: bool = False
