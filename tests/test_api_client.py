# tests/test_api_client.py

import pytest
import requests
from unittest.mock import MagicMock
import sys
import os
from tenacity import RetryError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.api_client import LuftdatenAPIClient

class DummyResponse:
    """
    A tiny stand‐in for requests.Response that lets us choose:
      - status_code
      - .json() output
      - whether raise_for_status() fails
    """

    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"status code was {self.status_code}")

    def json(self):
        return self._data

def test_get_components_success(monkeypatch):
    client = LuftdatenAPIClient()
    dummy_payload = {"components": [{"id": 1, "name": "PM10"}]}

    def fake_get(url, params):
        expected_url = f"{client.BASE_URL}/components/json"
        assert url == expected_url
        return DummyResponse(dummy_payload, status_code=200)

    client.session.get = fake_get
    result = client.get_components()
    assert result == dummy_payload

def test_get_stations_success(monkeypatch):
    client = LuftdatenAPIClient()
    dummy_payload = {"stations": [{"id": 42, "city": "Berlin"}]}

    def fake_get(url, params):
        expected_url = f"{client.BASE_URL}/stations/json"
        assert url == expected_url
        return DummyResponse(dummy_payload, status_code=200)

    client.session.get = fake_get
    result = client.get_stations()
    assert result == dummy_payload

def test_get_scopes_success(monkeypatch):
    client = LuftdatenAPIClient()
    dummy_payload = {"scopes": [{"id": 2, "description": "Outdoor"}]}

    def fake_get(url, params):
        expected_url = f"{client.BASE_URL}/scopes/json"
        assert url == expected_url
        return DummyResponse(dummy_payload, status_code=200)

    client.session.get = fake_get
    result = client.get_scopes()
    assert result == dummy_payload

def test_get_measures_success(monkeypatch):
    client = LuftdatenAPIClient()
    dummy_payload = {
        "measures": [
            {"timestamp": "2021-01-01T00:00:00Z", "value": 12.3}
        ]
    }

    def fake_get(url, params):
        expected_url = f"{client.BASE_URL}/measures/json"
        assert url == expected_url

        required_keys = {
            "date_from",
            "time_from",
            "date_to",
            "time_to",
            "station",
            "component",
            "scope",
        }
        assert required_keys.issubset(set(params.keys()))
        assert isinstance(params["station"], str)
        assert isinstance(params["component"], str)
        assert params["scope"] == "2"

        return DummyResponse(dummy_payload, status_code=200)

    client.session.get = fake_get
    result = client.get_measures(component_id=5, station_id=7, hours_back=24)
    assert result == dummy_payload

def test_get_measures_invalid_hours_back_raises_value_error():
    client = LuftdatenAPIClient()

    with pytest.raises(ValueError) as excinfo:
        client.get_measures(component_id=1, station_id=1, hours_back="not_an_int")

    assert "Invalid parameters for getting measures" in str(excinfo.value)

def test_get_components_http_error(monkeypatch):
    client = LuftdatenAPIClient()

    def fake_get(url, params):
        return DummyResponse({"error": "oops"}, status_code=500)

    client.session.get = fake_get

    with pytest.raises(RetryError) as excinfo:
        client.get_components()

    # Optional: Check the underlying exception
    assert isinstance(excinfo.value.last_attempt.exception(), requests.HTTPError)

def test_get_measures_http_error(monkeypatch):
    client = LuftdatenAPIClient()

    def fake_get(url, params):
        return DummyResponse({"error": "server down"}, status_code=500)

    client.session.get = fake_get

    with pytest.raises(RetryError) as excinfo:
        client.get_measures(component_id=10, station_id=20, hours_back=1)

    assert isinstance(excinfo.value.last_attempt.exception(), requests.HTTPError)

def test_get_measures_retry_error(monkeypatch):
    client = LuftdatenAPIClient()

    def fake_get(url, params):
        raise requests.ConnectionError("Simulated connection failure")

    client.session.get = fake_get

    with pytest.raises(RetryError):
        client.get_measures(component_id=5, station_id=7, hours_back=24)

def test_get_components_retry_error(monkeypatch):
    client = LuftdatenAPIClient()

    def fake_get(url, params):
        raise requests.ConnectionError("Simulated connection failure")

    client.session.get = fake_get

    with pytest.raises(RetryError):
        client.get_components()

def test_get_stations_retry_error(monkeypatch):
    client = LuftdatenAPIClient()

    def fake_get(url, params):
        raise requests.ConnectionError("Simulated connection failure")

    client.session.get = fake_get

    with pytest.raises(RetryError):
        client.get_stations()

def test_get_scopes_retry_error(monkeypatch):
    client = LuftdatenAPIClient()

    def fake_get(url, params):
        raise requests.ConnectionError("Simulated connection failure")

    client.session.get = fake_get

    with pytest.raises(RetryError):
        client.get_scopes()
