
from sqlalchemy.sql import func

from app.database.connection import Base

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text
)


class WebsiteSnapshot(Base):

    __tablename__ = "website_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    url = Column(String(1000), nullable=False, index=True)

    title = Column(String(500))

    content = Column(Text, nullable=False)

    content_hash = Column(String(64), nullable=False)

    scan_status = Column(String(30), default="SUCCESS")

    change_detected = Column(String(10), default="NO")

    scanned_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )





class University(Base):

    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False, unique=True)

    country = Column(String(100), nullable=False)

    website_url = Column(String(1000))

    active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    monitoring_sources = relationship(
        "MonitoringSource",
        back_populates="university",
        cascade="all, delete-orphan"
    )


class MonitoringSource(Base):

    __tablename__ = "monitoring_sources"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(
        Integer,
        ForeignKey("universities.id"),
        nullable=False
    )

    source_name = Column(String(255), nullable=False)

    source_type = Column(String(100), nullable=False)

    url = Column(String(1000), nullable=False, unique=True)

    active = Column(Boolean, default=True)

    scan_interval_minutes = Column(Integer, default=360)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    university = relationship(
        "University",
        back_populates="monitoring_sources"
    )


class WebsiteScan(Base):

    __tablename__ = "website_scans"

    id = Column(Integer, primary_key=True, index=True)

    source_id = Column(
        Integer,
        ForeignKey("monitoring_sources.id"),
        nullable=False,
        index=True
    )

    status = Column(String(30), nullable=False)

    change_detected = Column(Boolean, default=False)

    error_message = Column(Text, nullable=True)

    scanned_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    source = relationship("MonitoringSource")


class EducationUpdate(Base):
    __tablename__ = "education_updates"

    id = Column(Integer, primary_key=True, index=True)

    source_id = Column(
        Integer,
        ForeignKey("monitoring_sources.id"),
        nullable=False,
        index=True
    )

    snapshot_id = Column(
        Integer,
        ForeignKey("website_snapshots.id"),
        nullable=True
    )

    category = Column(String(50), nullable=False)
    update_type = Column(String(100), nullable=False)

    title = Column(String(500), nullable=False)

    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    importance = Column(String(20), default="MEDIUM")

    source_url = Column(String(1000), nullable=False)
    evidence_text = Column(Text, nullable=True)

    status = Column(String(30), default="DETECTED")

    detected_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    academic_cycle = Column(String(30), nullable=True)

    applicant_type = Column(String(50), nullable=True)

    deadline = Column(String(50), nullable=True)

    amount = Column(String(100), nullable=True)

    change_type = Column(
        String(50),
        default="NEW_INFORMATION"
    )

    verification_status = Column(
        String(30),
        default="UNVERIFIED"
    )
