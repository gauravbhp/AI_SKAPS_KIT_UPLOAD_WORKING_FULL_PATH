import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
CONTEXT_FILE = BASE_DIR / "auto_monitor_context.json"


def save_monitor_context(
    production_order_code,
    production_demand_code,
    pallet_number,
    box_number,
    folder_structure,
):
    """Persist the exact UI-selected DB scope + already-built folder path."""
    context = {
        "production_order_code": str(production_order_code or "").strip(),
        "production_demand_code": str(production_demand_code or "").strip(),
        "pallet_number": str(pallet_number or "1").strip(),
        "box_number": str(box_number or "1").strip(),
        "folder_structure": str(folder_structure or "").strip().strip("/\\"),
    }

    if not all([
        context["production_order_code"],
        context["production_demand_code"],
        context["pallet_number"],
        context["box_number"],
        context["folder_structure"],
    ]):
        raise ValueError("Incomplete automatic monitor context.")

    tmp_file = CONTEXT_FILE.with_suffix(".tmp")

    with tmp_file.open("w", encoding="utf-8") as fh:
        json.dump(context, fh, indent=2)

    tmp_file.replace(CONTEXT_FILE)

    logger.info(
        "[AUTO CONTEXT] Saved -> Order=%s Demand=%s Pallet=%s Box=%s Path=%s",
        context["production_order_code"],
        context["production_demand_code"],
        context["pallet_number"],
        context["box_number"],
        context["folder_structure"],
    )

    return context


def load_monitor_context():
    """Read the latest exact automatic monitor context."""
    if not CONTEXT_FILE.exists():
        logger.warning("[AUTO CONTEXT] Context file does not exist.")
        return None

    try:
        with CONTEXT_FILE.open("r", encoding="utf-8") as fh:
            context = json.load(fh)

        required = [
            "production_order_code",
            "production_demand_code",
            "pallet_number",
            "box_number",
            "folder_structure",
        ]

        if not all(str(context.get(k, "")).strip() for k in required):
            logger.error("[AUTO CONTEXT] Context is incomplete: %s", context)
            return None

        return context

    except Exception:
        logger.exception("[AUTO CONTEXT] Failed to read context.")
        return None