
import os
import httpx

API_BASE_URL = os.getenv(
    "SPARESYNC_API_URL",
    "http://127.0.0.1:8000"
)

TIMEOUT = 10.0


class APIClientError(Exception):
    """Raised when communication with the SpareSync API fails."""


def _request(method, endpoint, **kwargs):
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = httpx.request(
            method,
            url,
            timeout=TIMEOUT,
            **kwargs
        )
        response.raise_for_status()

        if response.status_code == 204:
            return None

        return response.json()

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise APIClientError(
            f"API returned HTTP {exc.response.status_code}: {detail}"
        ) from exc

    except httpx.RequestError as exc:
        raise APIClientError(
            "Cannot connect to SpareSync API. "
            "Make sure the FastAPI server is running."
        ) from exc


def check_api_health():
    return _request("GET", "/health")


def get_investigations():
    return _request("GET", "/investigations/")


def create_investigation(payload):
    return _request(
        "POST",
        "/investigations/",
        json=payload
    )


def update_investigation(investigation_id, payload):
    return _request(
        "PUT",
        f"/investigations/{investigation_id}",
        json=payload
    )


def delete_investigation(investigation_id):
    return _request(
        "DELETE",
        f"/investigations/{investigation_id}"
    )
