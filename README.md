# Uniswap-V3-APIs

### Overview

This application will provide a service that queries pricing data for various tokens via Uniswap's V3 subgraph.

The service will pull data from Uniswap's V3 subgraph for tokens: *$WBTC*, *$SHIB*, and *$GNO* on the Ethereum Mainnet network. The two objects that will be queried on the Uniswap subgraph are `TokenHourData` and `Token`.

This data is stored in a postgres instance, to allow our API to fetch user specified filtering from out API endpoint: 

`/api/chart-data/{symbol}?hours={hour-duration}&interval_hours={hour-increment}`

for example: 

`localhost:8000/api/chart-data/WBTC?hours=72&interval_hours=4`

The response object from the API endpoint is structured as a 3D array with the following properties:

```
[
    [
        ["unix-time", "open", price]
    ],
    [
        ["unix-time", "close", price]
    ],
    [
        ["unix-time", "high", price]
    ],
    [
        ["unix-time", "low", price]
    ],
    [
        ["unix-time", "priceUSD", price]
    ]
]
```

### Running

*TL;DR*

Build the containers:

`docker compose build`

To run the API service:

`docker compose up`

To destroy the running containers -

From the terminal running uvicorn ->

Stop the server:

`CTRL-c`

then:

`docker compose down`

To run the test suite:

`docker compose run test`

*Note: the tests are run against the seeded database, therefore the api service will need to run before the test service is initially run. Running the test service on newly built containers will fail the tests as the data used is not mocked, but from the data ingested from the uniswap subgraph.*

The application is structured as two docker containers managed with `docker compose`, the first container is the api service, and the other container is a vanilla instance of Postgres15. There is also a test service declared in the docker-compose.yml file to run the pytest unit tests without running uvicorn.

The entrypoint to the API service is declared in the docker-compose.yml file:

```
entrypoint: ["/bin/sh", "-c", "python scripts/reset_db.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
```

This starts the API service within the api docker container. This command will first run a script to reset and seed the database on every instanteation of the docker container creation. This happens outside of the python call to start the main application. Once `reset_db.py` completes, the `main.py` application runs, which will launch the uvicorn server and allow the API endpoints to be interrogated.

The following routes are available:

`localhost:8000`

`localhost:8000/api/tokens`

`localhost:8000/api/chart-data/{symbol}?hours={duration}&interval_hours={interval}`

`localhost:8000/api/chart-data-all/{symbol}`

`localhost:8000/api/debug-price-data/{symbol}`


### Process

This application started as an investigation into formmatting data, and became a research project in connecting many disparet pieces. I began the process in the following phases:

* Typescript vs Python
* Layout the API server
* Query the token data
* Store the token data
* Display the token data

Quickly the plan went awry with rabbitholes and technical challenges, which concluded with a rewarding experience of investigation and lessons.

Some of the lessons learned along the way of this exploration were:

* Async vs Synchronous FastAPI
* How to get the data out of Token and TokenHourData
* How to relate and model the data
* How to build the Postgres query for the time series
* Asynchronous testing with pytest

Before I continue into the weeds, some future considerations with this project and how far I build it out are as follows -

The structure for the project needs improvement, as it is not ideal for a production environment. I wanted to reset the database everytime that the containers were created just to test the ingestion and polling of the data, however, this split up the creation and initialization of the database connection, which I don't love. I would prefer the database connection to be created and destroyed in the same file. With the current design, the creation of the db connection is done in the rest_db.py file while the cleanup of the connection is done in the main.py fail. Ickky. I knew this would be the case, but at the onset I valued interacting with the database for seeding purposes, rather than for the API service. This makes sense as a demonstration, but not as a production service.

There needs to be more logging and error handling throughout the codebase. Every db call should be wrapped in a try/catch, and more logging for debugging purposes would be useful.

The testing framework is very minimal. This is more an exercise with engaging the API rather than exhaustively testing it. There are many more unit tests that should be run, as well as integration tests that would have been great to tackle. But time did not allow for this.

The question of code readability came up a lot in this project. "Can someone else understand some of this tight, minimal python code?" The answer I always respond to myself when I ask myself that question is, no! I am lucky if I can understand what I programmed six-months from now, let alone someone unfamiliar with the code base. But some of the code decisions were made for brevity, this being a project with a quick turn-around.

### Into the woods

For a detailed overview of the project, I will start with a couple of prelimiary decisions: 

* Typescript vs Python
* Docker Compose vs Docker
* Flask vs FastAPI
* Aysnc vs Sync

In thinking about how to begin the project I considered typescript, as the name of desired function of the task is camelCase, however, I went with python because I had the recollection that python was the target language for the company's backend (if I'm not mistaken). As for the decision to use docker compose, I used docker compose for a rather complex project back in school, and I just default to using it if there is more than one container. Being that there are two, it was a bit of a wash, but I went with container coordination to simulate a hosted database.

For the decision to use FastAPI, I went with it because it was a technology I hadn't used before, where Flask I had. And used this project as a learning opportunity to try out FastAPI, and because it is fast, or so the name would suggest.

Lastly, I went with an asynchronous approach to the API server in part due to the fact that I would program an Express server that way, and also that is where the rabbit hole lead when trying to debug the chart data endpoint. The async approach made the testing much more difficult, and in retrospect I would try to keep the server sychronous if at all possible.

The application is declared in the main.py file. Most of the server code is boiler plate, which has a similar structure to an Express server, load the models, routes, and middleware onto the application server and then start it on a port. A departure in this application was splitting the server initialization across a reset module and the main application module. The application is broken up among folders to help with architectural design, readability, and separation of concerns.

Within the root folder exists the docker-compose file, the pytest initialization file, this readme, and the requirements file for the python packages. The requirements file is at the root level which is where the python virtual environment is installed, where the requirements file is copied into the container working directory, detailed in the Dockerfile. 

