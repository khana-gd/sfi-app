from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, StudentProfile, FacultyProfile, AdminProfile
from app.db.schemas import UserCreate, UserOut
from app.core.security import get_password_hash
from app.api.dependencies import require_role

router = APIRouter()


@router.get("/", response_model=List[UserOut], dependencies=[Depends(require_role(["ADMIN"]))])
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=UserOut, dependencies=[Depends(require_role(["ADMIN"]))])
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(user)
    db.flush()  # Obtain user ID before creating profile records
    
    # Initialize appropriate profile
    if user.role == "STUDENT":
        # Create student profile with placeholder enrollment number
        student_profile = StudentProfile(
            user_id=user.id,
            enrollment_number=f"ENR-{datetime.now().year}-{user.id:03d}"
        )
        db.add(student_profile)
    elif user.role == "FACULTY":
        faculty_profile = FacultyProfile(
            user_id=user.id,
            employee_id=f"EMP-{datetime.now().year}-{user.id:03d}"
        )
        db.add(faculty_profile)
    elif user.role == "ADMIN":
        admin_profile = AdminProfile(
            user_id=user.id
        )
        db.add(admin_profile)
        
    db.commit()
    return user
