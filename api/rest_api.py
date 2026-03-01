import os
import configparser
import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import async_session, Prices, Route
from price_fetcher.stats import compute_stats

load_dotenv()

config = configparser.ConfigParser()
config.read("config.ini")

# Redis Seup
redis_client = aioredis.from_url(os.getenv("REDIS_URL"))
cache_time = config["settings"]["redis_cache_time"]

# FastAPI Setup
app = FastAPI(title="Flight Price Tracker")


async def get_session():
    async with async_session() as session:
        yield session


@app.get("/prices/{date}/{origin}/{destination}")
async def get_price_history(
    date: str,
    origin: str,
    destination: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Return the full price history for a route. Either fetch from cache or DB.

    :param date: flight date in YYYY-MM-DD format, e.g. "2026-05-29"
    :param origin: airport code for the departure airport, e.g. "BER"
    :param destination: airport code for the destination airport, e.g. "KTW"
    :param session: async session
    :return: JSON with route metadata and price history
    """
    # Cache key for Redis
    cache_key = f"price_hist:{date}:{origin.upper()}:{destination.upper()}"

    # Return cached result if available 
    cached = await redis_client.get(cache_key)
    if cached:
        return {"source": "cache", "data": cached}
    
    # Get route row from DB when not in cache
    result = await session.execute(
        select(Route).where(
            Route.date == date,
            Route.origin == origin.upper(),
            Route.destination == destination.upper(),
        )
    )
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found") #Print Error when route cannot be found

    # Fetch price history for this route
    result = await session.execute(
        select(Prices)
        .where(Prices.route_id == route.id)
        .order_by(Prices.timestamp.asc())
    )
    prices = result.scalars().all()
    price_hist = {
        "date": route.date,
        "origin": route.origin,
        "destination": route.destination,
        "unit": route.unit,
        "prices": [
            {"price": s.price, "timestamp": s.timestamp}
            for s in prices
        ],
    }

    # Cache result
    await redis_client.setex(cache_key, cache_time, str(price_hist))

    return {"source": "db", "data": price_hist}


@app.get("/prices/{date}/{origin}/{destination}/stats")
async def get_price_stats(
    date: str,
    origin: str,
    destination: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Return price summary statistics for a route. Either fetch from cache or DB.

    :param date: flight date in YYYY-MM-DD format,e.g. "2026-05-29"
    :param origin: airport code for the departure airport, e.g. "BER"
    :param destination: airport code for the destination airport, e.g. "KTW"
    :param session: async session
    :return: JSON with route metadata and price statistics
    """
    # Cache key for Redis
    cache_key = f"stats:{date}:{origin.upper()}:{destination.upper()}"

    # Return cached result if available
    cached = await redis_client.get(cache_key)
    if cached:
        return {"source": "cache", "data": cached}

    # Get route row from DB when not in cache
    result = await session.execute(
        select(Route).where(
            Route.date == date,
            Route.origin == origin.upper(),
            Route.destination == destination.upper(),
        )
    )
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found") #Print Error when route cannot be found

    # Compute statistics and attach route metadata
    stats = await compute_stats(session, route.id)
    stats["date"] = route.date
    stats["origin"] = route.origin
    stats["destination"] = route.destination
    stats["unit"] = route.unit

    # Cache result 
    await redis_client.setex(cache_key, cache_time, str(stats))

    return {"source": "db", "data": stats}
