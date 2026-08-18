import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, StudentProfile, DesignProject, Moodboard, MoodboardItem
from app.db.schemas import (
    DesignProjectCreate, DesignProjectOut,
    MoodboardCreate, MoodboardOut,
    MoodboardItemCreate, MoodboardItemOut
)
from app.api.v1.endpoints.auth import get_current_user
from app.core.image_provider import GeminiImageProvider

router = APIRouter()
logger = logging.getLogger("design_studio_endpoints")
image_provider = GeminiImageProvider()

@router.post("/projects", response_model=DesignProjectOut)
def create_project(
    payload: DesignProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new design project for the student."""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create design studio projects."
        )
    
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student profile not found."
        )
        
    project = DesignProject(
        student_id=student.id,
        name=payload.name,
        inspiration_source=payload.inspiration_source,
        fabric_notes=payload.fabric_notes,
        color_palette=payload.color_palette
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/projects", response_model=List[DesignProjectOut])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all design projects belonging to the student."""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students have active Design Studio spaces."
        )
        
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student:
        return []
        
    return db.query(DesignProject).filter(DesignProject.student_id == student.id).all()

@router.get("/projects/{project_id}", response_model=DesignProjectOut)
def get_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves a single design project. Enforces student ownership boundaries."""
    project = db.query(DesignProject).filter(DesignProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this design project."
            )
            
    return project

@router.get("/projects/{project_id}/moodboards", response_model=List[MoodboardOut])
def get_project_moodboards(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all moodboards under a specific project. Enforces ownership."""
    project = db.query(DesignProject).filter(DesignProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this project workspace."
            )
            
    return project.moodboards

@router.post("/moodboards", response_model=MoodboardOut)
def create_moodboard(
    payload: MoodboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new moodboard inside a design project. Enforces student ownership boundaries."""
    project = db.query(DesignProject).filter(DesignProject.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this project workspace."
            )
            
    moodboard = Moodboard(project_id=project.id, name=payload.name)
    db.add(moodboard)
    db.commit()
    db.refresh(moodboard)
    return moodboard

@router.get("/moodboards/{moodboard_id}", response_model=MoodboardOut)
def get_moodboard(
    moodboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves a single moodboard with its items. Enforces ownership boundaries."""
    moodboard = db.query(Moodboard).filter(Moodboard.id == moodboard_id).first()
    if not moodboard:
        raise HTTPException(status_code=404, detail="Moodboard not found.")
        
    project = moodboard.project
    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_430_ACCESS_DENIED if hasattr(status, "HTTP_430_ACCESS_DENIED") else 403,
                detail="Access denied: You do not own this moodboard workspace."
            )
            
    return moodboard

@router.post("/moodboards/{moodboard_id}/items", response_model=MoodboardItemOut)
def add_moodboard_item(
    moodboard_id: int,
    payload: MoodboardItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a item to a moodboard (AI concept, sketch reference, or third-party reference).

    For third-party reference images, source_url and source_title are validated to prevent claim of ownership.
    """
    moodboard = db.query(Moodboard).filter(Moodboard.id == moodboard_id).first()
    if not moodboard:
        raise HTTPException(status_code=404, detail="Moodboard not found.")
        
    project = moodboard.project
    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this moodboard workspace."
            )
            
    # Source attribution verification: third-party images must have title and url
    if payload.item_type == "REFERENCE_IMAGE":
        if not payload.source_url or not payload.source_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference images require clear source URL and title attribution."
            )
            
    item = MoodboardItem(
        moodboard_id=moodboard.id,
        item_type=payload.item_type,
        file_url=payload.file_url,
        caption=payload.caption,
        source_url=payload.source_url,
        source_title=payload.source_title,
        is_ai_generated=payload.is_ai_generated,
        position_x=payload.position_x,
        position_y=payload.position_y
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.post("/concept")
def generate_fashion_concept(
    silhouette: str = Form(...),
    fabric: str = Form(...),
    colors: str = Form(...),
    embroidery: str = Form(...),
    moodboard_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates an AI fashion concept based on student selections.

    Appends generated concept to moodboard if moodboard_id is supplied.
    """
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Concept generation is restricted to student workspaces."
        )
        
    if moodboard_id:
        moodboard = db.query(Moodboard).filter(Moodboard.id == moodboard_id).first()
        if not moodboard:
            raise HTTPException(status_code=404, detail="Moodboard not found.")
        project = moodboard.project
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this moodboard."
            )
            
    prompt = (
        f"A detailed fashion illustration front view of a modern {silhouette} "
        f"made of {fabric} in {colors} with {embroidery} motifs. "
        f"Clean background, fashion design studio concept board."
    )
    
    file_url = image_provider.generate_concept(prompt, silhouette)
    
    # Auto-tag and save to moodboard if ID is provided
    if moodboard_id:
        item = MoodboardItem(
            moodboard_id=moodboard_id,
            item_type="AI_CONCEPT",
            file_url=file_url,
            caption=f"AI Generated: {silhouette} | {fabric}",
            is_ai_generated=True
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {
            "status": "success",
            "file_url": file_url,
            "prompt": prompt,
            "moodboard_item_id": item.id,
            "is_ai_generated": True
        }
        
    return {
        "status": "success",
        "file_url": file_url,
        "prompt": prompt,
        "is_ai_generated": True
    }

@router.post("/sketch/analyze")
async def analyze_sketch(
    file: UploadFile = File(...),
    moodboard_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Performs multimodal analysis of uploaded sketch.

    Provides material recommendations.
    """
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sketch analysis is restricted to student workspaces."
        )
        
    if moodboard_id:
        moodboard = db.query(Moodboard).filter(Moodboard.id == moodboard_id).first()
        if not moodboard:
            raise HTTPException(status_code=404, detail="Moodboard not found.")
        project = moodboard.project
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or project.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_430_ACCESS_DENIED if hasattr(status, "HTTP_430_ACCESS_DENIED") else 403,
                detail="Access denied: You do not own this moodboard."
            )
            
    content = await file.read()
    analysis_result = image_provider.analyze_sketch(content)
    
    # Save the sketch itself as an item on the moodboard if requested
    if moodboard_id:
        # Mock file url saving (in production, upload to GCS/S3)
        import uuid
        filename = f"sketch_{uuid.uuid4().hex[:8]}.jpg"
        static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "static", "sketches"
        )
        os.makedirs(static_dir, exist_ok=True)
        filepath = os.path.join(static_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)
            
        item = MoodboardItem(
            moodboard_id=moodboard_id,
            item_type="SKETCH",
            file_url=f"/static/sketches/{filename}",
            caption=f"Uploaded Sketch: {analysis_result['silhouette']}"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        analysis_result["moodboard_item_id"] = item.id
        
    return analysis_result
