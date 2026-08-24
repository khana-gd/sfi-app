FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source files
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .

# Set environment paths
ENV PYTHONPATH=/app
ENV PORT=7860

# Run migrations, seed database, and launch uvicorn on port 7860 (Hugging Face default)
CMD alembic upgrade head && python -m app.db.seeds && uvicorn app.main:app --host 0.0.0.0 --port 7860
