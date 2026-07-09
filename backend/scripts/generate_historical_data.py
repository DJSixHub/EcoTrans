from datetime import datetime, timedelta
from pathlib import Path
import csv
import random

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT = BASE_DIR / "data" / "seeds" / "historical_bus_data.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

terminals = [
    {
        "name": "Centro Intermodal",
        "zone": "Central",
        "latitude": -34.6037,
        "longitude": -58.3816,
    },
    {
        "name": "Terminal Norte",
        "zone": "Norte",
        "latitude": -34.5600,
        "longitude": -58.4390,
    },
    {
        "name": "Terminal Sur",
        "zone": "Sur",
        "latitude": -34.6667,
        "longitude": -58.4400,
    },
    {
        "name": "Hub Este",
        "zone": "Este",
        "latitude": -34.5850,
        "longitude": -58.3500,
    },
    {
        "name": "Hub Oeste",
        "zone": "Oeste",
        "latitude": -34.6000,
        "longitude": -58.4700,
    },
    {
        "name": "Plaza Metro",
        "zone": "Central",
        "latitude": -34.6100,
        "longitude": -58.3900,
    },
]

routes = [
    {
        "code": "A1",
        "origin": "Centro Intermodal",
        "destination": "Terminal Norte",
        "route_type": "Regular",
        "base_duration": 38,
        "capacity": 60,
        "base_frequency": 18,
    },
    {
        "code": "B2",
        "origin": "Terminal Sur",
        "destination": "Centro Intermodal",
        "route_type": "Express",
        "base_duration": 45,
        "capacity": 55,
        "base_frequency": 22,
    },
    {
        "code": "C3",
        "origin": "Hub Este",
        "destination": "Hub Oeste",
        "route_type": "Regular",
        "base_duration": 32,
        "capacity": 50,
        "base_frequency": 20,
    },
    {
        "code": "D4",
        "origin": "Terminal Norte",
        "destination": "Terminal Sur",
        "route_type": "Regular",
        "base_duration": 50,
        "capacity": 65,
        "base_frequency": 24,
    },
    {
        "code": "E5",
        "origin": "Plaza Metro",
        "destination": "Hub Este",
        "route_type": "Shuttle",
        "base_duration": 28,
        "capacity": 45,
        "base_frequency": 16,
    },
    {
        "code": "F6",
        "origin": "Hub Oeste",
        "destination": "Centro Intermodal",
        "route_type": "Regular",
        "base_duration": 42,
        "capacity": 60,
        "base_frequency": 20,
    },
]

service_levels = ["Standard", "High", "Reduced"]
peak_periods = ["morning", "midday", "afternoon", "night"]

start_date = datetime(2014, 1, 1)
end_date = datetime(2023, 12, 31)

fieldnames = [
    "route_code",
    "origin",
    "destination",
    "route_type",
    "terminal_name",
    "zone",
    "terminal_latitude",
    "terminal_longitude",
    "planned_frequency_minutes",
    "scheduled_minutes",
    "actual_minutes",
    "on_time",
    "passengers_boarded",
    "vehicle_capacity",
    "passenger_load_factor",
    "dispatch_datetime",
    "day_type",
    "peak_period",
    "service_level",
    "weather_condition",
]

holiday_dates = {
    (1, 1),
    (5, 1),
    (7, 9),
    (12, 25),
}

weather_patterns = [
    ("Despejado", 0.55),
    ("Parcialmente nublado", 0.25),
    ("Nublado", 0.10),
    ("Lluvia ligera", 0.06),
    ("Tormenta", 0.03),
    ("Alerta de inundación", 0.01),
]

random.seed(42)

with OUTPUT.open("w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    current = start_date
    while current <= end_date:
        weekday = current.weekday()
        is_weekend = weekday >= 5
        is_holiday = (current.month, current.day) in holiday_dates
        day_type = "holiday" if is_holiday else ("weekend" if is_weekend else "weekday")
        season_factor = 1.1 if current.month in {12, 1, 2} else (0.9 if current.month in {6, 7, 8} else 1.0)
        raw_weather = random.random()
        cumulative = 0.0
        for condition, prob in weather_patterns:
            cumulative += prob
            if raw_weather <= cumulative:
                weather_condition = condition
                break
        else:
            weather_condition = "Despejado"

        for route in routes:
            terminal = terminals[(current.day + len(route["code"])) % len(terminals)]
            planned_frequency = route["base_frequency"]
            if day_type == "weekend":
                planned_frequency = int(planned_frequency * 1.5)
            elif route["route_type"] == "Express":
                planned_frequency = max(12, planned_frequency - 4)

            transit_segments = [
                {"name": "morning", "start": 6, "end": 9, "multiplier": 1.2},
                {"name": "midday", "start": 9, "end": 17, "multiplier": 1.0},
                {"name": "afternoon", "start": 17, "end": 20, "multiplier": 1.3},
                {"name": "night", "start": 20, "end": 23, "multiplier": 0.6},
            ]

            route_popularity = 1.0 + (0.1 if route["route_type"] == "Express" else 0) + (0.15 if route["code"] in {"A1", "D4"} else 0)
            for segment in transit_segments:
                if day_type == "weekend" and segment["name"] == "night":
                    continue
                interval = max(10, int(planned_frequency / segment["multiplier"] + random.randint(-2, 2)))
                if day_type == "weekend":
                    interval = int(interval * 1.6)
                if segment["name"] == "night":
                    interval = max(interval, 20)
                dispatch_time = datetime(current.year, current.month, current.day, segment["start"], random.choice([0, 5, 10]))
                while dispatch_time.hour < segment["end"]:
                    base_scheduled = route["base_duration"] + random.randint(-3, 4)
                    weather_delay = 3 if weather_condition in {"Lluvia ligera", "Tormenta", "Alerta de inundación"} else 0
                    peak_delay = 3 if segment["name"] in {"morning", "afternoon"} else 0
                    actual_minutes = max(12, base_scheduled + random.randint(-2, 8) + weather_delay + peak_delay)
                    on_time = actual_minutes - base_scheduled <= 5
                    capacity = route["capacity"]
                    load_factor = min(1.0, max(0.22, 0.6 * route_popularity * season_factor + (0.2 if segment["name"] in {"morning", "afternoon"} else 0) - (0.15 if day_type == "weekend" else 0) + random.uniform(-0.1, 0.1)))
                    passengers = int(capacity * load_factor)
                    passenger_load_factor = round(min(100, max(10, passengers / capacity * 100)), 1)
                    service_level = random.choices(service_levels, weights=[0.7, 0.2, 0.1], k=1)[0]

                    writer.writerow(
                        {
                            "route_code": route["code"],
                            "origin": route["origin"],
                            "destination": route["destination"],
                            "route_type": route["route_type"],
                            "terminal_name": terminal["name"],
                            "zone": terminal["zone"],
                            "terminal_latitude": terminal["latitude"],
                            "terminal_longitude": terminal["longitude"],
                            "planned_frequency_minutes": planned_frequency,
                            "scheduled_minutes": base_scheduled,
                            "actual_minutes": actual_minutes,
                            "on_time": str(on_time),
                            "passengers_boarded": passengers,
                            "vehicle_capacity": capacity,
                            "passenger_load_factor": passenger_load_factor,
                            "dispatch_datetime": dispatch_time.isoformat(),
                            "day_type": day_type,
                            "peak_period": segment["name"],
                            "service_level": service_level,
                            "weather_condition": weather_condition,
                        }
                    )
                    dispatch_time += timedelta(minutes=interval)
        current += timedelta(days=1)

print(f"Generated {OUTPUT} with historical data")
