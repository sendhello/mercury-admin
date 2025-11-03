from redis.asyncio import Redis

redis: Redis | None = None


# Function will be needed when implementing dependencies
async def get_redis() -> Redis:
    return redis
