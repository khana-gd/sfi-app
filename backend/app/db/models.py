from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Table,
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# Helper function for default timezone-aware datetime in SQLAlchemy
def get_utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False)  # STUDENT, FACULTY, ADMIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    admin_profile = relationship("AdminProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="SET NULL"), nullable=True)
    enrollment_number = Column(String(100), unique=True, nullable=False)

    user = relationship("User", back_populates="student_profile")
    batch = relationship("Batch", back_populates="students")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    issues = relationship("StudentIssue", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    portfolio_items = relationship("PortfolioItem", back_populates="student", cascade="all, delete-orphan")
    design_projects = relationship("DesignProject", back_populates="student", cascade="all, delete-orphan")


class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_id = Column(String(100), unique=True, nullable=False)

    user = relationship("User", back_populates="faculty_profile")
    assignments = relationship("Assignment", back_populates="faculty", cascade="all, delete-orphan")
    feedbacks = relationship("SubmissionFeedback", back_populates="faculty", cascade="all, delete-orphan")
    issues = relationship("StudentIssue", back_populates="faculty")


class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    user = relationship("User", back_populates="admin_profile")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    batches = relationship("Batch", back_populates="course", cascade="all, delete-orphan")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    academic_year = Column(String(50), nullable=False)

    course = relationship("Course", back_populates="batches")
    students = relationship("StudentProfile", back_populates="batch")
    calendar_events = relationship("CalendarEvent", back_populates="batch", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime(timezone=True), default=get_utc_now)
    deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="DRAFT")  # DRAFT, PUBLISHED, CANCELLED
    priority = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH
    category = Column(String(100), nullable=True)
    grading_criteria = Column(Text, nullable=True)
    drive_file_id = Column(String(255), nullable=True)
    drive_file_name = Column(String(255), nullable=True)
    drive_file_url = Column(String(500), nullable=True)

    faculty = relationship("FacultyProfile", back_populates="assignments")
    targets = relationship("AssignmentTarget", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")
    issues = relationship("StudentIssue", back_populates="assignment")


class AssignmentTarget(Base):
    __tablename__ = "assignment_targets"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=True)

    assignment = relationship("Assignment", back_populates="targets")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=get_utc_now)
    status = Column(String(50), default="SUBMITTED")  # SUBMITTED, UNDER_REVIEW, REVISION_REQUIRED, APPROVED, OVERDUE
    submission_text = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("StudentProfile", back_populates="submissions")
    feedback = relationship("SubmissionFeedback", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    issues = relationship("StudentIssue", back_populates="submission")


class SubmissionFeedback(Base):
    __tablename__ = "submission_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id", ondelete="CASCADE"), nullable=False)
    feedback_text = Column(Text, nullable=False)
    grade = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    submission = relationship("Submission", back_populates="feedback")
    faculty = relationship("FacultyProfile", back_populates="feedbacks")


class StudentIssue(Base):
    __tablename__ = "student_issues"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=False)  # INSTRUCTION_HELP, TECHNIQUE_HELP, RESEARCH_HELP, etc.
    description = Column(Text, nullable=False)
    status = Column(String(50), default="OPEN")  # OPEN, RESOLVED, ESCALATED
    escalation_level = Column(Integer, default=1)  # 1, 2, 3
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    student = relationship("StudentProfile", back_populates="issues")
    assignment = relationship("Assignment", back_populates="issues")
    submission = relationship("Submission", back_populates="issues")
    faculty = relationship("FacultyProfile", back_populates="issues")
    messages = relationship("IssueMessage", back_populates="issue", cascade="all, delete-orphan")


class IssueMessage(Base):
    __tablename__ = "issue_messages"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("student_issues.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_ai_response = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    issue = relationship("StudentIssue", back_populates="messages")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    conversation = relationship("Conversation", back_populates="participants")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    conversation = relationship("Conversation", back_populates="messages")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String(100), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    user = relationship("User", back_populates="notifications")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False)  # CLASS, DEADLINE, REVIEW, EVENT, HOLIDAY
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    batch = relationship("Batch", back_populates="calendar_events")
    attendance_records = relationship("Attendance", back_populates="calendar_event", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    calendar_event_id = Column(Integer, ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="PRESENT")  # PRESENT, ABSENT, LATE, EXCUSED
    marked_at = Column(DateTime(timezone=True), default=get_utc_now)

    student = relationship("StudentProfile", back_populates="attendance_records")
    calendar_event = relationship("CalendarEvent", back_populates="attendance_records")


class DesignProject(Base):
    __tablename__ = "design_projects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    inspiration_source = Column(Text, nullable=True)
    fabric_notes = Column(Text, nullable=True)
    color_palette = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    student = relationship("StudentProfile", back_populates="design_projects")
    moodboards = relationship("Moodboard", back_populates="project", cascade="all, delete-orphan")


class Moodboard(Base):
    __tablename__ = "moodboards"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("design_projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    project = relationship("DesignProject", back_populates="moodboards")
    items = relationship("MoodboardItem", back_populates="moodboard", cascade="all, delete-orphan")


class MoodboardItem(Base):
    __tablename__ = "moodboard_items"

    id = Column(Integer, primary_key=True, index=True)
    moodboard_id = Column(Integer, ForeignKey("moodboards.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String(50), nullable=False)  # AI_CONCEPT, SKETCH, REFERENCE_IMAGE, etc.
    file_url = Column(String(500), nullable=False)
    caption = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    source_title = Column(String(255), nullable=True)
    is_ai_generated = Column(Boolean, default=False)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    moodboard = relationship("Moodboard", back_populates="items")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # ILLUSTRATION, GARMENT_DESIGN, etc.
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    student = relationship("StudentProfile", back_populates="portfolio_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)

    user = relationship("User", back_populates="audit_logs")
