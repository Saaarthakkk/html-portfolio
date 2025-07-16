from __future__ import annotations

from datetime import date, timedelta
import logging

from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import Reservation, Room, Guest, ReservationStatus, RateCard

logger = logging.getLogger('reservations')


class ReservationService:
    """Service layer for reservation operations."""

    @staticmethod
    def create_reservation(guest: Guest, room: Room, check_in: date, check_out: date) -> Reservation:
        """Create a reservation if room available."""
        if guest is None or room is None:
            raise ValueError('Invalid guest or room')
        if not ReservationService.is_room_available(room, check_in, check_out):
            raise ValueError('Room not available for given dates')
        reservation = Reservation(guest=guest, room=room, check_in=check_in, check_out=check_out)
        reservation.total_cost = ReservationService.compute_total(room, check_in, check_out)
        db.session.add(reservation)
        try:
            db.session.commit()
            logger.info('Reservation created: guest=%s room=%s', guest.id, room.id)
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc
        return reservation

    @staticmethod
    def cancel(reservation: Reservation) -> None:
        """Cancel reservation."""
        reservation.status = ReservationStatus.CANCELLED
        try:
            db.session.commit()
            logger.info('Reservation cancelled: guest=%s room=%s', reservation.guest_id, reservation.room_id)
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc

    @staticmethod
    def update_dates(reservation: Reservation, check_in: date, check_out: date) -> Reservation:
        """Update reservation dates with availability check."""
        if not ReservationService.is_room_available(reservation.room, check_in, check_out, exclude=reservation.id):
            raise ValueError('Room not available for new dates')
        reservation.check_in = check_in
        reservation.check_out = check_out
        reservation.total_cost = ReservationService.compute_total(reservation.room, check_in, check_out)
        try:
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc
        return reservation

    @staticmethod
    def compute_total(room: Room, check_in: date, check_out: date) -> float:
        """Compute total cost for stay using rate cards."""
        total = 0.0
        current = check_in
        base_rate = float(room.base_rate or room.room_type.default_rate)
        while current < check_out:
            rate = base_rate
            rate_card = (
                RateCard.query.filter_by(room_type_id=room.room_type_id)
                .filter(RateCard.start_date <= current, RateCard.end_date >= current)
                .first()
            )
            if rate_card:
                rate = float(rate_card.override_rate)
            total += rate
            current += timedelta(days=1)
        return total

    @staticmethod
    def is_room_available(room: Room, check_in: date, check_out: date, exclude: int | None = None) -> bool:
        """Check availability of room for given dates."""
        active_statuses = [ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN]
        reservations = Reservation.query.filter_by(room_id=room.id).filter(Reservation.status.in_(active_statuses))
        if exclude:
            reservations = reservations.filter(Reservation.id != exclude)
        for res in reservations:
            if res.overlaps(check_in, check_out):
                return False
        return True

    @staticmethod
    def available_rooms(check_in: date, check_out: date, guests: int) -> list[Room]:
        """Return list of rooms available for the given dates and guest count."""
        rooms = (
            Room.query.join(RoomType)
            .filter(RoomType.capacity >= guests)
            .all()
        )
        return [room for room in rooms if ReservationService.is_room_available(room, check_in, check_out)]
