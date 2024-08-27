import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from services.database import close_db
from routes import token
from scripts.reset_db import reset_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup within reset_db.py
    uniswap_service = await reset_database()
    # Poll for new data every minute
    asyncio.create_task(uniswap_service.start_polling())
    yield
    # Shutdown
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

# Router for tokens data
app.include_router(token.router, prefix="/api", tags=["tokens"])

@app.get("/")
async def root():
    return {"message": "Welcome to Uniswap V3 Data API"}