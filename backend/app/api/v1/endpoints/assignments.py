from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Assignment, AssignmentTarget, StudentProfile, FacultyProfile
from app.db.schemas import AssignmentCreate, AssignmentOut
from app.api.dependencies import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[AssignmentOut])
def read_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "ADMIN":
        return db.query(Assignment).all()
        
    elif current_user.role == "FACULTY":
        # Fetch faculty profile to filter by ID
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if not faculty:
            raise HTTPException(status_code=400, detail="Faculty profile not found")
        return db.query(Assignment).filter(Assignment.faculty_id == faculty.id).all()
        
    elif current_user.role == "STUDENT":
        # Fetch student profile to identify batch
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=400, detail="Student profile not found")
            
        # Select assignments targeted to batch or directly to student
        query = db.query(Assignment).join(AssignmentTarget).filter(
            (AssignmentTarget.batch_id == student.batch_id) | 
            (AssignmentTarget.student_id == student.id)
        )
        return query.all()
        
    return []


@router.post("/", response_model=AssignmentOut)
def create_assignment(
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY"]))
):
    faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if not faculty:
        raise HTTPException(status_code=400, detail="Faculty profile not found")
        
    db_assignment = Assignment(
        title=assignment_in.title,
        description=assignment_in.description,
        faculty_id=faculty.id,
        deadline=assignment_in.deadline,
        status="PUBLISHED",  # Automatically publish for Phase 1 simplicity
        priority=assignment_in.priority,
        category=assignment_in.category,
        grading_criteria=assignment_in.grading_criteria,
        drive_file_id=assignment_in.drive_file_id,
        drive_file_name=assignment_in.drive_file_name,
        drive_file_url=assignment_in.drive_file_url
    )
    db.add(db_assignment)
    db.flush()

    # Sync milestone with Google Calendar mock
    from app.core.google_workspace import GoogleWorkspaceMockService
    try:
        GoogleWorkspaceMockService.create_calendar_event(
            title=f"Assignment: {db_assignment.title}",
            start_time=db_assignment.deadline,
            description=db_assignment.description,
            user_email=current_user.email
        )
    except Exception as e:
        print(f"Failed to sync calendar milestone: {e}")
    
    # Save target mappings
    if assignment_in.batch_ids:
        for b_id in assignment_in.batch_ids:
            db.add(AssignmentTarget(assignment_id=db_assignment.id, batch_id=b_id))
    if assignment_in.student_ids:
        for s_id in assignment_in.student_ids:
            db.add(AssignmentTarget(assignment_id=db_assignment.id, student_id=s_id))
            
    # Fallback to Batch 1 if no target specified
    if not assignment_in.batch_ids and not assignment_in.student_ids:
        db.add(AssignmentTarget(assignment_id=db_assignment.id, batch_id=1))
            
    db.commit()
    return db_assignment


@router.get("/{id}", response_model=AssignmentOut)
def read_assignment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = db.query(Assignment).filter(Assignment.id == id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    if current_user.role == "ADMIN":
        return assignment
        
    elif current_user.role == "FACULTY":
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if not faculty or assignment.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this assignment")
        return assignment
        
    elif current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=400, detail="Student profile not found")
            
        # Verify student is a target
        target = db.query(AssignmentTarget).filter(
            AssignmentTarget.assignment_id == id
        ).filter(
            (AssignmentTarget.batch_id == student.batch_id) |
            (AssignmentTarget.student_id == student.id)
        ).first()
        
        if not target:
            raise HTTPException(status_code=403, detail="Assignment not targeted to this student")
        return assignment
        
    raise HTTPException(status_code=403, detail="Access denied")
