"""
test_health.py — Basic API health check tests

Run with:  pytest app/tests/test_health.py -v
"""


def test_root_endpoint(client):
    """Root endpoint should return 200 with app info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint_returns_200(client):
    """Health endpoint should always return 200 even if DB is down."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
