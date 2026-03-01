# Flight Price Tracker

Tracks flight prices for configured routes using the Amadeus API. Prices are stored in a MySQL database and a summary email is sent after each fetch run. Additionally, results can be fetched from DB via a REST API with Redis caching.

For the project to work an .env is needed with the following entries:

```
AMADEUS_API_KEY             -> Amadeus API key
AMADEUS_API_SECRET          -> Amadeus API key

SMTP_MAIL                   -> Outgoing Email Address
SMTP_PASSWORD               -> Email  App Password
ALERT_MAIL                  -> Alert Email Address

DB_URL=mysql+aiomysql://user:password@localhost:3306/flightprices
REDIS_URL=redis://localhost:6379

```

## Structure

```
price_fetcher/main.py       -> main script, runs full pipeline
price_fetcher/amadeus.py    -> Amadeus API client, returns cheapest price for a route
price_fetcher/stats.py      -> computes price summary statistics from DB
price_fetcher/notifier.py   -> builds and sends the price summary email via Gmail SMTP
api/rest_api.py             -> FastAPI REST API to query price history and stats
api/test.py                 -> test the API by downloading price history and statistics
db/db.py                    -> SQLAlchemy models and DB connection
docker-compose.yml          -> MySQL 8 + Redis 7
```
