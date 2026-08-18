from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal
from app.db.models import (
    User,
    StudentProfile,
    FacultyProfile,
    AdminProfile,
    Course,
    Batch,
    CalendarEvent,
    Assignment,
    AssignmentTarget
)
from app.core.security import get_password_hash


def seed_db():
    db = SessionLocal()
    try:
        # 1. Check if seed already exists
        admin_user = db.query(User).filter_by(email="admin@kanha.local").first()
        if admin_user:
            print("Database already seeded.")
            return

        print("Seeding database...")
        dev_password_hash = get_password_hash("KanhaDevPass2026!")

        # 2. Create Base Course & Batch
        course = Course(
            name="Fashion Design & Illustration",
            code="FD-101",
            description="Foundation study of fashion illustrations, garment construction, and textiles."
        )
        db.add(course)
        db.flush()

        batch = Batch(
            course_id=course.id,
            name="Batch 2026 - Section A",
            academic_year="2026-2027"
        )
        db.add(batch)
        db.flush()

        # 3. Create Users
        # Admin
        admin = User(
            email="admin@kanha.local",
            hashed_password=dev_password_hash,
            first_name="SFI",
            last_name="Administrator",
            role="ADMIN"
        )
        db.add(admin)
        db.flush()
        db.add(AdminProfile(user_id=admin.id))

        # Faculty
        faculty_user = User(
            email="faculty@kanha.local",
            hashed_password=dev_password_hash,
            first_name="Prof. Ananya",
            last_name="Sen",
            role="FACULTY"
        )
        db.add(faculty_user)
        db.flush()
        faculty_profile = FacultyProfile(user_id=faculty_user.id, employee_id="EMP-2026-01")
        db.add(faculty_profile)

        # Student 1
        student1_user = User(
            email="student1@kanha.local",
            hashed_password=dev_password_hash,
            first_name="Aarav",
            last_name="Mehta",
            role="STUDENT"
        )
        db.add(student1_user)
        db.flush()
        student1_profile = StudentProfile(
            user_id=student1_user.id,
            batch_id=batch.id,
            enrollment_number="ENR-2026-001"
        )
        db.add(student1_profile)

        # Student 2
        student2_user = User(
            email="student2@kanha.local",
            hashed_password=dev_password_hash,
            first_name="Zara",
            last_name="Khan",
            role="STUDENT"
        )
        db.add(student2_user)
        db.flush()
        student2_profile = StudentProfile(
            user_id=student2_user.id,
            batch_id=batch.id,
            enrollment_number="ENR-2026-002"
        )
        db.add(student2_profile)
        db.flush()

        # 4. Create Seed Assignments
        due_tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        assignment1 = Assignment(
            title="Mughal Costume Sketches",
            description="Submit 3 conceptual pencil sketches of modern garments inspired by Mughal architecture motifs.",
            faculty_id=faculty_profile.id,
            deadline=due_tomorrow,
            status="PUBLISHED",
            priority="HIGH",
            category="Fashion Illustration",
            grading_criteria="Creativity (40%), Technical sketch lines (30%), Motif accuracy (30%)"
        )
        db.add(assignment1)
        db.flush()

        # Target the assignment to the batch
        db.add(AssignmentTarget(assignment_id=assignment1.id, batch_id=batch.id))

        due_next_week = datetime.now(timezone.utc) + timedelta(days=7)
        assignment2 = Assignment(
            title="Textile Surface Ornamentation",
            description="Complete research report detailing surface embroidery and fabric manipulations for winter apparel.",
            faculty_id=faculty_profile.id,
            deadline=due_next_week,
            status="DRAFT",
            priority="MEDIUM",
            category="Textiles",
            grading_criteria="Research depth (50%), Manipulation samples (50%)"
        )
        db.add(assignment2)
        db.flush()

        # 5. Create Calendar Events
        event1 = CalendarEvent(
            title="Fashion Illustration Critique",
            description="Open feedback session for Mughal Costume drawings.",
            event_type="CLASS",
            start_time=datetime.now(timezone.utc) + timedelta(hours=2),
            end_time=datetime.now(timezone.utc) + timedelta(hours=4),
            batch_id=batch.id,
            created_by=faculty_user.id
        )
        db.add(event1)

        db.commit()
        print("Database seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
