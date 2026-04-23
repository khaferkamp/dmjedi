"""Canonical source-row payloads for the all-entity integration fixture."""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal


def _hash_key(*parts: object) -> str:
    payload = "||".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


CUSTOMER_1001_HK = _hash_key(1001)
CUSTOMER_1002_HK = _hash_key(1002)

PRODUCT_2001_HK = _hash_key(2001, "SKU-001")
PRODUCT_2002_HK = _hash_key(2002, "SKU-002")

CUSTOMER_PRODUCT_1001_2001_HK = _hash_key(CUSTOMER_1001_HK, PRODUCT_2001_HK)
CUSTOMER_PRODUCT_1002_2002_HK = _hash_key(CUSTOMER_1002_HK, PRODUCT_2002_HK)

CUSTOMER_MATCH_1001_HK = _hash_key(CUSTOMER_1001_HK, CUSTOMER_1001_HK)


ALL_ENTITY_SOURCE_ROWS: dict[str, list[dict[str, object]]] = {
    "src_Customer": [
        {"customer_id": 1001},
        {"customer_id": 1002},
    ],
    "src_Product": [
        {"product_id": 2001, "sku": "SKU-001"},
        {"product_id": 2002, "sku": "SKU-002"},
    ],
    "src_CustomerDetails": [
        {
            "Customer_hk": CUSTOMER_1001_HK,
            "first_name": "Ana",
            "last_name": "Nguyen",
            "email": "ana.nguyen@example.com",
        },
        {
            "Customer_hk": CUSTOMER_1002_HK,
            "first_name": "Ben",
            "last_name": "Patel",
            "email": "ben.patel@example.com",
        },
    ],
    "src_CustomerProduct": [
        {
            "Customer_hk": CUSTOMER_1001_HK,
            "Product_hk": PRODUCT_2001_HK,
            "quantity": 2,
        },
        {
            "Customer_hk": CUSTOMER_1002_HK,
            "Product_hk": PRODUCT_2002_HK,
            "quantity": 1,
        },
    ],
    "src_CurrentStatus": [
        {
            "Customer_hk": CUSTOMER_1001_HK,
            "status": "active",
            "updated_at": datetime(2026, 1, 5, 9, 30, 0),
        },
        {
            "Customer_hk": CUSTOMER_1002_HK,
            "status": "trial",
            "updated_at": datetime(2026, 1, 6, 14, 45, 0),
        },
    ],
    "src_ActiveRelation": [
        {
            "Customer_hk": CUSTOMER_1001_HK,
            "Product_hk": PRODUCT_2001_HK,
            "score": Decimal("0.98"),
        },
        {
            "Customer_hk": CUSTOMER_1002_HK,
            "Product_hk": PRODUCT_2002_HK,
            "score": Decimal("0.87"),
        },
    ],
    "src_RelationValidity": [
        {
            "CustomerProduct_hk": CUSTOMER_PRODUCT_1001_2001_HK,
            "valid_from": datetime(2026, 1, 5, 0, 0, 0),
            "valid_to": datetime(2026, 12, 31, 23, 59, 59),
        },
        {
            "CustomerProduct_hk": CUSTOMER_PRODUCT_1002_2002_HK,
            "valid_from": datetime(2026, 1, 6, 0, 0, 0),
            "valid_to": datetime(2026, 12, 31, 23, 59, 59),
        },
    ],
    "src_CustomerMatch": [
        {
            "Customer_hk": CUSTOMER_1001_HK,
            "CustomerMatch_hk": CUSTOMER_MATCH_1001_HK,
            "confidence": Decimal("0.91"),
        }
    ],
}
