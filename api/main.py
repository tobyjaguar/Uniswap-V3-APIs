from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, close_db
from routes import token
# from routes import chart_data
# from services.uniswap_subgraph import UniswapSubgraphService
from scripts.load_static_data import load_static_data

# Initialize Uniswap subgraph service
# uniswap_service = UniswapSubgraphService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # await init_db()
    # await load_static_data()
    # Startup within reset_db.py
    yield
    await close_db()

app = FastAPI(title="Uniswap V3 Data API", lifespan=lifespan)

# CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Routers
# app.include_router(chart_data.router)
app.include_router(token.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Uniswap V3 Data API"}