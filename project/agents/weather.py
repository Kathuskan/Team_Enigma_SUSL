"""Forecasts use representative town coordinates, never a phone location."""
from datetime import datetime, timedelta, timezone
import math

import httpx

COLOMBO = timezone(timedelta(hours=5, minutes=30))
AREAS = {
    "Colombo": (6.93,79.86), "Gampaha": (7.09,80.01), "Kalutara": (6.59,79.96),
    "Kandy": (7.29,80.64), "Matale": (7.47,80.62), "Nuwara Eliya": (6.95,80.79),
    "Galle": (6.03,80.22), "Matara": (5.95,80.54), "Jaffna": (9.66,80.03),
    "Kilinochchi": (9.38,80.40), "Mannar": (8.98,79.90), "Vavuniya": (8.75,80.50),
    "Mullaitivu": (9.27,80.81), "Trincomalee": (8.59,81.22), "Puttalam": (8.04,79.83),
    "Badulla": (6.99,81.06), "Monaragala": (6.87,81.35), "Ratnapura": (6.68,80.40),
    "Kegalle": (7.25,80.35),
    "Polonnaruwa": (7.94, 81.00), "Anuradhapura": (8.31, 80.40),
    "Kurunegala": (7.49, 80.36), "Ampara": (7.30, 81.67),
    "Batticaloa": (7.72, 81.70), "Hambantota": (6.12, 81.12),
}
FIELDS = ("precipitation_probability", "precipitation", "wind_speed_10m", "relative_humidity_2m")


def assess(hourly, start):
    times = hourly["time"]
    indices = [times.index((start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:00")) for h in range(12)]
    readings = [[hourly[key][i] for i in indices] for key in FIELDS]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for row in readings for v in row):
        raise ValueError("Incomplete forecast")
    probability, rain, wind, humidity = readings
    return dict(start=start.isoformat(), probability=max(probability), rain_mm=round(sum(rain), 2),
                wind_kmh=max(wind), humidity=max(humidity),
                wash_off=max(probability) > 40 or sum(rain) > 2,
                drift=max(wind) > 15, humid=max(humidity) > 85)


def forecast(area, tomorrow):
    now = datetime.now(COLOMBO)
    start = now.replace(minute=0, second=0, microsecond=0)
    if tomorrow:
        start = (start + timedelta(days=1)).replace(hour=6)
    lat, lon = AREAS[area]
    try:
        result = httpx.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "hourly": ",".join(FIELDS),
            "forecast_days": 3, "timezone": "Asia/Colombo"}, timeout=5)
        result.raise_for_status()
        return assess(result.json()["hourly"], start)
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None
