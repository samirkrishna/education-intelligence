
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import EducationUpdate

from app.database.models import MonitoringSource, WebsiteSnapshot
from app.services.education_update_extractor import extract_updates

router = APIRouter(
    prefix="/education-updates",
    tags=["Education Updates"]
)


@router.get("/")
def get_education_updates(
    source_id: int | None = None,
    category: str | None = None,
    importance: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(EducationUpdate)

    if source_id is not None:
        query = query.filter(
            EducationUpdate.source_id == source_id
        )

    if category:
        query = query.filter(
            EducationUpdate.category == category.upper()
        )

    if importance:
        query = query.filter(
            EducationUpdate.importance == importance.upper()
        )

    updates = (
        query.order_by(EducationUpdate.detected_at.desc())
        .limit(100)
        .all()
    )

    return {
        "total": len(updates),
        "updates": [
            {
                "id": update.id,
                "source_id": update.source_id,
                "snapshot_id": update.snapshot_id,
                "category": update.category,
                "update_type": update.update_type,
                "title": update.title,
                "previous_value": update.previous_value,
                "new_value": update.new_value,
                "importance": update.importance,
                "source_url": update.source_url,
                "evidence_text": update.evidence_text,
                "status": update.status,
                "detected_at": update.detected_at
            }
            for update in updates
        ]
    }


@router.post("/reprocess/{source_id}")
def reprocess_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    source = (
        db.query(MonitoringSource)
        .filter(MonitoringSource.id == source_id)
        .first()
    )

    if not source:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Monitoring source not found"
        )

    snapshot = (
        db.query(WebsiteSnapshot)
        .filter(WebsiteSnapshot.url == source.url)
        .order_by(WebsiteSnapshot.id.desc())
        .first()
    )

    if not snapshot:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="No snapshot found for this source"
        )

    result = extract_updates(
        db=db,
        source_id=source_id,
        snapshot_id=snapshot.id,
        source_url=snapshot.url,
        content=snapshot.content
    )

    return {
        "source_id": source_id,
        "source_name": source.source_name,
        "snapshot_id": snapshot.id,
        "reprocessing_status": "SUCCESS",
        "extraction_result": result
    }
