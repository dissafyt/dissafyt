"""
WSGI config for dissafyt_platform project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import subprocess
import sys
import logging
from pathlib import Path

import fcntl

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dissafyt_platform.settings")

logger = logging.getLogger(__name__)


def _auto_apply_migrations() -> None:
	if os.environ.get("AUTO_APPLY_MIGRATIONS", "false").strip().lower() not in {"1", "true", "yes", "on"}:
		return

	base_dir = Path(__file__).resolve().parent.parent
	lock_path = base_dir / ".migration-lock"

	lock_path.parent.mkdir(parents=True, exist_ok=True)
	with open(lock_path, "w", encoding="utf-8") as lock_file:
		fcntl.flock(lock_file, fcntl.LOCK_EX)
		try:
			subprocess.run(
				[sys.executable, "manage.py", "migrate", "--noinput"],
				cwd=str(base_dir),
				check=True,
			)
		except subprocess.CalledProcessError as exc:
			logger.exception("Automatic startup migration failed", exc_info=exc)
			raise


_auto_apply_migrations()

application = get_wsgi_application()
