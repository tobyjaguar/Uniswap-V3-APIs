from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from services.database import Base


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(42), unique=True, index=True, nullable=False)
    symbol = Column(String(10), unique=True, index=True, nullable=False)    
    name = Column(String(100), nullable=False)
    decimals = Column(Integer, nullable=False)
    total_supply = Column(String)
    volumeUSD = Column(String)

    # relationship with PriceData for the index
    price_data = relationship("PriceData", back_populates="token")

    def __repr__(self):
        return f"<Token(symbol='{self.symbol}', name='{self.name}')>"