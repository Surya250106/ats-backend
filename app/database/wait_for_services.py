import sys
import time
import psycopg2
import redis
from app.core.config import settings


def wait_for_db() -> bool:
    print("Waiting for PostgreSQL...", flush=True)
    retries = 30
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                connect_timeout=3
            )
            conn.close()
            print("PostgreSQL is ready!", flush=True)
            return True
        except Exception as e:
            print(f"PostgreSQL not ready yet ({e.__class__.__name__}). Retrying in 1s...", flush=True)
            time.sleep(1)
            retries -= 1
    print("PostgreSQL connection timed out!", flush=True)
    return False


def wait_for_redis() -> bool:
    print("Waiting for Redis...", flush=True)
    retries = 30
    while retries > 0:
        try:
            r = redis.Redis.from_url(settings.QUEUE_URL)
            r.ping()
            print("Redis is ready!", flush=True)
            return True
        except Exception as e:
            print(f"Redis not ready yet ({e.__class__.__name__}). Retrying in 1s...", flush=True)
            time.sleep(1)
            retries -= 1
    print("Redis connection timed out!", flush=True)
    return False


if __name__ == "__main__":
    db_ok = wait_for_db()
    redis_ok = wait_for_redis()
    if not db_ok or not redis_ok:
        sys.exit(1)
    sys.exit(0)
