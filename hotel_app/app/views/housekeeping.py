from __future__ import annotations

from datetime import date
import logging

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..models import HousekeepingTask, HousekeepingStatus, UserRole
from ..services.housekeeping_service import HousekeepingService
from ..utils.roles import role_required

housekeeping_bp = Blueprint('housekeeping', __name__, url_prefix='/housekeeping')
logger = logging.getLogger('housekeeping')
handler = logging.FileHandler('logs/housekeeper.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@housekeeping_bp.route('/tasks/today')
@login_required
@role_required(UserRole.HK)
def todays_tasks() -> str:
    """Show today's tasks for the current user."""
    user_id = current_user.id
    tasks = HousekeepingTask.query.filter_by(
        assigned_to=user_id, task_date=date.today()
    ).all()
    return render_template(
        'housekeeping/tasks_today.html',
        tasks=tasks,
        status_enum=HousekeepingStatus,
    )


@housekeeping_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
@role_required(UserRole.HK)
def complete_task(task_id: int):
    """Mark the given task as done."""
    task = HousekeepingTask.query.get_or_404(task_id)
    HousekeepingService.complete_task(task)
    return redirect(url_for('housekeeping.todays_tasks'))
