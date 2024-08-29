import re
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from main import app


async def test_read_tokens():
    expected_tokens = [
        {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        },
        {
            "symbol": "GNO",
            "name": "Gnosis Token",
            "address": "0x6810e776880c02933d47db1b9fc05908e5386b96",
        },
        {
            "symbol": "SHIB",
            "name": "SHIBA INU",
            "address": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        },
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/tokens")
    respJSON = response.json()
    assert response.status_code == 200
    assert len(respJSON) == 3
    assert respJSON == expected_tokens


# The successive tests could all be combined into one test function
# but this way it's easier to see the tests in the terminal output
async def test_chart_data_has_correct_structure():
    token_symbol = "WBTC"
    hours = 24
    interval_hours = 1
    url = (
        f"/api/chart-data/{token_symbol}?hours={hours}&interval_hours={interval_hours}"
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(url)
    respJSON = response.json()
    assert response.status_code == 200
    # Assert the 3D array has 5 lists
    assert len(respJSON) == 5  # 5 lists for open, close, high, low, priceUSD
    # Assert number of data points in each category
    assert all(
        len(data_type) == 25 for data_type in respJSON
    ), "Each category should have 25 data points"


async def test_chart_data_has_correct_data():
    token_symbol = "WBTC"
    hours = 24
    interval_hours = 1
    url = (
        f"/api/chart-data/{token_symbol}?hours={hours}&interval_hours={interval_hours}"
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(url)
    respJSON = response.json()

    # Assert structure and types of each data point
    timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
    data_types = ["open", "close", "high", "low", "priceUSD"]
    for i, data_type in enumerate(respJSON):
        for point in data_type:
            assert (
                len(point) == 3
            ), f"Each data point in {data_types[i]} should have 3 elements"
            assert isinstance(
                point[0], str
            ), f"Timestamp in {data_types[i]} should be a string"
            assert re.match(
                timestamp_pattern, point[0]
            ), f"Timestamp should be in the format 'YYYY-MM-DDTHH:MM:SS'"
            assert isinstance(point[1], str), f"Second element should be a string"
            assert (
                point[1] == data_types[i]
            ), f"Second element should be '{data_types[i]}'"
            assert isinstance(
                point[2], float
            ), f"Value in {data_types[i]} should be a float"
            assert (
                str(point[2]).split(".")[-1] <= "9"
            ), f"Float value not truncated to one decimal place: {point[2]}"


async def test_chart_data_has_correct_format():
    token_symbol = "WBTC"
    hours = 24
    interval_hours = 1
    url = (
        f"/api/chart-data/{token_symbol}?hours={hours}&interval_hours={interval_hours}"
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(url)
    respJSON = response.json()

    # Assert timestamp format and sequence
    timestamps = [point[0] for point in respJSON[0]]
    assert all(
        datetime.fromisoformat(ts) for ts in timestamps
    ), "All timestamps should be in ISO format"
    # Assert chronological order
    for data_type in respJSON:
        timestamps = [datetime.fromisoformat(point[0]) for point in data_type]
        assert timestamps == sorted(
            timestamps
        ), "Timestamps are not in chronological order"
