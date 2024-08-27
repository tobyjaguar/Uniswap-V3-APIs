from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from routes import chart_data
from services.uniswap_subgraph import UniswapSubgraphService
from scripts.load_static_data import load_static_data

app = FastAPI(title="Uniswap V3 Data API")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize Uniswap subgraph service
uniswap_service = UniswapSubgraphService()

# Include routers
app.include_router(chart_data.router)

@app.on_event("startup")
async def startup_event():
    # You can add any startup events here, like initializing the database
    Base.metadata.create_all(bind=engine)
    # load static data
    load_static_data()

@app.get("/")
async def root():
    return {"message": "Welcome to Uniswap V3 Data API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)