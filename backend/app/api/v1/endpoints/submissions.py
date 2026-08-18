import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Submission, SubmissionFeedback, StudentProfile, FacultyProfile, Assignment, AssignmentTarget
from app.db.schemas import SubmissionOut, FeedbackOut, FeedbackCreate
from app.api.dependencies import get_current_user, require_role

router = APIRouter()

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def sanitize_filename(filename: str) -> str:
    # Basic filename sanitization
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF, PNG, JPG, and JPEG are allowed."
        )
    return f"{uuid.uuid4()}{ext}"


def validate_file_content(file: UploadFile, ext: str) -> None:
    header = file.file.read(8)
    file.file.seek(0)  # Reset pointer so file can be read again normally
    
    if ext == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file content signature."
            )
    elif ext == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PNG file content signature."
            )
    elif ext in [".jpg", ".jpeg"]:
        if not header.startswith(b"\xff\xd8\xff"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JPEG file content signature."
            )


@router.post("/", response_model=SubmissionOut)
async def create_submission(
    assignment_id: int = Form(...),
    submission_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["STUDENT"]))
):
    # 1. Fetch student profile
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student profile not found")

    # 2. Check that assignment exists and student is targeted
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    target = db.query(AssignmentTarget).filter(
        AssignmentTarget.assignment_id == assignment_id
    ).filter(
        (AssignmentTarget.batch_id == student.batch_id) |
        (AssignmentTarget.student_id == student.id)
    ).first()

    if not target:
        raise HTTPException(status_code=403, detail="You are not authorized to submit for this assignment")

    # 3. Handle file upload if present
    file_url = None
    if file:
        # Check size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum limit of 10MB."
            )

        ext = os.path.splitext(file.filename)[1].lower()
        unique_name = sanitize_filename(file.filename)
        
        # Verify content/magic bytes
        validate_file_content(file, ext)

        # Ensure upload folder exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        file_url = f"/uploads/{unique_name}"

    # 4. Insert submission record
    db_submission = Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        submission_text=submission_text,
        file_url=file_url,
        status="SUBMITTED",
        submitted_at=datetime.now(timezone.utc)
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


@router.get("/", response_model=List[SubmissionOut])
def read_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMIN":
        return db.query(Submission).all()

    elif current_user.role == "FACULTY":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if not faculty:
            raise HTTPException(status_code=400, detail="Faculty profile not found")
        # List submissions for assignments created by this faculty
        return db.query(Submission).join(Assignment).filter(Assignment.faculty_id == faculty.id).all()

    elif current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=400, detail="Student profile not found")
        return db.query(Submission).filter(Submission.student_id == student.id).all()

    return []


@router.get("/{id}", response_model=SubmissionOut)
def read_submission(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Authorize boundary check
    if current_user.role == "ADMIN":
        return submission

    elif current_user.role == "FACULTY":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if not faculty or submission.assignment.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this submission")
        return submission

    elif current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or submission.student_id != student.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this submission")
        return submission

    raise HTTPException(status_code=403, detail="Access denied")


@router.post("/{id}/feedback", response_model=FeedbackOut)
def create_feedback(
    id: int,
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY"]))
):
    # Note: feedback_in is just a payload schema
    submission = db.query(Submission).filter(Submission.id == id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if not faculty or submission.assignment.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="You do not teach this assignment's course")

    # 1. Update submission status based on evaluation
    # If a grade/feedback is provided, set status. E.g. revision required or approved.
    # To keep it simple: if feedback has a revision flag or status is passed, let's map it.
    # We will look for an existing feedback record or create a new one
    db_feedback = db.query(SubmissionFeedback).filter(SubmissionFeedback.submission_id == id).first()
    
    if db_feedback:
        db_feedback.feedback_text = feedback_in.feedback_text
        db_feedback.grade = feedback_in.grade
        db_feedback.created_at = datetime.now(timezone.utc)
    else:
        db_feedback = SubmissionFeedback(
            submission_id=id,
            faculty_id=faculty.id,
            feedback_text=feedback_in.feedback_text,
            grade=feedback_in.grade,
            created_at=datetime.now(timezone.utc)
        )
        db.add(db_feedback)

    # Automatically set submission state to APPROVED unless feedback indicates revision required
    if "revision" in feedback_in.feedback_text.lower():
        submission.status = "REVISION_REQUIRED"
    else:
        submission.status = "APPROVED"

    db.commit()
    db.refresh(db_feedback)
    return db_feedback
