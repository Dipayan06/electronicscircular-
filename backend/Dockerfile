# Backend container image (optional — see deployment.md).
FROM python:3.11-slim

WORKDIR /app

# System deps for building wheels (psycopg2 etc.) kept minimal.
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Uvicorn honours the platform-provided $PORT; defaults to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
