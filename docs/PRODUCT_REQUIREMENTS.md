# KANHA — Product Requirements Document (PRD)

## 1. Product Purpose & Concept
KANHA is an AI-powered academic companion and learning management system designed specifically for fashion design institutes. It acts as an intelligent bridge between faculty and students:
*   **FACULTY → KANHA → STUDENT**: Faculty post assignments, guidelines, and announcements. KANHA processes them, updates student tasks, triggers reminders, answers questions about the assignment, and provides research assistance.
*   **STUDENT → KANHA → FACULTY**: Students request task clarifications, ask research/styling questions, work on design concepts, or seek extensions. If a query requires human authority or evaluation (Level 3), KANHA escalates the issue to the relevant faculty member, collects the response, and communicates it back to the student.

KANHA does **not** replace teachers. It operates as an assistant to reduce administrative overhead and help students learn design methodology and history.

---

## 2. Target Roles & Access Control

### Student Role
Students require a dashboard answering **"What do I need to do today?"** via a feature called **"Today's Studio"**.
*   **Today's Studio**: View daily classes, active assignments, pending work, urgent deadlines, and faculty announcements.
*   **KANHA Study Companion**: Dedicated chat interface for assignment clarifications, fashion history research, textile techniques, and design concepts.
*   **Design Studio**: Moodboard generation, color palettes, sketch uploads (image-to-design recommendations), and AI-generated design concepts.
*   **Portfolio**: Organized sections (Fashion Illustration, Garment Design, Textile Projects, Embroidery, Assignments) with the ability to export as PDF/Web structure.
*   **Calendar & Attendance**: View scheduled classes, project reviews, assignment deadlines, and personal attendance metrics.
*   **Faculty Help System**: Direct text messaging with faculty and the ability to escalate KANHA conversations.

### Faculty Role
Faculty require a dashboard answering **"What needs my attention today?"** (e.g., student questions escalated, pending submissions, classes scheduled).
*   **Student Management**: View progress trackers, attendance logs, and student performance trends to identify who is falling behind.
*   **Assignment Management**: Create and target assignments (by course, batch, or individual student), set deadlines, attach PDFs/Drive resources, establish grading rubrics.
*   **Evaluation & Feedback**: Review submissions, add qualitative feedback, request revisions (updates status to REVISION_REQUIRED), approve submissions.
*   **Escalation Inbox**: View escalated student help requests with context logs and reply directly.
*   **KANHA Teacher Assistant**: Assist in generating rubrics, summarizing common student doubts (e.g., "12 students asked about fabric weights"), and generating assignment templates.

### Admin Role
Admins require a central dashboard to manage institute settings and user directories.
*   **Directories**: Add/edit/delete Students, Faculty, Admins, Courses, Batches, and Academic Years.
*   **Configuration**: Manage Google integrations (OAuth, Drive, Calendar), Gemini API settings, notification parameters, and system-wide default settings.
*   **Analytics**: Global student progress, institute submission rates, and AI utilization logs.
*   **Security & Audit**: Inspect system logs and role changes.

---

## 3. Core Features & System Workflows

### 3.1. Today's Studio (Student Homepage)
*   **Priority Feed**: Urgent assignments due within 24 hours, unread faculty announcements, and today's schedule.
*   **Progress Indicators**: Assignment completion status, overall attendance, and portfolio metrics.
*   **KANHA Prompts**: Context-aware prompts like: *"You have one assignment due today. Want to review it together?"*

### 3.2. Assignment System
*   **States**: `DRAFT`, `PUBLISHED`, `STARTED`, `SUBMITTED`, `UNDER_REVIEW`, `REVISION_REQUIRED`, `APPROVED`, `OVERDUE`, `CANCELLED`.
*   **Targeting**: Assignments can be assigned to a whole course, a specific batch, or targeted to individual students for remedial/advanced studies.
*   **Doubt/Help Button**: Built directly into the assignment view. Provides categorization (Technique, Instructions, Submission Issue, Request Extension) and immediately feeds to the KANHA chatbot with full assignment context.

### 3.3. Decision & Escalation Hierarchy
*   **Level 1 — AI Can Answer**: General definitions, fashion history concepts, technique explanations (e.g., "How do I do a running stitch?").
*   **Level 2 — AI Suggests Faculty Verification**: Ambiguous assignment details, conflicting guidelines (e.g., "The description says submit a PDF, but the title says Sketch"). KANHA answers to its best ability but reminds the student to check with their teacher.
*   **Level 3 — Faculty Required**: Requests for extensions, grading reviews, attendance exemptions, disciplinary issues, or changes to official rubrics. KANHA must block direct actions, offer to draft the request, and route it to the Faculty's dashboard.

### 3.4. Communication & Chat
*   **WebSocket Engine**: Powers real-time chat between Students and Faculty, as well as the streaming responses from KANHA.
*   **Context awareness**: Chat with KANHA remembers the active screen/assignment context.
*   **Announcements**: Faculty can broadcast announcements to whole batches, triggering immediate notifications.
