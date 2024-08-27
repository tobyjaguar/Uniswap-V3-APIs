from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from models.token import Token
from main import get_db

router = APIRouter()

@router.get("/tokens", response_model=List[dict])
async def read_tokens(db: Session = Depends(get_db)):
    tokens = db.query(Token).all()
    return [{"symbol": token.symbol, "name": token.name, "address": token.address} for token in tokens]