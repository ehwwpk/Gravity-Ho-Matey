from __future__ import annotations

APP_TITLE = "Gravity Ho, Matey!"
CANVAS_WIDTH = 960
CANVAS_HEIGHT = 640
SOLAR_STRIP_HEIGHT = 1680
FRAME_MS = 16
MAX_DT = 1.0 / 30.0
BACKGROUND = "#08111f"

# Pre-release only — set False before public release.
# Single gate: when True, main-menu chart keys 1/2/3 all work regardless of campaign progress.
DEV_UNLOCK_ALL_LEVELS = True

# Pre-release testing — set to 0 before ship; only applied in CampaignState.new().
DEV_START_JEWELS = 100
