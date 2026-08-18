# KANHA — Security & Privacy Architecture

This document describes the security protocols, encryption methods, role boundaries, and privacy protection controls in the KANHA platform.

---

## 1. Authentication & Token Security

*   **Password Hashing**: Done using `bcrypt` (via `passlib`). Raw passwords are never stored.
*   **Token Standard**: JSON Web Tokens (JWT) using `PyJWT`, signed with HMAC-SHA256 (restricted strictly to the `HS256` algorithm) and a 256-bit secret key loaded from environment variables (`JWT_SECRET_KEY`).
*   **Expirations**: Token expiration is strictly enforced (`ACCESS_TOKEN_EXPIRE_MINUTES`, default: 60 minutes).
*   **Transportation**: Tokens are transmitted via `Authorization: Bearer <JWT_TOKEN>` header or HTTP-only cookies in production.

---

## 2. Role-Based Access Control (RBAC)

FastAPI dependencies enforce strict boundaries for user roles: `STUDENT`, `FACULTY`, and `ADMIN`.

```python
from fastapi import Depends, HTTPException, status
from app.db.models import User
from app.api.dependencies import get_current_user

def require_role(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user
    return dependency

# Usage:
# @router.post("/assignments", dependencies=[Depends(require_role(["FACULTY"]))])
```

### 2.1. Security Boundary Rules
1.  **Student Boundary**:
    *   Students can only access assignments assigned to their specific batch or profile.
    *   Students can only read/edit/delete their own design projects, portfolio items, and submissions.
    *   Students have no access to faculty dashboards, lists of all students in other courses, or student profiles outside their batch.
2.  **Faculty Boundary**:
    *   Faculty can only view data, submissions, and calendar events for courses/batches they teach.
    *   Faculty have no access to admin system settings.
3.  **Admin Boundary**:
    *   Admins manage directories and settings but cannot view private student KANHA chat logs unless explicitly requested under audit log tracking.

---

## 3. Data Privacy & AI Guardrails

*   **Context Exposure Limits**: KANHA chatbot is loaded with the active user's ID. When fetching context (assignments, previous messages), the database queries are strictly filtered by user ID to prevent data leakages between students.
*   **Google Drive Security**: Google Drive access scopes are restricted to files attached by faculty for assignments. KANHA will only access attachments matching the student's active course ID.
*   **Audit Logging**: Every sensitive action (logins, role modifications, assignment publications, feedback submissions, and system-wide setting changes) creates an entry in the `audit_logs` table containing the user ID, action description, and timestamp.

---

## 4. Input Validations & Rate Limiting

*   **FastAPI Pydantic Schema Validations**: All routes utilize strict Pydantic schemas. String inputs (e.g. usernames, emails) are validated using standard regex patterns to block SQL injection and Cross-Site Scripting (XSS).
*   **File Upload Sanitization**: File uploads are restricted to standard formats (PDF, JPEG, PNG, ZIP). File sizes are capped at 10MB in backend routers.
