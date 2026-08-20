import logging
import os
import sys
import time
from pathlib import Path

# ============================================================
# DJANGO SETTINGS
# ============================================================

# Tumhare traceback ke hisaab se Django project package:
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "packing_list_system.settings"
)

import django

django.setup()


# ============================================================
# IMPORT AUTOMATIC MOVE FUNCTION
# ============================================================

from packing_system.views import move_txt_files_automatically


# ============================================================
# LOGGING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "auto_move_worker.log"


logger = logging.getLogger("auto_move_worker")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

# File logger
file_handler = logging.FileHandler(
    LOG_FILE,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

# Terminal logger
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ============================================================
# CONFIG
# ============================================================

CHECK_INTERVAL_SECONDS = 5


# ============================================================
# WORKER
# ============================================================

def run_worker():

    logger.info("=" * 90)
    logger.info("AUTOMATIC TXT FILE WORKER STARTED")
    logger.info("Check interval: %s seconds", CHECK_INTERVAL_SECONDS)
    logger.info("Worker is independent from Django runserver.")
    logger.info("=" * 90)

    while True:

        try:

            logger.info("[WORKER] Checking source folder...")

            result = move_txt_files_automatically()

            logger.info(
                "[WORKER] Result -> Found=%s | Moved=%s | "
                "Skipped=%s | Failed=%s | Status=%s",
                result.get("found", 0),
                result.get("moved", 0),
                result.get("skipped", 0),
                result.get("failed", 0),
                result.get("status"),
            )

        except KeyboardInterrupt:

            logger.info("[WORKER] Worker stopped by user.")
            break

        except Exception as exc:

            logger.exception(
                "[WORKER] Error while processing files: %s",
                exc
            )

        time.sleep(CHECK_INTERVAL_SECONDS)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    run_worker()