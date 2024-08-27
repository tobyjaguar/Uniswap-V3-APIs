# import sys
# import os

# # Add the parent directory to the Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from database import init_db
from scripts.load_static_data import load_static_data


async def reset_database():
    await init_db()
    await load_static_data()
    print("Database has been reset.")

if __name__ == "__main__":
    asyncio.run(reset_database())