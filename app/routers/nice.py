from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query

from ..data import gamedata
from ..data.models.common import Region, Settings
from ..data.models.raw import (
    BuffEntityNoReverse,
    FunctionEntityNoReverse,
    FuncType,
    SkillEntityNoReverse,
    SvtType,
    TdEntityNoReverse,
)
from ..data.models.nice import (
    ASSET_URL,
    ATTRIBUTE_NAME,
    BUFF_TYPE_NAME,
    CARD_TYPE_NAME,
    CLASS_NAME,
    ENEMY_FUNC_SIGNATURE,
    FUNC_APPLYTARGET_NAME,
    FUNC_TARGETTYPE_NAME,
    FUNC_TYPE_NAME,
    GENDER_NAME,
    TRAIT_NAME,
    NiceEquip,
    NiceServant,
    SvtClass,
    Trait,
)


FORMATTING_BRACKETS = {"[g][o]": "", "[/o][/g]": "", " [{0}] ": " ", "[{0}]": ""}


settings = Settings()


def strip_formatting_brackets(detail_string: str) -> str:
    for k, v in FORMATTING_BRACKETS.items():
        detail_string = detail_string.replace(k, v)
    return detail_string


def get_safe(input_dict: Dict[Any, Any], key: Any) -> Any:
    """
    A dict getter that returns the key if it's not found in the dict.
    The enums mapping is or will be incomplete eventually.
    """
    return input_dict.get(key, key)


def get_traits_list(input_idv: List[int]) -> List[Union[Trait, int]]:
    return [get_safe(TRAIT_NAME, item) for item in input_idv]


def parse_dataVals(datavals: str, functype: int) -> Dict[str, Union[int, str]]:
    output: Dict[str, Union[int, str]] = {}
    if datavals != "[]":
        array = datavals.replace("[", "").replace("]", "").split(",")
        for i, arrayi in enumerate(array):
            text = ""
            value: Union[int, str] = 0
            try:
                value = int(arrayi)
                if functype in [
                    FuncType.DAMAGE_NP_INDIVIDUAL,
                    FuncType.DAMAGE_NP_STATE_INDIVIDUAL,
                    FuncType.DAMAGE_NP_STATE_INDIVIDUAL_FIX,
                ]:
                    if i == 0:
                        text = "Rate"
                    elif i == 1:
                        text = "Value"
                    elif i == 2:
                        text = "Target"
                    elif i == 3:
                        text = "Correction"
                elif functype in [FuncType.ADD_STATE, FuncType.ADD_STATE_SHORT]:
                    if i == 0:
                        text = "Rate"
                    elif i == 1:
                        text = "Turn"
                    elif i == 2:
                        text = "Count"
                    elif i == 3:
                        text = "Value"
                    elif i == 4:
                        text = "UseRate"
                    elif i == 5:
                        text = "Value2"
                elif functype == FuncType.SUB_STATE:
                    if i == 0:
                        text = "Rate"
                    elif i == 1:
                        text = "Value"
                    elif i == 2:
                        text = "Value2"
                else:
                    if i == 0:
                        text = "Rate"
                    elif i == 1:
                        text = "Value"
                    elif i == 2:
                        text = "Target"
            except ValueError:
                array2 = arrayi.split(":")
                if len(array2) > 1:
                    text = array2[0]
                    try:
                        value = int(array2[1])
                    except ValueError:
                        value = array2[1]
                else:
                    raise HTTPException(
                        status_code=500, detail=f"Can't parse datavals: {datavals}"
                    )
            if text != "":
                output[text] = value
    return output


def is_level_dependent(function: Dict[str, Any]) -> Any:
    """Check for identical svalss dicts"""
    # not the best response type because of the Any in Dict
    return (
        function["svals"]
        == function.get("svals2")
        == function.get("svals3")
        == function.get("svals4")
        == function.get("svals5")
    )


