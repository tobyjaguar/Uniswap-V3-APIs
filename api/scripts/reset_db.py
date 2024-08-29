import sys
import os

# This is called from docker compose, 
# and doesn't have the parent directory in the path
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# pylint: disable=wrong-import-position
import logging
import asyncio
from services.database import init_db, get_db
from services.uniswap_subgraph import UniswapSubgraphService
from config import TOKEN_ADDRESS_ARRAY


async def reset_database():
    logging.basicConfig(level=logging.INFO)
    # Initialize the database
    logging.info(":::::::Initializing database:::::::")
    await init_db()
    db = await anext(get_db())
    # Initialize Uniswap subgraph service
    uniswap_service = UniswapSubgraphService(db)
    # Seed the database with historical data
    await uniswap_service.fetch_and_store_data(TOKEN_ADDRESS_ARRAY)
    logging.info("Database has been reset and initialized with data.")
    return uniswap_service


if __name__ == "__main__":
    asyncio.run(reset_database())
