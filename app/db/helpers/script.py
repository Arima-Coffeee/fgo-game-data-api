from typing import Optional

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import and_, func, literal_column, select

from ...models.raw import ScriptFileList
from ...schemas.raw import ScriptEntity, ScriptSearchResult
from .quest import get_quest_entity


async def get_script(conn: AsyncConnection, script_id: str) -> Optional[ScriptEntity]:
    stmt = select(
        ScriptFileList.c.scriptFileName,
        func.octet_length(ScriptFileList.c.rawScript).label("scriptSizeBytes"),
        ScriptFileList.c.questId,
    ).where(ScriptFileList.c.scriptFileName == script_id)

    rows = (await conn.execute(stmt)).fetchall()

    if len(rows) == 0:
        return None

    quest_ids: list[int] = [row.questId for row in rows if row.questId != -1]
    if quest_ids:
        quests = await get_quest_entity(conn, quest_ids)
    else:
        quests = []

    return ScriptEntity(
        scriptId=script_id, scriptSizeBytes=rows[0].scriptSizeBytes, quests=quests
    )


async def get_script_search(
    conn: AsyncConnection,
    search_query: str,
    script_file_name: str | None = None,
    limit_result: int = 50,
) -> list[ScriptSearchResult]:
    score = func.pgroonga_score(literal_column("tableoid"), literal_column("ctid"))
    snippets = func.pgroonga_snippet_html(
        ScriptFileList.c.textScript, func.pgroonga_query_extract_keywords(search_query)
    )

    where_conds = [ScriptFileList.c.textScript.op("&@~")(search_query)]

    if script_file_name:
        where_conds.append(
            ScriptFileList.c.scriptFileName.like(f"%{script_file_name}%")
        )

    stmt = (
        select(
            ScriptFileList.c.scriptFileName.distinct().label("scriptId"),
            score.label("score"),
            snippets.label("snippets"),
        )
        .where(and_(*where_conds))
        .order_by(score.desc())
        .limit(limit_result)
    )
    return [
        ScriptSearchResult.from_orm(result)
        for result in (await conn.execute(stmt)).fetchall()
    ]
