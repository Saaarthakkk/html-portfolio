from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models import User, UserRole, Guest

logger = logging.getLogger('portal')


class GuestService:
    """Service layer for guest portal operations."""

    @staticmethod
    def register_guest(username: str, password: str, name: str) -> User:
        """Create a new guest user and associated guest record."""
        if User.query.filter_by(username=username).first():
            raise ValueError('Username already taken')
        user = User(username=username, role=UserRole.GUEST)
        user.set_password(password)
        guest = Guest(name=name, user=user)
        db.session.add_all([user, guest])
        try:
            db.session.commit()
            logger.info('Guest registered: user=%s', user.id)
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise exc
        return user
