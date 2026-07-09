import asyncio
import logging
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict
from alembic import command
from alembic.config import Config
from sqlalchemy import select, func, literal, delete
from sqlalchemy.engine.row import Row
from app.core.config import get_settings
from app.db.models import DispatchEvent, Incident, Route, Terminal, User, WeatherObservation
from app.db.session import async_session
from app.services.users import create_default_users

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data" / "seeds" / "historical_bus_data.csv"
WEATHER_FILE = BASE_DIR / "data" / "weather_seeds" / "historical_weather.csv"
ALEMBIC_INI = BASE_DIR / "alembic.ini"


def _get_sync_database_url() -> str:
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def run_migrations() -> None:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", _get_sync_database_url())
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    command.upgrade(config, "head")


def _unwrap_scalar_entity(entity):
    if isinstance(entity, Row) and len(entity) == 1:
        return entity[0]
    return entity


async def load_weather_data() -> None:
    if not WEATHER_FILE.exists():
        raise FileNotFoundError(f"Weather file not found: {WEATHER_FILE}")

    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(WeatherObservation))
        if count and count > 0:
            return

        observations = []
        with WEATHER_FILE.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    observed_date = datetime.fromisoformat(row["observed_date"]).date()
                    precipitation_mm = float(row["precipitation_mm"])
                    condition = row["condition"].strip()
                    severe = row["severe"].strip().lower() in {"true", "1", "yes"}
                except Exception:
                    continue
                observations.append(
                    WeatherObservation(
                        observed_date=observed_date,
                        precipitation_mm=precipitation_mm,
                        condition=condition,
                        severe=severe,
                    )
                )
        session.add_all(observations)
        await session.commit()


async def load_seed_data() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Seed file not found: {DATA_FILE}")

    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(DispatchEvent))
        if count and count > 0:
            return

        terminals: Dict[str, Terminal] = {
            t.name: t
            for t in (await session.scalars(select(Terminal))).all()
        }
        routes: Dict[str, Route] = {
            r.code: r
            for r in (await session.scalars(select(Route))).all()
        }

        events = []
        with DATA_FILE.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    route_code = row["route_code"].strip().upper()
                    terminal_name = row["terminal_name"].strip().title()
                    scheduled_minutes = int(row["scheduled_minutes"])
                    actual_minutes = int(row["actual_minutes"])
                    passengers = int(row["passengers_boarded"])
                    dispatch_datetime = datetime.fromisoformat(row["dispatch_datetime"])
                    terminal_latitude = float(row.get("terminal_latitude", "0") or 0)
                    terminal_longitude = float(row.get("terminal_longitude", "0") or 0)
                    planned_frequency = int(row.get("planned_frequency_minutes", "0") or 0)
                    service_level = row.get("service_level", "Standard").strip() or "Standard"
                    day_type = row.get("day_type", "weekday").strip() or "weekday"
                    peak_period = row.get("peak_period", "offpeak").strip() or "offpeak"
                    vehicle_capacity = int(row.get("vehicle_capacity", "50") or 50)
                    passenger_load_factor = float(row.get("passenger_load_factor", "0") or 0)
                    weather_condition = row.get("weather_condition", "").strip() or None
                    route_type = row.get("route_type", "Regular").strip() or "Regular"
                except Exception:
                    continue

                if route_code == "" or terminal_name == "":
                    continue

                if terminal_name not in terminals:
                    terminal = Terminal(
                        name=terminal_name,
                        zone=row.get("zone", "Central"),
                        latitude=terminal_latitude,
                        longitude=terminal_longitude,
                    )
                    session.add(terminal)
                    await session.flush()
                    terminals[terminal_name] = terminal
                else:
                    terminal = terminals[terminal_name]
                    if terminal.latitude == 0.0 and terminal_latitude != 0.0:
                        terminal.latitude = terminal_latitude
                    if terminal.longitude == 0.0 and terminal_longitude != 0.0:
                        terminal.longitude = terminal_longitude

                if route_code not in routes:
                    route = Route(
                        code=route_code,
                        origin=row.get("origin", "Unknown"),
                        destination=row.get("destination", "Unknown"),
                        route_type=route_type,
                    )
                    session.add(route)
                    await session.flush()
                    routes[route_code] = route
                else:
                    route = routes[route_code]
                    if route.route_type == "Regular" and route_type != "Regular":
                        route.route_type = route_type

                if actual_minutes < 0 or scheduled_minutes < 0 or vehicle_capacity <= 0:
                    continue

                normalized_load = min(100.0, max(0.0, passenger_load_factor or round(passengers / vehicle_capacity * 100, 1)))
                events.append(
                    DispatchEvent(
                        route_id=route.id,
                        terminal_id=terminal.id,
                        dispatch_datetime=dispatch_datetime,
                        scheduled_minutes=scheduled_minutes,
                        actual_minutes=actual_minutes,
                        passengers_boarded=passengers,
                        on_time=(actual_minutes - scheduled_minutes) <= 5,
                        planned_frequency_minutes=planned_frequency,
                        route_type=route.route_type,
                        service_level=service_level,
                        day_type=day_type,
                        peak_period=peak_period,
                        vehicle_capacity=vehicle_capacity,
                        passenger_load_factor=normalized_load,
                        weather_condition=weather_condition,
                    )
                )

        session.add_all(events)
        await session.commit()


