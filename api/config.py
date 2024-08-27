import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_DB', 'db')  # Default to container name if not set
DB_PORT = os.getenv('DB_PORT', '5432')  # Default to 5432 if not set
DB_NAME = os.getenv('DB_NAME')

# Construct Database URL
# postgresql://user:password@db:5432/uniswap_data
DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# API keys
GRAPH_API_KEY = os.getenv('GRAPH_API_KEY')

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Uniswap Subgraph URL
SUBGRAPH_ID = os.getenv('SUBGRAPH_ID')
UNISWAP_SUBGRAPH_URL = f'https://gateway.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/{SUBGRAPH_ID}'