from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.render.health_bar_viz import hp_fraction


def test_hp_fraction_for_multi_hit_enemy() -> None:
    squid = SquidEnemy(pos=Vec2())
    squid.hits_remaining = 2
    assert hp_fraction(squid) == 2 / squid.hits_max


def test_hp_fraction_none_without_hits() -> None:
    assert hp_fraction(object()) is None
