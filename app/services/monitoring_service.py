
from sqlalchemy.orm import Session

from app.database.models import MonitoringSource, WebsiteScan

from app.monitors.website_monitor import (
    fetch_website_content,
    WebsiteAccessError
)

from app.services.snapshot_service import save_snapshot
from app.services.education_update_extractor import extract_updates


def scan_source(db: Session, source_id: int):

    source = db.query(MonitoringSource).filter(
        MonitoringSource.id == source_id,
        MonitoringSource.active == True
    ).first()

    if not source:
        raise ValueError(
            f"Active monitoring source {source_id} not found"
        )

    scan = WebsiteScan(
        source_id=source.id,
        status="IN_PROGRESS"
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        website_data = fetch_website_content(source.url)

        result = save_snapshot(db, website_data)
        extraction_result = {
            "updates_found": 0,
            "updates": []
        }

        if result["snapshot_saved"]:
            try:
                extraction_result = extract_updates(
                    db=db,
                    source_id=source_id,
                    snapshot_id=result["snapshot_id"],
                    source_url=website_data["url"],
                    content=website_data["content"]
                )

                print("Education updates extracted:")
                print(extraction_result)

            except Exception as extraction_error:
                print(
                    f"Education extraction failed for source "
                    f"{source_id}: {extraction_error}"
                )

        scan.status = "SUCCESS"
        scan.change_detected = result["change_detected"]

        db.commit()

        return {
            "source_id": source.id,
            "source_name": source.source_name,
            "scan_status": scan.status,
            "scan_result": result,
            "extraction_result": extraction_result
        }

    except Exception as exc:

        db.rollback()

        scan = db.query(WebsiteScan).filter(
            WebsiteScan.id == scan.id
        ).first()

        if scan:
            scan.status = "FAILED"
            scan.error_message = str(exc)[:2000]
            db.commit()

        raise
