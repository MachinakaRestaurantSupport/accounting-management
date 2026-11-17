"""Unit tests for accounting-management payment endpoints and service integrations."""

import json

import httpx
from fastapi.testclient import TestClient

from accounting_management.clients import GuestClient, OrderClient, SalesClient
from accounting_management.main import create_app


def _build_test_client(
    orders: dict[str, dict],
) -> tuple[TestClient, list[tuple[str, str, dict | None]]]:
    """Create a FastAPI TestClient with MockTransport-backed downstream clients."""
    calls: list[tuple[str, str, dict | None]] = []

    def order_handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path.startswith("/orders/"):
            order_id = path.removeprefix("/orders/")
            calls.append(("order", f"GET {path}", None))
            order = orders.get(order_id)
            if order is None:
                return httpx.Response(404, json={"detail": "Not found"})
            return httpx.Response(200, json=order)
        if request.method == "POST" and path.endswith("/mark-paid"):
            calls.append(("order", f"POST {path}", None))
            order_id = path.removeprefix("/orders/").removesuffix("/mark-paid")
            if order_id in orders:
                orders[order_id]["paid"] = True
            return httpx.Response(200, json={"status": "paid"})
        if request.method == "GET" and path.startswith("/tables/") and path.endswith("/bill"):
            calls.append(("order", f"GET {path}", None))
            table_id = path.removeprefix("/tables/").removesuffix("/bill")
            unpaid = [
                oid
                for oid, o in orders.items()
                if o.get("table_id") == table_id and not o.get("paid", False)
            ]
            return httpx.Response(
                200,
                json={
                    "table_id": table_id,
                    "order_ids": unpaid,
                    "total_amount": sum(orders[oid]["total_amount"] for oid in unpaid),
                },
            )
        return httpx.Response(404)

    def guest_handler(request: httpx.Request) -> httpx.Response:
        calls.append(("guest", f"{request.method} {request.url.path}", None))
        return httpx.Response(200, json={"status": "cleaning_requested"})

    def sales_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8")) if request.content else None
        calls.append(("sales", f"{request.method} {request.url.path}", body))
        return httpx.Response(201, json={"status": "recorded"})

    app = create_app(
        order_client=OrderClient(
            base_url="http://order-service",
            transport=httpx.MockTransport(order_handler),
        ),
        guest_client=GuestClient(
            base_url="http://guest-service",
            transport=httpx.MockTransport(guest_handler),
        ),
        sales_client=SalesClient(
            base_url="http://sales-service",
            transport=httpx.MockTransport(sales_handler),
        ),
    )
    return TestClient(app), calls


def test_health_endpoint() -> None:
    client, _ = _build_test_client({})
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "accounting-management"}


