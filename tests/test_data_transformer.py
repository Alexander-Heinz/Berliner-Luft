from core.data_transformer import DataTransformer
from config.constants import CONFIG
import pytest

# This sample mirrors exactly what's in your GCS JSON dump
_SAMPLE = {
    "count": 12,
    "indices": ["0: Id - string", "1: Code - string", "2: Symbol - string", "3: Unit - string", "4: Translated name - string"],
    "PM10": ["1", "PM10", "PM\u2081\u2080", "\u00b5g/m\u00b3", "Feinstaub"],
    "CO": ["2", "CO", "CO", "mg/m\u00b3", "Kohlenmonoxid"],
    # …etc…
}


def test_transform_components_excludes_meta_keys():
    rows = DataTransformer.transform_components(_SAMPLE)

    # 1) We never get one of the excluded keys back
    codes = [r["code"] for r in rows]
    for bad in CONFIG["excluded_component_keys"]:
        assert bad not in codes, f"{bad} should be excluded"

    # 2) We get exactly len(SAMPLE) - len(excluded) rows
    expected = len(_SAMPLE) - len(CONFIG["excluded_component_keys"])
    assert len(rows) == expected

    # 3) And each row has the right types
    for row in rows:
        assert isinstance(row["id"], int)
        assert isinstance(row["code"], str)
        assert isinstance(row["symbol"], str)
        assert isinstance(row["unit"], str)
        assert isinstance(row["name"], str)


def test_transform_components_excludes_keys():
    # Prepare sample data, including an excluded component key
    data = {
        "CO": ["1", "ignored", "CO", "µg/m3", "Carbon Monoxide"],
        "count": ["99", "ignored", "X", "u", "Count"],  # excluded via CONFIG
        "indices": ["2", "ignored", "Y", "v", "Indices"]  # excluded via CONFIG
    }
    result = DataTransformer.transform_components(data)
    assert isinstance(result, list)
    # Only 'CO' should be transformed
    assert result == [
        {
            "id": 1,
            "code": "CO",
            "symbol": "CO",
            "unit": "µg/m3",
            "name": "Carbon Monoxide"
        }
    ]


def test_transform_stations_includes_only_valid_ids_and_handles_none():
    # Prepare sample data with numeric and non-numeric keys, and an excluded key
    data = {
        "data": {
            "10": ["10", "b", "StationA", "d", "e", "f", "g", "10.5", "20.5"],
            "request": ["x"] * 9,
            "abc": ["x"] * 9,
            "20": ["20", "y", "StationB", "", "", "", "", None, "30.5"]
        }
    }

    result = DataTransformer.transform_stations(data)
    # Expect two stations: 10 and 20
    expected = [
        {
            "station_id": 10,
            "name": "StationA",
            "longitude": 10.5,
            "latitude": 20.5
        },
        {
            "station_id": 20,
            "name": "StationB",
            "longitude": None,
            "latitude": 30.5
        }
    ]
    # Order may vary since dict order is preserved in Python 3.7+, so check both
    assert len(result) == 2
    assert expected[0] in result
    assert expected[1] in result


def test_transform_scopes_excludes_keys_and_formats_description():
    # Prepare sample data with an excluded key and valid entries
    data = {
        "1": ["1", "Hourly", "1", "3600", "x", "ScopeName1", "y"],
        "count": ["x"] * 6,  # excluded via CONFIG
        "2": ["2", "Daily", "24", "86400", "x", "ScopeName2", "y"]
    }
    result = DataTransformer.transform_scopes(data)
    # Expect two scopes: 1 and 2
    expected = [
        {
            "scope_id": 1,
            "name": "ScopeName1",
            "description": "Hourly (1 basis, 3600 seconds)"
        },
        {
            "scope_id": 2,
            "name": "ScopeName2",
            "description": "Daily (24 basis, 86400 seconds)"
        }
    ]
    assert len(result) == 2
    assert expected[0] in result
    assert expected[1] in result