import pytest
from core.dimension_manager import DimensionManager
from config import constants, schemas

# a minimal fake API client that returns exactly one component
class DummyAPI:
    def get_components(self):
        return {
            # the two meta keys should be excluded…
            "count": 1,
            "indices": ["0", "1", "2", "3", "4"],
            # …and this one real component should survive:
            "PM_TEST": ["42", "PM_TEST", "T", "µg/m³", "Test Particulate"]
        }
    def get_stations(self):
        return {}  # not used in this test
    def get_scopes(self):
        return {}  # not used in this test


# a dummy GCS uploader that does nothing
class DummyGCS:
    def __init__(self, bucket): pass
    def upload_json(self, data, blob_name): pass


# a dummy BQ client that simply records what it was asked to load
class DummyBQ:
    def __init__(self, dataset_id=None):
        self.loaded = []

    def load_table(self, *, rows, table_id, schema, write_disposition):
        # record the exact arguments
        self.loaded.append({
            "rows": rows,
            "table_id": table_id,
            "schema": schema,
            "write_disposition": write_disposition
        })


def test_components_flow(monkeypatch):
    api = DummyAPI()
    gcs = DummyGCS(bucket="unused")
    bq = DummyBQ()

    # run only the components step
    dm = DimensionManager(api, gcs, bq)
    dm._load_to_bigquery("components", api.get_components())

    # we should have exactly one load_table call
    assert len(bq.loaded) == 1

    call = bq.loaded[0]

    # it should target your dim_components table…
    assert call["table_id"] == "dim_components"

    # …with WRITE_TRUNCATE
    assert call["write_disposition"] == "WRITE_TRUNCATE"

    # schema should be exactly what you defined for "components"
    assert call["schema"] == schemas.DIMENSION_SCHEMAS["components"]

    # and rows should be the one real component (meta‑keys filtered out)
    expected_row = {
        "id": 42,
        "code": "PM_TEST",
        "symbol": "T",
        "unit": "µg/m³",
        "name": "Test Particulate",
    }
    assert call["rows"] == [expected_row]


def test_full_process_dimensions(monkeypatch):
    # here we also exercise process_dimensions() end‑to‑end
    api = DummyAPI()
    gcs = DummyGCS(bucket="unused")
    bq = DummyBQ()

    dm = DimensionManager(api, gcs, bq)
    # override constants so we only loop 'components'
    monkeypatch.setitem(constants.CONFIG, "dimension_tables", ["components"])
    dm.process_dimensions()

    # it should have uploaded _and_ loaded exactly one component
    assert len(bq.loaded) == 1
    assert bq.loaded[0]["table_id"] == "dim_components"
