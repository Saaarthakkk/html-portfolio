from __future__ import annotations

import logging

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from wtforms import (
    Form,
    StringField,
    DecimalField,
    IntegerField,
    SelectField,
    DateField,
    validators,
)

from ..models import Room, RoomType, RoomStatus, UserRole, RateCard
from ..services.room_service import RoomService
from ..utils.roles import role_required

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')
logger = logging.getLogger('rooms')
handler = logging.FileHandler('logs/rooms.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RoomTypeForm(Form):
    """Form for creating a room type."""

    name = StringField('Name', [validators.InputRequired()])
    description = StringField('Description')
    default_rate = DecimalField('Default Rate', [validators.InputRequired()])
    capacity = IntegerField('Capacity', [validators.InputRequired()])


class RoomForm(Form):
    """Form for creating a room."""

    room_number = StringField('Room Number', [validators.InputRequired()])
    room_type_id = SelectField('Room Type', coerce=int)
    floor = IntegerField('Floor', [validators.InputRequired()])
    base_rate = DecimalField('Base Rate')


class RateCardForm(Form):
    """Form for creating a rate card."""

    room_type_id = SelectField('Room Type', coerce=int)
    start_date = DateField('Start Date', [validators.InputRequired()], format='%Y-%m-%d')
    end_date = DateField('End Date', [validators.InputRequired()], format='%Y-%m-%d')
    override_rate = DecimalField('Override Rate', [validators.InputRequired()])


@rooms_bp.route('/room_types', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.MANAGER, UserRole.ADMIN)
def room_types() -> str:
    """List and create room types."""
    form = RoomTypeForm(request.form)
    if request.method == 'POST' and form.validate():
        RoomService.create_room_type(
            form.name.data,
            form.description.data,
            float(form.default_rate.data),
            form.capacity.data,
        )
    types = RoomType.query.all()
    return render_template('rooms/form.html', form=form, types=types)


@rooms_bp.route('/', methods=['GET'])
@login_required
def list_rooms() -> str:
    """List rooms with optional search."""
    status_filter = request.args.get('status')
    query = Room.query
    if status_filter:
        query = query.filter_by(status=RoomStatus(status_filter))
    rooms = query.all()
    return render_template('rooms/list.html', rooms=rooms, RoomStatus=RoomStatus)


@rooms_bp.route('/<int:room_id>/set_status', methods=['POST'])
@login_required
@role_required(UserRole.MANAGER, UserRole.ADMIN)
def set_status(room_id: int):
    """AJAX endpoint to update room status."""
    status = RoomStatus(request.form.get('status'))
    user_id = 1  # placeholder for authenticated admin
    room = RoomService.set_status(room_id, status, user_id)
    return jsonify({'room_id': room.id, 'status': room.status.value})


@rooms_bp.route('/rooms/create', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.MANAGER, UserRole.ADMIN)
def create_room() -> str:
    """Create a new room."""
    form = RoomForm(request.form)
    form.room_type_id.choices = [(rt.id, rt.name) for rt in RoomType.query.all()]
    if request.method == 'POST' and form.validate():
        room_type = RoomType.query.get(form.room_type_id.data)
        try:
            RoomService.create_room(
                form.room_number.data,
                room_type,
                form.floor.data,
                float(form.base_rate.data) if form.base_rate.data else None,
                current_user.id,
            )
            flash('Room created')
            return redirect(url_for('rooms.list_rooms'))
        except Exception as exc:  # pylint: disable=broad-except
            flash(str(exc))
    return render_template('rooms/room_form.html', form=form)


@rooms_bp.route('/ratecards', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.MANAGER, UserRole.ADMIN)
def ratecards() -> str:
    """List and create rate card overrides."""
    form = RateCardForm(request.form)
    form.room_type_id.choices = [(rt.id, rt.name) for rt in RoomType.query.all()]
    if request.method == 'POST' and form.validate():
        room_type = RoomType.query.get(form.room_type_id.data)
        RoomService.set_rate_override(
            room_type,
            form.start_date.data,
            form.end_date.data,
            float(form.override_rate.data),
            current_user.id,
        )
    cards = RateCard.query.all()
    return render_template('rooms/ratecards.html', form=form, cards=cards)
