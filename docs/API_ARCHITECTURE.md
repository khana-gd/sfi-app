# KANHA — API Architecture

This document describes the REST and WebSocket API architecture of the KANHA platform.

---

## 1. Authentication & Security Endpoints

*   **`POST /api/v1/auth/login`**:
    *   Form parameters: `username` (email), `password`.
    *   Returns: `{ "access_token": "JWT...", "token_type": "bearer", "role": "STUDENT" }`.
*   **`POST /api/v1/auth/logout`**:
    *   Invalidates token / clears HTTP-only cookie.
*   **`GET /api/v1/auth/me`**:
    *   Returns current active user details.

---

## 2. Directory & User Management (Admin Only)

*   **`GET /api/v1/admin/users`**: List all users.
*   **`POST /api/v1/admin/users`**: Create a user (Student, Faculty, or Admin).
*   **`PUT /api/v1/admin/users/{user_id}`**: Edit user status/role.
*   **`DELETE /api/v1/admin/users/{user_id}`**: Delete a user.
*   **`GET/POST/PUT/DELETE /api/v1/admin/courses`**: Manage course database.
*   **`GET/POST/PUT/DELETE /api/v1/admin/batches`**: Manage student batches.

---

## 3. Academic & Assignment Endpoints (Student & Faculty)

*   **`GET /api/v1/assignments`**:
    *   Student: List assignments targeted to their batch/profile.
    *   Faculty: List assignments they authored.
*   **`POST /api/v1/assignments`** (Faculty Only): Create assignment.
*   **`GET /api/v1/assignments/{id}`**: Get specific assignment details.
*   **`PUT /api/v1/assignments/{id}`** (Faculty Only): Edit assignment rules, publish or cancel.
*   **`POST /api/v1/assignments/{id}/submit`** (Student Only): Upload submission.
    *   Multipart Form: file (optional), submission_text.
*   **`GET /api/v1/submissions`**:
    *   Student: View their own submissions.
    *   Faculty: View submissions matching their created assignments.
*   **`POST /api/v1/submissions/{id}/feedback`** (Faculty Only): Post grade/review feedback.

---

## 4. KANHA Doubt & Escalation Endpoints

*   **`POST /api/v1/issues`** (Student Only): Initiate help request ticket.
    *   Body: `assignment_id`, `category`, `description`.
*   **`GET /api/v1/issues`**:
    *   Student: View their active help requests.
    *   Faculty: View escalated requests assigned to them.
*   **`POST /api/v1/issues/{id}/messages`**: Post message in ticket thread.
*   **`POST /api/v1/issues/{id}/resolve`**: Close ticket.

---

## 5. Realtime WebSockets

All real-time communication flows through:
`ws://localhost:8000/api/v1/ws/chat?token={JWT_TOKEN}`

### 5.1. Message Structure
Clients must send JSON frames:
```json
{
  "type": "chat_message",
  "data": {
    "conversation_id": 123,
    "content": "Hello, is the assignment due at 6 PM?"
  }
}
```

### 5.2. Typing Indicator
```json
{
  "type": "typing",
  "data": {
    "conversation_id": 123,
    "is_typing": true
  }
}
```

### 5.3. KANHA Streaming Responses
Server pushes chunks:
```json
{
  "type": "ai_stream",
  "data": {
    "conversation_id": 123,
    "chunk": "Sure, let's break it "
  }
}
```
At the end of stream:
```json
{
  "type": "ai_stream_end",
  "data": {
    "conversation_id": 123
  }
}
```

---

## 6. Centralized Event Hooks (Notification SSE)

For status modifications and alerts, client listens on:
`GET /api/v1/events/stream?token={JWT_TOKEN}`
(Server-Sent Events)

Triggers payload structures like:
*   `ASSIGNMENT_PUBLISHED`
*   `SUBMISSION_REVIEWED`
*   `NOTIFICATION_CREATED` (containing title/message to update badge counts).
