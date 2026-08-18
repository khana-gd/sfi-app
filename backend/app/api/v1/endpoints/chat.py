import time
import json
from datetime import datetime, timezone
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User, Message, Conversation, ConversationParticipant, StudentProfile, FacultyProfile
from app.core.tickets import ticket_store
from app.core.websocket import manager

router = APIRouter()

RATE_LIMIT_WINDOW = 1.0  # seconds
RATE_LIMIT_MAX = 5


from app.db.models import Assignment, AssignmentTarget

def check_chat_boundary(db: Session, sender_id: int, recipient_id: int) -> bool:
    sender = db.query(User).filter(User.id == sender_id).first()
    recipient = db.query(User).filter(User.id == recipient_id).first()
    if not sender or not recipient:
        return False

    if sender.role == "ADMIN" or recipient.role == "ADMIN":
        return True

    if sender.role == "STUDENT" and recipient.role == "FACULTY":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == sender_id).first()
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == recipient_id).first()
        if student and faculty:
            teaches = db.query(Assignment).join(AssignmentTarget).filter(
                Assignment.faculty_id == faculty.id,
                AssignmentTarget.batch_id == student.batch_id
            ).first()
            return teaches is not None
    elif sender.role == "FACULTY" and recipient.role == "STUDENT":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == sender_id).first()
        student = db.query(StudentProfile).filter(StudentProfile.user_id == recipient_id).first()
        if faculty and student:
            teaches = db.query(Assignment).join(AssignmentTarget).filter(
                Assignment.faculty_id == faculty.id,
                AssignmentTarget.batch_id == student.batch_id
            ).first()
            return teaches is not None

    return False


from fastapi import Depends, HTTPException
from app.db.session import get_db
from app.api.dependencies import get_current_user

@router.get("/messages/{recipient_id}")
def get_chat_history(
    recipient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_chat_boundary(db, current_user.id, recipient_id):
        raise HTTPException(status_code=403, detail="Access denied: boundary violation.")

    sender_convs = db.query(ConversationParticipant.conversation_id).filter(
        ConversationParticipant.user_id == current_user.id
    ).all()
    sender_conv_ids = [c[0] for c in sender_convs]

    shared_conv = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id.in_(sender_conv_ids),
        ConversationParticipant.user_id == recipient_id
    ).first()

    if not shared_conv:
        return []

    messages = db.query(Message).filter(
        Message.conversation_id == shared_conv.conversation_id
    ).order_by(Message.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "content": m.content,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ticket: str = Query(...)
):
    # 1. Ticket Handshake Verification
    user_payload = ticket_store.consume_ticket(ticket)
    if not user_payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user_payload["user_id"]

    # 2. Establish connection
    await manager.connect(user_id, websocket)

    msg_timestamps: List[float] = []
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_text()
            
            # --- Rate Limiter ---
            now = time.time()
            msg_timestamps = [t for t in msg_timestamps if now - t < RATE_LIMIT_WINDOW]
            if len(msg_timestamps) >= RATE_LIMIT_MAX:
                await websocket.send_json({
                    "type": "ERROR",
                    "content": "Rate limit exceeded. Max 5 messages per second."
                })
                continue
            msg_timestamps.append(now)
            # --------------------

            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "ERROR", "content": "Invalid JSON format"})
                continue

            event_type = event.get("type")
            recipient_id = event.get("recipient_id")

            if not event_type or not recipient_id:
                await websocket.send_json({"type": "ERROR", "content": "Missing event type or recipient"})
                continue

            # Verify context boundaries
            if not check_chat_boundary(db, user_id, recipient_id):
                await websocket.send_json({
                    "type": "ERROR", 
                    "content": "Unauthorized chat target: context boundary violation."
                })
                continue

            if event_type == "SEND_MESSAGE":
                content = event.get("content", "")
                if not content:
                    continue

                # Query to find shared conversation
                sender_convs = db.query(ConversationParticipant.conversation_id).filter(
                    ConversationParticipant.user_id == user_id
                ).all()
                sender_conv_ids = [c[0] for c in sender_convs]
                
                shared_conv = db.query(ConversationParticipant).filter(
                    ConversationParticipant.conversation_id.in_(sender_conv_ids),
                    ConversationParticipant.user_id == recipient_id
                ).first()
                
                if shared_conv:
                    conversation_id = shared_conv.conversation_id
                else:
                    new_conv = Conversation()
                    db.add(new_conv)
                    db.flush()
                    
                    db.add(ConversationParticipant(conversation_id=new_conv.id, user_id=user_id))
                    db.add(ConversationParticipant(conversation_id=new_conv.id, user_id=recipient_id))
                    db.flush()
                    conversation_id = new_conv.id

                # Save message
                db_message = Message(
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    content=content,
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(db_message)
                db.commit()
                db.refresh(db_message)

                await manager.send_personal_message(recipient_id, {
                    "type": "MESSAGE",
                    "id": db_message.id,
                    "sender_id": user_id,
                    "recipient_id": recipient_id,
                    "content": content,
                    "created_at": db_message.created_at.isoformat()
                })

            elif event_type == "TYPING_SIGNAL":
                is_typing = event.get("is_typing", False)
                await manager.send_personal_message(recipient_id, {
                    "type": "TYPING",
                    "sender_id": user_id,
                    "is_typing": is_typing
                })

            elif event_type == "READ_RECEIPT":
                message_id = event.get("message_id")
                if message_id:
                    msg = db.query(Message).filter(Message.id == message_id).first()
                    if msg and msg.conversation.participants: # basic verification
                        msg.is_read = True
                        db.commit()
                        
                        await manager.send_personal_message(recipient_id, {
                            "type": "READ",
                            "message_id": message_id,
                            "reader_id": user_id
                        })

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
        db.close()
