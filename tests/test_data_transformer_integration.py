from services.api_client import LuftdatenAPIClient
from core.data_transformer import DataTransformer
import pytest


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
def test_transform_stations_end_to_end():
    client = LuftdatenAPIClient()

    # Fetch raw data
    raw_stations = client.get_stations()
    assert isinstance(raw_stations, dict), "Expected raw API response to be a dict"

    # Transform
    transformed = DataTransformer.transform_stations(raw_stations)
    assert isinstance(transformed, list), "transform_stations should return a list"
    assert len(transformed) > 0, "Expected at least one station in the result"

    expected_keys = {"station_id", "name", "latitude", "longitude"}

    for station in transformed:
        # 1) Exactly the right keys
        assert set(station.keys()) == expected_keys, f"Station dict keys mismatch: {station.keys()}"

        # 2) station_id must be an int and > 0
        sid = station["station_id"]
        assert isinstance(sid, int), "station_id must be an int"
        assert sid > 0, "station_id should be positive"

        # 3) name must be a non-empty string
        name = station["name"]
        assert isinstance(name, str), "name must be a string"
        assert name.strip() != "", "name should not be empty"

        # 4) latitude and longitude must be floats or None
        lat = station["latitude"]
        lon = station["longitude"]
        assert (isinstance(lat, float) or lat is None), "latitude must be float or None"
        assert (isinstance(lon, float) or lon is None), "longitude must be float or None"

        # 5) If present, lat/lon must be within valid ranges
        if lat is not None and lon is not None:
            assert -90.0 <= lat <= 90.0, f"latitude {lat} out of range"
            assert -180.0 <= lon <= 180.0, f"longitude {lon} out of range"


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