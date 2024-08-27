from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.token import Base, Token
from config import DATABASE_URL

def load_static_data():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Sample static data
    tokens = [
        Token(address="0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", symbol="WBTC", name="Wrapped BTC", decimals=8, total_supply="18240", volumeUSD="131145349577.8606626294325873098926"),
        Token(address="0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce", symbol="SHIB", name="SHIBA INU", decimals=18, total_supply="18240", volumeUSD="4390786715.834872099328410391396641"),
        Token(address="0x6810e776880c02933d47db1b9fc05908e5386b96", symbol="GNO", name="Gnosis Token", decimals=6, total_supply="28240", volumeUSD="521604365.044597280535076201717078"),
    ]

    for token in tokens:
        existing_token = db.query(Token).filter_by(address=token.address).first()
        if not existing_token:
            db.add(token)

    db.commit()
    db.close()

if __name__ == "__main__":
    load_static_data()