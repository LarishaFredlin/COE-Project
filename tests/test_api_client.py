import httpx
import pytest

from frontend import api_client


def mock_response(status_code=200, json_data=None):
    request = httpx.Request(
        "GET",
        "http://127.0.0.1:8000/test"
    )

    return httpx.Response(
        status_code,
        json=json_data or {},
        request=request
    )


def test_check_api_health(monkeypatch):
    def mock_request(*args, **kwargs):
        return mock_response(
            200,
            {"status": "healthy"}
        )

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    result = api_client.check_api_health()

    assert result["status"] == "healthy"


def test_get_investigations(monkeypatch):
    expected_data = [
        {"investigation_id": "INV-001"},
        {"investigation_id": "INV-002"}
    ]

    def mock_request(*args, **kwargs):
        return mock_response(200, expected_data)

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    result = api_client.get_investigations()

    assert len(result) == 2
    assert result[0]["investigation_id"] == "INV-001"


def test_create_investigation(monkeypatch):
    payload = {
        "part_id": "SP-001",
        "location": "Chennai",
        "system_stock": 100,
        "physical_stock": 95
    }

    expected_response = {
        "investigation_id": "INV-001",
        "part_id": "SP-001"
    }

    def mock_request(method, url, **kwargs):
        assert method == "POST"
        assert kwargs["json"] == payload

        return mock_response(201, expected_response)

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    result = api_client.create_investigation(payload)

    assert result["investigation_id"] == "INV-001"


def test_update_investigation(monkeypatch):
    payload = {
        "status": "IN_PROGRESS",
        "notes": "Verification started"
    }

    expected_response = {
        "investigation_id": "INV-001",
        "status": "IN_PROGRESS"
    }

    def mock_request(method, url, **kwargs):
        assert method == "PUT"
        assert url.endswith("/investigations/INV-001")
        assert kwargs["json"] == payload

        return mock_response(200, expected_response)

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    result = api_client.update_investigation(
        "INV-001",
        payload
    )

    assert result["status"] == "IN_PROGRESS"


def test_delete_investigation(monkeypatch):
    def mock_request(method, url, **kwargs):
        assert method == "DELETE"
        assert url.endswith("/investigations/INV-001")

        return mock_response(
            200,
            {"message": "Investigation deleted successfully"}
        )

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    result = api_client.delete_investigation("INV-001")

    assert "message" in result


def test_http_error_is_converted_to_api_client_error(monkeypatch):
    request = httpx.Request(
        "GET",
        "http://127.0.0.1:8000/health"
    )

    response = httpx.Response(
        500,
        text="Internal Server Error",
        request=request
    )

    def mock_request(*args, **kwargs):
        return response

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    with pytest.raises(api_client.APIClientError):
        api_client.check_api_health()


def test_connection_error_is_converted_to_api_client_error(monkeypatch):
    def mock_request(*args, **kwargs):
        request = httpx.Request(
            "GET",
            "http://127.0.0.1:8000/health"
        )

        raise httpx.ConnectError(
            "Connection refused",
            request=request
        )

    monkeypatch.setattr(
        api_client.httpx,
        "request",
        mock_request
    )

    with pytest.raises(
        api_client.APIClientError,
        match="Cannot connect to SpareSync API"
    ):
        api_client.check_api_health()
