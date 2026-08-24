import asyncio
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, StudentIssue, IssueMessage, StudentProfile, FacultyProfile, Assignment, Submission
from app.db.schemas import IssueOut, IssueCreate, IssueMessageCreate, IssueMessageOut
from app.api.dependencies import get_current_user, require_role
from app.core.ai import detect_distress_semantic, generate_gemini_response, generate_copilot_draft, DistressCrisisDetected
from app.core.notifications import dispatch_notification

router = APIRouter()


@router.post("/", response_model=IssueOut)
async def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["STUDENT"]))
):
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student profile not found")

    # Determine faculty ID
    faculty_id = None
    if issue_in.assignment_id:
        assignment = db.query(Assignment).filter(Assignment.id == issue_in.assignment_id).first()
        if assignment:
            faculty_id = assignment.faculty_id
            
    if not faculty_id:
        first_faculty = db.query(FacultyProfile).first()
        if not first_faculty:
            raise HTTPException(status_code=400, detail="No faculty members found in directory to assign this issue")
        faculty_id = first_faculty.id

    # Resolve faculty user_id for notifications
    fac_profile = db.query(FacultyProfile).filter(FacultyProfile.id == faculty_id).first()
    fac_user_id = fac_profile.user_id if fac_profile else None

    # Determine escalation level based on distress & category
    is_crisis = detect_distress_semantic(issue_in.description)
    is_grading_dispute = issue_in.category == "GRADING_DISPUTE"

    esc_level = 1
    issue_status = "OPEN"

    if is_crisis or is_grading_dispute:
        esc_level = 3
        issue_status = "ESCALATED"

    # Create the issue
    db_issue = StudentIssue(
        student_id=student.id,
        assignment_id=issue_in.assignment_id,
        submission_id=issue_in.submission_id,
        faculty_id=faculty_id,
        category=issue_in.category,
        description=issue_in.description,
        status=issue_status,
        escalation_level=esc_level,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_issue)
    db.flush()

    # Save initial student query
    initial_message = IssueMessage(
        issue_id=db_issue.id,
        sender_id=current_user.id,
        content=issue_in.description,
        is_ai_response=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(initial_message)
    db.flush()

    # Level 1 AI Response generation (if not escalated straight to Level 3)
    if esc_level == 1:
        try:
            ai_reply = generate_gemini_response(issue_in.description, issue_in.category)
            ai_message = IssueMessage(
                issue_id=db_issue.id,
                sender_id=None,  # None denotes AI response
                content=ai_reply,
                is_ai_response=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(ai_message)
        except DistressCrisisDetected:
            # Upgrade to Level 3 dynamically
            db_issue.escalation_level = 3
            db_issue.status = "ESCALATED"
            
            reassurance_msg = (
                "KANHA Support System:\n"
                "We notice you might be going through a difficult time. Please know that you are not alone.\n\n"
                "We have immediately escalated this ticket to Level 3 for direct faculty intervention. "
                "AI assistance has been suspended on this thread.\n\n"
                "If you need immediate help, please contact the SFI Student Care Desk at studentcare@sfi.edu "
                "or call the Suicide & Crisis Lifeline by dialing 988 (free, confidential, 24/7)."
            )
            reassurance_message = IssueMessage(
                issue_id=db_issue.id,
                sender_id=None,
                content=reassurance_msg,
                is_ai_response=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(reassurance_message)
            
            if fac_user_id:
                await dispatch_notification(
                    db=db,
                    user_id=fac_user_id,
                    title="Critical Student Doubt Escalated",
                    content="Crisis detected. Immediate human intervention required."
                )
    else:
        # Distress or grading dispute -> Immediate notification dispatch and reassurance message
        if is_crisis:
            reassurance_msg = (
                "KANHA Support System:\n"
                "We notice you might be going through a difficult time. Please know that you are not alone.\n\n"
                "We have immediately escalated this ticket to Level 3 for direct faculty intervention. "
                "AI assistance has been suspended on this thread.\n\n"
                "If you need immediate help, please contact the SFI Student Care Desk at studentcare@sfi.edu "
                "or call the Suicide & Crisis Lifeline by dialing 988 (free, confidential, 24/7)."
            )
            reassurance_message = IssueMessage(
                issue_id=db_issue.id,
                sender_id=None,
                content=reassurance_msg,
                is_ai_response=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(reassurance_message)

        if fac_user_id:
            msg = "Crisis detected. Immediate human intervention required." if is_crisis else "New grading dispute ticket filed."
            await dispatch_notification(
                db=db,
                user_id=fac_user_id,
                title="Critical Student Doubt Escalated",
                content=msg
            )

    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.get("/", response_model=List[IssueOut])
def read_issues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMIN":
        return db.query(StudentIssue).all()

    elif current_user.role == "FACULTY":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if not faculty:
            raise HTTPException(status_code=400, detail="Faculty profile not found")
        return db.query(StudentIssue).filter(StudentIssue.faculty_id == faculty.id).all()

    elif current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=400, detail="Student profile not found")
        return db.query(StudentIssue).filter(StudentIssue.student_id == student.id).all()

    return []


@router.get("/{id}", response_model=IssueOut)
def read_issue(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issue = db.query(StudentIssue).filter(StudentIssue.id == id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue ticket not found")

    # Access control boundaries
    if current_user.role == "ADMIN":
        return issue

    elif current_user.role == "FACULTY":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if not faculty or issue.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
        return issue

    elif current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or issue.student_id != student.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
        return issue

    raise HTTPException(status_code=403, detail="Access denied")


@router.post("/{id}/messages", response_model=IssueMessageOut)
def add_message(
    id: int,
    message_in: IssueMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issue = db.query(StudentIssue).filter(StudentIssue.id == id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue ticket not found")

    # Authorize sender
    is_authorized = False
    if current_user.role == "ADMIN":
        is_authorized = True
    elif current_user.role == "FACULTY":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if faculty and issue.faculty_id == faculty.id:
            is_authorized = True
    elif current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if student and issue.student_id == student.id:
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=403, detail="You do not have access to this ticket thread")

    # Add message
    db_message = IssueMessage(
        issue_id=id,
        sender_id=current_user.id,
        content=message_in.content,
        is_ai_response=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_message)

    # Escalation classification logic
    if current_user.role == "STUDENT":
        lower_content = message_in.content.lower()
        if "extension" in lower_content or "more time" in lower_content or "grade" in lower_content:
            issue.escalation_level = 3
            issue.status = "ESCALATED"

    db.commit()
    db.refresh(db_message)
    return db_message


@router.post("/{id}/escalate", response_model=IssueOut)
async def escalate_issue(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["STUDENT"]))
):
    issue = db.query(StudentIssue).filter(StudentIssue.id == id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue ticket not found")

    # Enforce Student Ownership
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student or issue.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized to escalate this issue")

    # Escalate to Level 2
    issue.escalation_level = 2
    issue.status = "ESCALATED"

    # Send Notification to Faculty
    fac_profile = db.query(FacultyProfile).filter(FacultyProfile.id == issue.faculty_id).first()
    if fac_profile:
        await dispatch_notification(
            db=db,
            user_id=fac_profile.user_id,
            title="Doubt Ticket Escalated to Level 2",
            content="Student Aarav Mehta has escalated their AI tutor ticket for review."
        )

    db.commit()
    db.refresh(issue)
    return issue


@router.get("/{id}/draft")
def get_issue_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY"]))
):
    issue = db.query(StudentIssue).filter(StudentIssue.id == id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue ticket not found")

    # Enforce Faculty Ownership
    faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if not faculty or issue.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="Not authorized to access draft for this ticket")

    if issue.escalation_level != 2:
        raise HTTPException(status_code=400, detail="Draft generation is only available for Level 2 escalated issues")

    draft = generate_copilot_draft(issue.description, issue.category)
    return {"draft": draft}
