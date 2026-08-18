import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, StudentProfile, PortfolioItem
from app.db.schemas import PortfolioItemCreate, PortfolioItemOut
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("portfolio_endpoints")

@router.get("/items", response_model=List[PortfolioItemOut])
def get_portfolio_items(
    student_id: Optional[int] = Query(None, description="Faculty viewing specific student portfolio"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves portfolio items. Enforces privacy boundaries."""
    if current_user.role == "STUDENT":
        # A student can only view their own portfolio
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=403, detail="Student profile not found.")
        
        # If student_id is passed, it must match the logged-in student's id
        if student_id is not None and student_id != student.id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot view another student's portfolio.")
        
        target_student_id = student.id
    else:
        # Faculty/Admin can view portfolios
        if student_id is None:
            raise HTTPException(status_code=400, detail="student_id parameter is required for faculty/admin.")
        target_student_id = student_id

    items = db.query(PortfolioItem).filter(PortfolioItem.student_id == target_student_id).all()
    return items

@router.post("/items", response_model=PortfolioItemOut)
def create_portfolio_item(
    payload: PortfolioItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a new portfolio item to the student's showcase."""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create/upload portfolio items."
        )
    
    student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=403, detail="Student profile not found.")

    item = PortfolioItem(
        student_id=student.id,
        title=payload.title,
        category=payload.category,
        description=payload.description,
        file_url=payload.file_url
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/items/{item_id}")
def delete_portfolio_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a portfolio item. Enforces strict ownership checks."""
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found.")
    
    # Ownership boundary validation
    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student or item.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_430_ACCESS_DENIED if hasattr(status, "HTTP_430_ACCESS_DENIED") else 403,
                detail="Access denied: You do not own this portfolio item."
            )
    else:
        # Non-students cannot delete student portfolio items
        raise HTTPException(status_code=403, detail="Only students can manage/delete their own portfolio items.")

    db.delete(item)
    db.commit()
    return {"detail": "Portfolio item deleted successfully."}

@router.get("/export/pdf", response_class=HTMLResponse)
def export_portfolio_pdf(
    student_id: Optional[int] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Generates a print-ready HTML page containing all portfolio items grouped by category.
    Includes styled cover page and page breaks for print-to-PDF output.
    """
    if token:
        from app.core.security import verify_token
        user_id_str = verify_token(token)
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid token")
        current_user = db.query(User).filter(User.id == int(user_id_str)).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=401, detail="Authentication token required")

    if current_user.role == "STUDENT":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=403, detail="Student profile not found.")
        target_student_id = student.id
    else:
        if student_id is None:
            raise HTTPException(status_code=400, detail="student_id is required.")
        target_student_id = student_id

    student_profile = db.query(StudentProfile).filter(StudentProfile.id == target_student_id).first()
    if not student_profile:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    
    student_name = f"{student_profile.user.first_name or ''} {student_profile.user.last_name or ''}".strip() or student_profile.user.email
    items = db.query(PortfolioItem).filter(PortfolioItem.student_id == target_student_id).all()

    # Group items by category
    categories = {}
    for item in items:
        cat = item.category.replace("_", " ").title()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    # Compile the HTML booklet
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fashion Design Portfolio - {student_name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Playfair+Display:ital,wght@0,600;1,400&display=swap');
            
            body {{
                font-family: 'Outfit', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #ffffff;
                color: #1A1A1A;
            }}
            .page {{
                width: 210mm;
                min-height: 297mm;
                padding: 20mm;
                margin: 10mm auto;
                background: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                box-sizing: border-box;
                page-break-after: always;
                position: relative;
            }}
            @media print {{
                body {{
                    background: none;
                }}
                .page {{
                    margin: 0;
                    box-shadow: none;
                    page-break-after: always;
                }}
            }}
            
            /* Cover Page Styling */
            .cover-container {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                height: 100%;
                border: 2px solid #C9A65B;
                padding: 40px;
                box-sizing: border-box;
                text-align: center;
            }}
            .cover-title {{
                font-family: 'Playfair Display', serif;
                font-size: 48px;
                font-weight: 800;
                color: #0B132B;
                margin-top: 100px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }}
            .cover-subtitle {{
                font-size: 18px;
                color: #C9A65B;
                text-transform: uppercase;
                letter-spacing: 0.2em;
                margin-bottom: 120px;
            }}
            .cover-meta {{
                margin-top: auto;
                font-size: 16px;
                color: #555;
            }}
            .cover-meta strong {{
                color: #0B132B;
            }}
            
            /* Category Page Styling */
            .category-title {{
                font-family: 'Playfair Display', serif;
                font-size: 28px;
                color: #0B132B;
                border-bottom: 2px solid #C9A65B;
                padding-bottom: 8px;
                margin-bottom: 30px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .item-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }}
            .item-card {{
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                overflow: hidden;
                background: #FAF8F5;
            }}
            .item-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
                background-color: #F1F5F9;
            }}
            .item-details {{
                padding: 15px;
            }}
            .item-name {{
                font-size: 16px;
                font-weight: 600;
                color: #0B132B;
                margin: 0 0 8px 0;
            }}
            .item-desc {{
                font-size: 13px;
                color: #4A5568;
                margin: 0;
                line-height: 1.4;
            }}
        </style>
    </head>
    <body>
        <!-- Cover Page -->
        <div class="page" style="display: flex; flex-direction: column; justify-content: center;">
            <div class="cover-container">
                <div class="cover-title">Fashion Portfolio</div>
                <div class="cover-subtitle">Kanha Design Academy</div>
                
                <div class="cover-meta">
                    <p>Prepared by:</p>
                    <p style="font-size: 24px; font-weight: 600; margin: 5px 0 20px 0;">{student_name}</p>
                    <p>Enrollment: <strong>{student_profile.enrollment_number}</strong></p>
                    <p>Date Generated: <strong>{datetime_now_str()}</strong></p>
                </div>
            </div>
        </div>
    """

    # Add items by category
    for cat_name, cat_items in categories.items():
        html_content += f"""
        <div class="page">
            <div class="category-title">{cat_name}</div>
            <div class="item-grid">
        """
        for item in cat_items:
            # Handle static path resolving
            file_url = item.file_url
            if file_url.startswith("/"):
                file_url = "http://localhost:8000" + file_url
            
            html_content += f"""
                <div class="item-card">
                    <img class="item-image" src="{file_url}" alt="{item.title}">
                    <div class="item-details">
                        <h4 class="item-name">{item.title}</h4>
                        <p class="item-desc">{item.description or ''}</p>
                    </div>
                </div>
            """
        html_content += """
            </div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def datetime_now_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%B %d, %Y")
