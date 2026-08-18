import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import auth, users, assignments, submissions, issues, chat, google, research, design_studio, portfolio, analytics
from fastapi.staticfiles import StaticFiles
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kanha")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Mount static folder for serving mock Google Doc exports
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Health check endpoint
@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "api_version": "v1"
    }


# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(assignments.router, prefix=f"{settings.API_V1_STR}/assignments", tags=["assignments"])
app.include_router(submissions.router, prefix=f"{settings.API_V1_STR}/submissions", tags=["submissions"])
app.include_router(issues.router, prefix=f"{settings.API_V1_STR}/issues", tags=["issues"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(google.router, prefix=f"{settings.API_V1_STR}/google", tags=["google"])
app.include_router(research.router, prefix=f"{settings.API_V1_STR}/research", tags=["research"])
app.include_router(design_studio.router, prefix=f"{settings.API_V1_STR}/design-studio", tags=["design-studio"])
app.include_router(portfolio.router, prefix=f"{settings.API_V1_STR}/portfolio", tags=["portfolio"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
