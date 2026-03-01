from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from db.db import Prices


async def compute_stats(session, route_id: int):
    """
    Compute price statistics for a given route

    :param session: SQLAlchemy AsyncSession
    :param route_id: Route ID
    :return: dict with price statistics
    """
    # start date for 30-day window
    start_dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)

    # last price
    result = await session.execute(
        select(Prices.price)
        .where(Prices.route_id == route_id)
        .order_by(Prices.timestamp.desc())
        .offset(1)
        .limit(1)
    )
    last_price = result.scalar_one_or_none()

    # all-time low
    result = await session.execute(
        select(func.min(Prices.price)).where(
            Prices.route_id == route_id
        )
    )
    all_time_low = result.scalar_one_or_none()

    # all-time high
    result = await session.execute(
        select(func.max(Prices.price)).where(
            Prices.route_id == route_id
        )
    )
    all_time_high = result.scalar_one_or_none()

    # 30-day low
    result = await session.execute(
        select(func.min(Prices.price)).where(
            Prices.route_id == route_id,
            Prices.timestamp >= start_dt,
        )
    )
    low_30d = result.scalar_one_or_none()

    # 30-day high
    result = await session.execute(
        select(func.max(Prices.price)).where(
            Prices.route_id == route_id,
            Prices.timestamp >= start_dt,
        )
    )
    high_30d = result.scalar_one_or_none()

    return {
        "last_price": last_price,
        "all_time_low": all_time_low,
        "all_time_high": all_time_high,
        "low_30d": low_30d,
        "high_30d": high_30d,
    }
