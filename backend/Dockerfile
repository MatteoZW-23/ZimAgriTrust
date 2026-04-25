FROM python:3.12-slim

WORKDIR /app

# ── System dependencies (cached until this block changes) ──────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# ── Python dependencies (cached until requirements.txt changes) ────────────
# Copy ONLY requirements.txt first so this layer is only invalidated when
# requirements.txt actually changes — not when any source file changes.
COPY requirements.txt .

# --mount=type=cache persists the pip HTTP cache on the Docker build host
# across ALL rebuilds, so packages are never re-downloaded from PyPI.
# The cache id is pinned so every backend rebuild shares the same cache.
RUN --mount=type=cache,target=/root/.cache/pip,id=agritrust-pip \
    pip install --default-timeout=300 --retries=5 -r requirements.txt

# ── Application source (invalidated on any source change, but pip is cached) 
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "app"]
