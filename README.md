# EcoTrans
Sistema de Monitoreo y Análisis de la Red de Transporte Urbano

## Fase 1 - Infraestructura Base e Ingestión Histórica

Este proyecto implementa:
- Base de datos PostgreSQL en contenedor Docker.
- Backend Python con FastAPI y SQLModel.
- Pipeline ETL para ingestión de datos históricos de transporte urbano.
- Interfaz web inicial en un contenedor independiente.
- Migraciones versionadas con Alembic.

## Arquitectura

Servicios:
- `database`: PostgreSQL.
- `backend_api`: FastAPI + SQLModel, expone `/api/analytics/summary`.
- `frontend`: sitio estático con visualizaciones básicas.

## Ejecución

Desde la raíz del repositorio:

```bash
docker-compose up --build
```

Luego abrir:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Validación

- `docker-compose up --build` construye y levanta los tres servicios.
- El backend inicializa la base de datos y carga el dataset histórico automáticamente.
- La interfaz consume el backend para mostrar métricas de cumplimiento y tiempos de espera.

## Desarrollo futuro (Fases 2 y 3)

- Autenticación y roles (Administrador, Inspector, Analista).
- Endpoints REST protegidos por JWT.
- Registros de incidencias en tiempo real.
- Integración de datos meteorológicos y correlación con retrasos.
