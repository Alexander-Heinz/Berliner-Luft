from typing import Dict, Any, List
from config import constants


class DataTransformer:
    @staticmethod
    def transform_components(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(values[0]),
                "code": code,
                "symbol": values[2],
                "unit": values[3],
                "name": values[4]
            }
            for code, values in data.items()
            if code not in constants.CONFIG["excluded_component_keys"]
        ]

    @staticmethod
    def transform_stations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Expects the full API response (including 'request', 'indices', 'data', 'count').
        We'll grab only data['data'], then for each record use values[0] as the
        station's numeric ID (string), values[2] as the name, values[7] and values[8]
        as longitude/latitude.
        """

        raw_stations = data.get("data", {})  # This is the inner dict of actual station entries.

        result: List[Dict[str, Any]] = []

        for wrapper_key, values in raw_stations.items():
            # values is a list, where:
            #   values[0] = station_id (string), e.g. "10"
            #   values[2] = name
            #   values[7] = longitude (string or None)
            #   values[8] = latitude (string or None)
            str_id = values[0]

            # 1) must be numeric
            if not str_id.isdigit():
                continue

            # 2) exclude if in config
            if str_id in constants.CONFIG["excluded_station_keys"]:
                continue

            # 3) parse lon/lat safely
            lon_raw = values[7]
            lat_raw = values[8]

            try:
                lon = float(lon_raw) if lon_raw not in (None, "", "null") else None
            except (ValueError, TypeError):
                lon = None

            try:
                lat = float(lat_raw) if lat_raw not in (None, "", "null") else None
            except (ValueError, TypeError):
                lat = None

            # 4) build the dict
            result.append({
                "station_id": int(str_id),
                "name": values[2],
                "longitude": lon,
                "latitude": lat
            })

        return result

    @staticmethod
    def transform_scopes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "scope_id": int(values[0]),
                "name": values[5],  # Translated name
                "description": f"{values[1]} ({values[2]} basis, {values[3]} seconds)"
            }
            for key, values in data.items()
            if key not in constants.CONFIG["excluded_scope_keys"]
        ]