import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, Assignment, StudentProfile, AssignmentTarget
from app.api.v1.endpoints.auth import get_current_user
from app.core.google_workspace import GoogleWorkspaceMockService

router = APIRouter()
logger = logging.getLogger("google_endpoints")

class DriveAttachIn(BaseModel):
    assignment_id: int
    file_id: str
    file_name: str
    file_url: str

class DocExportIn(BaseModel):
    title: str
    content_markdown: str

@router.post("/drive/attach")
def attach_drive_file(
    payload: DriveAttachIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allows Faculty to attach a Google Drive document to an assignment."""
    if current_user.role != "FACULTY":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty profiles can attach study materials."
        )
    
    assignment = db.query(Assignment).filter_by(id=payload.assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_444_NOT_FOUND if hasattr(status, "HTTP_444_NOT_FOUND") else 404,
            detail="Assignment not found."
        )
    
    # Update assignment drive columns
    assignment.drive_file_id = payload.file_id
    assignment.drive_file_name = payload.file_name
    assignment.drive_file_url = payload.file_url
    db.commit()
    db.refresh(assignment)
    
    # Sync milestone to Google Calendar mock automatically when attached
    GoogleWorkspaceMockService.create_calendar_event(
        title=f"Milestone: {assignment.title}",
        start_time=assignment.deadline,
        description=assignment.description,
        user_email=current_user.email
    )
    
    return {
        "status": "success",
        "drive_file_name": assignment.drive_file_name,
        "drive_file_url": assignment.drive_file_url
    }

@router.get("/drive/stream/{file_id}")
def stream_drive_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Streams a mock Google Drive attachment securely to authorized users."""
    # Enforce targeted assignment ownership boundaries
    if current_user.role == "STUDENT":
        # Find the assignment that features this attachment
        assignment = db.query(Assignment).filter(Assignment.drive_file_id == file_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Drive file attachment not found."
            )
        
        # Load student profile
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_430_ACCESS_DENIED if hasattr(status, "HTTP_430_ACCESS_DENIED") else 403,
                detail="Student profile not found."
            )
            
        # Check target maps
        is_targeted = db.query(AssignmentTarget).filter(
            AssignmentTarget.assignment_id == assignment.id,
            (AssignmentTarget.student_id == student.id) | (AssignmentTarget.batch_id == student.batch_id)
        ).first()
        
        if not is_targeted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not targeted by this assignment."
            )

    try:
        file_stream = GoogleWorkspaceMockService.stream_drive_file(file_id)
        # We can serve it with standard octet-stream attachment headers
        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=drive_download_{file_id}.bin"}
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive file not found."
        )

@router.post("/calendar/sync")
def sync_calendar_milestone(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually triggers academic calendar synchronization."""
    assignment = db.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found."
        )
        
    event_id = GoogleWorkspaceMockService.create_calendar_event(
        title=f"Deadline: {assignment.title}",
        start_time=assignment.deadline,
        description=assignment.description,
        user_email=current_user.email
    )
    
    return {"status": "success", "event_id": event_id}

@router.post("/docs/export")
def export_docs(
    payload: DocExportIn,
    current_user: User = Depends(get_current_user)
):
    """Exports assignment notes or portfolio logs to Google Docs mock."""
    doc_url = GoogleWorkspaceMockService.export_to_google_doc(
        title=payload.title,
        content_markdown=payload.content_markdown,
        user_email=current_user.email
    )
    return {"status": "success", "google_doc_url": doc_url}
