import asyncio
import configparser
from datetime import datetime, timezone
import warnings
from sqlalchemy import select
from db.db import async_session, Prices, Route, init_db
from price_fetcher.amadeus_api import get_cheapest_price
from price_fetcher.notifier import send_email
from price_fetcher.stats import compute_stats

config = configparser.ConfigParser()
config.read("config.ini")


async def get_or_create_route(session, origin: str, destination: str, unit: str, date: str):
    """
    Get an existing route or create a new one if it doesn't exist

    :param session: Active SQLAlchemy AsyncSession.
    :param origin: Airport code for the departure airport, e.g. "BER"
    :param destination: Airport code for the arrival airport, e.g. "KTW"
    :param unit: Currency unit, e.g. "EUR"
    :param date: Flight date in YYYY-MM-DD format, e.g. "2026-05-29"
    :return: SQLALchemy route object
    """
    # Get specified route from DB
    result = await session.execute(
        select(Route).where(
            Route.origin == origin,
            Route.destination == destination,
            Route.date == date
        )
    )
    route = result.scalar_one_or_none()

    if not route:
        # Create route
        route = Route(origin=origin, destination=destination, unit=unit, date=date)
        session.add(route)
        await session.commit() # Add to route row to DB
        await session.refresh(route) # reload route object to get the new ID

    return route


async def fetch_and_store_price(origin: str, destination: str, unit: str, date: str):
    """
    Fetch the current price from Amadeus, store it in the DB, and compute stats

    :param origin: Airport code for the departure airport, e.g. "BER"
    :param destination: Airport code for the arrival airport, e.g. "KTW"
    :param unit: Currency unit, e.g. "EUR"
    :param date: Flight date in YYYY-MM-DD format, e.g. "2026-05-29"
    :return: dict with flight information as well as summary statistics
    """
    # Get the cheapest flight price
    price = get_cheapest_price(origin, destination, date)

    if price is None:
        print(f"No price found for {origin} to {destination} on {date}, skipping.")
        return None

    async with async_session() as session:
        # Get route object
        route = await get_or_create_route(session, origin, destination, unit, date)

        # Create price object
        price_row = Prices(
            route_id=route.id,
            price=price,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(price_row) 
        await session.commit() #Add new price to Prices table in DB

        print(f"Stored price {price} {unit} for {origin}->{destination}")

        # Compute statistics now that the new price is committed
        stats = await compute_stats(session, route.id)
        stats["origin"] = origin
        stats["destination"] = destination
        stats["unit"] = unit
        stats["current_price"] = price
        stats["date"] = date

    return stats


async def run():
    """
    Full price fetching pipeline: init DB, fetch prices for all configured routes and send an email summary.
    """
    # Create tables if they dont exist yet
    await init_db()

    # Get departure and return routes from config
    routes = []
    for key, value in config["routes"].items():
        if key.startswith("dep"):
            origin, destination, unit = value.split(",")
            date = config["dates"]["dep_date"]
            routes.append((origin.strip(), destination.strip(), unit.strip(), date.strip()))

        if key.startswith("ret"):
            origin, destination, unit = value.split(",")
            date = config["dates"]["ret_date"]
            routes.append((origin.strip(), destination.strip(), unit.strip(), date.strip()))

    # Build one coroutine per route and run them all simultaneously
    tasks = [
        fetch_and_store_price(origin, destination, unit, date)
        for origin, destination, unit, date in routes
    ]
    # Get data for all routes
    results = await asyncio.gather(*tasks)

    # Filter out None when API returned nothing
    all_stats = [r for r in results if r is not None]

    # send mail or print warnings
    if all_stats:
        await send_email(all_stats)
    else:
        warnings.warn("No prices fetched, email not sent!")

if __name__ == "__main__":
    asyncio.run(run())
