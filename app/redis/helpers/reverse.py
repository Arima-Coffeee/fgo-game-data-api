from enum import Enum

import orjson
from redis.asyncio import Redis  # type: ignore

from ...config import Settings
from ...schemas.common import Region


settings = Settings()


class RedisReverse(str, Enum):
    BUFF_TO_FUNC = "buff_to_func"
    FUNC_TO_SKILL = "func_to_skill"
    FUNC_TO_TD = "func_to_td"
    TD_TO_SVT = "td_to_svt"
    ACTIVE_SKILL_TO_SVT = "active_skill_to_svt"
    PASSIVE_SKILL_TO_SVT = "passive_skill_to_svt"
    SKILL_TO_MC = "skill_to_mc"
    SKILL_TO_CC = "skill_to_cc"


async def get_reverse_ids(
    redis: Redis, region: Region, reverse_type: RedisReverse, item_id: int
) -> list[int]:
    redis_key = f"{settings.redis_prefix}:data:{region.name}:{reverse_type.name}"
    item_redis = await redis.hget(redis_key, item_id)

    if item_redis:
        id_list: list[int] = orjson.loads(item_redis)
        return id_list

    return []
