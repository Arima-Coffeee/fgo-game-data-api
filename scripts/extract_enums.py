import argparse

from black import FileMode, format_str


PYTHON_NAME_JSON_NAME_OVERRIDE = {
    "UPPER": "upper_",
    "LOWER": "lower_",
    "SELF": "self_",
    "CENTER": "center_",
    "SET": "set_",
    "NAME": "name_",
}


def convert_name(name: str) -> str:
    if name in PYTHON_NAME_JSON_NAME_OVERRIDE:
        return PYTHON_NAME_JSON_NAME_OVERRIDE[name]
    else:
        words = name.split("_")
        return "".join([words[0].lower()] + [w.title() for w in words[1:]])


def enum_to_dict(cstype: list[str]) -> dict[int, str]:
    enum_dict: dict[int, str] = {}
    for enum_item in cstype:
        enum_item = enum_item.split(";")[0]
        splitted = enum_item.split(" = ")
        i = int(splitted[1])
        enum_item = splitted[0].split()[-1].strip()
        enum_dict[i] = enum_item
    return {k: enum_dict[k] for k in sorted(enum_dict.keys(), key=abs)}


def out_intenum(input_dict: dict[int, str], className: str) -> list[str]:
    intenum_lines = [f"class {className}(IntEnum):\n"]
    for enumint, enumstr in input_dict.items():
        intenum_lines.append(f"    {enumstr} = {enumint}\n")
    return intenum_lines


EXTRA_STR_NAME = {
    "NiceStatusRank": {-1: "UNKNOWN"},
    "NiceSvtFlag": {0: "NORMAL", 63: "GOETIA", 64: "MAT_DROP_RATE_UP_CE"},
    "NiceAiActNum": {-9999: "UNKNOWN"},
    "NicePurchaseType": {13: "KIARA_PUNISHER_RESET"},
}


STR_NAME_OVERRIDE = {
    "NiceCardType": {"addattack": "extra"},
    "NiceGender": {"other": "unknown"},
    "NiceStatusRank": {
        "a": "A",
        "aPlus": "A+",
        "aPlus2": "A++",
        "aMinus": "A-",
        "aPlus3": "A+++",
        "b": "B",
        "bPlus": "B+",
        "bPlus2": "B++",
        "bMinus": "B-",
        "bPlus3": "B+++",
        "c": "C",
        "cPlus": "C+",
        "cPlus2": "C++",
        "cMinus": "C-",
        "cPlus3": "C+++",
        "d": "D",
        "dPlus": "D+",
        "dPlus2": "D++",
        "dMinus": "D-",
        "dPlus3": "D+++",
        "e": "E",
        "ePlus": "E+",
        "ePlus2": "E++",
        "eMinus": "E-",
        "ePlus3": "E+++",
        "ex": "EX",
        "question": "?",
        "none": "None",
        "unknown": "Unknown",
    },
}


def out_strenum(
    input_dict: dict[int, str], nice_class: str, nice_class_title: str
) -> list[str]:
    strenum_lines = [
        f"class {nice_class}(str, Enum):\n",
        f'    """{nice_class_title}"""\n',
        "\n",
    ]
    for enumstr in list(input_dict.values()) + list(
        EXTRA_STR_NAME.get(nice_class, {}).values()
    ):
        json_name = convert_name(enumstr)
        str_name = (
            STR_NAME_OVERRIDE.get(nice_class, {})
            .get(json_name, json_name)
            .removesuffix("_")
        )
        strenum_lines.append(f'    {json_name} = "{str_name}"\n')
    return strenum_lines


EXTRA_ENUM_DICT = {"NiceEventType": {21: "COMEBACK_CAMPAIGN"}}


