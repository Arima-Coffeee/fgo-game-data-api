import orjson
from redis.asyncio import Redis  # type: ignore
from sqlalchemy.ext.asyncio import AsyncConnection

from ...core.basic import get_basic_servant
from ...core.utils import get_nice_trait
from ...schemas.common import Language, NiceTrait, Region
from ...schemas.gameenums import COND_TYPE_NAME
from ...schemas.nice import (
    EnemySkill,
    NiceEquip,
    SupportServant,
    SupportServantEquip,
    SupportServantLimit,
    SupportServantMisc,
    SupportServantRelease,
    SupportServantScript,
    SupportServantTd,
)
from ...schemas.raw import NpcFollower, NpcFollowerRelease, NpcSvtEquip, NpcSvtFollower
from .nice import get_nice_equip_model
from .skill import MultipleNiceSkills, SkillSvt, get_multiple_nice_skills
from .td import MultipleNiceTds, TdSvt, get_multiple_nice_tds


def get_nice_follower_release(
    npcFollowerRelease: NpcFollowerRelease,
) -> SupportServantRelease:
    return SupportServantRelease(
        type=COND_TYPE_NAME[npcFollowerRelease.condType],
        targetId=npcFollowerRelease.condTargetId,
        value=npcFollowerRelease.condValue,
    )


def get_nice_follower_traits(followerIndividuality: str) -> list[NiceTrait]:
    if followerIndividuality == "NONE":
        return []

    return [get_nice_trait(trait) for trait in orjson.loads(followerIndividuality)]


def get_nice_follower_skills(
    svt: NpcSvtFollower, all_skills: MultipleNiceSkills
) -> EnemySkill:
    return EnemySkill(
        skillId1=svt.skillId1,
        skillId2=svt.skillId2,
        skillId3=svt.skillId3,
        skill1=all_skills.get(SkillSvt(svt.skillId1, svt.svtId), None),
        skill2=all_skills.get(SkillSvt(svt.skillId2, svt.svtId), None),
        skill3=all_skills.get(SkillSvt(svt.skillId3, svt.svtId), None),
        skillLv1=svt.skillLv1,
        skillLv2=svt.skillLv2,
        skillLv3=svt.skillLv3,
    )


def get_nice_follower_td(
    svt: NpcSvtFollower, all_nps: MultipleNiceTds
) -> SupportServantTd:
    return SupportServantTd(
        noblePhantasmId=svt.treasureDeviceId,
        noblePhantasm=all_nps.get(TdSvt(svt.treasureDeviceId, svt.svtId), None),
        noblePhantasmLv=svt.treasureDeviceLv,
    )


def get_nice_follower_limit(npcSvtFollower: NpcSvtFollower) -> SupportServantLimit:
    return SupportServantLimit(limitCount=npcSvtFollower.limitCount)


def get_nice_follower_equip(
    npcSvtEquip: NpcSvtEquip, all_equips: dict[int, NiceEquip]
) -> SupportServantEquip:
    return SupportServantEquip(
        equip=all_equips[npcSvtEquip.svtId],
        lv=npcSvtEquip.lv,
        limitCount=npcSvtEquip.limitCount,
    )


def get_nice_follower_misc(
    npcFollower: NpcFollower, npcSvtFollower: NpcSvtFollower
) -> SupportServantMisc:
    return SupportServantMisc(
        followerFlag=npcFollower.flag,
        svtFollowerFlag=npcSvtFollower.flag,
    )


def get_nice_follower_script(npcScript: str) -> SupportServantScript:
    script = SupportServantScript()
    try:
        parsed = orjson.loads(npcScript)

        if "dispLimitCount" in parsed:
            script.dispLimitCount = int(parsed["dispLimitCount"])
    except orjson.JSONDecodeError:  # pragma: no cover
        pass

    return script


async def get_nice_support_servant(
    redis: Redis,
    region: Region,
    npcFollower: NpcFollower,
    npcFollowerRelease: list[NpcFollowerRelease],
    npcSvtFollower: NpcSvtFollower,
    npcSvtEquip: list[NpcSvtEquip],
    all_skills: MultipleNiceSkills,
    all_tds: MultipleNiceTds,
    all_equips: dict[int, NiceEquip],
    lang: Language,
) -> SupportServant:
    npcScript = get_nice_follower_script(npcFollower.npcScript)
    npcLimit = (
        npcScript.dispLimitCount
        if npcScript.dispLimitCount
        else npcSvtFollower.limitCount
    )

    return SupportServant(
        id=npcFollower.id,
        priority=npcFollower.priority,
        name=npcSvtFollower.name,
        svt=await get_basic_servant(
            redis, region, npcSvtFollower.svtId, npcLimit, lang
        ),
        releaseConditions=[
            get_nice_follower_release(release) for release in npcFollowerRelease
        ],
        lv=npcSvtFollower.lv,
        atk=npcSvtFollower.atk,
        hp=npcSvtFollower.hp,
        traits=get_nice_follower_traits(npcSvtFollower.individuality),
        skills=get_nice_follower_skills(npcSvtFollower, all_skills),
        noblePhantasm=get_nice_follower_td(npcSvtFollower, all_tds),
        equips=[get_nice_follower_equip(equip, all_equips) for equip in npcSvtEquip],
        script=npcScript,
        limit=get_nice_follower_limit(npcSvtFollower),
        misc=get_nice_follower_misc(npcFollower, npcSvtFollower),
    )


async def get_nice_support_servants(
    conn: AsyncConnection,
    redis: Redis,
    region: Region,
    npcFollower: list[NpcFollower],
    npcFollowerRelease: list[NpcFollowerRelease],
    npcSvtFollower: list[NpcSvtFollower],
    npcSvtEquip: list[NpcSvtEquip],
    lang: Language,
) -> list[SupportServant]:
    all_skill_ids: set[SkillSvt] = set()
    all_td_ids: set[TdSvt] = set()
    for npcSvt in npcSvtFollower:
        if npcSvt.treasureDeviceId != 0:
            all_td_ids.add(TdSvt(npcSvt.treasureDeviceId, npcSvt.svtId))
        for skill_id in [
            npcSvt.skillId1,
            npcSvt.skillId2,
            npcSvt.skillId3,
        ]:
            if skill_id != 0:
                all_skill_ids.add(SkillSvt(skill_id, npcSvt.svtId))

    all_skills = await get_multiple_nice_skills(conn, region, all_skill_ids, lang)
    all_tds = await get_multiple_nice_tds(conn, region, all_td_ids, lang)

    all_equip_ids = {equip.svtId for equip in npcSvtEquip}
    all_equips = {
        equip_id: await get_nice_equip_model(conn, region, equip_id, lang, lore=False)
        for equip_id in all_equip_ids
    }

    out_support_servants: list[SupportServant] = []
    for npc in npcFollower:
        svt_follower = next(svt for svt in npcSvtFollower if svt.id == npc.leaderSvtId)
        follower_release = [rel for rel in npcFollowerRelease if rel.id == npc.id]
        svt_equip = [equip for equip in npcSvtEquip if equip.id in npc.svtEquipIds]

        nice_support_servant = await get_nice_support_servant(
            redis=redis,
            region=region,
            npcFollower=npc,
            npcFollowerRelease=follower_release,
            npcSvtFollower=svt_follower,
            npcSvtEquip=svt_equip,
            all_skills=all_skills,
            all_tds=all_tds,
            all_equips=all_equips,
            lang=lang,
        )
        out_support_servants.append(nice_support_servant)

    return out_support_servants
