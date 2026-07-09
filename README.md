# EcoTrans

Sistema de Monitoreo y Análisis de la Red de Transporte Urbano.

## Stack

- **Base de datos**: PostgreSQL 15 en contenedor Docker
- **Backend**: Python + FastAPI + SQLModel, puerto `8000`
- **Frontend**: HTML/CSS/JS estático servido con nginx, puerto `3000`

## Levantar el proyecto

```bash
docker-compose up --build
```

Esto construye e inicia tres contenedores: `database`, `backend_api`, `frontend`.

## Visualización

| Componente | URL |
|------------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Documentación Swagger | http://localhost:8000/docs |

## Usuarios y roles

| Usuario | Contraseña | Rol | Permisos |
|---------|-----------|-----|----------|
| `admin` | `Admin123!` | Administrador | CRUD de eventos, incidencias, usuarios; acceso a todos los paneles |
| `inspector` | `Inspect123!` | Inspector | CRUD de incidencias, lectura de eventos y paneles |
| `analyst` | `Analyst123!` | Analista | Solo visualización de paneles (sin CRUD) |

## Funcionalidades

- **Autenticación JWT** con roles (admin, inspector, analyst)
- **Dashboard con paneles**: resumen, gráficos (cumplimiento, espera, serie temporal), mapa geo de terminales, correlación con lluvia
- **Gestión de eventos históricos** (`DispatchEvent`): CRUD de salidas programadas
- **Registro de incidencias** en tiempo real
- **Panel admin**: listar/eliminar usuarios, estadísticas del sistema
- **Mapa interactivo** con las 6 terminales georreferenciadas
- **Correlación lluvia**: compara días lluviosos vs secos (pasajeros, espera, cumplimiento)
