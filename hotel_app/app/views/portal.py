from __future__ import annotations

import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, current_user
from wtforms import Form, StringField, PasswordField, DateField, IntegerField, HiddenField, validators

from ..services.guest_service import GuestService
from ..services.reservation_service import ReservationService
from ..models import Room, UserRole

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')
logger = logging.getLogger('portal')
handler = logging.FileHandler('logs/portal.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RegisterForm(Form):
    """Guest registration form."""

    username = StringField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])
    name = StringField('Name', [validators.InputRequired()])


class SearchForm(Form):
    """Form for searching room availability."""

    check_in = DateField('Check In', [validators.InputRequired()], format='%Y-%m-%d')
    check_out = DateField('Check Out', [validators.InputRequired()], format='%Y-%m-%d')
    guests = IntegerField('Guests', [validators.InputRequired(), validators.NumberRange(min=1)])
    room_id = HiddenField('Room')


@portal_bp.route('/register', methods=['GET', 'POST'])
def register() -> str:
    """Register a guest account and log in."""
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            user = GuestService.register_guest(form.username.data, form.password.data, form.name.data)
            login_user(user)
            flash('Registration successful')
            return redirect(url_for('portal.search'))
        except Exception as exc:  # pylint: disable=broad-except
            flash(str(exc))
    return render_template('portal/register.html', form=form)


@portal_bp.route('/search', methods=['GET'])
@login_required
def search() -> str:
    """Search for available rooms."""
    form = SearchForm(request.args)
    rooms: list[Room] = []
    if request.args and form.validate():
        rooms = ReservationService.available_rooms(form.check_in.data, form.check_out.data, form.guests.data)
    return render_template('portal/search.html', form=form, rooms=rooms)


@portal_bp.route('/book', methods=['POST'])
@login_required
def book() -> str:
    """Book a selected room."""
    form = SearchForm(request.form)
    if form.validate():
        room = Room.query.get_or_404(int(form.room_id.data))
        guest = current_user.guest
        try:
            ReservationService.create_reservation(guest, room, form.check_in.data, form.check_out.data)
            logger.info('Guest booking: user=%s room=%s', current_user.id, room.id)
            return render_template('portal/confirm.html', room=room)
        except Exception as exc:  # pylint: disable=broad-except
            flash(str(exc))
            return redirect(url_for('portal.search', **request.form))
    flash('Invalid data')
    return redirect(url_for('portal.search'))