There are two subfolders for the database and the api application. The database directory is rather sparse with only the SQL initialization script for creating the tables in the database. Everything else lives in the api directory. This directory has the models, scripts, services, and tests folders. All contain the files that one would expect given their naming.

To model the data, there is a relationship between the two tables within the database, tokens, and price_data. The connection between these tables is the token id, or the primary key for tokens on the token table, which serves as a foreign key on the price_data table. This decision was made to optimize the query of price data given a token symbol. However, in the fog of war the api router endpoint does two queries, one for the token id from the token symbol, and another big-ole-mammajamma to query the price data:

```python
result = await db.execute(query, {
        'start_time': start_time,
        'end_time': end_time,
        'interval': interval_hours,
        'token_id': token.id
    })
    price_data = result.fetchall()
```

I believe having these two asynchronous calls within the `chart-data` endpoint necessitated the asynch api server, which was an addtional complexity to the project. The intention and initial data modeling design was to join the tables on the token symbol to retrieve the price data, which ultimately didn't happen due to the complexity of the querying the price data and time considerations. 

**This is most likely the most illuminating lesson of the project, efficient data modeling for query performance.** 

As stated above, most of the code is boiler plate for the api server, and the finer detail of this task is likely within the query for the `getChartdata(tokenSymbol, timeUnitInHours)` response data. The following is my description of that query and some caveats.

### The Query

```SQL
WITH time_series AS (
        SELECT generate_series(:start_time, :end_time, :interval * '1 hour'::interval) AS interval_timestamp
    ),
    price_data_hourly AS (
        SELECT
            date_trunc('hour', timestamp) AS hour,
            open,
            close,
            high,
            low,
            price_usd,
            ROW_NUMBER() OVER (PARTITION BY date_trunc('hour', timestamp) ORDER BY timestamp ASC) AS rn_first,
            ROW_NUMBER() OVER (PARTITION BY date_trunc('hour', timestamp) ORDER BY timestamp DESC) AS rn_last
        FROM price_data
        WHERE token_id = :token_id AND timestamp >= :start_time AND timestamp <= :end_time
    ),
    price_data_agg AS (
        SELECT
            hour,
            MAX(CASE WHEN rn_first = 1 THEN open END) AS open,
            MAX(CASE WHEN rn_last = 1 THEN close END) AS close,
            MAX(high) AS high,
            MIN(low) AS low,
            MAX(CASE WHEN rn_last = 1 THEN price_usd END) AS price_usd
        FROM price_data_hourly
        GROUP BY hour
    )
    SELECT
        time_series.interval_timestamp,
        COALESCE(price_data_agg.open, LAG(price_data_agg.close) OVER (ORDER BY time_series.interval_timestamp)) AS open,
        COALESCE(price_data_agg.close, LAG(price_data_agg.close) OVER (ORDER BY time_series.interval_timestamp)) AS close,
        COALESCE(price_data_agg.high, LAG(price_data_agg.close) OVER (ORDER BY time_series.interval_timestamp)) AS high,
        COALESCE(price_data_agg.low, LAG(price_data_agg.close) OVER (ORDER BY time_series.interval_timestamp)) AS low,
        COALESCE(price_data_agg.price_usd, LAG(price_data_agg.price_usd) OVER (ORDER BY time_series.interval_timestamp)) AS price_usd
    FROM time_series
    LEFT JOIN price_data_agg ON time_series.interval_timestamp = price_data_agg.hour
    ORDER BY time_series.interval_timestamp
```

A starting note is that the api for this data is called `chart-data` while the function that executes the api request is called `get_chart_data(symbol, hours, interval)`. The discrepancies are due to decisions made during the programming assignment. The snake case naming is due to the python convention, and the decision to add the hour time frame was a design decision to play with more data from the Uniswap subgraph. The route is declared as:

```python
@router.get("/chart-data/{symbol}")
async def get_chart_data(symbol: str, hours: int, interval_hours: int = 1, db: AsyncSession = Depends(get_db)):
```

Breaking down the query, we begin with the common table expression to manage the multiple temporary tables created for the query to help separate the elements to make up the query. There are three CTEs in this query, the *time_series*, *price_data_hourly*, and *price_data_agg*.

The Time Series CTE creates a series of timestamps from :start_time to :end_time at intervals of :interval hours. It ensures we have a continuous series of timestamps, even if there's no data for some intervals.

The Price Data Hourly CTE creates the price data for the specified token and time range. It uses window functions (ROW_NUMBER()) to identify the first and last rows for each hour. This is crucial for correctly determining the open and close prices for each hour.

The Price Data Agg CTE aggregates the hourly data. It selects the open price from the first row of each hour, the close price from the last row, the highest high, the lowest low, and the last price_usd for each hour.

Finally the select statement joins the continuous time series with the aggregated price data. The COALESCE and LAG functions are used to fill in missing data where

* COALESCE returns the first non-null value in its arguments.
* LAG accesses data from a previous row in the ordered set.

So, if there's no data for a particular timestamp, it uses the close price from the previous timestamp. This ensures a continuous data series without gaps. The query is also resilient to null data in the event that the close price is null, the extrapolated data is also then null.

### Commands

quit uvicorn:

`CTRL-c`

Start venv with:

`source .venv/bin/activate`

Docker Compose:

`docker compose build`

`docker compose up`

`docker compose down`

### Notes

Resources for the development: 

https://fastapi.tiangolo.com/advanced/async-tests/

https://github.com/pytest-dev/pytest-asyncio/issues/207

https://rogulski.it/blog/sqlalchemy-14-async-orm-with-fastapi/

https://github.com/Diapolo10/5G00EV25-3001_server/blob/main/tests/conftest.py