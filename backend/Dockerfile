# Production-grade multi-stage Dockerfile for AgriTrust Backend v2.0
# Supports both legacy and new DDD architecture

FROM python:3.10-slim AS builder

WORKDIR /app

# ── System dependencies ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Build Python dependencies ──────────────────────────────────────────────
COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip,id=agritrust-pip \
    pip install --upgrade pip && \
    pip install \
        --default-timeout=600 \
        --retries=10 \
        --no-cache-dir \
        -r requirements.txt

# ============================================================================
# Production Runtime Stage
# ============================================================================
FROM python:3.10-slim AS production

WORKDIR /app

# Non-root user for security
RUN useradd -m -u 1000 appuser

# ── Runtime dependencies only ────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libgthread-2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Copy Python packages from builder ────────────────────────────────────────
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# ── Copy application code ────────────────────────────────────────────────────
COPY . .

# ── Set ownership ────────────────────────────────────────────────────────────
RUN chown -R appuser:appuser /app
USER appuser

# ── Health check ─────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Environment ──────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH

# Port exposed
EXPOSE 8000

# ── Startup Command ──────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# Production-Slim Stage — <500MB, NO PyTorch/TensorFlow/Ultralytics
# Uses ONNX Runtime + scikit-learn inference only.
# Build with: docker build --target production-slim -t agritrust-backend:slim .
# ============================================================================
FROM python:3.11-slim AS slim-builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.prod.txt ./

RUN --mount=type=cache,target=/root/.cache/pip,id=agritrust-pip-slim \
    pip install --upgrade pip && \
    pip install \
        --default-timeout=600 \
        --retries=10 \
        --no-cache-dir \
        -r requirements.prod.txt

FROM python:3.11-slim AS production-slim

LABEL maintainer="ZimAgriTrust DevOps" \
      description="Production backend — no PyTorch/TensorFlow/Ultralytics (<500MB)" \
      version="1.0"

WORKDIR /app

RUN useradd -m -u 1000 appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=slim-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=slim-builder /usr/local/bin /usr/local/bin

COPY . .

# Models are provided via shared volume at runtime; this ensures the path exists
RUN mkdir -p /app/models && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# ============================================================================
# Development Stage — used by docker-compose.dev.yml (target: development)
# Runs as root, source is bind-mounted so edits hot-reload via uvicorn --reload
# ============================================================================
FROM python:3.10-slim AS development

WORKDIR /app

# Runtime + dev utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libgthread-2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code (will be overridden by volume mount in compose, but needed for
# initial migrations/celery containers that don't mount volumes)
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# No USER switch — dev runs as root so mounted volumes are writable
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

