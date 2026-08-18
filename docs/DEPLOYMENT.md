# KANHA — Deployment Guide

This document describes the deployment architecture and setup steps for production release.

---

## 1. Production Technology Stack
*   **Hosting**: Cloud Run (or GCP VM instance).
*   **Database**: Managed PostgreSQL (e.g. Cloud SQL).
*   **Caching & Sessions**: Redis (Optional, for token revocation lists).
*   **Storage**: Google Cloud Storage (GCS) for submissions, sketches, and portfolio files.
*   **Process Manager**: Gunicorn running Uvicorn workers.

---

## 2. PostgreSQL Configuration

Production database connections require configuring the connection string in the environment:

`DATABASE_URL=postgresql://user:password@host:port/database`

### Migration Strategy
Migrations are managed via Alembic. To run migrations in production:
```bash
# Set the production DATABASE_URL in your env
export DATABASE_URL="postgresql://user:password@host:port/database"
# Execute migrations to bring the database schema to the latest version
alembic upgrade head
```

---

## 3. Environment Variables (Production)

Ensure the following variables are securely managed in secrets management (e.g. Secret Manager) rather than configuration files:

```ini
# Core Backend
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=secure-random-256bit-string
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI Provider Credentials
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image

# Google Integrations (OAuth, Calendar, Drive)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://kanha.yourdomain.com/api/v1/auth/google/callback
```

---

## 4. WebSocket Scaling & Redis Pub/Sub

> [!WARNING]
> The default `ConnectionManager` stores WebSocket client connections in-memory within the local Python process. 
> To support horizontal scaling across multiple Gunicorn workers or distributed Cloud Run containers, the local in-memory manager **must** be upgraded to use a Redis-backed Pub/Sub architecture (e.g. Broadcaster or custom Redis pub/sub messaging channels) to route messages correctly between processes.