def out_enumdict(
    input_dict: dict[int, str], nice_class: str, dict_name: str
) -> list[str]:
    strenumdict_lines = [f"{dict_name}: dict[int, {nice_class}] = {{\n"]
    for enumint, enumstr in (
        list(input_dict.items())
        + list(EXTRA_STR_NAME.get(nice_class, {}).items())
        + list(EXTRA_ENUM_DICT.get(nice_class, {}).items())
    ):
        json_name = convert_name(enumstr)
        strenumdict_lines.append(f"    {enumint}: {nice_class}.{json_name},\n")
    strenumdict_lines.append("}\n")
    return strenumdict_lines


def cs_enums_to_lines(
    cs_enums: list[str],
    raw_class: str,
    nice_class: str,
    nice_class_title: str,
    dict_name: str,
) -> list[str]:
    enum_dict = enum_to_dict(cs_enums)
    if raw_class == "DataValsType":
        return out_intenum(enum_dict, raw_class)
    else:
        return (
            out_intenum(enum_dict, raw_class)
            + ["\n"] * 2
            + out_strenum(enum_dict, nice_class, nice_class_title)
            + ["\n"] * 2
            + out_enumdict(enum_dict, nice_class, dict_name)
        )


def cs_enum_to_ts(cs_enums: list[str], nice_class: str) -> list[str]:
    enum_dict = enum_to_dict(cs_enums)
    ts_enum_lines = [f"export enum {nice_class} {{\n"]
    for enumstr in list(enum_dict.values()) + list(
        EXTRA_STR_NAME.get(nice_class, {}).values()
    ):
        json_name = convert_name(enumstr)
        str_name = (
            STR_NAME_OVERRIDE.get(nice_class, {})
            .get(json_name, json_name)
            .removesuffix("_")
        )
        ts_enum_lines.append(f'    {enumstr} = "{str_name}",\n')
    ts_enum_lines.append("}\n")
    return ts_enum_lines


