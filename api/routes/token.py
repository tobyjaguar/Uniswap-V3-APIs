from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta

from models.token import Token
from models.chart_data import PriceData
from services.database import get_db

router = APIRouter()

@router.get("/tokens", response_model=List[dict])
async def read_tokens(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Token))
    tokens = result.scalars().all()
    return [{"symbol": token.symbol, "name": token.name, "address": token.address} for token in tokens]

@router.get("/token_price_data/{symbol}")
async def get_token_price_data(symbol: str, hours: int, interval_hours: int = 1, db: AsyncSession = Depends(get_db)):
    # Get the token record by symbol
    token_result = await db.execute(select(Token).filter(Token.symbol == symbol))
    token = token_result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Calculate the start time and end time
    end_time = datetime.now(datetime.UTC).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours)

    # Construct the query with interval grouping
    query = select(
        func.date_trunc('hour', PriceData.timestamp).label('interval_timestamp'),
        func.first_value(PriceData.open).over(partition_by=func.date_trunc('hour', PriceData.timestamp), order_by=PriceData.timestamp).label('open'),
        func.last_value(PriceData.close).over(partition_by=func.date_trunc('hour', PriceData.timestamp), order_by=PriceData.timestamp).label('close'),
        func.max(PriceData.high).label('high'),
        func.min(PriceData.low).label('low'),
        func.last_value(PriceData.price_usd).over(partition_by=func.date_trunc('hour', PriceData.timestamp), order_by=PriceData.timestamp).label('price_usd')
    ).filter(
        PriceData.token_id == token.id,
        PriceData.timestamp >= start_time,
        PriceData.timestamp <= end_time
    ).group_by(
        func.date_trunc('hour', PriceData.timestamp)
    ).order_by(
        func.date_trunc('hour', PriceData.timestamp)
    )

    result = await db.execute(query)
    price_data = result.fetchall()

    # Construct the data array with the interval data
    data = [[] for _ in range(5)]  # 5 lists for open, close, high, low, priceUSD
    current_time = start_time
    data_index = 0
    while current_time <= end_time:
        if data_index < len(price_data) and price_data[data_index].interval_timestamp == current_time:
            entry = price_data[data_index]
            timestamp = entry.interval_timestamp.isoformat()
            data[0].append([timestamp, "open", float(entry.open)])
            data[1].append([timestamp, "close", float(entry.close)])
            data[2].append([timestamp, "high", float(entry.high)])
            data[3].append([timestamp, "low", float(entry.low)])
            data[4].append([timestamp, "priceUSD", float(entry.price_usd)])
            data_index += 1
        else:
            # If no data for this interval, use the last known values or None
            timestamp = current_time.isoformat()
            last_known = data[0][-1] if data[0] else [timestamp, "open", None]
            data[0].append([timestamp, "open", last_known[2]])
            data[1].append([timestamp, "close", last_known[2]])
            data[2].append([timestamp, "high", last_known[2]])
            data[3].append([timestamp, "low", last_known[2]])
            data[4].append([timestamp, "priceUSD", last_known[2]])
        
        current_time += timedelta(hours=interval_hours)

    return data