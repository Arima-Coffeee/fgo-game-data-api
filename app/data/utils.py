from typing import Type, TypeVar

import orjson
from pydantic import DirectoryPath

from ..schemas.base import BaseModelORJson
from ..schemas.raw import (
    MstAi,
    MstAiAct,
    MstBuff,
    MstClassRelationOverwrite,
    MstCombineCostume,
    MstCombineLimit,
    MstCombineSkill,
    MstCommandCode,
    MstCommandCodeSkill,
    MstEquip,
    MstEquipSkill,
    MstEvent,
    MstEventMissionCondition,
    MstEventMissionConditionDetail,
    MstFunc,
    MstItem,
    MstShop,
    MstShopRelease,
    MstShopScript,
    MstSkill,
    MstSkillLv,
    MstSvt,
    MstSvtAppendPassiveSkill,
    MstSvtComment,
    MstSvtCostume,
    MstSvtExtra,
    MstSvtLimitAdd,
    MstSvtPassiveSkill,
    MstSvtSkill,
    MstSvtTreasureDevice,
    MstSvtVoice,
    MstTreasureDevice,
    MstTreasureDeviceLv,
    MstVoice,
    MstWar,
)


PydanticModel = TypeVar("PydanticModel", bound=BaseModelORJson)


MODEL_FILE_NAME: dict[Type[BaseModelORJson], str] = {
    MstEvent: "mstEvent",
    MstShop: "mstShop",
    MstSkill: "mstSkill",
    MstSvt: "mstSvt",
    MstSvtLimitAdd: "mstSvtLimitAdd",
    MstSvtComment: "mstSvtComment",
    MstSvtExtra: "mstSvtExtra",
    MstSvtSkill: "mstSvtSkill",
    MstShopRelease: "mstShopRelease",
    MstShopScript: "mstShopScript",
    MstWar: "mstWar",
    MstEventMissionCondition: "mstEventMissionCondition",
    MstEventMissionConditionDetail: "mstEventMissionConditionDetail",
    MstBuff: "mstBuff",
    MstClassRelationOverwrite: "mstClassRelationOverwrite",
    MstItem: "mstItem",
    MstCombineSkill: "mstCombineSkill",
    MstCombineLimit: "mstCombineLimit",
    MstCombineCostume: "mstCombineCostume",
    MstSvtCostume: "mstSvtCostume",
    MstAi: "mstAi",
    MstFunc: "mstFunc",
    MstBuff: "mstBuff",
    MstCommandCode: "mstCommandCode",
    MstCommandCodeSkill: "mstCommandCodeSkill",
    MstEquip: "mstEquip",
    MstEquipSkill: "mstEquipSkill",
    MstFunc: "mstFunc",
    MstSkillLv: "mstSkillLv",
    MstSvtAppendPassiveSkill: "mstSvtAppendPassiveSkill",
    MstSvtPassiveSkill: "mstSvtPassiveSkill",
    MstAiAct: "mstAiAct",
    MstTreasureDevice: "mstTreasureDevice",
    MstTreasureDeviceLv: "mstTreasureDeviceLv",
    MstSvtTreasureDevice: "mstSvtTreasureDevice",
    MstSvtVoice: "mstSvtVoice",
    MstVoice: "mstVoice",
}


def load_master_data(
    gamedata_path: DirectoryPath, model: Type[PydanticModel]
) -> list[PydanticModel]:
    file_name = MODEL_FILE_NAME[model]
    with open(gamedata_path / "master" / f"{file_name}.json", "rb") as fp:
        data = orjson.loads(fp.read())
    return [model.parse_obj(item) for item in data]
