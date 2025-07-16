from __future__ import annotations

from decimal import Decimal
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from wtforms import Form, DecimalField, SelectField, validators

from ..models import Invoice, PaymentMethod, UserRole
from ..services.billing_service import BillingService
from ..utils.roles import role_required

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')
logger = logging.getLogger('billing')
handler = logging.FileHandler('logs/billing.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class PaymentForm(Form):
    """Form for recording payments."""

    amount = DecimalField('Amount', [validators.InputRequired()])
    method = SelectField('Method', choices=[(m.name, m.name) for m in PaymentMethod])


@billing_bp.route('/invoices/open')
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def open_invoices() -> str:
    """List unpaid invoices."""
    invoices = Invoice.query.filter_by(paid=False).all()
    return render_template('billing/open_invoices.html', invoices=invoices)


@billing_bp.route('/invoice/<int:invoice_id>')
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def invoice_detail(invoice_id: int) -> str:
    """Show invoice with payment form."""
    invoice = Invoice.query.get_or_404(invoice_id)
    form = PaymentForm()
    return render_template('billing/invoice_detail.html', invoice=invoice, form=form)


@billing_bp.route('/invoice/<int:invoice_id>/pay', methods=['POST'])
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def pay_invoice(invoice_id: int):
    """Record payment for an invoice."""
    form = PaymentForm(request.form)
    if form.validate():
        BillingService.add_payment(
            invoice_id,
            Decimal(form.amount.data),
            PaymentMethod(form.method.data),
            current_user.id,
        )
        flash('Payment recorded')
    else:
        flash('Invalid payment data')
    return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
