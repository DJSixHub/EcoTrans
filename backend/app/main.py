from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from app.core.config import get_settings
from app.services.etl import bootstrap_database

settings = get_settings()
app = FastAPI(title="EcoTrans Backend API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event() -> None:
    if settings.initialize_db:
        try:
            await bootstrap_database()
        except Exception as e:
            import logging
            logging.getLogger("ecotrans.startup").exception("Database bootstrap failed: %s", e)


@app.get("/")
def root() -> dict:
    return {"project": "EcoTrans", "status": "running"}
