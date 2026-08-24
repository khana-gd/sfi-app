---
title: Kanha Backend
emoji: 🎓
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
---

# KANHA — AI-Powered Institute Learning & Management Platform

KANHA is an AI-powered academic companion and learning management system tailored for fashion design institutes. It serves as an intelligent coordinator and bridge between students and faculty.

## Features Overview
*   **Today's Studio**: Immediate display of daily classes, active tasks, and unread announcements.
*   **Doubt/Help Escalation**: Level-based routing (Level 1 direct AI, Level 2 check with faculty, Level 3 direct escalation ticket).
*   **Design Studio & Moodboard**: Digital moodboard grid supporting drag-and-drop reference files and AI-generated concepts with source attribution.
*   **Grounded Research Engine**: Google Search grounding integration for verified citations and links.
*   **Academic Workflows**: Roles (Student, Faculty, Admin), assignments list, submissions, and portfolio compilation.

---

## Development Environment Setup

### Prerequisites
*   Python 3.11.9
*   Node.js v24.18.0
*   npm 11.16.0

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd kanha
    ```

2.  **Configure environment variables**:
    Copy `.env.example` to `.env` and fill in your keys:
    ```bash
    cp .env.example .env
    ```

3.  **Setup Backend (FastAPI)**:
    ```bash
    cd backend
    python -m venv venv
    source venv/Scripts/activate # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    alembic upgrade head
    python -m app.db.seeds
    uvicorn app.main:app --reload
    ```

4.  **Setup Frontend (React + TS + Vite)**:
    ```bash
    cd ../frontend
    npm install
    npm run dev
    ```

---

## Seed Accounts (Local Development)

All seed accounts share the password: **`KanhaDevPass2026!`**

*   **Admin**: `admin@kanha.local`
*   **Faculty**: `faculty@kanha.local`
*   **Student 1**: `student1@kanha.local`
*   **Student 2**: `student2@kanha.local`

---

## Running Verification Tests

### Pytest Backend
```bash
cd backend
pytest -v
```

### Playwright E2E
```bash
cd tests/e2e
npx playwright test
```