async def load_sample_incidents() -> None:
    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(Incident))
        if count and count > 0:
            return

        routes = [
            _unwrap_scalar_entity(route)
            for route in (await session.scalars(select(Route))).all()
        ]
        terminals = [
            _unwrap_scalar_entity(terminal)
            for terminal in (await session.scalars(select(Terminal))).all()
        ]
        reporter_user = await session.scalar(select(User).where(User.username == "inspector"))

        if not routes or not terminals or not reporter_user:
            return

        samples = [
            {
                "route_id": routes[0].id,
                "terminal_id": terminals[0].id,
                "type": "Vehículo fuera de servicio",
                "description": "Unidad averiada en estación central durante hora pico.",
                "status": "open",
            },
            {
                "route_id": routes[1].id,
                "terminal_id": terminals[1].id,
                "type": "Desvío temporal",
                "description": "Obras viales generaron cambio de recorrido en el tramo norte.",
                "status": "investigating",
            },
            {
                "route_id": routes[2].id,
                "terminal_id": terminals[2].id,
                "type": "Incidente de tráfico",
                "description": "Accidente menor en el acceso este y retraso en salida.",
                "status": "open",
            },
            {
                "route_id": routes[-1].id,
                "terminal_id": terminals[-1].id,
                "type": "Alta ocupación",
                "description": "Saturación de pasajeros en horas punta, recomendada reasignación.",
                "status": "open",
            },
        ]

        for sample in samples:
            incident = Incident(
                report_time=datetime.utcnow(),
                route_id=sample["route_id"],
                terminal_id=sample["terminal_id"],
                type=sample["type"],
                description=sample["description"],
                status=sample["status"],
                reported_by_id=reporter_user.id,
            )
            session.add(incident)

        await session.commit()


async def reset_database() -> None:
    async with async_session() as session:
        await session.exec(delete(Incident))
        await session.exec(delete(DispatchEvent))
        await session.exec(delete(WeatherObservation))
        await session.exec(delete(Route))
        await session.exec(delete(Terminal))
        await session.exec(delete(User))
        await session.commit()


async def bootstrap_database() -> None:
    async def wait_for_database() -> None:
        logger = logging.getLogger("ecotrans.etl")
        retries = 60
        delay = 2
        attempt = 0
        while retries > 0:
            attempt += 1
            try:
                async with async_session() as session:
                    await session.exec(select(literal(1)))
                logger.info("Database is available (attempt %d)", attempt)
                return
            except Exception as e:
                logger.debug("Database not available yet (attempt %d): %s", attempt, e)
                retries -= 1
                await asyncio.sleep(delay)
        raise RuntimeError("Database did not become available in time after %d attempts" % attempt)

    await wait_for_database()
    run_migrations()
    if settings.force_db_reset:
        await reset_database()
    await load_seed_data()
    await load_weather_data()
    await create_default_users()
    await load_sample_incidents()
