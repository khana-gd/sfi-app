from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.db.schemas import Token, UserOut
from app.core.security import verify_password, create_access_token
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


from app.core.tickets import ticket_store

@router.post("/ws-ticket")
def get_websocket_ticket(current_user: User = Depends(get_current_user)):
    ticket = ticket_store.generate_ticket(user_id=current_user.id, role=current_user.role)
    return {"ticket": ticket}


from pydantic import BaseModel
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models import StudentProfile

class GoogleTokenIn(BaseModel):
    id_token: str


@router.post("/google", response_model=Token)
def google_login(
    payload: GoogleTokenIn,
    db: Session = Depends(get_db)
):
    from google.oauth2 import id_token
    from google.auth.transport import requests
    
    # Check if Google client ID is configured. If not, raise an error telling them to add it.
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Sign-In is not configured on this server. GOOGLE_CLIENT_ID must be set in the .env configuration."
        )

    try:
        # Verify the Google ID Token locally using google-auth library's signature verification
        idinfo = id_token.verify_oauth2_token(
            payload.id_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google ID Token: {str(e)}"
        )
        
    # Check email_verified in the payload before auto-registering
    if not idinfo.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified"
        )
        
    email = idinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not present in Google ID Token claims"
        )
        
    # Look up user in db
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Auto-registration checks:
        email_domain = email.split("@")[-1].lower()
        allowed_domain = settings.SFI_EMAIL_DOMAIN.lower()
        
        # Determine if active or pending based on domain match
        is_active = (email_domain == allowed_domain)
        
        import secrets
        random_password = secrets.token_urlsafe(32)
        hashed_password = get_password_hash(random_password)
        
        first_name = idinfo.get("given_name", "Google")
        last_name = idinfo.get("family_name", "User")
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role="STUDENT",
            is_active=is_active
        )
        db.add(user)
        db.flush()
        
        # Initialize student profile
        student_profile = StudentProfile(
            user_id=user.id,
            enrollment_number=f"ENR-GGL-{user.id:04d}-{secrets.token_hex(4).upper()}"
        )
        db.add(student_profile)
        db.commit()
        db.refresh(user)
        
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your registration was successful, but your account is pending administrator approval since you signed in using a non-institute email."
            )
    else:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your account is inactive. If this is a new sign-in from a non-institute email, it is pending administrator approval."
            )
            
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }


@router.post("/google-mock", response_model=Token)
def google_mock_login(
    payload: GoogleTokenIn,
    db: Session = Depends(get_db)
):
    # Gate the dev bypass behind ENVIRONMENT=development check
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development bypass is disabled in this environment."
        )
    
    # In development mode, we bypass signature verification and use the input as mock email
    email = payload.id_token
    if "@" not in email:
        email = f"{email}@{settings.SFI_EMAIL_DOMAIN}"
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Auto-registration checks (similar to real flow, but for mock emails)
        email_domain = email.split("@")[-1].lower()
        allowed_domain = settings.SFI_EMAIL_DOMAIN.lower()
        is_active = (email_domain == allowed_domain)
        
        import secrets
        random_password = secrets.token_urlsafe(32)
        hashed_password = get_password_hash(random_password)
        
        username = email.split("@")[0]
        first_name = username.capitalize()
        last_name = "MockUser"
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role="STUDENT",
            is_active=is_active
        )
        db.add(user)
        db.flush()
        
        # Initialize student profile
        student_profile = StudentProfile(
            user_id=user.id,
            enrollment_number=f"ENR-MOCK-{user.id:04d}-{secrets.token_hex(4).upper()}"
        )
        db.add(student_profile)
        db.commit()
        db.refresh(user)
        
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your registration was successful, but your account is pending administrator approval since you signed in using a non-institute email."
            )
    else:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your account is inactive. If this is a new sign-in from a non-institute email, it is pending administrator approval."
            )
        
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

