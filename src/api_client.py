import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, timedelta, timezone

class LuftdatenAPIClient:
    BASE_URL = "https://www.umweltbundesamt.de/api/air_data/v3/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'User-Agent': 'BerlinerLuft/1.0 (https://github.com/Berliner-Luft)'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def _get_data(self, endpoint, params=None):
        response = self.session.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params or {'lang': 'de', 'index': 'code'}
        )
        response.raise_for_status()
        return response.json()
    
    def get_components(self):
        return self._get_data("components/json")
    
    def get_stations(self):
        return self._get_data("stations/json")
    
    def get_scopes(self):
        return self._get_data("scopes/json")
    
    def get_measures(self, component_id, station_id, hours_back=24):
        try:
            now = datetime.now(timezone.utc)
            params = {
                'date_from': (now - timedelta(hours=hours_back)).strftime('%Y-%m-%d'),
                'time_from': '0',
                'date_to': now.strftime('%Y-%m-%d'),
                'time_to': now.strftime('%H'),
                'station': str(station_id),
                'component': str(component_id),
                'scope': '2'
            }
        except Exception as e:
            raise ValueError("Invalid parameters for getting measures") from e
        return self._get_data("measures/json", params)  # Note v3 in endpoint
