import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.models import User, StudentProfile, Submission, SubmissionFeedback, Attendance, Assignment, PortfolioItem
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("analytics_endpoints")

@router.get("/student/progress")
def get_student_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculates student dashboard progress and attendance trends."""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their progress analytics."
        )
        
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=403, detail="Student profile not found.")

    # 1. Assignment submission breakdown
    submissions = db.query(Submission).filter(Submission.student_id == student.id).all()
    approved = sum(1 for s in submissions if s.status == "APPROVED")
    revision = sum(1 for s in submissions if s.status == "REVISION_REQUIRED")
    under_review = sum(1 for s in submissions if s.status == "UNDER_REVIEW")
    submitted = sum(1 for s in submissions if s.status == "SUBMITTED")
    
    # 2. Attendance percentage
    attendance_records = db.query(Attendance).filter(Attendance.student_id == student.id).all()
    total_classes = len(attendance_records)
    present_classes = sum(1 for r in attendance_records if r.status in ("PRESENT", "LATE"))
    attendance_rate = (present_classes / total_classes * 100.0) if total_classes > 0 else 100.0

    # 3. Portfolio items count
    portfolio_count = db.query(PortfolioItem).filter(PortfolioItem.student_id == student.id).count()

    # 4. Grade trend history
    grades_query = db.query(SubmissionFeedback).join(Submission).filter(Submission.student_id == student.id).all()
    grade_trend = []
    for f in grades_query:
        grade_trend.append({
            "assignment": f.submission.assignment.title,
            "grade": f.grade or "Ungraded",
            "score": grade_to_numeric(f.grade)
        })

    return {
        "submission_stats": {
            "approved": approved,
            "revision_required": revision,
            "under_review": under_review,
            "submitted": submitted
        },
        "attendance_rate": round(attendance_rate, 1),
        "total_classes": total_classes,
        "present_classes": present_classes,
        "portfolio_items_count": portfolio_count,
        "grade_trend": grade_trend
    }

@router.get("/faculty/warnings")
def get_faculty_warnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Identifies and flags students falling behind based on low attendance or overdue work."""
    if current_user.role not in ("FACULTY", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only faculty or admins can view watchlist warnings."
        )

    students = db.query(StudentProfile).all()
    warnings = []
    now = datetime.now(timezone.utc)

    for student in students:
        reasons = []
        
        # 1. Check attendance rate
        attendance_records = db.query(Attendance).filter(Attendance.student_id == student.id).all()
        total_classes = len(attendance_records)
        present_classes = sum(1 for r in attendance_records if r.status in ("PRESENT", "LATE"))
        attendance_rate = (present_classes / total_classes * 100.0) if total_classes > 0 else 100.0
        
        if total_classes > 0 and attendance_rate < 75.0:
            reasons.append(f"Low attendance rate: {round(attendance_rate, 1)}% ({present_classes}/{total_classes} classes)")

        # 2. Check overdue work (past deadline and no approved submission)
        # Find assignments targeted to this student
        # To keep it simple, fetch all submissions and count overdue states or revision required
        submissions = db.query(Submission).filter(Submission.student_id == student.id).all()
        overdue_count = sum(1 for s in submissions if s.status == "REVISION_REQUIRED")
        
        # Also check assignments targeted to student's batch or individual student that have NO submission and deadline is past
        all_assignments = db.query(Assignment).all()
        unsubmitted_overdue = 0
        for a in all_assignments:
            # check if targeted to this student
            is_targeted = False
            for target in a.targets:
                if target.student_id == student.id or target.batch_id == student.batch_id:
                    is_targeted = True
                    break
            
            if is_targeted:
                # check if student submitted
                has_submitted = any(s.assignment_id == a.id for s in submissions)
                if not has_submitted and a.deadline.replace(tzinfo=timezone.utc) < now:
                    unsubmitted_overdue += 1
                    
        total_overdue = overdue_count + unsubmitted_overdue
        if total_overdue > 1:
            reasons.append(f"Unfinished overdue work: {total_overdue} assignments")

        # 3. Flag student if any warnings exist
        if reasons:
            warnings.append({
                "student_id": student.id,
                "name": f"{student.user.first_name or ''} {student.user.last_name or ''}".strip() or student.user.email,
                "email": student.user.email,
                "attendance_rate": round(attendance_rate, 1),
                "overdue_count": total_overdue,
                "reasons": reasons
            })

    return warnings

def grade_to_numeric(grade: str) -> int:
    """Helper to convert letter grades to coordinates for trending charts."""
    mapping = {
        "A+": 100, "A": 95, "A-": 90,
        "B+": 85, "B": 80, "B-": 75,
        "C+": 70, "C": 65, "C-": 60,
        "D": 50, "F": 0
    }
    return mapping.get(grade.upper() if grade else "", 70)
