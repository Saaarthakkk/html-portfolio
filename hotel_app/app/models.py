from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from . import db


class ReservationStatus(Enum):
    """Enumerates reservation statuses."""

    BOOKED = 'Booked'
    CHECKED_IN = 'Checked-In'
    CHECKED_OUT = 'Checked-Out'
    CANCELLED = 'Cancelled'


class UserRole(Enum):
    """Enumerates user roles."""

    ADMIN = 'Admin'
    MANAGER = 'Manager'
    RECEPTION = 'Receptionist'
    HK = 'Housekeeping'
    GUEST = 'Guest'


class User(UserMixin, db.Model):
    """Application user model."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.GUEST)
    guest = db.relationship('Guest', back_populates='user', uselist=False)

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if password matches stored hash."""
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)


class Guest(db.Model):
    """Guest model."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    name = db.Column(db.String(100), nullable=False)
    reservations = db.relationship('Reservation', back_populates='guest')
    user = db.relationship('User', back_populates='guest', uselist=False)


class RoomStatus(Enum):
    """Status of a hotel room."""

    AVAILABLE = 'Available'
    OUT_OF_ORDER = 'Out-of-Order'
    CLEANING = 'Cleaning'


class RoomType(db.Model):
    """Category of rooms."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    default_rate = db.Column(db.Numeric(10, 2), nullable=False)
    capacity = db.Column(db.Integer)
    rooms = db.relationship('Room', back_populates='room_type')


class Room(db.Model):
    """Physical room in the hotel."""

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    room_type_id = db.Column(
        db.Integer, db.ForeignKey('room_type.id', ondelete='RESTRICT'), nullable=False
    )
    floor = db.Column(db.Integer)
    status = db.Column(db.Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    base_rate = db.Column(db.Numeric(10, 2))
    clean_status = db.Column(db.String(20), default='Dirty')

    room_type = db.relationship('RoomType', back_populates='rooms')
    reservations = db.relationship('Reservation', back_populates='room')


class RateCard(db.Model):
    """Rate override for a room type."""

    id = db.Column(db.Integer, primary_key=True)
    room_type_id = db.Column(
        db.Integer, db.ForeignKey('room_type.id', ondelete='CASCADE'), nullable=False
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    override_rate = db.Column(db.Numeric(10, 2), nullable=False)

    room_type = db.relationship('RoomType')


class Reservation(db.Model):
    """Reservation model."""

    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), default=ReservationStatus.BOOKED)
    total_cost = db.Column(db.Float)

    guest = db.relationship('Guest', back_populates='reservations')
    room = db.relationship('Room', back_populates='reservations')

    def overlaps(self, other_check_in: date, other_check_out: date) -> bool:
        """Return True if dates overlap."""
        return not (self.check_out <= other_check_in or self.check_in >= other_check_out)


class HousekeepingStatus(Enum):
    """Status of housekeeping tasks."""

    PENDING = 'Pending'
    IN_PROGRESS = 'In-Progress'
    DONE = 'Done'


class HousekeepingTask(db.Model):
    """Housekeeping task assigned to staff."""

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    assigned_to = db.Column(db.Integer, nullable=False)
    task_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(HousekeepingStatus), default=HousekeepingStatus.PENDING)
    notes = db.Column(db.String(200))
    completed_at = db.Column(db.DateTime)

    room = db.relationship('Room')


class Stay(db.Model):
    """Represents an active stay derived from a reservation."""

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(
        db.Integer, db.ForeignKey('reservation.id'), nullable=False, unique=True
    )
    actual_check_in = db.Column(db.DateTime)
    actual_check_out = db.Column(db.DateTime)
    assigned_room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    reservation = db.relationship('Reservation')
    room = db.relationship('Room')


class Invoice(db.Model):
    """Billing record for a reservation."""

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    total = db.Column(db.Numeric(10, 2))
    paid = db.Column(db.Boolean, default=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    reservation = db.relationship('Reservation')
    extras = db.relationship('ExtraCharge', back_populates='invoice')
    payments = db.relationship('Payment', back_populates='invoice')


class ExtraCharge(db.Model):
    """Additional charge attached to an invoice."""

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    invoice = db.relationship('Invoice', back_populates='extras')


class PaymentMethod(Enum):
    """Payment methods."""

    CASH = 'CASH'
    CARD = 'CARD'


class Payment(db.Model):
    """Payment for an invoice."""

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.Enum(PaymentMethod))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship('Invoice', back_populates='payments')
