from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from models.token import Token
from database import get_db

router = APIRouter()

@router.get("/tokens", response_model=List[dict])
async def read_tokens(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Token))
    tokens = result.scalars().all()
    return [{"symbol": token.symbol, "name": token.name, "address": token.address} for token in tokens]