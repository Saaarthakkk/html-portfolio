from __future__ import annotations

from decimal import Decimal
import logging

from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import Invoice, Payment, PaymentMethod

logger = logging.getLogger('billing')


class BillingService:
    """Service layer for billing operations."""

    @staticmethod
    def add_payment(invoice_id: int, amount: Decimal, method: PaymentMethod, user_id: int) -> Payment:
        """Record a payment and update invoice status."""
        invoice = Invoice.query.get(invoice_id)
        if invoice is None:
            raise ValueError('Invoice not found')
        payment = Payment(invoice=invoice, amount=amount, method=method)
        db.session.add(payment)
        try:
            db.session.flush()
            total_paid = sum(p.amount for p in invoice.payments)
            if total_paid >= invoice.total:
                invoice.paid = True
            db.session.commit()
            logger.info(
                'Payment recorded: invoice=%s user=%s amount=%s method=%s',
                invoice_id,
                user_id,
                amount,
                method.value,
            )
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc
        return payment
