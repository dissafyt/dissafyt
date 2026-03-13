#!/usr/bin/env bash
# exit on error
set -o errexit

python manage.py runserver 0.0.0.0:$PORT