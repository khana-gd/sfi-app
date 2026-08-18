# KANHA — Development Roadmap

This document outlines the phased development roadmap of KANHA.

---

## Phased Development Schedule

### Phase 1 — Foundation (Completed)
*   **Tasks**:
    *   Setup Python FastAPI monorepo and directory structure.
    *   Configure database models with SQLAlchemy ORM and Alembic migrations.
    *   Establish JWT-based authentication.
    *   Implement Role-Based Access Control (RBAC) routing dependencies.
    *   Write RBAC boundary tests (student trying to hit faculty endpoints, cross-student privacy checks) in pytest and Playwright login flows.
    *   Setup React, TypeScript, and Vite frontend.
    *   Implement the Navy/Gold/Pink design system using Vanilla CSS custom variables.
    *   Create base structural layouts for Student, Faculty, and Admin dashboards.
    *   Populate database with local development seed accounts: `admin@kanha.local`, `faculty@kanha.local`, `student1@kanha.local`, `student2@kanha.local` using password `KanhaDevPass2026!`.
*   **Definition of Done**: Backend and frontend compile and start, migrations run, authentication works, all RBAC and E2E login tests pass.

### Phase 2 — Academic Core System
*   **Tasks**:
    *   Student Dashboard (`Today's Studio`).
    *   Faculty Dashboard (`What needs my attention today?`).
    *   Assignment Creation and Targeting System.
    *   Submissions upload and revision tracking.
    *   Attendance tracking and visual indicators.
    *   Local calendar milestones display.
    *   *Note*: The keyword-based escalation logic implemented in Phase 2 is a temporary heuristic placeholder. It will be replaced by the multi-level AI doubt classification engine in Phase 4.

### Phase 3 — Realtime Communication
*   **Tasks**:
    *   WebSocket Manager setup.
    *   Student ↔ Faculty live chat interface.
    *   Typing indicators, message reading status, and unread badges.
    *   Notification Dispatcher linking DB, email mock, and live UI pushes.

### Phase 4 — KANHA AI Integration
*   **Tasks**:
    *   `AIProvider` and `GeminiProvider` implementation using the `google-genai` SDK.
    *   Streaming responses over WebSockets.
    *   Doubt classification & escalation engine (Levels 1, 2, 3).
    *   Assignment-aware prompt context ingestion.

### Phase 5 — Grounded Research Engine
*   **Tasks**:
    *   Configure Google Search Grounding with Gemini.
    *   Parse citation sources (metadata, URLs) and display reference cards.
    *   Categorize fashion-specific fields (embroidery, textiles, silhouettes).

### Phase 6 — Fashion AI & Design Studio
*   **Tasks**:
    *   `FashionImageProvider` with `GeminiImageProvider` using configurable image generation models.
    *   Design Studio text-to-design, sketch analysis (multimodal), and moodboard grids.
    *   AI-generated content watermarking.

### Phase 7 — Portfolio System
*   **Tasks**:
    *   Portfolio collections layout.
    *   Portfolio PDF compilation structure.

### Phase 8 — Analytics Suite
*   **Tasks**:
    *   Student progress tracking graphs.
    *   Faculty warning systems identifying students falling behind.

### Phase 9 — Production Hardening
*   **Tasks**:
    *   PostgreSQL production migration verification.
    *   Security reviews and credential audit.
    *   Playwright comprehensive regression testing.

---

## Roadmap Status Summary
As of August 2026, all **Phases 1 through 9** are fully implemented, local seeds and database connection compatibility are validated, and the complete backend pytest and frontend Playwright E2E suites are running at 100% success.

