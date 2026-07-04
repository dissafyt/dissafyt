#!/usr/bin/env bash
set -euo pipefail

python manage.py check

python - <<'PY'
import os
import sys
import time

import django
from django.db import connections

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dissafyt_platform.settings")
django.setup()

connection = connections["default"]
deadline = time.time() + int(os.environ.get("DB_READY_TIMEOUT", "120"))
last_error = None

while time.time() < deadline:
    try:
        connection.ensure_connection()
        connection.close()
        break
    except Exception as exc:  # pragma: no cover - deployment readiness guard
        last_error = exc
        time.sleep(2)
else:
    raise SystemExit(f"Database was not ready before timeout: {last_error}")
PY

python manage.py migrate --noinput