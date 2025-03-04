from pydantic import HttpUrl

from ....config import Settings
from ....schemas.common import Region
from ....schemas.nice import AssetURL, NiceEventReward
from ....schemas.raw import MstEventReward, MstGift
from ...utils import fmt_url
from .utils import get_nice_gifts


settings = Settings()


def get_bgImage_url(
    region: Region, bgImageId: int, event_id: int, prefix: str
) -> HttpUrl:
    base_settings = {"base_url": settings.asset_url, "region": region}
    return (
        fmt_url(AssetURL.eventReward, **base_settings, fname=f"{prefix}{bgImageId}")
        if bgImageId > 0
        else fmt_url(
            AssetURL.eventReward, **base_settings, fname=f"{prefix}{event_id}00"
        )
    )


def get_nice_reward(
    region: Region,
    reward: MstEventReward,
    event_id: int,
    gift_maps: dict[int, list[MstGift]],
) -> NiceEventReward:
    return NiceEventReward(
        groupId=reward.groupId,
        point=reward.point,
        gifts=get_nice_gifts(reward.giftId, gift_maps),
        bgImagePoint=get_bgImage_url(
            region, reward.bgImageId, event_id, "event_rewardpoint_"
        ),
        bgImageGet=get_bgImage_url(
            region, reward.bgImageId, event_id, "event_rewardget_"
        ),
    )
