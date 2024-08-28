import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from your_app.routes import get_chart_data  # Import your function

@pytest.mark.asyncio
async def test_get_chart_data():
    # Mock the database session
    mock_db = AsyncMock()
    
    # Mock the token query result
    mock_token = MagicMock()
    mock_token.id = 1
    mock_token.symbol = "BTC"
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_token
    
    # Mock the price data query result
    mock_price_data = [
        MagicMock(interval_timestamp=datetime.now(ZoneInfo("UTC")), open=100, close=101, high=102, low=99, price_usd=100.5)
        for _ in range(24)  # 24 hours of mock data
    ]
    mock_db.execute.return_value.fetchall.return_value = mock_price_data
    
    # Call the function
    result = await get_chart_data("BTC", 24, 1, mock_db)
    
    # Assertions
    assert len(result) == 5  # 5 lists for open, close, high, low, priceUSD
    assert all(len(data_type) == 24 for data_type in result)  # 24 data points for each type
    assert all(isinstance(point[0], str) and isinstance(point[2], float) for data_type in result for point in data_type)

    # You can add more specific assertions here