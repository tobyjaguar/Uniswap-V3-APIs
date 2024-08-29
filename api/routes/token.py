import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel
from models.token import Token
from models.chart_data import PriceData
from services.database import get_db
from utils.format_prices import format_float

logger = logging.getLogger(__name__)
router = APIRouter()


class PriceDataResponse(BaseModel):
    timestamp: datetime
    open: float
    close: float
    high: float
    low: float
    priceUSD: float


class TokenDataResponse(BaseModel):
    name: str
    symbol: str
    decimals: int
    address: str
    totalSupply: str
    VolumeUSD: str
    price_data: List[PriceDataResponse]


@router.get("/tokens", response_model=List[dict])
async def read_tokens(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Token))
    tokens = result.scalars().all()
    return [
        {"symbol": token.symbol, "name": token.name, "address": token.address}
        for token in tokens
    ]


    """
    Retrieve chart data for a specific token over a given time period.

    This function fetches price data for a token, aggregates it into specified 
    time intervals, and formats it for chart display. It handles missing data 
    points by using the last known values.

    Parameters:
        symbol (str): The symbol of the token to retrieve data for.
        hours (int): The number of hours of historical data to retrieve.
        interval_hours (int, optional): The interval in hours for data 
        aggregation. Defaults to 1. db (AsyncSession): The database session, 
        provided by FastAPI's dependency injection.

    Raises:
        HTTPException: 
            - 404 status code if the specified token is not found.
            - 500 status code if there's an error executing the database query.
            - 422 status code if the input parameters are invalid.

    Returns:
        List[List[List[Union[str, float, None]]]]: A list of 5 sublists, 
        each containing data for open, close, high, low, 
        and priceUSD respectively. Each data point is a list of 
        [timestamp, data_type, value].

    Example:
        >>> get_chart_data("BTC", 24, 1)
        [
            [["2023-01-01T00:00:00", "open", 50000.0], ...],
            [["2023-01-01T00:00:00", "close", 51000.0], ...],
            [["2023-01-01T00:00:00", "high", 52000.0], ...],
            [["2023-01-01T00:00:00", "low", 49000.0], ...],
            [["2023-01-01T00:00:00", "priceUSD", 50500.0], ...]
        ]
    """
@router.get("/chart-data/{symbol}")
async def get_chart_data(
    symbol: str,
    hours: int,
    interval_hours: int = 1,
    db: AsyncSession = Depends(get_db)
):
    # Get the token record by symbol
    token_result = await db.execute(select(Token).filter(Token.symbol == symbol))
    token = token_result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Calculate the start time and end time
    end_time = datetime.now(ZoneInfo("UTC")).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours)

    # Construct the query with interval grouping
    query = text(
        """
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
    """
    )

    result = await db.execute(
        query,
        {
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval_hours,
            "token_id": token.id,
        },
    )
    price_data = result.fetchall()

    # Structure the data with the specified interval
    # 5 lists for open, close, high, low, priceUSD
    data = [[] for _ in range(5)]

    for entry in price_data:
        # Return timestamp without UTC designation
        timestamp = entry.interval_timestamp.replace(tzinfo=None).isoformat()
        data[0].append([timestamp, "open", format_float(entry.open)])
        data[1].append([timestamp, "close", format_float(entry.close)])
        data[2].append([timestamp, "high", format_float(entry.high)])
        data[3].append([timestamp, "low", format_float(entry.low)])
        data[4].append([timestamp, "priceUSD", format_float(entry.price_usd)])

    return data


@router.get("/chart-data-all/{symbol}", response_model=TokenDataResponse)
async def get_all_chart_data(
    symbol: str,
    limit: Optional[int] = Query(100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Fetching chart data for symbol: {symbol}, limit: {limit}")
    try:
        # Get the token record by symbol, including the associated price data
        query = (
            select(Token)
            .options(joinedload(Token.price_data))
            .filter(Token.symbol == symbol)
        )
        result = await db.execute(query)
        token = await result.unique().scalar_one_or_none()

        if not token:
            logger.warning(f"Token not found for symbol: {symbol}")
            raise HTTPException(status_code=404, detail="Token not found")

        logger.info(
            f"Token found: {token.symbol}, Price data count: {len(token.price_data)}"
        )

        if len(token.price_data) == 0:
            logger.warning(f"No price data found for token: {symbol}")
        else:
            logger.info(f"First price data entry: {token.price_data[0]}")
            logger.info(f"Last price data entry: {token.price_data[-1]}")

        price_data = sorted(token.price_data, key=lambda x: x.timestamp, reverse=True)[:limit]

        logger.info(f"Returning {len(price_data)} price data points")

        return TokenDataResponse(
            symbol=token.symbol,
            name=token.name,
            address=token.address,
            decimals=token.decimals,
            totalSupply=str(token.total_supply),
            VolumeUSD=str(token.volume_usd),
            price_data=[
                PriceDataResponse(
                    timestamp=entry.timestamp,
                    open=float(entry.open),
                    close=float(entry.close),
                    high=float(entry.high),
                    low=float(entry.low),
                    priceUSD=float(entry.price_usd),
                )
                for entry in price_data
            ],
        )
    except Exception as e:
        logger.exception(f"Error fetching chart data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/debug-price-data/{symbol}")
async def debug_price_data(
    symbol: str,
    limit: int = Query(10, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
):
    try:
        # First, get the token
        token_query = select(Token).filter(Token.symbol == symbol)
        token_result = await db.execute(token_query)
        token = await token_result.scalar_one_or_none()

        if not token:
            return {"error": "Token not found"}

        # Now, query for price data
        price_data_query = (
            select(PriceData)
            .filter(PriceData.token_id == token.id)
            .order_by(PriceData.timestamp.desc())
            .limit(limit)
        )
        price_data_result = await db.execute(price_data_query)
        price_data = await price_data_result.scalars().all()

        return {
            "token": {
                "id": token.id,
                "symbol": token.symbol,
                "name": token.name,
            },
            "price_data_count": len(price_data),
            "price_data": [
                {
                    "timestamp": entry.timestamp,
                    "open": float(entry.open),
                    "close": float(entry.close),
                    "high": float(entry.high),
                    "low": float(entry.low),
                    "price_usd": float(entry.price_usd),
                }
                for entry in price_data
            ],
        }
    except Exception as e:
        logger.exception(f"Error in debug route for {symbol}: {str(e)}")
        return {"error": str(e)}
