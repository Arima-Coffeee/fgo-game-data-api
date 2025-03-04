from enum import Enum
from pathlib import Path
from typing import Union

import orjson


file_path = Path(__file__)
MAPPING_PATH = file_path.parent / "mappings"


TRANSLATIONS: dict[str, str] = {}


class Translation(str, Enum):
    ENEMY = "enemy_names"
    VOICE = "voice_names"
    OVERWRITE_VOICE = "overwrite_voice_names"
    BGM = "bgm_names"
    SKILL = "skill_names"
    NP = "np_names"
    EVENT = "event_names"
    WAR = "war_names"
    ITEM = "item_names"
    ENTITY = "entity_names"
    QUEST = "quest_names"
    SPOT = "spot_names"
    ILLUSTRATOR = "illustrator_names"
    CV = "cv_names"
    SERVANT = "servant_names"
    EQUIP = "equip_names"
    CC = "cc_names"
    MC = "mc_names"
    COSTUME = "costume_names"


for translation_file in Translation.__members__.values():
    with open(MAPPING_PATH / f"{translation_file.value}.json", "rb") as fp:
        TRANSLATIONS |= orjson.loads(fp.read())

with open(MAPPING_PATH / "translation_override.json", "rb") as fp:
    TRANSLATION_OVERRIDE: dict[Translation, dict[str, str]] = orjson.loads(fp.read())


ILLUSTRATOR_EN_TO_JP: dict[str, str] = {}
with open(MAPPING_PATH / f"{Translation.ILLUSTRATOR.value}.json", "rb") as fp:
    ILLUSTRATOR_EN_TO_JP = {v: k for k, v in orjson.loads(fp.read()).items() if k != v}

CV_EN_TO_JP: dict[str, str] = {}
with open(MAPPING_PATH / f"{Translation.CV.value}.json", "rb") as fp:
    CV_EN_TO_JP = {v: k for k, v in orjson.loads(fp.read()).items() if k != v}


EXTRA_CHARAFIGURES: dict[int, list[int]] = {}

with open(MAPPING_PATH / "extra_charafigure.json", "rb") as fp:
    EXTRA_CHARAFIGURES = {
        cf["svtId"]: sorted(cf["charaFigureIds"]) for cf in orjson.loads(fp.read())
    }

EXTRA_IMAGES: dict[int, list[Union[int, str]]] = {}

with open(MAPPING_PATH / "extra_image.json", "rb") as fp:
    EXTRA_IMAGES = {
        im["svtId"]: sorted(im["imageIds"]) for im in orjson.loads(fp.read())
    }
