import databases
import asyncio
import aioredis

import config

mysql = databases.Database(str(config.MYSQL_DSN))
redis = aioredis.from_url(str(config.REDIS_DSN))

# @mysql.transaction()
async def run_cron() -> None:
    for table, whitelist_int in (
        ("scores", 1),
        ("scores_relax", 2),
        ("scores_ap", 2),
    ):
        query = (
            f"SELECT users.username, users.id, ROUND(s.pp) AS pp FROM {table} s "
            "LEFT JOIN beatmaps b USING(beatmap_md5) LEFT JOIN users ON users.id = s.userid "
            f"WHERE s.play_mode = 0 AND s.completed = 3 AND b.ranked = 2 AND users.privileges & 1 AND users.whitelist & {whitelist_int} "
            "ORDER BY s.pp DESC LIMIT 1"
        )

        result = await mysql.fetch_one(query)
        if not result:
            await redis.set(f"akatsuki:top:{table}:pp", 0)
            await redis.set(f"akatsuki:top:{table}:id", 0)
            await redis.set(f"akatsuki:top:{table}:name", "")
            continue

        await redis.set(f"akatsuki:top:{table}:pp", result["pp"])
        await redis.set(f"akatsuki:top:{table}:id", result["id"])
        await redis.set(f"akatsuki:top:{table}:name", result["username"])

    print(f"Updated top play cache!")


async def main() -> int:
    async with (mysql, redis):
        await run_cron()

    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
