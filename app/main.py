import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from redis import Redis

from app.database import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)

    yield

    pool.close()


app = FastAPI(lifespan=lifespan)


redis_client = Redis(
    host=os.environ["REDIS_HOST"],
    port=6379,
    decode_responses=True,
    ssl=True,
)


@app.get("/hello")
def hello():
    return {"message": "hello"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    cache_key = f"user:{user_id}"

    # 1. Check Redis
    cached_user = redis_client.get(cache_key)

    if cached_user:
        return json.loads(cached_user)

    # 2. Cache miss → use PostgreSQL connection pool
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (user_id,),
            )

            user = cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    result = {
        "id": user[0],
        "name": user[1],
        "email": user[2],
    }

    # 3. Store result in Redis
    redis_client.setex(
        cache_key,
        60,
        json.dumps(result),
    )

    return result
