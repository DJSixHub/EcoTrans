from datetime import date, timedelta
from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT = BASE_DIR / "data" / "weather_seeds" / "historical_weather.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

conditions = [
    (0, "Despejado"),
    (2, "Nublado"),
    (8, "Lluvia"),
    (12, "Tormenta"),
    (20, "Alerta de inundación"),
]

start_date = date(2014, 1, 1)
end_date = date(2023, 12, 31)

with OUTPUT.open("w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["observed_date", "precipitation_mm", "condition", "severe"])
    writer.writeheader()
    current = start_date
    while current <= end_date:
        day_index = (current.toordinal() % 30)
        if day_index < 4:
            precipitation = 0.0
            condition = "Clear"
            severe = False
        elif day_index < 12:
            precipitation = round((day_index - 3) * 1.4, 1)
            condition = "Cloudy"
            severe = False
        elif day_index < 20:
            precipitation = round((day_index - 10) * 2.2, 1)
            condition = "Rain"
            severe = False
        else:
            precipitation = round((day_index - 18) * 5.1, 1)
            condition = "Thunderstorm"
            severe = True

        writer.writerow(
            {
                "observed_date": current.isoformat(),
                "precipitation_mm": precipitation,
                "condition": condition,
                "severe": str(severe),
            }
        )
        current += timedelta(days=1)

print(f"Generated {OUTPUT}")
