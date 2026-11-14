
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import University
from app.api.schemas import UniversityCreate, UniversityResponse

router = APIRouter(
    prefix="/universities",
    tags=["Universities"]
)


@router.post("/", response_model=UniversityResponse, status_code=201)
def create_university(
    university: UniversityCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(University).filter(
        University.name == university.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="University already exists"
        )

    new_university = University(
        name=university.name,
        country=university.country,
        website_url=(
            str(university.website_url)
            if university.website_url else None
        )
    )

    db.add(new_university)
    db.commit()
    db.refresh(new_university)

    return new_university


@router.get("/", response_model=list[UniversityResponse])
def get_universities(db: Session = Depends(get_db)):
    return db.query(University).all()


@router.get("/{university_id}", response_model=UniversityResponse)
def get_university(
    university_id: int,
    db: Session = Depends(get_db)
):
    university = db.query(University).filter(
        University.id == university_id
    ).first()

    if not university:
        raise HTTPException(
            status_code=404,
            detail="University not found"
        )

    return university
