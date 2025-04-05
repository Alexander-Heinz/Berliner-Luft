from typing import Dict, Any, List
from config import constants

class DataTransformer:
    @staticmethod
    def transform_components(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(values[0]),
                "code": code,
                "name": values[1],
                "description": values[2],
                "unit": values[3]
            }
            for code, values in data.items()
            if code not in constants.CONFIG["excluded_component_keys"]
        ]

    @staticmethod
    def transform_stations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "station_id": int(station_id),
                "name": values[0],
                "latitude": float(values[1]),
                "longitude": float(values[2])
            }
            for station_id, values in data.items()
            if (station_id not in constants.CONFIG["excluded_station_keys"] 
                and station_id.isdigit())
        ]

    @staticmethod
    def transform_scopes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "scope_id": int(scope_id),
                "name": values[0],
                "description": values[1]
            }
            for scope_id, values in data.items()
            if (scope_id not in constants.CONFIG["excluded_scope_keys"] 
                and scope_id.isdigit())
        ]