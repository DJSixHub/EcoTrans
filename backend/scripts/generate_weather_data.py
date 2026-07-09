from datetime import date, timedelta
from pathlib import Path
import csv
import random

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT = BASE_DIR / "data" / "weather_seeds" / "historical_weather.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

condition_profiles = [
    ("Despejado", 0.55),
    ("Parcialmente nublado", 0.20),
    ("Nublado", 0.12),
    ("Lluvia ligera", 0.08),
    ("Tormenta", 0.04),
    ("Alerta de inundación", 0.01),
]

start_date = date(2014, 1, 1)
end_date = date(2023, 12, 31)

random.seed(311)

def seasonal_temperature(month):
    if month in {12, 1, 2}:
        return random.uniform(22.0, 32.0)
    if month in {3, 4, 5}:
        return random.uniform(16.0, 26.0)
    if month in {6, 7, 8}:
        return random.uniform(10.0, 18.0)
    return random.uniform(18.0, 28.0)

with OUTPUT.open("w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(
        csvfile,
        fieldnames=[
            "observed_date",
            "precipitation_mm",
            "condition",
            "severe",
            "temperature_c",
            "wind_kmh",
            "humidity_pct",
            "visibility_km",
        ],
    )
    writer.writeheader()

    current = start_date
    while current <= end_date:
        month = current.month
        temperature_c = round(seasonal_temperature(month) + random.uniform(-3, 3), 1)
        humidity_pct = min(100, max(40, int(60 + (12 - month) * 1.5 + random.uniform(-15, 15))))
        wind_kmh = round(max(5.0, min(55.0, random.gauss(18.0, 8.0))), 1)
        visibility_km = round(max(2.0, min(16.0, 14.0 - humidity_pct / 15 + random.uniform(-2.0, 2.0))), 1)

        base_roll = random.random()
        cumulative = 0.0
        for condition, probability in condition_profiles:
            cumulative += probability
            if base_roll <= cumulative:
                selected_condition = condition
                break
        else:
            selected_condition = "Despejado"

        if selected_condition == "Despejado":
            precipitation_mm = round(random.uniform(0.0, 0.4), 1)
        elif selected_condition == "Parcialmente nublado":
            precipitation_mm = round(random.uniform(0.0, 1.2), 1)
        elif selected_condition == "Nublado":
            precipitation_mm = round(random.uniform(0.2, 3.5), 1)
        elif selected_condition == "Lluvia ligera":
            precipitation_mm = round(random.uniform(3.0, 14.0), 1)
        elif selected_condition == "Tormenta":
            precipitation_mm = round(random.uniform(12.0, 35.0), 1)
        else:
            precipitation_mm = round(random.uniform(30.0, 90.0), 1)

        severe = selected_condition in {"Tormenta", "Alerta de inundación"}

        writer.writerow(
            {
                "observed_date": current.isoformat(),
                "precipitation_mm": precipitation_mm,
                "condition": selected_condition,
                "severe": str(severe),
                "temperature_c": temperature_c,
                "wind_kmh": wind_kmh,
                "humidity_pct": humidity_pct,
                "visibility_km": visibility_km,
            }
        )
        current += timedelta(days=1)

print(f"Generated {OUTPUT}")
