
from app.database.models import WebsiteSnapshot
from app.monitors.change_detector import compare_content


def save_snapshot(db, website_data):
    url = website_data["url"]

    # Find the latest saved snapshot for this URL.
    previous_snapshot = (
        db.query(WebsiteSnapshot)
        .filter(WebsiteSnapshot.url == url)
        .order_by(WebsiteSnapshot.id.desc())
        .first()
    )

    # First scan: save the baseline snapshot.
    if previous_snapshot is None:
        snapshot = WebsiteSnapshot(
            url=url,
            title=website_data["title"],
            content=website_data["content"],
            content_hash=website_data["content_hash"],
            scan_status="SUCCESS",
            change_detected="false"
        )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "snapshot_id": snapshot.id,
            "url": url,
            "title": website_data["title"],
            "change_detected": False,
            "previous_hash": None,
            "current_hash": website_data["content_hash"],
            "snapshot_saved": True,
            "message": "Initial snapshot saved"
        }

    # Compare the latest content with the newly fetched content.
    comparison = compare_content(
        previous_snapshot.content,
        website_data["content"]
    )

    # Also consider a title change meaningful.
    title_changed = (
        previous_snapshot.title != website_data["title"]
    )

    change_detected = comparison["changed"] or title_changed

    # No change: do not create another snapshot.
    if not change_detected:
        return {
            "snapshot_id": previous_snapshot.id,
            "url": url,
            "title": previous_snapshot.title,
            "change_detected": False,
            "previous_hash": comparison["old_hash"],
            "current_hash": comparison["new_hash"],
            "snapshot_saved": False,
            "message": "No changes detected. Existing snapshot retained"
        }

    # Change detected: save a new version.
    snapshot = WebsiteSnapshot(
        url=url,
        title=website_data["title"],
        content=website_data["content"],
        content_hash=website_data["content_hash"],
        scan_status="SUCCESS",
        change_detected="true"
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return {
        "snapshot_id": snapshot.id,
        "url": url,
        "title": website_data["title"],
        "change_detected": True,
        "previous_hash": comparison["old_hash"],
        "current_hash": comparison["new_hash"],
        "snapshot_saved": True,
        "message": "Website content changed. New snapshot saved"
    }
