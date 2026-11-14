
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.monitoring_service import scan_source
from app.monitors.website_monitor import WebsiteAccessError

router = APIRouter(
    prefix="/monitoring",
    tags=["Website Monitoring"]
)


@router.post("/scan/{source_id}")
def scan_website(
    source_id: int,
    db: Session = Depends(get_db)
):

    try:
        return scan_source(db, source_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except WebsiteAccessError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message
        )
