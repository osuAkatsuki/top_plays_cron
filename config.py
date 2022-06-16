from starlette.config import Config
from starlette.datastructures import Secret

cfg = Config(".env")

MYSQL_DSN: Secret = cfg("MYSQL_DSN", cast=Secret)
REDIS_DSN: Secret = cfg("REDIS_DSN", cast=Secret)
