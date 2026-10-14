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


def test_stock_movement_metric(client, product):
    client.post(f"/api/products/{product['id']}/movements", json={"change": -2, "reason": "SALE"})
    metrics = client.get("/metrics").text
    assert 'stockroom_stock_units_moved_total{direction="out",reason="SALE"}' in metrics
