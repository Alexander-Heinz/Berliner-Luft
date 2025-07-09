from services.api_client import LuftdatenAPIClient
from core.data_transformer import DataTransformer
import pytest
from datetime import datetime


@pytest.mark.integration
def test_get_stations_live_api_has_expected_schema():
    client = LuftdatenAPIClient()
    response = client.get_stations()

    # Test Schlüsselstruktur
    assert isinstance(response, dict)
    assert "request" in response
    assert "indices" in response
    assert "data" in response
    assert "count" in response

    # check if required columns are inside the dataset
    expected_columns = [
        "Id", "Code", "Name", "City", "Synonym",
        "Active from", "Active to", "Longitude", "Latitude",
        "Id of network", "Id of station setting", "Id of station type",
        "Network code", "Translated network name",
        "Translated station setting name", 
        "Translated station setting short name",
        "Translated station type name", "Street", "Street number"
    ]
    indices_str = [i.split(" - ")[0].split(": ")[1] 
                   for i in response["indices"]]
    
    for col in expected_columns:
        assert col in indices_str, f"{col} not found in indices"

    # Test data
    data = response["data"]
    assert isinstance(data, dict)
    assert response["count"] == len(data)

    # Prüfe einige Datenpunkte
    for station_code, values in data.items():
        assert isinstance(station_code, str)
        assert isinstance(values, list)
        assert len(values) == len(response["indices"])
        break  # nur einen Eintrag prüfen

    print(f"Stations fetched: {response['count']}")


@pytest.mark.integration
def test_get_components_live_api():
    """
    Calls the real /components/json endpoint and ensures:

      1. We get back a dict with expected structure.
      2. 'indices' is present and defines the expected fields.
      3. For each component entry (key != 'count', 'indices'), data has correct fields and types.
    """
    client = LuftdatenAPIClient()
    components = client.get_components()

    assert isinstance(components, dict), "Expected get_components() to return a dict"
    assert "indices" in components, "'indices' key not found in response"
    assert "count" in components, "'count' key not found in response"

    expected_keys = [
        "Id",        # string
        "Code",      # string
        "Symbol",    # string
        "Unit",      # string
        "Translated name"  # string
    ]
    indices_str = [i.split(" - ")[0].split(": ")[1] for i in components["indices"]]
    missing = [col for col in expected_keys if col not in indices_str]
    assert not missing, f"Missing expected columns in indices: {missing}"

    # Validate each component entry (excluding 'count' and 'indices')
    for comp_key, comp_data in components.items():
        if comp_key in ("count", "indices"):
            continue
        assert isinstance(comp_data, list), f"Component '{comp_key}' should be a list"
        assert len(comp_data) == len(indices_str), f"Component '{comp_key}' data length mismatch"

        # Optional: validate fields by position
        field_map = dict(zip(indices_str, comp_data))
        for field in expected_keys:
            assert field in field_map, f"Field '{field}' missing in component '{comp_key}'"
            value = field_map[field]
            assert isinstance(value, str) and value.strip() != "", f"Invalid value for '{field}' in component '{comp_key}'"

@pytest.mark.integration
def test_get_scopes_live_api():
    """
    Calls the real /scopes/json endpoint and ensures:
      1. We get back a dictionary with expected structure.
      2. Contains at least one scope record.
      3. Each scope has valid 'Id' and 'Description' equivalents.
    """
    client = LuftdatenAPIClient()
    scopes_data = client.get_scopes()  # Returns a dictionary

    # Verify top-level structure
    assert isinstance(scopes_data, dict), "Expected get_scopes() to return a dictionary"
    assert 'count' in scopes_data, "Response missing 'count' field"
    assert 'indices' in scopes_data, "Response missing 'indices' field"
    assert scopes_data['count'] > 0, "Expected at least one scope in the response"

    # Collect scope records (ignore metadata keys)
    scope_keys = [k for k in scopes_data.keys() if k not in ('count', 'indices')]
    assert len(scope_keys) > 0, "No scope records found in response"

    # Verify each scope record
    for key in scope_keys:
        record = scopes_data[key]
        assert isinstance(record, list), f"Scope '{key}' should be a list"
        
        # Verify ID (index 0) and Description (index 5)
        assert len(record) >= 6, f"Scope '{key}' has insufficient data (expected 6 fields)"
        
        # Check ID (field 0)
        assert record[0].strip() != "", f"Scope '{key}' has empty/missing ID"
        
        # Check Description (field 5 - 'Translated name')
        assert record[5].strip() != "", f"Scope '{key}' has empty/missing Description"


@pytest.mark.integration
def test_get_measures_live_api():
    """Tests the measures endpoint with real API calls"""
    client = LuftdatenAPIClient()
    
    # Get measures for a known station/component
    response = client.get_measures(
        component_id=2,
        station_id=10,
        hours_back=1
    )

    # Verify top-level response structure
    assert isinstance(response, dict), "Expected response to be a dictionary"
    assert 'request' in response, "Missing request metadata"
    assert 'data' in response, "Missing data payload"

    # Verify request metadata structure
    assert isinstance(response['request'], dict), "Request metadata should be a dictionary"
    required_meta_fields = ['component', 'station', 'datetime_from', 'datetime_to']
    for field in required_meta_fields:
        assert field in response['request'], f"Missing '{field}' in request metadata"

    # Verify data payload
    data = response['data']
    assert isinstance(data, dict), "Data payload should be a dictionary"

    if data:  # Only validate if there's actual data
        for timestamp, measures in data.items():
            # Verify timestamp format
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

            # Verify measures structure
            for measure_id, measure in measures.items():
                required_fields = {
                    'Value': (int, float, str),
                    'Unit': str,
                    'StationId': (int, str),
                    'ComponentId': (int, str),
                    'Scope': (int, str)
                }

                for field, types in required_fields.items():
                    assert field in measure, f"Missing field '{field}' in measure {measure_id}"
                    assert isinstance(measure[field], types), (
                        f"Field '{field}' should be {types}, got {type(measure[field])}"
                    )

                # Additional value validation
                if isinstance(measure['Value'], str):
                    try:
                        float(measure['Value'])
                    except ValueError:
                        pytest.fail(f"Value '{measure['Value']}' cannot be converted to float")