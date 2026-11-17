"""FastAPI application and endpoints for accounting-management."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status

from accounting_management.clients import GuestClient, OrderClient, SalesClient
from accounting_management.models import HealthResponse, Payment, PaymentCreate
from accounting_management.store import PaymentStore
from accounting_management.ui import create_ui_router


def create_app(
    order_client: OrderClient | None = None,
    guest_client: GuestClient | None = None,
    sales_client: SalesClient | None = None,
) -> FastAPI:
    """Create and configure the accounting-management FastAPI application."""
    application = FastAPI(title="accounting-management", version="0.1.0")
    store = PaymentStore()
    resolved_order_client = order_client or OrderClient()
    resolved_guest_client = guest_client or GuestClient()
    resolved_sales_client = sales_client or SalesClient()
    application.include_router(create_ui_router(store, resolved_order_client))

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="accounting-management")

    @application.post(
        "/payments",
        response_model=Payment,
        status_code=status.HTTP_201_CREATED,
    )
    def create_payment(payload: PaymentCreate) -> Payment:
        order = resolved_order_client.get_order(payload.order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order '{payload.order_id}' not found",
            )

        if order.get("paid") is True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Order '{payload.order_id}' is already paid",
            )

        total_amount = int(order["total_amount"])
        if payload.received_amount < total_amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Insufficient received_amount ({payload.received_amount}) "
                    f"for total_amount ({total_amount})"
                ),
            )

        payment_id = f"pay_{uuid4().hex[:12]}"
        paid_at = datetime.now(UTC).isoformat()
        receipt_number = f"RCP-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        change_amount = payload.received_amount - total_amount

        resolved_order_client.mark_paid(payload.order_id)

        source = str(order.get("source", ""))
        table_id = order.get("table_id")
        if source == "dine_in" and table_id:
            resolved_guest_client.request_cleaning(str(table_id))

        resolved_sales_client.record_sale(
            order_id=payload.order_id,
            payment_id=payment_id,
            channel=source,
            amount=total_amount,
            recorded_at=paid_at,
        )

        payment = Payment(
            id=payment_id,
            order_id=payload.order_id,
            amount=total_amount,
            received_amount=payload.received_amount,
            change_amount=change_amount,
            method=payload.method,
            receipt_number=receipt_number,
            paid_at=paid_at,
        )
        return store.save(payment)

    @application.get("/payments/{payment_id}", response_model=Payment)
    def get_payment(payment_id: str) -> Payment:
        payment = store.get(payment_id)
        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment '{payment_id}' not found",
            )
        return payment

    return application


app = create_app()
