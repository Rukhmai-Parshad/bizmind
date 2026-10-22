#!/usr/bin/env bash
set -o errexit

python manage.py collectstatic --no-input
python manage.py migrate

# Retention: remove expired login sessions and expired refresh-token records.
python manage.py clearsessions
python manage.py flushexpiredtokens
