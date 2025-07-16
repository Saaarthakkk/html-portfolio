from __future__ import annotations

import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from wtforms import Form, DateField, IntegerField, validators

from ..models import Guest, Room, Reservation
from ..services.reservation_service import ReservationService
from ..utils.roles import role_required
from ..models import UserRole

reservations_bp = Blueprint('reservations', __name__, url_prefix='/reservations')
logger = logging.getLogger('reservations')
handler = logging.FileHandler('logs/reservations.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class ReservationCreateForm(Form):
    """Form for creating reservations."""

    guest_id = IntegerField('Guest ID', [validators.InputRequired()])
    room_id = IntegerField('Room ID', [validators.InputRequired()])
    check_in = DateField('Check In', [validators.InputRequired()], format='%Y-%m-%d')
    check_out = DateField('Check Out', [validators.InputRequired()], format='%Y-%m-%d')


class ReservationDatesForm(Form):
    """Form for updating reservation dates."""

    check_in = DateField('Check In', [validators.InputRequired()], format='%Y-%m-%d')
    check_out = DateField('Check Out', [validators.InputRequired()], format='%Y-%m-%d')


@reservations_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def create() -> str:
    """Create a reservation."""
    form = ReservationCreateForm(request.form)
    if request.method == 'POST' and form.validate():
        guest = Guest.query.get(form.guest_id.data)
        room = Room.query.get(form.room_id.data)
        try:
            ReservationService.create_reservation(guest, room, form.check_in.data, form.check_out.data)
            flash('Reservation created')
            return redirect(url_for('reservations.list_reservations'))
        except Exception as exc:  # pylint: disable=broad-except
            flash(str(exc))
    return render_template('reservations/create.html', form=form)


@reservations_bp.route('/list')
@login_required
def list_reservations() -> str:
    """List reservations."""
    reservations = Reservation.query.all()
    return render_template('reservations/list.html', reservations=reservations)


@reservations_bp.route('/edit/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def edit(reservation_id: int) -> str:
    """Edit reservation dates."""
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ReservationDatesForm(request.form, obj=reservation)
    if request.method == 'POST' and form.validate():
        try:
            ReservationService.update_dates(reservation, form.check_in.data, form.check_out.data)
            flash('Reservation updated')
            return redirect(url_for('reservations.list_reservations'))
        except Exception as exc:  # pylint: disable=broad-except
            flash(str(exc))
    return render_template('reservations/edit.html', form=form, reservation=reservation)


@reservations_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@login_required
@role_required(UserRole.RECEPTION, UserRole.MANAGER)
def cancel(reservation_id: int):
    """Cancel reservation."""
    reservation = Reservation.query.get_or_404(reservation_id)
    ReservationService.cancel(reservation)
    flash('Cancelled')
    return redirect(url_for('reservations.list_reservations'))
