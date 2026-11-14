
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import Base, engine, get_db
from app.monitors.website_monitor import (
    fetch_website_content,
    WebsiteAccessError
)
from app.services.snapshot_service import save_snapshot
from app.api.university_controller import router as university_router
from app.api.source_controller import router as source_router
from app.api.monitoring_controller import router as monitoring_router
from app.services.scheduler_service import (
    start_scheduler,
    stop_scheduler
)

from app.api.scan_controller import router as scan_router
from app.api.education_update_controller import router as education_update_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    start_scheduler()

    yield

    stop_scheduler()


app = FastAPI(
    title="Education Intelligence",
    description="AI-powered University Update Monitoring Platform",
    version="1.0.0",
    lifespan=lifespan
)
app.include_router(university_router)
app.include_router(source_router)
app.include_router(monitoring_router)
app.include_router(scan_router)
app.include_router(education_update_router)

@app.get("/")
def home():
    return {
        "message": "Education Intelligence API is running!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {"status": "UP"}


@app.get("/monitor")
def monitor_website(
    url: str,
    db: Session = Depends(get_db)
):
    try:
        website_data = fetch_website_content(url)

        result = save_snapshot(db, website_data)

        return {
            "message": result["message"],
            "snapshot_id": result["snapshot_id"],
            "url": result["url"],
            "title": result["title"],
            "change_detected": result["change_detected"],
            "previous_hash": result["previous_hash"],
            "current_hash": result["current_hash"]
        }

    except WebsiteAccessError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message
        )
