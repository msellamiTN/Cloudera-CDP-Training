"""HTTP contract tests; run against an API connected to a populated HBase table."""
import os
import requests

BASE_URL = os.getenv("API_TEST_URL", "http://localhost:8001")


def test_health():
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_known_product():
    product_id = os.getenv("TEST_PRODUCT_ID", "1004")
    response = requests.get(
        f"{BASE_URL}/products/{product_id}/analytics", timeout=10
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["product_id"] == product_id
    assert "product_name" in payload
    assert "revenue" in payload
    assert "view_number" in payload


def test_unknown_product():
    response = requests.get(
        f"{BASE_URL}/products/__missing_product__", timeout=10
    )
    assert response.status_code == 404
