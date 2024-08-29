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

To run the test suite:

`docker compose run test`

To run the API service:

`docker compose build`

then:

`docker compose up`

To destroy the running containers -

From the terminal running uvicorn ->

Stop the server:

`CTRL-c`

then:

`docker compose down`

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

In thinking about how to begin the project I considered typescript, as the name of desired function of the task is camelCase, however, I went with python because I had the recollection that python was the target language for the company's backend. 

### Commands

quit uvicorn:

`CTRL-c`

Start venv with:

`source .venv/bin/activate`

Docker Compose:

`docker compose build`

`docker compose up`

`docker compose down`