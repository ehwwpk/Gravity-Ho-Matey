from __future__ import annotations

from typing import TYPE_CHECKING

from gravity_ho_matey.gameplay.campaign import CampaignState

if TYPE_CHECKING:
    from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene
    from gravity_ho_matey.scenes.launch_countdown import LaunchCountdownScene
    from gravity_ho_matey.scenes.level_intro import LevelIntroScene
    from gravity_ho_matey.scenes.play import PlayScene


def start_play(level_id: str, campaign: CampaignState | None = None) -> PlayScene:
    from gravity_ho_matey.scenes.play import PlayScene

    return PlayScene(level_id=level_id, campaign=campaign or CampaignState.new())


def start_launch_countdown(level_id: str, campaign: CampaignState | None = None) -> LaunchCountdownScene:
    from gravity_ho_matey.scenes.launch_countdown import LaunchCountdownScene

    return LaunchCountdownScene(
        level_id=level_id,
        campaign=campaign or CampaignState.new(),
    )


def start_level_intro(
    level_id: str,
    campaign: CampaignState | None = None,
) -> LevelIntroScene | LaunchCountdownScene:
    """Post-holo narrative clip when configured; otherwise 3-2-1 launch countdown."""
    from gravity_ho_matey.narrative.level_intros import has_level_intro
    from gravity_ho_matey.scenes.level_intro import LevelIntroScene

    state = campaign or CampaignState.new()
    if not has_level_intro(level_id):
        return start_launch_countdown(level_id, state)
    return LevelIntroScene(level_id=level_id, campaign=state)


def start_chart_briefing(
    upcoming_level_id: str,
    *,
    campaign: CampaignState | None = None,
    cleared_level_id: str | None = None,
    elapsed: float = 0.0,
) -> ChartBriefingScene:
    from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene

    return ChartBriefingScene(
        upcoming_level_id=upcoming_level_id,
        campaign=campaign or CampaignState.new(),
        cleared_level_id=cleared_level_id,
        elapsed=elapsed,
    )
