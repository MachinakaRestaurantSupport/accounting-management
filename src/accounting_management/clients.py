"""HTTP clients for downstream order, guest, and sales services."""

import os
from typing import Any

import httpx


class _BaseServiceClient:
    """Base HTTP client wrapper supporting base_url and transport injection."""

    def __init__(
        self,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            transport=transport,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close underlying HTTP client."""
        self._client.close()


class OrderClient(_BaseServiceClient):
    """Client for the order-management service (I-3)."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 5.0,
    ) -> None:
        resolved_url = base_url or os.getenv("ORDER_SERVICE_URL", "http://localhost:8003")
        super().__init__(base_url=resolved_url, transport=transport, timeout=timeout)

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        """Fetch an order by ID; return None when the order does not exist."""
        response = self._client.get(f"/orders/{order_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def mark_paid(self, order_id: str) -> dict[str, Any]:
        """Notify order-management that the order has been paid."""
        response = self._client.post(f"/orders/{order_id}/mark-paid")
        response.raise_for_status()
        return response.json() if response.content else {}

    def list_orders(self) -> list[dict[str, Any]]:
        """Fetch all orders from order-management."""
        response = self._client.get("/orders")
        response.raise_for_status()
        return response.json()

    def get_table_bill(self, table_id: str) -> dict[str, Any]:
        """Fetch unpaid orders summary for a table."""
        response = self._client.get(f"/tables/{table_id}/bill")
        response.raise_for_status()
        return response.json()


class GuestClient(_BaseServiceClient):
    """Client for the guest-management service (I-6)."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 5.0,
    ) -> None:
        resolved_url = base_url or os.getenv("GUEST_SERVICE_URL", "http://localhost:8006")
        super().__init__(base_url=resolved_url, transport=transport, timeout=timeout)

    def request_cleaning(self, table_id: str) -> dict[str, Any]:
        """Request table cleaning after dine-in payment completion."""
        response = self._client.post(f"/tables/{table_id}/request-cleaning")
        response.raise_for_status()
        return response.json() if response.content else {}


class SalesClient(_BaseServiceClient):
    """Client for the sales-management service (I-4)."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 5.0,
    ) -> None:
        resolved_url = base_url or os.getenv("SALES_SERVICE_URL", "http://localhost:8004")
        super().__init__(base_url=resolved_url, transport=transport, timeout=timeout)

    def record_sale(
        self,
        *,
        order_id: str,
        payment_id: str,
        channel: str,
        amount: int,
        recorded_at: str,
    ) -> dict[str, Any]:
        """Record a completed sale in sales-management."""
        payload = {
            "order_id": order_id,
            "payment_id": payment_id,
            "channel": channel,
            "amount": amount,
            "recorded_at": recorded_at,
        }
        response = self._client.post("/sales/records", json=payload)
        response.raise_for_status()
        return response.json() if response.content else {}
