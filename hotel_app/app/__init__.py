from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler

from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

scheduler = BackgroundScheduler()

from .services.housekeeping_service import HousekeepingService
from .models import User


def create_app(config_name: str = 'development') -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """Return user by ID."""
        return User.query.get(int(user_id))

    from .views.auth import auth_bp
    from .views.reservations import reservations_bp
    from .views.housekeeping import housekeeping_bp
    from .views.rooms import rooms_bp
    from .views.frontdesk import frontdesk_bp
    from .views.billing import billing_bp
    from .views.portal import portal_bp
    from .views.reports import reports_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(housekeeping_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(frontdesk_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(reports_bp)

    # Schedule daily housekeeping task assignment at 02:00 local time
    scheduler.add_job(
        HousekeepingService.assign_daily_tasks,
        'cron',
        hour=2,
        minute=0,
    )
    scheduler.start()
    app.scheduler = scheduler

    @app.route('/health')
    def health() -> 'flask.wrappers.Response':
        try:
            db.session.execute('SELECT 1')
            return jsonify({'status': 'ok'})
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({'status': 'error', 'details': str(exc)}), 500

    return app
