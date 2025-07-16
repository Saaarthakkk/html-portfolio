# Hotel App

This project uses Flask-Migrate for database migrations.

## Initial setup

```bash
export FLASK_APP=hotel_app.app:create_app
export PYTHONPATH=$PWD/hotel_app
flask db init
flask db migrate -m "baseline"
flask db upgrade
```

## Refresh the database
Run the helper script to recreate the SQLite database and apply migrations:

```bash
scripts/refresh_db.sh
```

