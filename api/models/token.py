from sqlalchemy import Column, Integer, String, Float
from database import Base


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True)
    symbol = Column(String)
    name = Column(String)
    decimals = Column(Integer)
    total_supply = Column(Float)

    def __repr__(self):
        return f"<Token(symbol='{self.symbol}', name='{self.name}')>"