ENUMS: list[tuple[str, str, str, str, str]] = [
    ("Gender.Type", "GenderType", "NiceGender", "Gender Enum", "GENDER_TYPE_NAME"),
    ("SvtType.Type", "SvtType", "NiceSvtType", "Servant Type Enum", "SVT_TYPE_NAME"),
    (
        "ServantEntity.FlagField",
        "SvtFlag",
        "NiceSvtFlag",
        "Servant Flag Enum",
        "SVT_FLAG_NAME",
    ),
    (
        "FuncList.TYPE",
        "FuncType",
        "NiceFuncType",
        "Function Type Enum",
        "FUNC_TYPE_NAME",
    ),
    (
        "Target.TYPE",
        "FuncTargetType",
        "NiceFuncTargetType",
        "Function Target Type Enum",
        "FUNC_TARGETTYPE_NAME",
    ),
    ("BuffList.TYPE", "BuffType", "NiceBuffType", "Buff Type Enum", "BUFF_TYPE_NAME"),
    (
        "BuffList.ACTION",
        "BuffAction",
        "NiceBuffAction",
        "Buff Action Type Enum",
        "BUFF_ACTION_NAME",
    ),
    (
        "BuffList.LIMIT",
        "BuffLimit",
        "NiceBuffLimit",
        "Buff Limit Enum",
        "BUFF_LIMIT_NAME",
    ),
    (
        "DataVals.TYPE",
        "DataValsType",
        "NiceDataValsType",
        "DataVals Enum",
        "DATA_VALS_TYPE_NAME",
    ),
    (
        "ClassRelationOverwriteEntity",
        "ClassRelationOverwriteType",
        "NiceClassRelationOverwriteType",
        "Class Relation Overwrite Type Enum",
        "CLASS_OVERWRITE_NAME",
    ),
    ("ItemType.Type", "ItemType", "NiceItemType", "Item Type Enum", "ITEM_TYPE_NAME"),
    ("Gift.Type", "GiftType", "NiceGiftType", "Gift Type Enum", "GIFT_TYPE_NAME"),
    ("ShopType.Type", "ShopType", "NiceShopType", "Shop Type Enum", "SHOP_TYPE_NAME"),
    ("PayType.Type", "PayType", "NicePayType", "Pay Type Enum", "PAY_TYPE_NAME"),
    (
        "GamePurchase.Type",
        "PurchaseType",
        "NicePurchaseType",
        "Purchase Type Enum",
        "PURCHASE_TYPE_NAME",
    ),
    (
        "BattleCommand.TYPE",
        "CardType",
        "NiceCardType",
        "Card Type Enum",
        "CARD_TYPE_NAME",
    ),
    (
        "CondType.Kind",
        "CondType",
        "NiceCondType",
        "Condition Type Enum",
        "COND_TYPE_NAME",
    ),
    (
        "VoiceCondType.Type",
        "VoiceCondType",
        "NiceVoiceCondType",
        "Voice Condition Type Enum",
        "VOICE_COND_NAME",
    ),
    (
        "SvtVoiceType.Type",
        "SvtVoiceType",
        "NiceSvtVoiceType",
        "Servant Voice Type Enum",
        "VOICE_TYPE_NAME",
    ),
    (
        "QuestEntity.enType",
        "QuestType",
        "NiceQuestType",
        "Quest Type Enum",
        "QUEST_TYPE_NAME",
    ),
    (
        "QuestEntity.ConsumeType",
        "QuestConsumeType",
        "NiceConsumeType",
        "Consume Type Enum",
        "QUEST_CONSUME_TYPE_NAME",
    ),
    (
        "QuestEntity.enAfterClear",
        "QuestAfterClearType",
        "NiceQuestAfterClearType",
        "Quest After Clear Enum",
        "QUEST_AFTER_CLEAR_NAME",
    ),
    (
        "QuestEntity.Flag",
        "QuestFlag",
        "NiceQuestFlag",
        "Quest Flag Enum",
        "Quest_FLAG_NAME",
    ),
    (
        "StatusRank.Kind",
        "StatusRank",
        "NiceStatusRank",
        "Status Rank Enum",
        "STATUS_RANK_NAME",
    ),
    (
        "GameEventType.TYPE",
        "EventType",
        "NiceEventType",
        "Event Type Enum",
        "EVENT_TYPE_NAME",
    ),
    (
        "WarEntity.Flag",
        "WarEntityFlag",
        "NiceWarFlag",
        "War Flag Enum",
        "WAR_FLAG_NAME",
    ),
    (
        "WarEntity.StartType",
        "WarEntityStartType",
        "NiceWarStartType",
        "War Start Type Enum",
        "WAR_START_TYPE_NAME",
    ),
    (
        "WarAddEntity.WarOverwriteType",
        "WarOverwriteType",
        "NiceWarOverwriteType",
        "War Overwrite Type Enum",
        "WAR_OVERWRITE_TYPE_NAME",
    ),
    ("Ai.COND", "AiCond", "NiceAiCond", "AI Cond Enum", "AI_COND_NAME"),
    (
        "AiAct.TYPE",
        "AiActType",
        "NiceAiActType",
        "AI Act Type Enum",
        "AI_ACT_TYPE_NAME",
    ),
    (
        "AiAct.TARGET",
        "AiActTarget",
        "NiceAiActTarget",
        "AI Act Target Enum",
        "AI_ACT_TARGET_NAME",
    ),
    ("Ai.ACT_NUM", "AiActNum", "NiceAiActNum", "AI Act Num Enum", "AI_ACT_NUM_NAME"),
    (
        "MissionType.Type",
        "MissionType",
        "NiceMissionType",
        "Mission Type Enum",
        "MISSION_TYPE_NAME",
    ),
    (
        "RewardType.Type",
        "MissionRewardType",
        "NiceMissionRewardType",
        "Mission Reward Type Enum",
        "MISSION_REWARD_TYPE_NAME",
    ),
    (
        "MissionProgressType.Type",
        "MissionProgressType",
        "NiceMissionProgressType",
        "Mission Progress Type Enum",
        "MISSION_PROGRESS_TYPE_NAME",
    ),
    (
        "BoxGachaEntity.Flag",
        "BoxGachaFlag",
        "NiceLotteryFlag",
        "Event Lottery Flag",
        "EVENT_LOTTERY_FLAG_NAME",
    ),
    ("BgmEntity.Flag", "BgmFlag", "NiceBgmFlag", "Bgm Flag", "BGM_FLAG_NAME"),
    (
        "ServantExceedEntity.FRAMETYPE",
        "SvtFrameType",
        "NiceSvtFrameType",
        "Servant Frame Type",
        "SERVANT_FRAME_TYPE_NAME",
    ),
    (
        "CommonConsumeEntity.CommonConsumeType",
        "CommonConsumeType",
        "NiceCommonConsumeType",
        "Common Consume Type",
        "COMMON_CONSUME_TYPE_NAME",
    ),
    (
        "EventRewardSceneEntity.Flag",
        "EventRewardSceneFlag",
        "NiceEventRewardSceneFlag",
        "Event Reward Scene Flag",
        "EVENT_REWARD_SCENE_FLAG",
    ),
]


