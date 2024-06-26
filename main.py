#!/usr/bin/env python3.9
import asyncio

import redis.asyncio as aioredis
import databases

import settings


def dsn(
    scheme: str,
    user: str,
    password: str,
    host: str,
    port: int,
    path: str,
) -> str:
    return f"{scheme}://{user}:{password}@{host}:{port}/{path}"


mysql = databases.Database(
    dsn(
        scheme="mysql",
        user=settings.DB_USER,
        password=settings.DB_PASS,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        path=settings.DB_NAME,
    )
)
redis = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASS,
    db=settings.REDIS_DB,
    ssl=settings.REDIS_USE_SSL,
)


# @mysql.transaction()
async def run_cron() -> None:
    for table, whitelist_int in (
        ("scores", 1),
        ("scores_relax", 2),
        ("scores_ap", 2),
    ):
        query = f"""
            SELECT users.username,
                   users.id,
                   ROUND(s.pp) AS pp
              FROM {table} s
         LEFT JOIN beatmaps b
             USING (beatmap_md5)
         LEFT JOIN users ON users.id = s.userid
             WHERE s.play_mode = 0
               AND s.completed = 3
               AND b.ranked = 2
               AND users.privileges & 1
               AND users.whitelist & {whitelist_int}
          ORDER BY s.pp DESC
             LIMIT 1
            """

        result = await mysql.fetch_one(query)
        if not result:
            await redis.set(f"akatsuki:top:{table}:pp", 0)
            await redis.set(f"akatsuki:top:{table}:id", 0)
            await redis.set(f"akatsuki:top:{table}:name", "")
            continue

        await redis.set(f"akatsuki:top:{table}:pp", int(result["pp"]))
        await redis.set(f"akatsuki:top:{table}:id", result["id"])
        await redis.set(f"akatsuki:top:{table}:name", result["username"])

    print(f"Updated top play cache!")


async def main() -> int:
    async with (mysql, redis):
        await run_cron()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
