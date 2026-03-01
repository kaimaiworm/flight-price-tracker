import os
import configparser
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import warnings

load_dotenv()

config = configparser.ConfigParser()
config.read("config.ini")

# Init Amadeus API client
amadeus = Client(
    client_id=os.getenv("AMADEUS_API_KEY"),
    client_secret=os.getenv("AMADEUS_API_SECRET"),
)


def get_cheapest_price(origin: str, destination: str, date: str):
    """
    Get the cheapest flight price for a given route and date.

    :param origin: airport code for the departure airport, e.g. "BER"
    :param destination: airport code for the arrival airport, e.g. "KTW"
    :param date: flight date in YYYY-MM-DD format, e.g. "2026-05-29"
    :return: flight price or None on failure
    """
    try:
        #get chepeast offer for specified flight route from Amadeus
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1,
            max=1,  
        )

        if response.data:
            return float(response.data[0]["price"]["total"])
        return None

    except:
        # If price cannot be fetched, print warning
        warnings.warn(f"Failed to get price from API for route: {origin} to {destination} on {date}")
        return None