cs_signatures: dict[str, str] = {f"public enum {enum[0]}": enum[0] for enum in ENUMS}


def main(dump_path: str, gameenums_path: str, typescript_path: str = "") -> None:
    print(f"Reading {dump_path} ...")
    with open(dump_path, "r", encoding="utf-8") as fp:
        lines = fp.readlines()

    all_cs_enums: dict[str, list[str]] = {}
    enum_lines: list[str] = []
    in_recording_signature = ""
    in_recording_mode = False

    for line in lines:
        if not in_recording_mode:
            for signature in cs_signatures:
                if line.startswith(signature):
                    in_recording_signature = cs_signatures[signature]
                    print(f"Found {in_recording_signature}")
                    enum_lines = []
                    in_recording_mode = True
                    continue
        elif line.startswith("}"):
            all_cs_enums[in_recording_signature] = enum_lines
            in_recording_mode = False
            continue
        else:
            if "public const" in line:
                enum_lines.append(line.strip())

    not_found = cs_signatures.values() - all_cs_enums.keys()
    for not_found_enum in not_found:
        print(f"Can't find {not_found_enum}")

    python_lines = [
        "# This file is auto-generated by extract_enums.py in the scripts folder.\n",
        "# You shouldn't edit this file directly.\n",
        "\n",
        "\n",
        "from enum import Enum, IntEnum\n",
        "\n",
        "\n",
    ]
    for cs_enum, raw_class, nice_class, nice_class_title, dict_name in ENUMS:
        python_lines += cs_enums_to_lines(
            all_cs_enums[cs_enum], raw_class, nice_class, nice_class_title, dict_name
        )
        if cs_enum != ENUMS[-1][0]:
            python_lines += ["\n"] * 2

    print(f"Writing {gameenums_path} ...")
    with open(gameenums_path, "w", encoding="utf-8", newline="") as fp:
        blacked = format_str("".join(python_lines), mode=FileMode())
        fp.writelines(blacked)

    if typescript_path:
        ts_lines: list[str] = []
        for cs_enum, _, nice_class, *_ in ENUMS:
            ts_lines += cs_enum_to_ts(all_cs_enums[cs_enum], nice_class)
            if cs_enum != ENUMS[-1][0]:
                ts_lines.append("\n")

        print(f"Writing {typescript_path} ...")
        with open(typescript_path, "w", encoding="utf-8", newline="") as fp:
            fp.writelines(ts_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract enums valus from the dump.cs file."
    )
    parser.add_argument("input", type=str, help="Path to the dump.cs file")
    parser.add_argument("output", type=str, help="Path to the gameenums.py file")
    parser.add_argument(
        "--typescript",
        "-ts",
        type=str,
        help="Write a typescript enum file",
        required=False,
        default="",
    )
    args = parser.parse_args()

    main(args.input, args.output, args.typescript)
