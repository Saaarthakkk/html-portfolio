from __future__ import annotations

from datetime import datetime
import logging
from decimal import Decimal
from typing import Iterable, Mapping, Any

from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import Reservation, Stay, Invoice, ExtraCharge, Room, ReservationStatus

logger = logging.getLogger('frontdesk')


class FrontDeskService:
    """Service layer for front desk operations."""

    @staticmethod
    def check_in(reservation_id: int, receptionist_id: int) -> Stay:
        """Check a guest in and create a Stay."""
        reservation = Reservation.query.get_or_404(reservation_id)
        assert reservation.status == ReservationStatus.BOOKED
        assert reservation.room.clean_status == 'Clean'
        stay = Stay(
            reservation=reservation,
            actual_check_in=datetime.utcnow(),
            assigned_room_id=reservation.room_id,
        )
        reservation.status = ReservationStatus.CHECKED_IN
        db.session.add(stay)
        try:
            db.session.commit()
            logger.info(
                'Check-in reservation=%s receptionist=%s', reservation_id, receptionist_id
            )
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc
        return stay

    @staticmethod
    def check_out(stay_id: int, extras_list: Iterable[Mapping[str, Any]]) -> Invoice:
        """Check out a stay and generate invoice."""
        stay = Stay.query.get_or_404(stay_id)
        reservation = stay.reservation
        assert reservation.status == ReservationStatus.CHECKED_IN
        stay.actual_check_out = datetime.utcnow()
        reservation.status = ReservationStatus.CHECKED_OUT
        room = stay.room
        room.clean_status = 'Dirty'
        total_room = reservation.total_cost
        invoice = Invoice(reservation=reservation, total=Decimal(total_room))
        db.session.add(invoice)
        for extra in extras_list:
            charge = ExtraCharge(
                invoice=invoice,
                description=extra.get('description', ''),
                amount=Decimal(extra.get('amount', 0)),
            )
            db.session.add(charge)
            invoice.total += charge.amount
        try:
            db.session.commit()
            logger.info('Check-out stay=%s invoice=%s', stay_id, invoice.id)
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc
        return invoice
