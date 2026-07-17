import logging
import requests
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return getattr(settings, "COURIER_BASE_URL", "https://api.shiplogic.com")


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = getattr(settings, "COURIER_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _request(method: str, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not getattr(settings, "COURIER_ENABLED", False):
        return {"ok": False, "error": "courier_disabled", "message": "Courier integration is disabled"}

    url = f"{_get_base_url().rstrip('/')}/{path.lstrip('/') }"
    timeout = getattr(settings, "COURIER_TIMEOUT_SECONDS", 15)
    try:
        resp = requests.request(method, url, json=json, params=params or {}, headers=_headers(), timeout=timeout)
    except requests.RequestException as exc:
        logger.exception("Courier request failed: %s %s", method, url)
        return {"ok": False, "error": "request_exception", "message": str(exc)}

    try:
        data = resp.json()
    except ValueError:
        data = {"raw_text": resp.text}

    if resp.status_code >= 400:
        return {"ok": False, "status_code": resp.status_code, "error": data}

    return {"ok": True, "status_code": resp.status_code, "data": data}


def quote_rates(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Request a rate quote from the courier provider.

    Expected to call POST /rates
    """
    return _request("POST", "/rates", json=payload)


def create_shipment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a shipment. Expected POST /shipments"""
    return _request("POST", "/shipments", json=payload)


def track_shipment(shipment_id: str) -> Dict[str, Any]:
    """Track a shipment by ID. Expected GET /tracking/shipments or similar."""
    path = f"/tracking/shipments/{shipment_id}"
    return _request("GET", path)
