import pytest
from httpx import AsyncClient
from httpx import AsyncClient, ASGITransport

from main import app

# async def test_read_main(async_client: AsyncClient):
#     response = await async_client.get("/")

#     assert response.status_code == 200
#     assert response.json() == {"message": "Welcome to Uniswap V3 Data API"}

async def test_read_main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac: 
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Uniswap V3 Data API"}
