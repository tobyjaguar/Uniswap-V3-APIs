from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from services.database import Base

"""
    A not about the PriceData model:
    The fields are numeric(78, 18) because we are dealing with token prices.
    Typically on the frontend these are strings because the precision will 
    overflow the Number type in javascript. The tokens table uses strings for
    total_supply and volumeUSD for this default reason. Here, however, the
    expectation is that these values will be used for calculations and as such
    the database numeric type is leveraged for large numbers, maintaining the precision.
"""

class PriceData(Base):
    __tablename__ = "price_data"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Numeric(78, 18), nullable=False)
    close = Column(Numeric(78, 18), nullable=False)
    high = Column(Numeric(78, 18), nullable=False)
    low = Column(Numeric(78, 18), nullable=False)
    price_usd = Column(Numeric(78, 18), nullable=False)

    __table_args__ = (
        UniqueConstraint('token_id', 'timestamp', name='uix_token_timestamp'),
    )

    # relationship with tokens for the index
    token = relationship("Token", back_populates="price_data")

    def __repr__(self):
        return f"<PriceData(token_id='{self.token_id}', timestamp='{self.timestamp}', price_usd='{self.price_usd}')>"