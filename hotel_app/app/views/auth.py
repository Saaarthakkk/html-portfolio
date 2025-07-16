from __future__ import annotations

import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import Form, StringField, PasswordField, validators

from ..models import User, UserRole
from .. import db
from ..utils.roles import role_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger('auth')
handler = logging.FileHandler('logs/auth.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class LoginForm(Form):
    """Login form."""

    username = StringField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])


class RegisterForm(Form):
    """User registration form."""

    username = StringField('Username', [validators.InputRequired()])
    password = PasswordField('Password', [validators.InputRequired()])
    role = StringField('Role', [validators.InputRequired()])


@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> str:
    """Handle user login."""
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            logger.info('Login success user=%s', user.username)
            return redirect(url_for('reservations.list_reservations'))
        logger.warning('Login failed user=%s', form.username.data)
        flash('Invalid credentials')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout() -> str:
    """Log the current user out."""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ADMIN)
def register() -> str:
    """Register a new user (admin only)."""
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(username=form.username.data, role=UserRole(form.role.data))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created')
        return redirect(url_for('auth.login'))
    return render_template('auth/login.html', form=form)
