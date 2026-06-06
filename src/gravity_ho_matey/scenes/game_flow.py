from __future__ import annotations

from typing import TYPE_CHECKING

from gravity_ho_matey.gameplay.campaign import CampaignState

if TYPE_CHECKING:
    from gravity_ho_matey.scenes.play import PlayScene


def start_play(level_id: str, campaign: CampaignState | None = None) -> PlayScene:
    from gravity_ho_matey.scenes.play import PlayScene

    return PlayScene(level_id=level_id, campaign=campaign or CampaignState.new())
