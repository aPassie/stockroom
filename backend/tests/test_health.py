def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    assert client.get("/ready").json() == {"status": "READY"}


def test_metrics_exposed(client):
    client.get("/api/products")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
