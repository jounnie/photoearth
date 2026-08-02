# CLAUDE.md (backend-java — Spring Boot port)

Spring Boot port of the FastAPI backend (`backend/`); the two backends must serve an identical REST API so the same frontend build runs against either one unmodified.

## Commands
```bash
mvn spring-boot:run   # Start dev server on :8000
mvn test              # Run all tests
```

## Parity constraints with `backend/`
- Serves on the same port (`:8000`) and serves `frontend/dist/` as static files, same as the Python backend
- Jackson is configured for `SNAKE_CASE` property naming to match the FastAPI JSON contract
- SQLite connection pool is pinned to `maximum-pool-size: 1` (Hikari) — mirrors the Python side's need for a single shared connection; SQLite doesn't handle concurrent writers well
- Uses `hibernate-community-dialects`' `SQLiteDialect` since SQLite isn't a first-class Hibernate dialect

## Structure (`src/main/java/com/photoearth/`)
- `controller/` — `PhotoController`, `AlbumController`, `AiController` (mirror the FastAPI routers)
- `service/` — business logic, incl. `ExifExtractionService` and `AiLocationService`
- `domain/` / `repository/` — JPA entities and Spring Data repositories (mirror `models.py`)
- `dto/` + `mapper/` — request/response shapes and entity↔DTO mapping (mirror `schemas.py`)
