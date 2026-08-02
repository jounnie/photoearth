# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.13-slim

# Copy the uv binary from the official image (fast, no pip needed)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps before copying app code so Docker can cache this layer
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --no-dev --frozen

# Copy backend source
COPY backend/ ./backend/

# main.py resolves frontend at ../../frontend/dist (relative to backend/app/)
COPY --from=frontend /build/dist ./frontend/dist

# /data is the Fly.io persistent volume mount point
RUN mkdir -p /data/uploads

ENV DATABASE_URL=sqlite:////data/photoearth.db
ENV UPLOAD_DIR=/data/uploads

EXPOSE 8000
WORKDIR /app/backend
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
