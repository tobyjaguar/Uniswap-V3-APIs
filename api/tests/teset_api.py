import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from services.database import Base
from config import DATABASE_URL

# Test database URL
TEST_DATABASE_URL = DATABASE_URL + "_test"

@pytest.fixture(scope="module")
def test_app():
    # Set up
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Tear down
    Base.metadata.drop_all(bind=engine)

def test_read_main(test_app):
    response = test_app.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Uniswap V3 Data API"}

def test_read_tokens(test_app):
    response = test_app.get("/tokens")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Add more specific assertions based on your data model