def test_cash_payment_change_and_dine_in_integrations() -> None:
    orders = {
        "ord-1": {
            "id": "ord-1",
            "source": "dine_in",
            "table_id": "T-05",
            "total_amount": 1850,
            "paid": False,
        }
    }
    client, calls = _build_test_client(orders)

    response = client.post(
        "/payments",
        json={"order_id": "ord-1", "method": "cash", "received_amount": 2000},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == "ord-1"
    assert data["amount"] == 1850
    assert data["received_amount"] == 2000
    assert data["change_amount"] == 150
    assert data["method"] == "cash"
    assert data["receipt_number"].startswith("RCP-")
    assert data["paid_at"]

    # Verify downstream calls: I-3 mark-paid, I-6 cleaning, I-4 sales record
    assert ("order", "GET /orders/ord-1", None) in calls
    assert ("order", "POST /orders/ord-1/mark-paid", None) in calls
    assert ("guest", "POST /tables/T-05/request-cleaning", None) in calls

    sales_calls = [c for c in calls if c[0] == "sales"]
    assert len(sales_calls) == 1
    assert sales_calls[0][1] == "POST /sales/records"
    assert sales_calls[0][2] == {
        "order_id": "ord-1",
        "payment_id": data["id"],
        "channel": "dine_in",
        "amount": 1850,
        "recorded_at": data["paid_at"],
    }

    # Verify GET /payments/{payment_id}
    get_resp = client.get(f"/payments/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json() == data


def test_takeout_payment_skips_table_cleaning() -> None:
    orders = {
        "ord-2": {
            "id": "ord-2",
            "source": "takeout",
            "table_id": None,
            "total_amount": 1200,
            "paid": False,
        }
    }
    client, calls = _build_test_client(orders)

    response = client.post(
        "/payments",
        json={"order_id": "ord-2", "method": "qr", "received_amount": 1200},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["change_amount"] == 0

    assert not any(c[0] == "guest" for c in calls)
    sales_calls = [c for c in calls if c[0] == "sales"]
    assert len(sales_calls) == 1
    assert sales_calls[0][2]["channel"] == "takeout"


def test_duplicate_payment_returns_409() -> None:
    orders = {
        "ord-paid": {
            "id": "ord-paid",
            "source": "dine_in",
            "table_id": "T-01",
            "total_amount": 1000,
            "paid": True,
        }
    }
    client, calls = _build_test_client(orders)

    response = client.post(
        "/payments",
        json={"order_id": "ord-paid", "method": "card", "received_amount": 1000},
    )
    assert response.status_code == 409
    assert calls == [("order", "GET /orders/ord-paid", None)]


def test_insufficient_amount_returns_422() -> None:
    orders = {
        "ord-3": {
            "id": "ord-3",
            "source": "dine_in",
            "table_id": "T-02",
            "total_amount": 1500,
            "paid": False,
        }
    }
    client, calls = _build_test_client(orders)

    response = client.post(
        "/payments",
        json={"order_id": "ord-3", "method": "cash", "received_amount": 1000},
    )
    assert response.status_code == 422
    assert calls == [("order", "GET /orders/ord-3", None)]


def test_not_found_order_and_payment_return_404() -> None:
    client, _ = _build_test_client({})

    order_resp = client.post(
        "/payments",
        json={"order_id": "missing", "method": "cash", "received_amount": 1000},
    )
    assert order_resp.status_code == 404

    payment_resp = client.get("/payments/non-existent")
    assert payment_resp.status_code == 404


def test_accounting_ui_screens() -> None:
    orders = {
        "ord-1": {
            "id": "ord-1",
            "source": "dine_in",
            "table_id": "T-05",
            "total_amount": 1850,
            "paid": False,
        }
    }
    client, _ = _build_test_client(orders)
    client.post(
        "/payments",
        json={"order_id": "ord-1", "method": "cash", "received_amount": 2000},
    )
    for path in (
        "/ui/accounting/checkout",
        "/ui/accounting/payment",
        "/ui/accounting/receipt",
    ):
        res = client.get(path)
        assert res.status_code == 200
        assert "会計管理" in res.text


def test_split_payment_same_table_requests_cleaning_only_after_last_order() -> None:
    orders = {
        "ord-a": {
            "id": "ord-a",
            "source": "dine_in",
            "table_id": "T-10",
            "total_amount": 1000,
            "paid": False,
        },
        "ord-b": {
            "id": "ord-b",
            "source": "dine_in",
            "table_id": "T-10",
            "total_amount": 500,
            "paid": False,
        },
    }
    client, calls = _build_test_client(orders)

    res_first = client.post(
        "/payments",
        json={"order_id": "ord-a", "method": "card", "received_amount": 1000},
    )
    assert res_first.status_code == 201
    assert not any(c[0] == "guest" for c in calls)

    res_second = client.post(
        "/payments",
        json={"order_id": "ord-b", "method": "cash", "received_amount": 500},
    )
    assert res_second.status_code == 201
    guest_calls = [c for c in calls if c[0] == "guest"]
    assert guest_calls == [("guest", "POST /tables/T-10/request-cleaning", None)]
