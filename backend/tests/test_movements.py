def test_opening_stock_is_recorded(client, product):
    movements = client.get(f"/api/products/{product['id']}/movements").json()
    assert len(movements) == 1
    assert movements[0]["change"] == 20
    assert movements[0]["reason"] == "RESTOCK"


def test_sale_reduces_quantity(client, product):
    response = client.post(f"/api/products/{product['id']}/movements", json={"change": -8, "reason": "SALE"})
    assert response.status_code == 201
    assert response.json()["product_name"] == "Mechanical Keyboard"
    assert client.get(f"/api/products/{product['id']}").json()["quantity"] == 12


def test_cannot_go_below_zero(client, product):
    response = client.post(f"/api/products/{product['id']}/movements", json={"change": -21, "reason": "SALE"})
    assert response.status_code == 409
    assert client.get(f"/api/products/{product['id']}").json()["quantity"] == 20


def test_zero_change_rejected(client, product):
    response = client.post(f"/api/products/{product['id']}/movements", json={"change": 0, "reason": "SALE"})
    assert response.status_code == 422


def test_unknown_reason_rejected(client, product):
    response = client.post(f"/api/products/{product['id']}/movements", json={"change": 1, "reason": "GIFT"})
    assert response.status_code == 422


def test_movement_for_missing_product(client):
    response = client.post("/api/products/42/movements", json={"change": 1, "reason": "RESTOCK"})
    assert response.status_code == 404


def test_recent_movements_newest_first(client, product):
    client.post(f"/api/products/{product['id']}/movements", json={"change": -3, "reason": "SALE"})
    movements = client.get("/api/movements?limit=5").json()
    assert [m["change"] for m in movements] == [-3, 20]
