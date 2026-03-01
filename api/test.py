## Important: start API server before executing this script: uvicorn api.rest_api:app --reload

import httpx
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

BASE_URL = "http://localhost:8000"

# Get configurations
routes = {key: value for key, value in config["routes"].items()}
dates = {key: value for key, value in config["dates"].items()}
origin, destination, unit = [v.strip() for v in routes["dep_ber"].split(",")]
date = dates["dep_date"]

# Test price history 
response = httpx.get(f"{BASE_URL}/prices/{date}/{origin}/{destination}")
print(response.json())

# Test stats 
response = httpx.get(f"{BASE_URL}/prices/{date}/{origin}/{destination}/stats")
print(response.json())
