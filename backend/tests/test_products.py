def test_create_product_normalises_sku(product):
    assert product["sku"] == "KB-101"
    assert product["quantity"] == 20
    assert product["low_stock"] is False


def test_duplicate_sku_rejected(client, product):
    response = client.post("/api/products", json={"sku": "KB-101", "name": "Another"})
    assert response.status_code == 409


def test_invalid_payload_rejected(client):
    response = client.post("/api/products", json={"sku": "bad sku!", "name": "", "unit_price": -1})
    assert response.status_code == 422


def test_get_product(client, product):
    response = client.get(f"/api/products/{product['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Mechanical Keyboard"


def test_get_missing_product_returns_404(client):
    assert client.get("/api/products/999").status_code == 404


def test_update_product(client, product):
    response = client.put(f"/api/products/{product['id']}", json={"unit_price": "59.00", "reorder_level": 25})
    body = response.json()
    assert response.status_code == 200
    assert body["unit_price"] == "59.00"
    assert body["low_stock"] is True


def test_update_cannot_change_quantity_directly(client, product):
    response = client.put(f"/api/products/{product['id']}", json={"quantity": 999})
    assert response.status_code == 200
    assert response.json()["quantity"] == 20


def test_delete_product(client, product):
    assert client.delete(f"/api/products/{product['id']}").status_code == 204
    assert client.get(f"/api/products/{product['id']}").status_code == 404


def test_list_filters(client, product):
    client.post("/api/products", json={"sku": "CBL-1", "name": "USB-C Cable", "category": "Cables",
                                       "quantity": 2, "reorder_level": 10})

    assert len(client.get("/api/products").json()) == 2
    assert [p["sku"] for p in client.get("/api/products?q=usb").json()] == ["CBL-1"]
    assert [p["sku"] for p in client.get("/api/products?category=Peripherals").json()] == ["KB-101"]
    assert [p["sku"] for p in client.get("/api/products?low_stock=true").json()] == ["CBL-1"]
