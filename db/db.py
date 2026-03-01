import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Load .env 
load_dotenv()

#Get database url from .env
DB_URL = os.getenv("DB_URL")

#create engine
engine = create_async_engine(DB_URL, echo=False)

# Create async session
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# map db tables to python classes
Base = declarative_base()
class Route(Base):
    """
    DB table of unique routes being tracked

    id: unique ID for each route
    date: flight date in YYYY-MM-DD format,e.g. "2026-05-29"
    origin: airport code for the departure airport, e.g. "BER"
    destination: airport code for the destination airport, e.g. "KTW"
    unit: currency unit of the prices fetched for this route
    """

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)
    origin = Column(String(10), nullable=False)
    destination = Column(String(10), nullable=False)
    unit = Column(String(10), default="EUR")
    prices = relationship("Prices", back_populates="route")


class Prices(Base):
    """
    DB table of historic prices for a specified route

    id: unique ID for the specific price
    route_id: identifier for the route this historic price belongs to
    timestamp: timestamp when the price was fetched
    """

    __tablename__ = "prices"

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    route = relationship("Route", back_populates="prices")

# Create Tables (when not existing)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)