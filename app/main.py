import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from redis import Redis

from app.database import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start PostgreSQL connection pool
    pool.open(wait=True)

    yield

    # Close PostgreSQL connection pool
    pool.close()


app = FastAPI(lifespan=lifespan)


# Redis connection
redis_client = Redis(
    host=os.environ["REDIS_HOST"],
    port=6379,
    decode_responses=True,
    ssl=True,
)


# --------------------------------------------------
# Baseline endpoint
# --------------------------------------------------

@app.get("/hello")
def hello():
    return {"message": "hello"}


# --------------------------------------------------
# Redis + PostgreSQL endpoint
# --------------------------------------------------

@app.get("/users/{user_id}")
def get_user(user_id: int):

    cache_key = f"user:{user_id}"

    # 1. Check Redis cache
    cached_user = redis_client.get(cache_key)

    if cached_user:
        return json.loads(cached_user)

    # 2. Cache miss → query PostgreSQL using connection pool
    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id, name, email
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )

            user = cur.fetchone()

    # 3. User not found
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # 4. Create response
    result = {
        "id": user[0],
        "name": user[1],
        "email": user[2],
    }

    # 5. Store result in Redis for 60 seconds
    redis_client.setex(
        cache_key,
        60,
        json.dumps(result),
    )

    return result


# --------------------------------------------------
# PostgreSQL-only endpoint
# Used to benchmark connection pooling
# --------------------------------------------------

@app.get("/users-db/{user_id}")
def get_user_db(user_id: int):

    # Every request goes directly to PostgreSQL.
    # The connection is obtained from the pool.
    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id, name, email
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )

            user = cur.fetchone()

    # User not found
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
    }
