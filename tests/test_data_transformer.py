import pytest
import sys
import os

# Ensure src is in the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SRC_ROOT)

from src.core.data_transformer import DataTransformer
from src.config.constants import CONFIG


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