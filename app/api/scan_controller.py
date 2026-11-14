
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import WebsiteScan

router = APIRouter(
    prefix="/scans",
    tags=["Scan History"]
)


@router.get("/")
def get_scan_history(
    db: Session = Depends(get_db)
):
    return (
        db.query(WebsiteScan)
        .order_by(WebsiteScan.id.desc())
        .limit(100)
        .all()
    )


@router.get("/source/{source_id}")
def get_source_scan_history(
    source_id: int,
    db: Session = Depends(get_db)
):
    return (
        db.query(WebsiteScan)
        .filter(WebsiteScan.source_id == source_id)
        .order_by(WebsiteScan.id.desc())
        .limit(100)
        .all()
    )
