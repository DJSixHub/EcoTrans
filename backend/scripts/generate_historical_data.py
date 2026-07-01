from datetime import datetime, timedelta
from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT = BASE_DIR / "data" / "seeds" / "historical_bus_data.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

terminals = [
    ("Centro Intermodal", "Central"),
    ("Terminal Norte", "Norte"),
    ("Terminal Sur", "Sur"),
    ("Hub Este", "Este"),
    ("Hub Oeste", "Oeste"),
    ("Plaza Metro", "Central"),
]
routes = [
    ("A1", "Centro Intermodal", "Terminal Norte"),
    ("B2", "Terminal Sur", "Centro Intermodal"),
    ("C3", "Hub Este", "Hub Oeste"),
    ("D4", "Terminal Norte", "Terminal Sur"),
    ("E5", "Plaza Metro", "Hub Este"),
    ("F6", "Hub Oeste", "Centro Intermodal"),
]

start_date = datetime(2019, 1, 1)
end_date = datetime(2023, 12, 31)

fieldnames = [
    "route_code",
    "origin",
    "destination",
    "terminal_name",
    "zone",
    "dispatch_datetime",
    "scheduled_minutes",
    "actual_minutes",
    "passengers_boarded",
]

with OUTPUT.open("w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    current = start_date
    while current <= end_date:
        for route_code, origin, destination in routes:
            terminal_name, zone = terminals[(current.day + len(route_code)) % len(terminals)]
            scheduled = 25 + ((current.day * len(route_code)) % 20)
            delay = ((current.day + len(route_code) * 2) % 18) - 4
            actual = max(10, scheduled + delay)
            passengers = 30 + ((current.toordinal() + len(route_code) * 5) % 70)
            writer.writerow(
                {
                    "route_code": route_code,
                    "origin": origin,
                    "destination": destination,
                    "terminal_name": terminal_name,
                    "zone": zone,
                    "dispatch_datetime": current.isoformat(),
                    "scheduled_minutes": str(scheduled),
                    "actual_minutes": str(actual),
                    "passengers_boarded": str(passengers),
                }
            )
        current += timedelta(days=2)

print(f"Generated {OUTPUT} with historical data")
