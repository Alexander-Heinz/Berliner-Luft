import pytest
import sys
import os

# Setup paths so imports work:
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SRC_ROOT)

from src.services.api_client import LuftdatenAPIClient
from src.core.data_transformer import DataTransformer


@pytest.mark.integration
def test_integration_transform_components():
    client = LuftdatenAPIClient()
    raw_components = client.get_components()
    # Verify raw_components is a dict
    assert isinstance(raw_components, dict)
    processed = DataTransformer.transform_components(raw_components)
    # Should return a non-empty list of dicts
    assert isinstance(processed, list)
    assert len(processed) > 0
    # Each item should have expected keys with appropriate types
    for item in processed:
        assert isinstance(item.get("id"), int)
        assert isinstance(item.get("code"), str)
        assert isinstance(item.get("symbol"), str)
        assert isinstance(item.get("unit"), (str, type(None)))
        assert isinstance(item.get("name"), str)


@pytest.mark.integration
def test_integration_transform_stations():
    client = LuftdatenAPIClient()
    raw_stations = client.get_stations()
    assert isinstance(raw_stations, dict)
    processed = DataTransformer.transform_stations(raw_stations)
    assert isinstance(processed, list)
    assert len(processed) > 0
    
    for item in processed:
        assert isinstance(item["station_id"], int)
        assert isinstance(item["name"], str)
        lon = item["longitude"]
        lat = item["latitude"]
        assert lon is None or isinstance(lon, float)
        assert lat is None or isinstance(lat, float)

@pytest.mark.integration
def test_integration_transform_scopes():
    client = LuftdatenAPIClient()
    raw_scopes = client.get_scopes()
    assert isinstance(raw_scopes, dict)
    processed = DataTransformer.transform_scopes(raw_scopes)
    assert isinstance(processed, list)
    assert len(processed) > 0
    for item in processed:
        assert isinstance(item.get("scope_id"), int)
        assert isinstance(item.get("name"), str)
        assert isinstance(item.get("description"), str)