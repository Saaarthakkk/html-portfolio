from __future__ import annotations

from datetime import date, datetime
import itertools
import logging

from .. import db
from ..models import (
    HousekeepingTask,
    HousekeepingStatus,
    Room,
    User,
    UserRole,
)

logger = logging.getLogger('housekeeping')


class HousekeepingService:
    """Service layer for housekeeping operations."""

    @staticmethod
    def assign_daily_tasks() -> None:
        """Assign housekeeping tasks for all rooms needing cleaning."""
        logger.info("Assigning daily housekeeping tasks")

        today = date.today()
        rooms = Room.query.filter(Room.clean_status != "Clean").all()
        staff = User.query.filter_by(role=UserRole.HK).order_by(User.id).all()
        if not staff:
            logger.warning("No housekeeping staff available")
            return

        cycle = itertools.cycle(staff)
        created = 0
        for room in rooms:
            existing = HousekeepingTask.query.filter_by(room_id=room.id, task_date=today).first()
            if existing:
                continue
            assignee = next(cycle)
            task = HousekeepingTask(
                room_id=room.id,
                assigned_to=assignee.id,
                task_date=today,
                status=HousekeepingStatus.PENDING,
            )
            db.session.add(task)
            logger.info("Task created: room=%s assigned_to=%s", room.id, assignee.id)
            created += 1

        if created:
            db.session.commit()

    @staticmethod
    def complete_task(task: HousekeepingTask) -> None:
        """Mark task as completed."""
        task.status = HousekeepingStatus.DONE
        task.completed_at = datetime.utcnow()
        task.room.clean_status = 'Clean'
        db.session.commit()
        logger.info('Task complete: id=%s room=%s', task.id, task.room_id)
