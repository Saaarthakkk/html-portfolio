from __future__ import annotations

from datetime import date
import logging
from blinker import Namespace

from .. import db
from ..models import Room, RoomStatus, RoomType, RateCard

logger = logging.getLogger('rooms')

_signals = Namespace()
room_status_changed = _signals.signal('room_status_changed')


class RoomService:
    """Service layer for room management."""

    @staticmethod
    def create_room(
        room_number: str,
        room_type: RoomType,
        floor: int,
        base_rate: float | None,
        user_id: int,
    ) -> Room:
        """Create a new room with validation."""
        if Room.query.filter_by(room_number=room_number).first():
            raise ValueError("Room number already exists")
        room = Room(
            room_number=room_number,
            room_type=room_type,
            floor=floor,
            base_rate=base_rate,
        )
        db.session.add(room)
        db.session.commit()
        logger.info("Room created: room=%s user=%s", room.id, user_id)
        return room

    @staticmethod
    def create_room_type(name: str, description: str, default_rate: float, capacity: int) -> RoomType:
        """Create a new room type."""
        room_type = RoomType(
            name=name,
            description=description,
            default_rate=default_rate,
            capacity=capacity,
        )
        db.session.add(room_type)
        db.session.commit()
        return room_type

    @staticmethod
    def set_status(room_id: int, status: RoomStatus, user_id: int) -> Room:
        """Update room status and emit signal."""
        room = Room.query.get(room_id)
        if room is None:
            raise ValueError('Room not found')
        room.status = status
        db.session.commit()
        logger.info('Status change: room=%s user=%s status=%s', room.id, user_id, status.value)
        room_status_changed.send(RoomService, room=room)
        return room

    @staticmethod
    def set_rate_override(room_type: RoomType, start_date: date, end_date: date, rate: float, user_id: int) -> RateCard:
        """Create a rate override for given dates."""
        card = RateCard(
            room_type=room_type,
            start_date=start_date,
            end_date=end_date,
            override_rate=rate,
        )
        db.session.add(card)
        db.session.commit()
        logger.info('Rate override set: room_type=%s user=%s rate=%s', room_type.id, user_id, rate)
        return card
