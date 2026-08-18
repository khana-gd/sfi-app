from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None


# User schemas
class UserBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str  # STUDENT, FACULTY, ADMIN
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Profiles
class StudentProfileBase(BaseModel):
    batch_id: Optional[int] = None
    enrollment_number: str


class StudentProfileOut(StudentProfileBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class FacultyProfileBase(BaseModel):
    employee_id: str


class FacultyProfileOut(FacultyProfileBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# Academic
class CourseBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseOut(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BatchBase(BaseModel):
    course_id: int
    name: str
    academic_year: str


class BatchCreate(BatchBase):
    pass


class BatchOut(BatchBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Assignments
class AssignmentBase(BaseModel):
    title: str
    description: str
    deadline: datetime
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    category: Optional[str] = None
    grading_criteria: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_file_name: Optional[str] = None
    drive_file_url: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    batch_ids: Optional[List[int]] = None
    student_ids: Optional[List[int]] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None  # DRAFT, PUBLISHED, CANCELLED
    grading_criteria: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_file_name: Optional[str] = None
    drive_file_url: Optional[str] = None


class AssignmentOut(AssignmentBase):
    id: int
    faculty_id: int
    status: str
    start_date: datetime

    model_config = ConfigDict(from_attributes=True)


# Submissions
class SubmissionBase(BaseModel):
    submission_text: Optional[str] = None
    file_url: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    assignment_id: int


class SubmissionOut(SubmissionBase):
    id: int
    assignment_id: int
    student_id: int
    submitted_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


# Submission Feedback
class FeedbackCreate(BaseModel):
    feedback_text: str
    grade: Optional[str] = None


class FeedbackOut(FeedbackCreate):
    id: int
    submission_id: int
    faculty_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Help/Doubt System
class IssueCreate(BaseModel):
    assignment_id: Optional[int] = None
    submission_id: Optional[int] = None
    category: str
    description: str


class IssueMessageCreate(BaseModel):
    content: str


class IssueMessageOut(BaseModel):
    id: int
    issue_id: int
    sender_id: Optional[int] = None
    content: str
    is_ai_response: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueOut(BaseModel):
    id: int
    student_id: int
    assignment_id: Optional[int] = None
    submission_id: Optional[int] = None
    faculty_id: int
    category: str
    description: str
    status: str
    escalation_level: int
    created_at: datetime
    messages: List[IssueMessageOut] = []

    model_config = ConfigDict(from_attributes=True)


# Design Studio Schemas
class DesignProjectCreate(BaseModel):
    name: str
    inspiration_source: Optional[str] = None
    fabric_notes: Optional[str] = None
    color_palette: Optional[str] = None

class DesignProjectOut(BaseModel):
    id: int
    student_id: int
    name: str
    inspiration_source: Optional[str] = None
    fabric_notes: Optional[str] = None
    color_palette: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MoodboardCreate(BaseModel):
    project_id: int
    name: str

class MoodboardItemCreate(BaseModel):
    item_type: str
    file_url: str
    caption: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    is_ai_generated: Optional[bool] = False
    position_x: Optional[int] = 0
    position_y: Optional[int] = 0

class MoodboardItemOut(BaseModel):
    id: int
    moodboard_id: int
    item_type: str
    file_url: str
    caption: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    is_ai_generated: bool
    position_x: int
    position_y: int

    model_config = ConfigDict(from_attributes=True)

class MoodboardOut(BaseModel):
    id: int
    project_id: int
    name: str
    created_at: datetime
    items: List[MoodboardItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class PortfolioItemCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    file_url: str

class PortfolioItemOut(BaseModel):
    id: int
    student_id: int
    title: str
    category: str
    description: Optional[str] = None
    file_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


