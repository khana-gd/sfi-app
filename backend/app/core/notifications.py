import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import User, Notification
from app.core.websocket import manager

LOG_FILE = "logs/notifications.log"

async def dispatch_notification(db: Session, user_id: int, title: str, content: str):
    # 1. Save notification to database
    db_notification = Notification(
        user_id=user_id,
        title=title,
        message=content,
        event_type="SYSTEM",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # 2. Check if user is actively connected via WebSocket
    if user_id in manager.active_connections:
        # Push real-time event
        await manager.send_personal_message(user_id, {
            "type": "NOTIFICATION",
            "id": db_notification.id,
            "title": title,
            "content": content,
            "created_at": db_notification.created_at.isoformat()
        })
    else:
        # User is offline -> Write a mock notification email log
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        user = db.query(User).filter(User.id == user_id).first()
        email_addr = user.email if user else f"user_{user_id}@kanha.local"
        
        log_entry = (
            f"[{datetime.now(timezone.utc).isoformat()}] EMAIL MOCK\n"
            f"To: {email_addr}\n"
            f"Subject: {title}\n"
            f"Content: {content}\n"
            f"----------------------------------------\n"
        )
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
