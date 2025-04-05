from datetime import datetime, timedelta

def parse_airquality_timestamp(ts: str) -> datetime:
    """Parse timestamps with 24:00:00 handling"""
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        if "24:00:00" in ts:
            base_ts = ts.replace("24:00:00", "00:00:00")
            base_dt = datetime.strptime(base_ts, "%Y-%m-%d %H:%M:%S")
            return base_dt + timedelta(days=1)
        raise