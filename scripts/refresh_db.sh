#!/bin/bash
set -e
DB_FILE="hotel.db"
rm -f "$DB_FILE"
flask db upgrade
