# KANHA — Testing Strategy

This document details the testing architecture, pytest coverage, and Playwright End-to-End browser verification test suites.

---

## 1. Pytest Backend Suite (Unit & Integration)

The backend tests are executed using `pytest` and `pytest-asyncio`. Tests utilize a temporary SQLite database (configured to run in memory or a test file `test_kanha.db`) to ensure isolation.

### 1.1. Test Suites (Required for Phase 1)
*   **Authentication Suite**:
    *   `test_user_registration`: Checks that user database accounts can be added with hashed passwords.
    *   `test_user_login`: Verifies JWT token generation and verification.
    *   `test_invalid_credentials`: Verifies block rules for incorrect credentials.
*   **RBAC & Boundary Access Control Suite** (Must pass before completing Phase 1):
    *   `test_student_access_limits`: Verifies that a user authenticated as `STUDENT` receives `403 FORBIDDEN` when hitting faculty-only endpoints (e.g. `POST /api/v1/assignments`) or admin-only directories (e.g. `GET /api/v1/admin/users`).
    *   `test_student_privacy_boundary`: Verifies that a student cannot query submissions, design projects, or portfolios belonging to another student (should return `403` or `404`).
    *   `test_faculty_access_limits`: Verifies that `FACULTY` cannot access admin system configurations or delete users.
*   **Database & Migration Suite**:
    *   Verifies that tables can be successfully created and populated via SQLAlchemy ORM models.
    *   Verifies that foreign key constraints throw database integrity errors when broken.

---

## 2. Playwright E2E Browser Suite

Playwright tests verify the integrated frontend-backend UI flows using headless and headed browser execution.

### 2.1. E2E Flows to Verify (Phase 1 Ready)
*   **Login Flow**:
    *   Student log in -> validates redirection to student dashboard (`Today's Studio`).
    *   Faculty log in -> validates redirection to faculty dashboard.
    *   Admin log in -> validates redirection to admin control room.
*   **Assignment Creation & Submission Flow**:
    *   Faculty logs in -> opens "Create Assignment" -> publishes an assignment.
    *   Student logs in -> sees notification badge update -> opens assignment description -> posts a submission.
*   **KANHA Help & Escalation Flow**:
    *   Student opens assignment -> clicks "Need Help" -> posts query to KANHA.
    *   KANHA responds with Level 1 help.
    *   Student posts extension request -> KANHA blocks action and escalates ticket to faculty.
    *   Faculty logs in -> views escalated issue -> types a reply.
    *   Student receives notification of reply.

---

## 3. Test Command Usage

### 3.1. Running backend tests
```bash
cd backend
pytest -v
```

### 3.2. Running Playwright tests
```bash
cd tests/e2e
npx playwright test
```
