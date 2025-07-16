from __future__ import annotations

import logging

from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_required
from wtforms import Form, StringField, DecimalField, FieldList, FormField, validators

from ..services.frontdesk_service import FrontDeskService
from ..models import Stay, UserRole
from ..utils.roles import role_required

frontdesk_bp = Blueprint('frontdesk', __name__, url_prefix='/frontdesk')
logger = logging.getLogger('frontdesk')
handler = logging.FileHandler('logs/frontdesk.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class ExtraForm(Form):
    """Form representing a single extra charge."""

    description = StringField('Description')
    amount = DecimalField('Amount', [validators.InputRequired()])


class ExtrasForm(Form):
    """Container form for multiple extras."""

    extras = FieldList(FormField(ExtraForm))


@frontdesk_bp.route('/check_in/<int:reservation_id>', methods=['POST'])
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def check_in(reservation_id: int):
    """Handle check-in for a reservation."""
    receptionist_id = 1  # placeholder for auth user
    FrontDeskService.check_in(reservation_id, receptionist_id)
    flash('Checked in')
    return redirect(url_for('reservations.list_reservations'))


@frontdesk_bp.route('/check_out/<int:stay_id>', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def check_out(stay_id: int):
    """Handle check-out for a stay."""
    form = ExtrasForm(request.form)
    if request.method == 'POST' and form.validate():
        extras = [field.data for field in form.extras]
        invoice = FrontDeskService.check_out(stay_id, extras)
        flash('Checked out')
        return render_template('invoice.html', invoice=invoice)
    stay = Stay.query.get_or_404(stay_id)
    return render_template('frontdesk/check_out.html', form=form, stay=stay)
