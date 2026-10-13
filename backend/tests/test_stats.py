def test_stats_empty(client):
    body = client.get("/api/stats").json()
    assert body["products"] == 0
    assert body["inventory_value"] == "0.00"


def test_stats_totals(client, product):
    client.post("/api/products", json={"sku": "MS-1", "name": "Mouse", "category": "Peripherals",
                                       "unit_price": "10.00", "quantity": 0, "reorder_level": 3})
    body = client.get("/api/stats").json()

    assert body["products"] == 2
    assert body["units"] == 20
    assert body["inventory_value"] == "999.80"
    assert body["low_stock"] == 1
    assert body["out_of_stock"] == 1
    assert body["categories"] == [{"category": "Peripherals", "products": 2, "units": 20}]
