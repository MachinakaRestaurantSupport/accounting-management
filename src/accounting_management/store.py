"""In-memory store for payment records."""

from accounting_management.models import Payment


class PaymentStore:
    """Thread-safe-ready simple in-memory store for payments."""

    def __init__(self) -> None:
        self._payments: dict[str, Payment] = {}

    def save(self, payment: Payment) -> Payment:
        """Persist a payment record and return it."""
        self._payments[payment.id] = payment
        return payment

    def get(self, payment_id: str) -> Payment | None:
        """Retrieve a payment record by ID, or None if not found."""
        return self._payments.get(payment_id)

    def list_all(self) -> list[Payment]:
        """Return all stored payment records."""
        return list(self._payments.values())