def is_overcharge_dependent(function: Dict[str, Any]) -> bool:
    """Check for invariant dataVals arrays within all the svals"""
    isOvercharge = True
    svalsCount = len([key for key in function.keys() if key.startswith("svals")])
    for vali in range(1, svalsCount + 1):
        valName = f"svals{vali}" if vali >= 2 else "svals"
        if valName in function:
            for valValues in function[valName].values():
                isOvercharge &= len(set(valValues)) == 1
    return isOvercharge


def is_constant(function: Dict[str, Any]) -> bool:
    """Check if function is neither level nor overcharge dependent"""
    return is_overcharge_dependent(function) and is_level_dependent(function)


def combine_svals_overcharge(function: Dict[str, Any]) -> Dict[str, Any]:
    """Create svals item that varies with overcharge instead of level"""
    svals: Dict[str, List[Any]] = {}
    for valType in function["svals"]:
        svals[valType] = []
        for vali in range(1, 6):
            valName = f"svals{vali}" if vali >= 2 else "svals"
            svals[valType].append(function[valName][valType][0])
    return svals


def categorize_functions(
    combinedFunctionList: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Categorize functions based on how their dataVals change"""
    functions: Dict[str, List[Dict[str, Any]]] = {
        "level": [],
        "overcharge": [],
        "constant": [],
        "other": [],
    }
    if combinedFunctionList:
        svalsCount = len(
            [key for key in combinedFunctionList[0].keys() if key.startswith("svals")]
        )
        if svalsCount > 1:
            # TD combinedFunc
            for combinedFunc in combinedFunctionList:
                if is_constant(combinedFunc):
                    for vali in range(2, 6):
                        combinedFunc.pop(f"svals{vali}")
                    functions["constant"].append(combinedFunc)
                elif is_level_dependent(combinedFunc):
                    for vali in range(2, 6):
                        combinedFunc.pop(f"svals{vali}")
                    functions["level"].append(combinedFunc)
                elif is_overcharge_dependent(combinedFunc):
                    svals = combine_svals_overcharge(combinedFunc)
                    for vali in range(2, 6):
                        combinedFunc.pop(f"svals{vali}")
                    combinedFunc["svals"] = svals
                    functions["overcharge"].append(combinedFunc)
                else:
                    functions["other"].append(combinedFunc)
        else:
            # Skill combinedFunc
            for combinedFunc in combinedFunctionList:
                if is_overcharge_dependent(combinedFunc):
                    # check for constant value in the datavals arrays
                    functions["constant"].append(combinedFunc)
                else:
                    functions["level"].append(combinedFunc)

    functions = {k: v for k, v in functions.items() if v}
    return functions


def get_nice_buff(buffEntity: BuffEntityNoReverse, region: Region) -> Dict[str, Any]:
    buffInfo: Dict[str, Any] = {}
    buffInfo["id"] = buffEntity.mstBuff.id
    buffInfo["name"] = buffEntity.mstBuff.name
    buffInfo["detail"] = buffEntity.mstBuff.detail
    iconId = buffEntity.mstBuff.iconId
    if iconId != 0:
        buffInfo["icon"] = ASSET_URL["buffIcon"].format(
            base_url=settings.asset_url, region=region, item_id=iconId
        )
    buffInfo["type"] = get_safe(BUFF_TYPE_NAME, buffEntity.mstBuff.type)
    buffInfo["vals"] = get_traits_list(buffEntity.mstBuff.vals)
    buffInfo["tvals"] = get_traits_list(buffEntity.mstBuff.tvals)
    buffInfo["ckOpIndv"] = get_traits_list(buffEntity.mstBuff.ckOpIndv)
    buffInfo["ckSelfIndv"] = get_traits_list(buffEntity.mstBuff.ckSelfIndv)
    return buffInfo


def get_nice_base_function(
    function: FunctionEntityNoReverse, region: Region
) -> Dict[str, Any]:
    functionInfo: Dict[str, Any] = {}
    functionInfo["funcId"] = function.mstFunc.id
    functionInfo["funcPopupText"] = function.mstFunc.popupText
    functionInfo["functvals"] = get_traits_list(function.mstFunc.tvals)
    funcPopupIconId = function.mstFunc.popupIconId
    if funcPopupIconId != 0:
        functionInfo["funcPopupIcon"] = ASSET_URL["buffIcon"].format(
            base_url=settings.asset_url, region=region, item_id=funcPopupIconId
        )
    functionInfo["funcType"] = get_safe(FUNC_TYPE_NAME, function.mstFunc.funcType)
    functionInfo["funcTargetTeam"] = get_safe(
        FUNC_APPLYTARGET_NAME, function.mstFunc.applyTarget
    )
    functionInfo["funcTargetType"] = get_safe(
        FUNC_TARGETTYPE_NAME, function.mstFunc.targetType
    )

    buffs = [get_nice_buff(buff, region) for buff in function.mstFunc.expandedVals]
    functionInfo["buffs"] = buffs
    return functionInfo


def get_nice_skill(
    skillEntity: SkillEntityNoReverse, svtId: int, region: Region
) -> Dict[str, Any]:
    nice_skill: Dict[str, Any] = {}
    nice_skill["id"] = skillEntity.mstSkill.id
    nice_skill["name"] = skillEntity.mstSkill.name
    iconId = skillEntity.mstSkill.iconId
    if iconId != 0:
        iconAtlas = 1 if iconId < 520 else 2
        nice_skill["icon"] = ASSET_URL["skillIcon"].format(
            base_url=settings.asset_url,
            region=region,
            atlas_id=iconAtlas,
            item_id=iconId,
        )
    nice_skill["detail"] = strip_formatting_brackets(
        skillEntity.mstSkillDetail[0].detail
    )

    chosenSvt = [item for item in skillEntity.mstSvtSkill if item.svtId == svtId]
    if chosenSvt:
        nice_skill["strengthStatus"] = chosenSvt[0].strengthStatus
        nice_skill["num"] = chosenSvt[0].num
        nice_skill["priority"] = chosenSvt[0].priority
        nice_skill["condQuestId"] = chosenSvt[0].condQuestId
        nice_skill["condQuestPhase"] = chosenSvt[0].condQuestPhase

    nice_skill["coolDown"] = [skillEntity.mstSkillLv[0].chargeTurn]

    combinedFunctionList: List[Dict[str, Any]] = []

    # Build the first function item and add the first svals value
    player_funcis: List[int] = []
    for funci in range(len(skillEntity.mstSkillLv[0].funcId)):
        function = skillEntity.mstSkillLv[0].expandedFuncId[funci]
        functionInfo = get_nice_base_function(function, region)
        functionSignature = (
            functionInfo["funcTargetType"],
            functionInfo["funcTargetTeam"],
        )
        if functionSignature not in ENEMY_FUNC_SIGNATURE:
            player_funcis.append(funci)
            dataVals = parse_dataVals(
                skillEntity.mstSkillLv[0].svals[funci], function.mstFunc.funcType
            )
            svals: Dict[str, List[Union[str, int]]] = {}
            for key, value in dataVals.items():
                svals[key] = [value]
            functionInfo["svals"] = svals
            combinedFunctionList.append(functionInfo)

    # Add the remaining cooldown and svals values
    for skillLv in skillEntity.mstSkillLv[1:]:
        nice_skill["coolDown"].append(skillLv.chargeTurn)
        for combinedfunci, funci in enumerate(player_funcis):
            dataVals = parse_dataVals(
                skillLv.svals[funci], skillLv.expandedFuncId[funci].mstFunc.funcType
            )
            for key, value in dataVals.items():
                combinedFunctionList[combinedfunci]["svals"][key].append(value)

    nice_skill["functions"] = categorize_functions(combinedFunctionList)

    return nice_skill


def get_nice_td(
    tdEntity: TdEntityNoReverse, svtId: int, region: Region
) -> Dict[str, Any]:
    nice_td: Dict[str, Any] = {}
    nice_td["id"] = tdEntity.mstTreasureDevice.id
    nice_td["name"] = tdEntity.mstTreasureDevice.name
    nice_td["rank"] = tdEntity.mstTreasureDevice.rank
    nice_td["typeText"] = tdEntity.mstTreasureDevice.typeText
    nice_td["npNpGain"] = tdEntity.mstTreasureDeviceLv[0].tdPoint / 10000
    nice_td["detail"] = strip_formatting_brackets(
        tdEntity.mstTreasureDeviceDetail[0].detail
    )

    chosenSvt = [item for item in tdEntity.mstSvtTreasureDevice if item.svtId == svtId]
    nice_td["strengthStatus"] = chosenSvt[0].strengthStatus
    nice_td["num"] = chosenSvt[0].num
    nice_td["priority"] = chosenSvt[0].priority
    nice_td["condQuestId"] = chosenSvt[0].condQuestId
    nice_td["condQuestPhase"] = chosenSvt[0].condQuestPhase
    nice_td["card"] = CARD_TYPE_NAME[chosenSvt[0].cardId]
    nice_td["npDistribution"] = chosenSvt[0].damage

    combinedFunctionList: List[Dict[str, Any]] = []

    # Build the first function item and add the first svals value
    player_funcis: List[int] = []
    for funci in range(len(tdEntity.mstTreasureDeviceLv[0].funcId)):
        function = tdEntity.mstTreasureDeviceLv[0].expandedFuncId[funci]
        functionInfo = get_nice_base_function(function, region)
        functionSignature = (
            functionInfo["funcTargetType"],
            functionInfo["funcTargetTeam"],
        )
        if functionSignature not in ENEMY_FUNC_SIGNATURE:
            player_funcis.append(funci)
            for vali in range(1, 6):
                valName = f"svals{vali}" if vali >= 2 else "svals"
                dataVals = parse_dataVals(
                    getattr(tdEntity.mstTreasureDeviceLv[0], valName)[funci],
                    function.mstFunc.funcType,
                )
                svals: Dict[str, List[Union[str, int]]] = {}
                for key, value in dataVals.items():
                    svals[key] = [value]
                functionInfo[valName] = svals
            combinedFunctionList.append(functionInfo)

    # Add the remaining svals values
    for tdLv in tdEntity.mstTreasureDeviceLv[1:]:
        for combinedfunci, funci in enumerate(player_funcis):
            for vali in range(1, 6):
                valName = f"svals{vali}" if vali >= 2 else "svals"
                dataVals = parse_dataVals(
                    getattr(tdLv, valName)[funci],
                    tdLv.expandedFuncId[funci].mstFunc.funcType,
                )
                for key, value in dataVals.items():
                    combinedFunctionList[combinedfunci][valName][key].append(value)

    nice_td["functions"] = categorize_functions(combinedFunctionList)

    return nice_td


def get_nice_servant(region: Region, item_id: int) -> Dict[str, Any]:
    raw_data = gamedata.get_servant_entity(region, item_id, True)
    nice_data: Dict[str, Any] = {}

    nice_data["id"] = raw_data.mstSvt.id
    nice_data["collectionNo"] = raw_data.mstSvt.collectionNo
    nice_data["name"] = raw_data.mstSvt.name
    nice_data["gender"] = GENDER_NAME[raw_data.mstSvt.genderType]
    nice_data["attribute"] = ATTRIBUTE_NAME[raw_data.mstSvt.attri]
    nice_data["className"] = CLASS_NAME[raw_data.mstSvt.classId]
    nice_data["cost"] = raw_data.mstSvt.cost
    nice_data["instantDeathChance"] = raw_data.mstSvt.deathRate / 1000
    nice_data["starGen"] = raw_data.mstSvt.starRate / 1000
    nice_data["traits"] = [
        get_safe(TRAIT_NAME, item)
        for item in sorted(raw_data.mstSvt.individuality)
        if item != item_id
    ]

    charaGraph: Dict[str, Dict[int, str]] = {}
    if raw_data.mstSvt.type == SvtType.NORMAL:
        charaGraph["ascension"] = {
            i: ASSET_URL[f"charaGraph{i}"].format(
                base_url=settings.asset_url, region=region, item_id=item_id
            )
            for i in range(1, 5)
        }
        costume_ids = [
            item.battleCharaId
            for item in raw_data.mstSvtLimitAdd
            if item.limitCount == 11
        ]
        for costume_id in costume_ids:
            charaGraph["costume"] = {
                costume_id: ASSET_URL["charaGraphcostume"].format(
                    base_url=settings.asset_url, region=region, item_id=costume_id
                )
            }
    elif raw_data.mstSvt.type == SvtType.SERVANT_EQUIP:
        charaGraph["equip"] = {
            item_id: ASSET_URL["charaGraphEquip"].format(
                base_url=settings.asset_url, region=region, item_id=item_id
            )
        }
    nice_data["extraAssets"] = {"charaGraph": charaGraph}

    nice_data["starAbsorb"] = raw_data.mstSvtLimit[0].criticalWeight
    nice_data["rarity"] = raw_data.mstSvtLimit[0].rarity
    lvMax = max([item.lvMax for item in raw_data.mstSvtLimit])
    nice_data["lvMax"] = lvMax
    if raw_data.mstSvt.type == SvtType.NORMAL:
        lvMax = 100
    atkMax = raw_data.mstSvtLimit[0].atkMax
    atkBase = raw_data.mstSvtLimit[0].atkBase
    hpMax = raw_data.mstSvtLimit[0].hpMax
    hpBase = raw_data.mstSvtLimit[0].hpBase
    growthCurve = raw_data.mstSvt.expType
    growthCurveValues = [
        gamedata.masters[region].mstSvtExpId[growthCurve][lv].curve
        for lv in range(1, lvMax + 1)
    ]
    atkGrowth = [
        atkBase + (atkMax - atkBase) * curve // 1000 for curve in growthCurveValues
    ]
    hpGrowth = [
        hpBase + (hpMax - hpBase) * curve // 1000 for curve in growthCurveValues
    ]

    nice_data["growthCurve"] = growthCurve
    nice_data["atkMax"] = atkMax
    nice_data["atkBase"] = atkBase
    nice_data["hpMax"] = hpMax
    nice_data["hpBase"] = hpBase
    nice_data["atkGrowth"] = atkGrowth
    nice_data["hpGrowth"] = hpGrowth

    nice_data["cards"] = [CARD_TYPE_NAME[item] for item in raw_data.mstSvt.cardIds]
    cardsDistribution = {item.cardId: item.normalDamage for item in raw_data.mstSvtCard}
    if cardsDistribution:
        nice_data["hitsDistribution"] = {
            "arts": cardsDistribution[1],
            "buster": cardsDistribution[2],
            "quick": cardsDistribution[3],
            "extra": cardsDistribution[4],
        }

    # Filter out dummy TDs that are probably used by enemy servants that don't use their NPs
    actualTDs: List[TdEntityNoReverse] = [
        item
        for item in raw_data.mstTreasureDevice
        if item.mstTreasureDevice.id != 100 and item.mstTreasureDevice.id % 100 != 99
    ]
    if actualTDs:
        nice_data["npGain"] = {
            "buster": actualTDs[0].mstTreasureDeviceLv[0].tdPointB / 10000,
            "arts": actualTDs[0].mstTreasureDeviceLv[0].tdPointA / 10000,
            "quick": actualTDs[0].mstTreasureDeviceLv[0].tdPointQ / 10000,
            "extra": actualTDs[0].mstTreasureDeviceLv[0].tdPointEx / 10000,
            "defence": actualTDs[0].mstTreasureDeviceLv[0].tdPointDef / 10000,
        }

    ascenionMaterials = {}
    for combineLimit in raw_data.mstCombineLimit:
        itemLists = [
            {
                "id": item,
                "name": gamedata.masters[region].mstItemId[item].name,
                "icon": ASSET_URL["items"].format(
                    base_url=settings.asset_url, region=region, item_id=item
                ),
                "amount": amount,
            }
            for item, amount in zip(combineLimit.itemIds, combineLimit.itemNums)
        ]
        ascenionMaterials[combineLimit.svtLimit + 1] = {
            "items": itemLists,
            "qp": combineLimit.qp,
        }
    nice_data["ascenionMaterials"] = ascenionMaterials

    skillMaterials = {}
    for combineSkill in raw_data.mstCombineSkill:
        itemLists = [
            {
                "id": item,
                "name": gamedata.masters[region].mstItemId[item].name,
                "icon": ASSET_URL["items"].format(
                    base_url=settings.asset_url, region=region, item_id=item
                ),
                "amount": amount,
            }
            for item, amount in zip(combineSkill.itemIds, combineSkill.itemNums)
        ]
        skillMaterials[combineSkill.skillLv] = {
            "items": itemLists,
            "qp": combineSkill.qp,
        }
    nice_data["skillMaterials"] = skillMaterials

    nice_data["skills"] = [
        get_nice_skill(skill, item_id, region) for skill in raw_data.mstSkill
    ]
    nice_data["classPassive"] = [
        get_nice_skill(skill, item_id, region)
        for skill in raw_data.mstSvt.expandedClassPassive
    ]
    nice_data["NPs"] = [get_nice_td(td, item_id, region) for td in actualTDs]
    return nice_data


router = APIRouter()


@router.get(
    "/{region}/servant/search",
    summary="Find and get servant data",
    response_description="Servant Entity",
    response_model=List[NiceServant],
    response_model_exclude_unset=True,
)
async def find_servant(
    region: Region,
    name: Optional[str] = None,
    trait: List[Union[Trait, int]] = Query(None),
    className: List[SvtClass] = Query(None),
):
    """
    Search and return the list of matched nice servant entities.
    """
    if trait or className or name:
        matches = gamedata.search_servant(region, name, trait, className)
        return [get_nice_servant(region, item) for item in matches]
    else:
        raise HTTPException(status_code=400, detail="No query found")


@router.get(
    "/{region}/servant/{item_id}",
    summary="Get servant data",
    response_description="Servant Entity",
    response_model=NiceServant,
    response_model_exclude_unset=True,
)
async def get_servant(region: Region, item_id: int):
    """
    Get servant info from ID

    If the given ID is a servants's collectionNo, the corresponding servant data is returned.
    Otherwise, it will look up the actual ID field.
    """
    if item_id in gamedata.masters[region].mstSvtServantCollectionNo:
        item_id = gamedata.masters[region].mstSvtServantCollectionNo[item_id]
    if item_id in gamedata.masters[region].mstSvtServantCollectionNo.values():
        return get_nice_servant(region, item_id)
    else:
        raise HTTPException(status_code=404, detail="Servant not found")


@router.get(
    "/{region}/equip/{item_id}",
    summary="Get CE data",
    response_description="CE Entity",
    response_model=NiceEquip,
    response_model_exclude_unset=True,
)
async def get_equip(region: Region, item_id: int):
    """
    Get servant info from ID

    If the given ID is a servants's collectionNo, the corresponding servant data is returned.
    Otherwise, it will look up the actual ID field.
    """
    if item_id in gamedata.masters[region].mstSvtEquipCollectionNo:
        item_id = gamedata.masters[region].mstSvtEquipCollectionNo[item_id]
    if item_id in gamedata.masters[region].mstSvtEquipCollectionNo.values():
        return get_nice_servant(region, item_id)
    else:
        raise HTTPException(status_code=404, detail="Equip not found")
