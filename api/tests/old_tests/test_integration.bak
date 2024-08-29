from fastapi.testclient import TestClient
from your_app.main import app  # Import your FastAPI app

client = TestClient(app)

def test_get_chart_data_endpoint():
    response = client.get("/chart-data/BTC?hours=24&interval_hours=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # 5 lists for open, close, high, low, priceUSD
    assert all(len(data_type) == 24 for data_type in data)  # 24 data points for each type
    assert all(isinstance(point[0], str) and isinstance(point[2], (float, type(None))) for data_type in data for point in data_type)

    # Test error case
    response = client.get("/chart-data/INVALID_TOKEN?hours=24&interval_hours=1")
    assert response.status_code == 404