
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import University, MonitoringSource
from app.api.schemas import (
    MonitoringSourceCreate,
    MonitoringSourceResponse
)

router = APIRouter(
    prefix="/sources",
    tags=["Monitoring Sources"]
)


@router.post("/", response_model=MonitoringSourceResponse, status_code=201)
def create_source(
    source: MonitoringSourceCreate,
    db: Session = Depends(get_db)
):
    university = db.query(University).filter(
        University.id == source.university_id
    ).first()

    if not university:
        raise HTTPException(
            status_code=404,
            detail="University not found"
        )

    existing = db.query(MonitoringSource).filter(
        MonitoringSource.url == str(source.url)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Monitoring source URL already registered"
        )

    new_source = MonitoringSource(
        university_id=source.university_id,
        source_name=source.source_name,
        source_type=source.source_type,
        url=str(source.url),
        scan_interval_minutes=source.scan_interval_minutes
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source


@router.get("/", response_model=list[MonitoringSourceResponse])
def get_sources(db: Session = Depends(get_db)):
    return db.query(MonitoringSource).all()


@router.get("/{source_id}", response_model=MonitoringSourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    source = db.query(MonitoringSource).filter(
        MonitoringSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(
            status_code=404,
            detail="Monitoring source not found"
        )

    return source
