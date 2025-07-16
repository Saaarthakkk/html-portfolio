from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from sqlalchemy import func

from .. import db
from ..models import Reservation, ReservationStatus, Room, Invoice, Payment, Stay

logger = logging.getLogger('reports')


class ReportingService:
    """Service providing reporting KPIs."""

    @staticmethod
    def occupancy(start_date: date, end_date: date) -> float:
        """Return occupancy percentage between dates."""
        days = (end_date - start_date).days
        if days <= 0:
            return 0.0
        rooms = Room.query.count()
        if rooms == 0:
            return 0.0

        occupied_nights = 0
        reservations = (
            Reservation.query.filter(
                Reservation.status.in_([ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN])
            )
            .filter(Reservation.check_in < end_date, Reservation.check_out > start_date)
            .all()
        )
        for res in reservations:
            start = max(res.check_in, start_date)
            end = min(res.check_out, end_date)
            occupied_nights += (end - start).days
        total_nights = rooms * days
        return (occupied_nights / total_nights) * 100

    @staticmethod
    def revenue(start_date: date, end_date: date):
        """Return total revenue from payments."""
        total = (
            db.session.query(func.sum(Payment.amount))
            .join(Invoice)
            .filter(Payment.paid_at >= datetime.combine(start_date, datetime.min.time()))
            .filter(Payment.paid_at < datetime.combine(end_date, datetime.min.time()))
            .scalar()
        )
        return float(total or 0)

    @staticmethod
    def revpar(start_date: date, end_date: date) -> float:
        """Return revenue per available room."""
        revenue = ReportingService.revenue(start_date, end_date)
        days = (end_date - start_date).days
        rooms = Room.query.count()
        if days <= 0 or rooms == 0:
            return 0.0
        return revenue / (rooms * days)

    @staticmethod
    def avg_length_of_stay(month_start: date) -> float:
        """Return average length of stay for stays starting within given month."""
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        stays = (
            Stay.query.join(Reservation)
            .filter(Reservation.check_in >= month_start, Reservation.check_in < next_month)
            .all()
        )
        if not stays:
            return 0.0
        lengths = [(res.actual_check_out or res.reservation.check_out) - (res.actual_check_in or res.reservation.check_in) for res in stays]
        days = [length.days for length in lengths]
        return sum(days) / len(days)
