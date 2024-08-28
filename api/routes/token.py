import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel

from models.token import Token
from models.chart_data import PriceData
from services.database import get_db

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
    return [{"symbol": token.symbol, "name": token.name, "address": token.address} for token in tokens]
    
@router.get("/chart-data/{symbol}")
async def get_chart_data(symbol: str, hours: int, interval_hours: int = 1, db: AsyncSession = Depends(get_db)):
    # Get the token record by symbol
    token_result = await db.execute(select(Token).filter(Token.symbol == symbol))
    token = token_result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Calculate the start time and end time
    end_time = datetime.now(ZoneInfo("UTC")).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours)

    # Construct the query with interval grouping
    query = text("""
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
    """)

    result = await db.execute(query, {
        'start_time': start_time,
        'end_time': end_time,
        'interval': interval_hours,
        'token_id': token.id
    })
    price_data = result.fetchall()

    # Structure the data with the specified interval
    data = [[] for _ in range(5)]  # 5 lists for open, close, high, low, priceUSD
    for entry in price_data:
        timestamp = entry.interval_timestamp.isoformat()
        data[0].append([timestamp, "open", float(entry.open) if entry.open is not None else None])
        data[1].append([timestamp, "close", float(entry.close) if entry.close is not None else None])
        data[2].append([timestamp, "high", float(entry.high) if entry.high is not None else None])
        data[3].append([timestamp, "low", float(entry.low) if entry.low is not None else None])
        data[4].append([timestamp, "priceUSD", float(entry.price_usd) if entry.price_usd is not None else None])

    return data

# @router.get("/token_price_data/{symbol}")
# async def get_token_price_data(symbol: str, hours: int, interval_hours: int = 1, db: AsyncSession = Depends(get_db)):
#     # Get the token record by symbol
#     token_result = await db.execute(select(Token).filter(Token.symbol == symbol))
#     token = token_result.scalar_one_or_none()
#     if not token:
#         raise HTTPException(status_code=404, detail="Token not found")

#     # Calculate the start time and end time
#     end_time = datetime.now(ZoneInfo('UTC')).replace(minute=0, second=0, microsecond=0)
#     start_time = end_time - timedelta(hours=hours)

#     # Construct the query with interval grouping
#     query = select(
#         func.date_trunc('hour', PriceData.timestamp).label('interval_timestamp'),
#         func.first_value(PriceData.open).over(partition_by=func.date_trunc('hour', PriceData.timestamp), order_by=PriceData.timestamp).label('open'),
#         func.last_value(PriceData.close).over(partition_by=func.date_trunc('hour', PriceData.timestamp), order_by=PriceData.timestamp).label('close'),
#         func.max(PriceData.high).label('high'),
#         func.min(PriceData.low).label('low'),
#         func.last_value(PriceData.price_usd).over(partition_by=func.date_trunc('hour', PriceData.timestamp), order_by=PriceData.timestamp).label('price_usd')
#     ).filter(
#         PriceData.token_id == token.id,
#         PriceData.timestamp >= start_time,
#         PriceData.timestamp <= end_time
#     ).group_by(
#         func.date_trunc('hour', PriceData.timestamp)
#     ).order_by(
#         func.date_trunc('hour', PriceData.timestamp)
#     )

#     result = await db.execute(query)
#     price_data = result.fetchall()

#     # Construct the data array with the interval data
#     data = [[] for _ in range(5)]  # 5 lists for open, close, high, low, priceUSD
#     current_time = start_time
#     data_index = 0
#     while current_time <= end_time:
#         if data_index < len(price_data) and price_data[data_index].interval_timestamp == current_time:
#             entry = price_data[data_index]
#             timestamp = entry.interval_timestamp.isoformat()
#             data[0].append([timestamp, "open", float(entry.open)])
#             data[1].append([timestamp, "close", float(entry.close)])
#             data[2].append([timestamp, "high", float(entry.high)])
#             data[3].append([timestamp, "low", float(entry.low)])
#             data[4].append([timestamp, "priceUSD", float(entry.price_usd)])
#             data_index += 1
#         else:
#             # If no data for this interval, use the last known values or None
#             timestamp = current_time.isoformat()
#             last_known = data[0][-1] if data[0] else [timestamp, "open", None]
#             data[0].append([timestamp, "open", last_known[2]])
#             data[1].append([timestamp, "close", last_known[2]])
#             data[2].append([timestamp, "high", last_known[2]])
#             data[3].append([timestamp, "low", last_known[2]])
#             data[4].append([timestamp, "priceUSD", last_known[2]])
        
#         current_time += timedelta(hours=interval_hours)

#     return data

@router.get("/chart-data-all/{symbol}", response_model=TokenDataResponse)
async def get_all_chart_data(
    symbol: str, 
    limit: Optional[int] = Query(100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Fetching chart data for symbol: {symbol}, limit: {limit}")
    try:
        # Get the token record by symbol, including the associated price data
        query = select(Token).options(joinedload(Token.price_data)).filter(Token.symbol == symbol)
        result = await db.execute(query)
        token = result.unique().scalar_one_or_none()

        if not token:
            logger.warning(f"Token not found for symbol: {symbol}")
            raise HTTPException(status_code=404, detail="Token not found")

        logger.info(f"Token found: {token.symbol}, Price data count: {len(token.price_data)}")

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
                    priceUSD=float(entry.price_usd)
                ) for entry in price_data
            ]
        )
    except Exception as e:
        logger.exception(f"Error fetching chart data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/debug-price-data/{symbol}")
async def debug_price_data(
    symbol: str,
    limit: int = Query(10, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    try:
        # First, get the token
        token_query = select(Token).filter(Token.symbol == symbol)
        token_result = await db.execute(token_query)
        token = token_result.scalar_one_or_none()

        if not token:
            return {"error": "Token not found"}

        # Now, query for price data
        price_data_query = select(PriceData).filter(PriceData.token_id == token.id).order_by(PriceData.timestamp.desc()).limit(limit)
        price_data_result = await db.execute(price_data_query)
        price_data = price_data_result.scalars().all()

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
                    "price_usd": float(entry.price_usd)
                } for entry in price_data
            ]
        }
    except Exception as e:
        logger.exception(f"Error in debug route for {symbol}: {str(e)}")
        return {"error": str(e)}