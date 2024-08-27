# Uniswap-V3-APIs

A Service that queries pricing data for various tokens via Uniswap's V3 subgraph

This service will pull data from Uniswap's V3 subgraph for tokens: *$WBTC*, *$SHIB*, and *$GNO* on the Ethereum Mainnet network. The two objects that will be queried on the Uniswap subgraph are `TokenHourData` and `Token`.

This data is stored in a postgres instance, to allow our API to fetch user specified filtering from out API endpoint: 

`get-chart-data?token-symbol={symbol}&time-unit-in-hours={hour-increment}`

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

Start venv with:

`source .venv/bin/activate`