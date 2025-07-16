from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from ..services.reporting_service import ReportingService
from ..utils.roles import role_required
from ..models import UserRole

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
logger = logging.getLogger('reports')
handler = logging.FileHandler('logs/reports.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _parse_dates() -> tuple[date, date]:
    """Parse start_date and end_date from query parameters."""
    today = date.today()
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if start_str and end_str:
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
    else:
        start = today.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, end


@reports_bp.route('/dashboard')
@login_required
@role_required(UserRole.ADMIN, UserRole.MANAGER)
def dashboard():
    """Render or return the reporting dashboard."""
    start, end = _parse_dates()
    occupancy = ReportingService.occupancy(start, end)
    revenue = ReportingService.revenue(start, end)
    revpar = ReportingService.revpar(start, end)
    avg_stay = ReportingService.avg_length_of_stay(start)

    logger.info('dashboard view: user=%s start=%s end=%s', current_user.id, start, end)

    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify({
            'occupancy': occupancy,
            'revenue': revenue,
            'revpar': revpar,
            'avg_length_of_stay': avg_stay,
        })

    # Generate daily revenue data
    days = []
    current = start
    daily_revenue = []
    while current < end:
        next_day = current + timedelta(days=1)
        days.append(current.strftime('%Y-%m-%d'))
        daily_revenue.append(ReportingService.revenue(current, next_day))
        current = next_day

    return render_template(
        'reports/dashboard.html',
        occupancy=occupancy,
        revenue=revenue,
        revpar=revpar,
        avg_length=avg_stay,
        days=days,
        daily_revenue=daily_revenue,
        start=start,
        end=end,
    )
